import requests

gutenburg_url = input("Enter the url of the gutenburg book: ")

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

description = "No description available."
genre = "No genre available."

# extract number
book_id = gutenburg_url.split("/")[-1][0]

# get the cover
cover_url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.cover.medium.jpg"
cover_bytes = requests.get(cover_url).content

# get the text
text_url = f"https://www.gutenberg.org/ebooks/{book_id}.txt.utf-8"
text_bytes = requests.get(text_url).content

# send to backend
backend_url = "http://localhost:8001/upload_book/"

data = {
    "title": title,
    "author": author,
    "description": description,
    "genre": genre,
    "user_id": "admin-ftyujbvfdertyuiohgfrert",
}

files = {
    "cover_bytes": cover_bytes,
    "text_bytes": text_bytes,
}

r = requests.post(backend_url, data=data, files=files, allow_redirects=True)

print(r.text)
