FROM python:3.11

WORKDIR /code

COPY ./req.txt /code/req.txt

RUN pip install --no-cache-dir --upgrade -r /code/req.txt

COPY main.py /code/main.py
COPY models.py /code/models.py

COPY images /code/images
COPY text/ /code/text

COPY docker.env /code/.env

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]