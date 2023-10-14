from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

import requests

import dotenv
import os

dotenv.load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    return RedirectResponse(url="/static/login.html")

@app.get("/home")
async def root(request: Request):
    books_req = requests.get(f"http://{BACKEND_URL}:8001/get_books/")
    genres_req = requests.get(f"http://{BACKEND_URL}:8001/get_genres/")


    print("!!!!!!!!!!!!!!!!!!")
    print(books_req.content)

    books = books_req.json()
    genres = genres_req.json()

    print(books)

    return templates.TemplateResponse("home.html", {"request": request, "books": books, "genres": genres})

@app.get("/read/{book_id}")
def read(request: Request, book_id: str):
    book_req = requests.get(f"http://{BACKEND_URL}:8001/get_book/{book_id}")
    book = book_req.json()

    return templates.TemplateResponse("read.html", {"request": request, "book": book})