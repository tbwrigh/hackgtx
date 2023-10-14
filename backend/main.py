from typing import Annotated
from fastapi import FastAPI, Form, File, UploadFile

import dotenv
import os
import openai 
from pymongo import MongoClient

from models import User, Book, Section, Current, BookUpload

dotenv.load_dotenv()

openai_key = os.getenv("OPENAI_KEY")

openai.api_key = openai_key

mongo_url = os.getenv("MONGO_URL")

client = MongoClient(mongo_url)

user_db = client['users']
currentread_db = client['reads']
book_db = client['books']
section_db = client['sections']


IMAGES_FOLDER = os.getenv("IMAGES_FOLDER")
TEXT_FOLDER = os.getenv("TEXT_FOLDER")

app = FastAPI()

@app.get("/sectiond/{section_id}")
def get_section(section_id: str) -> Section:
    section = section_db['sections'].find_one({"section_id": section_id})
    return section

@app.post("/login/")
def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    res = user_db.find({"username": username, "password": password})
    if len(res) == 1:
        return True
    else:
        return False

@app.post("/upload_book/")
def upload_book(info: BookUpload):
    user = user_db['users'].find_one({"user_id": info.user_id})
    if user.admin:
        # write cover bytes to file
        book = Book(title=info.title, author=info.author, description=info.description, genre=info.genre)

        with open(f"{IMAGES_FOLDER}/{book.book_id}.jpg", "wb") as f:
            f.write(info.cover_bytes)
        
        # write text bytes to file
        with open(f"{TEXT_FOLDER}/{book.book_id}.txt", "wb") as f:
            f.write(info.text_bytes)

        book_db['books'].insert_one(book)
        return True
    else:
        return False
