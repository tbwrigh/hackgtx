from typing import Annotated, List
from fastapi import FastAPI, Form, File

import dotenv
import os
import openai 
from pymongo import MongoClient

from models import User, Book, Section, Current

from PIL import Image
import io


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
            "content": f"You are to split the text into sections. Each section should be about {chunk_word_count} words long. Indicate splits putting a | character in between sections."
        }
    ]
    messages.append({
        "role": "user",
        "content": text_chunk
    })
    chat = openai.CreateCompletion.create(model="gpt-3.5-turbo", messages=messages, max_tokens=1000)
    output = chat.choices[0].message.content
    sections = output.split("|")
    return sections[:-1]

def genArt(text_chunk:str) -> bytes:
    messages = [
        {
            "role": "system",
            "content": f"You are to write a description of any given passage that could be translated to a visual piece of art."
        }
    ]
    messages.append({
        "role": "user",
        "content": text_chunk
    })
    chat = openai.CreateCompletion.create(model="gpt-3.5-turbo", messages=messages, max_tokens=1000)
    output = chat.choices[0].message.content
    response = openai.Image.create(
        prompt = output, 
        n = 1,
        size = "1024x1024",
    )
    img_url = response['data'][0]['url']
    r = requests.get(img_url, allow_redirects = True)
    return r.content

app = FastAPI()

@app.get("/sectiond/{section_id}")
def get_section(section_id: str) -> Section:
    section = section_col.find_one({"section_id": section_id})
    return section

@app.post("/login/")
def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    res = user_col.find({"username": username, "password": password})
    if len(res) == 1:
        return res.user_id
    else:
        return False

@app.post("/upload_book/")
def upload_book(title: Annotated[str, Form()], author: Annotated[str, Form()], description: Annotated[str, Form()], genre: Annotated[str, Form()], user_id: Annotated[str, Form()], cover_bytes: Annotated[bytes, File()], text_bytes: Annotated[bytes, File()]):
    user = user_col.find_one({"user_id": user_id})
    if user.admin:
        # write cover bytes to file
        book = Book(title=title, author=author, description=description, genre=genre)

        with open(f"{IMAGES_FOLDER}/{book.book_id}.jpg", "wb") as f:
            f.write(cover_bytes)
        
        # write text bytes to file
        with open(f"{TEXT_FOLDER}/{book.book_id}.txt", "wb") as f:
            f.write(text_bytes)

        book_col.insert_one(book)
        return True
    else:
        return False

@app.post("/signup/")
def signup(email: Annotated[str, Form()], username: Annotated[str, Form()], password: Annotated[str, Form()]):
    user = User(username = username, email = email, password_hash = password, admin = False)
    user_col.insert_one(user.dict())
    return user.user_id

@app.get("/start_read/")
def start_read(book_id: str, user_id: str) -> Section:
    book = book_col.find_one({"book_id": book_id})

    # make the sections here
    with open(f"{TEXT_FOLDER}/{book_id}.txt", "r") as f:
        text = f.read()
    
    init_para = text[:1800]

    text_sections = gptNaturalSplit(init_para, 60)

    sections = []

    dist_count = 0
    for i in range(len(text_sections)):
        old = dist_count
        dist_count+=len(text_sections[i])
        section = Section(book_id=book_id, user_id=user_id, start=old, end=dist_count)
        section_col.insert_one(section)
        sections.append(section.section_id)

        image_data = genArt(text_sections[i])
        image_stream = io.BytesIO(image_data)
        image = Image.open(image_stream)
        image.save(f"{IMAGES_FOLDER}/{section.section_id}.jpg",  optimize=True, quality=10)

    return sections[0].section_id

@app.get("/section_text/{section_id}")
def get_section_text(section_id: str) -> str:
    section = section_col.find_one({"section_id": section_id})
    book = book_col.find_one({"book_id": section.book_id})
    with open(f"{TEXT_FOLDER}/{book.book_id}.txt", "r") as f:
        text = f.read()
    return text[section.start:section.end]

@app.get("/get_current/")
def get_current(user_id: str) -> List[Current]:
    current = list(currentread_col.find({"user_id": user_id}))
    return current

@app.post("/update_current/")
def update_current(user_id: str, book_id: str, section_id: str):
    currentread_col.update_one({"user_id": user_id}, {"book_id": book_id, "section_id": section_id})
