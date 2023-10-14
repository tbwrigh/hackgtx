from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

import requests

import dotenv
import os

dotenv.load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    return RedirectResponse(url="/static/login.html")

@app.get("/home")
async def root(request: Request):
    books_req = requests.get(f"http://{BACKEND_URL}:8001/get_books/")
    genres_req = requests.get(f"http://{BACKEND_URL}:8001/get_genres/")

    books = books_req.json()
    genres = genres_req.json()

    return templates.TemplateResponse("home.html", {"request": request, "books": books, "genres": genres})

@app.get("/read/{book_id}/user/{user_id}")
def read(request: Request, book_id: str, user_id: str):
    print("READ!")

    book_req = requests.get(f"http://{BACKEND_URL}:8001/last_read_section/book/{book_id}/user/{user_id}", allow_redirects=True)
    section = book_req.json()

    section_text_req = requests.get(f"http://{BACKEND_URL}:8001/section_text/{section['section_id']}")
    section_text = section_text_req.text

    return templates.TemplateResponse("reader.html", {"request": request, "book_text": section_text, "section_id": section['section_id']})

@app.get("/next_section/{section_id}")
def next_section(section_id: str):
    print("NEXT SECTION")

    section_req = requests.get(f"http://{BACKEND_URL}:8001/next_section/{section_id}")
    section = section_req.json()

    section_text_req = requests.get(f"http://{BACKEND_URL}:8001/section_text/{section['section_id']}")
    section_text = section_text_req.text


    return {"book_text": section_text, "section_id": section['section_id']}

@app.get("/prev_section/{section_id}")
def prev_section(section_id: str):
    print("PREV SECTION")

    section_req = requests.get(f"http://{BACKEND_URL}:8001/prev_section/{section_id}")
    section = section_req.json()

    section_text_req = requests.get(f"http://{BACKEND_URL}:8001/section_text/{section['section_id']}")
    section_text = section_text_req.text

    return {"section_id": section['section_id'], "book_text": section_text}