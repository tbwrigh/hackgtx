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

def process_text(text, name):
    paragraphs = preprocess_text(text)

    for i in range(len(paragraphs)):
        genArt(paragraphs[i], f"{name}-{i}")
    
from pymongo import MongoClient

mongo_url = os.getenv("MONGO_URL")
client = MongoClient(mongo_url)

db = client['main']
book_col = db['books']

from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()

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

    for book in book_col.find():
        print(book)

    return templates.TemplateResponse("index.html", {"request": request})