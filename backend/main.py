from typing import Annotated
from fastapi import FastAPI, Form

import dotenv
import os
import openai 
from pymongo import MongoClient

from models import User, Book, Section, Current

dotenv.load_dotenv()

openai_key = os.getenv("OPENAI_KEY")

openai.api_key = openai_key

mongo_url = os.getenv("MONGO_URL")

client = MongoClient(mongo_url)

user_db = client['users']
currentread_db = client['reads']
book_db = client['books']
section_db = client['sections']

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