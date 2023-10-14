from typing import Annotated, List
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import FileResponse

import dotenv
import os
import openai 
from pymongo import MongoClient

from models import User, Book, Section, Current

from PIL import Image
import io
import requests


dotenv.load_dotenv()

openai_key = os.getenv("OPENAI_KEY")

openai.api_key = openai_key

mongo_url = os.getenv("MONGO_URL")

client = MongoClient(mongo_url)

db = client['main']
user_col = db['users']
currentread_col = db['reads']
book_col = db['books']
section_col = db['sections']

IMAGES_FOLDER = os.getenv("IMAGES_FOLDER")
TEXT_FOLDER = os.getenv("TEXT_FOLDER")

def gptNaturalSplit(text_chunk: str, chunk_word_count: int) -> List[str]:
    messages = [
        {
            "role": "system",
            "content": f"You are to split the text into sections. Each section should be about {chunk_word_count} words long. Indicate splits putting a | character in between sections. You should not modify the text in any way. If there is only one section place a | character at the end of the string, but if there is more than one, please place a | character in between each section."
        }
    ]
    messages.append({
        "role": "user",
        "content": text_chunk
    })
    chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, max_tokens=1000, temperature=0.7)
    output = chat.choices[0].message.content
    sections = output.split("|")
    return sections[:-1]

def genArt(text_chunk:str) -> bytes:
    messages = [
        {
            "role": "system",
            "content": f"You are to write a description of any given passage that could be translated to a visual piece of art. Your reponse must be 1000 characters or less."
        }
    ]
    messages.append({
        "role": "user",
        "content": text_chunk
    })
    chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, max_tokens=1000)
    output = chat.choices[0].message.content
    output = output[:1000]
    response = openai.Image.create(
        prompt = output, 
        n = 1,
        size = "1024x1024",
    )
    img_url = response['data'][0]['url']
    r = requests.get(img_url, allow_redirects = True)
    return r.content

app = FastAPI()

@app.get("/section/{section_id}")
def get_section(section_id: str) -> Section:
    section = section_col.find_one({"section_id": section_id})
    return section

@app.post("/login/")
def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    res = list(user_col.find({"username": username, "password_hash": password}))
    print(res)
    if len(res) == 1:
        return res[0]['user_id']
    else:
        return False

@app.post("/upload_book/")
def upload_book(title: Annotated[str, Form()], author: Annotated[str, Form()], description: Annotated[str, Form()], genre: Annotated[str, Form()], user_id: Annotated[str, Form()], cover_bytes: UploadFile, text_bytes: UploadFile):
    user = user_col.find_one({"user_id": user_id})
    print(user)
    if user['admin']:
        # write cover bytes to file
        book = Book(title=title, author=author, description=description, genre=genre)

        with open(f"{IMAGES_FOLDER}/{book.book_id}.jpg", "wb") as f:
            f.write(cover_bytes.file.read())
        
        # write text bytes to file
        with open(f"{TEXT_FOLDER}/{book.book_id}.txt", "wb") as f:
            f.write(text_bytes.file.read())

        book_col.insert_one(book.dict())
        return True
    else:
        return False

@app.post("/signup/")
def signup(email: Annotated[str, Form()], username: Annotated[str, Form()], password: Annotated[str, Form()]):
    user = User(username = username, email = email, password_hash = password, admin = False)
    user_col.insert_one(user.dict())
    return user.user_id

@app.get("/start_read/")
def start_read(book_id: str = Form(...), user_id: str = Form(...)) -> Section:
    cr = list(currentread_col.find({"user_id": user_id, "book_id": book_id}))

    if len(cr) >= 1:
        return section_col.find_one({"section_id": cr[0]['section_id']})

    # make the sections here
    with open(f"{TEXT_FOLDER}/{book_id}.txt", "r") as f:
        text = f.read()
    
    init_para = text[:1800]

    text_sections = gptNaturalSplit(init_para, 60)

    sections = []

    print(text_sections)

    dist_count = 0
    
    if (text.endswith(text_sections[-1]) or text.endswith(text_sections[-1].strip())) and text_sections[-1] != "":
        text_sections.append("") 
    
    print(text_sections)

    for i in range(min(len(text_sections)-1, 5)):
        old = dist_count
        dist_count+=len(text_sections[i])
        section = Section(book_id=book_id, user_id=user_id, start=old, end=dist_count)
        section_col.insert_one(section.dict())
        sections.append(section)

        print("start art")

        image_data = genArt(text_sections[i])
        image_stream = io.BytesIO(image_data)
        image = Image.open(image_stream)
        image.save(f"{IMAGES_FOLDER}/{section.section_id}.jpg",  optimize=True, quality=10)

        print("end art")

    current = Current(user_id=user_id, book_id=book_id, section_id=sections[0].section_id)
    currentread_col.insert_one(current.dict())

    return sections[0]

@app.get("/section_text/{section_id}")
def get_section_text(section_id: str) -> str:
    section = section_col.find_one({"section_id": section_id})
    with open(f"{TEXT_FOLDER}/{section['book_id']}.txt", "r") as f:
        text = f.read()
    return text[section['start']:section['end']]

@app.get("/get_current/{user_id}")
def get_current(user_id: str) -> List[Current]:
    current = list(currentread_col.find({"user_id": user_id}))
    return current

@app.post("/update_current/")
def update_current(user_id: str, book_id: str, section_id: str):
    currentread_col.update_one({"user_id": user_id}, {"book_id": book_id, "section_id": section_id})

@app.get("/next_section/{section_id}")
def next_section(section_id: str) -> Section:
    section = section_col.find_one({"section_id": section_id})
    next_section = section_col.find_one({"book_id": section['book_id'], "start": section['end']})

    # attempt to generate art for another section

    sections = section_col.find({"book_id": section['book_id']})
    latest_section = sections[0]
    for s in sections:
        if s['start'] > latest_section['start']:
            latest_section = s
    new_start = latest_section['end']+1
    with open(f"{TEXT_FOLDER}/{section['book_id']}.txt", "r") as f:
        text = f.read()
    section_text = gptNaturalSplit(text[new_start:new_start+1800], 60)[0]

    section = Section(book_id=next_section['book_id'], user_id=next_section['user_id'], start=new_start, end=new_start+len(section_text))
    section_col.insert_one(section.dict())

    print("start art")

    image_data = genArt(section_text)
    image_stream = io.BytesIO(image_data)
    image = Image.open(image_stream)
    image.save(f"{IMAGES_FOLDER}/{section.section_id}.jpg",  optimize=True, quality=10)

    return next_section

@app.get("/get_section_image/{section_id}")
def get_section_image(section_id: str) -> bytes:
    return FileResponse(f"{IMAGES_FOLDER}/{section_id}.jpg")


@app.get("/get_book_image/{book_id}")
def get_book_image(book_id: str) -> bytes:
    return FileResponse(f"{IMAGES_FOLDER}/{book_id}.jpg")

@app.get("/get_books/")
def get_books() -> List[Book]:
    books = list(book_col.find({}))
    return books

@app.get("/get_books/{genre}")
def get_book(genre: str) -> List[Book]:
    books = list(book_col.find({"genre": genre}))
    return books

@app.get("/get_genres/")
def get_genres() -> List[str]:
    genres = list(book_col.distinct("genre"))
    return genres