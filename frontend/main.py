from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

import requests

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    return RedirectResponse(url="/static/login.html")

@app.get("/home")
async def root(request: Request):
    books_req = requests.get("http://localhost:8001/get_books/")


    print("!!!!!!!!!!!!!!!!!!")
    print(books_req.content)

    books = books_req.json()

    print(books)

    return templates.TemplateResponse("home.html", {"request": request, "books": books})
