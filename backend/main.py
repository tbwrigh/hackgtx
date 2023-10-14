from fastapi import FastAPI

import dotenv
import os
import openai 
from pymongo import MongoClient

dotenv.load_dotenv()

openai_key = os.getenv("OPENAI_KEY")

openai.api_key = openai_key

mongo_url = os.getenv("MONGO_URL")

client = MongoClient(mongo_url)

user_db = client.users



app = FastAPI()

