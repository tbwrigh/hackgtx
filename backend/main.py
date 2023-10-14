from fastapi import FastAPI

import dotenv
import os

dotenv.load_dotenv()

openai_key = os.getenv("OPENAI_KEY")

app = FastAPI()

