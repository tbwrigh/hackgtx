import re
from cohere import Client
import dotenv
import os
import openai
import requests

from threading import Thread

import uuid

dotenv.load_dotenv()

cohere_key = os.getenv("COHERE_KEY")
co = Client(cohere_key)

openai_key = os.getenv("OPENAI_KEY")
openai.api_key = openai_key

IMAGES_FOLDER = "images"

def preprocess_text(text):
    text = text.replace("\r\n", "\n")
    paragraphs = re.split(r'\n{2,}', text)

    true_paragraphs = []

    for paragraph in paragraphs:
        sentences = re.split(r'\.|\!|\?|\;', paragraph) 
        if len(sentences) < 6:
            continue

        avg_sentence_length = sum([len(sentence) for sentence in sentences]) / len(sentences)
        if avg_sentence_length < 15:
            continue         
        
        true_paragraphs.append(paragraph)
    
    original_order = true_paragraphs.copy()

    true_paragraphs = sorted(true_paragraphs, key=lambda x: len(x), reverse=True)
    true_paragraphs = true_paragraphs[:21]

    true_paragraphs = sorted(true_paragraphs, key=lambda x: original_order.index(x))
    return true_paragraphs

def genArt(text, name):
    try:
        reply = co.summarize(text = text, additional_command="Extract all the meaningful descriptions of the scene set by the paragraph.", length="medium", extractiveness="high")
        reply=reply.summary
        reply = reply[:900]
        response = openai.Image.create(
            prompt = "In an water color realism style depict the scene described by the following: " + reply, 
            n = 1,
            size = "1024x1024",
        )
        img_url = response['data'][0]['url']
        r = requests.get(img_url, allow_redirects = True)
        # save file to name
        open(f"{IMAGES_FOLDER}/{name}.png", "wb").write(r.content)
        return 0
    except:
        return -1

def process_text(text, name):
    paragraphs = preprocess_text(text)

    delta = 0

    for i in range(len(paragraphs)):
        delta += genArt(paragraphs[i], f"{name}-{i+delta}")
    
from pymongo import MongoClient

mongo_url = os.getenv("MONGO_URL")
client = MongoClient(mongo_url)

db = client['main']
book_col = db['books']

from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI()

app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/covers", StaticFiles(directory="covers"), name="covers")

templates = Jinja2Templates(directory="templates")

COVERS_FOLDER = "covers"
TEXT_FOLDER = "text"

@app.post("/upload/")
def upload(text: UploadFile, cover: UploadFile, title: str = Form(...), author: str = Form(...)):
    name = str(uuid.uuid4())

    with open(f"{COVERS_FOLDER}/{name}.jpg", "wb") as f:
        f.write(cover.file.read())
    
    # write text bytes to file
    with open(f"{TEXT_FOLDER}/{name}.txt", "wb") as f:
        book_text = text.file.read()
        f.write(book_text)
        t = Thread(target=process_text, args=(book_text.decode("utf-8"), name))
        t.start()
        
    book = {
        "book_id": name,
        "title": title,
        "author": author,
        "cover": f"images/{name}-0.png",
        "text": name
    }

    book_col.insert_one(book)

    return {"success": True}


@app.get("/")
def root(request: Request):

    book_data = []

    for book in book_col.find():
        # find num images in images folder based on they are prefixed with book_id
        num_images = len([name for name in os.listdir(IMAGES_FOLDER) if book['book_id'] in name])

        book_data.append({
            "book_id": book['book_id'],
            "title": book['title'],
            "author": book['author'],
            "num_images": num_images
        })


    return templates.TemplateResponse("index.html", {"request": request, "books": book_data})

@app.get("/book/{book_id}")
def book(request: Request, book_id: str):
    book = book_col.find_one({"book_id": book_id})

    num_images = len([name for name in os.listdir(IMAGES_FOLDER) if book['book_id'] in name])

    return templates.TemplateResponse("book.html", {"request": request, "book": book, "num_images": num_images})

import requests

@app.post("/upload_easy/")
def upload_easy(gutenburg_url: str = Form(...)):
    # if url is not in form of https://www.gutenberg.org/ebooks/number
    if not (gutenburg_url.startswith("https://www.gutenberg.org/ebooks/") or gutenburg_url.startswith("http://www.gutenberg.org/ebooks/")):
        return RedirectResponse(url="/", status_code=303)

    # extract author and title
    page = requests.get(gutenburg_url)
    page_text = page.text
    page_lines = page_text.split("\n")

    author = "No author available."
    title = "No title available."

    next_line = False

    for line in page_lines:
        if "itemprop=\"creator\">" in line:
            author = line.split(">")[1].split("<")[0]
        if "itemprop=\"headline\">" in line:
            next_line = True
        elif next_line:
            title = line
            next_line = False

    # extract number
    book_id = gutenburg_url.split("/")[-1]

    print(book_id)

    # get the cover
    cover_url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.cover.medium.jpg"
    cover_bytes = requests.get(cover_url).content

    # get the text
    text_url = f"https://www.gutenberg.org/ebooks/{book_id}.txt.utf-8"
    text_bytes = requests.get(text_url).content

    # send to backend
    backend_url = "http://127.0.0.1:8000/upload/"

    data = {
        "title": title,
        "author": author,
    }

    files = {
        "cover": cover_bytes,
        "text": text_bytes,
    }

    requests.post(backend_url, data=data, files=files, allow_redirects=True)

    return RedirectResponse(url="/", status_code=303)

@app.get("/upload_easy/")
def upload_easy_get(request: Request):
    return templates.TemplateResponse("upload_easy.html", {"request": request})