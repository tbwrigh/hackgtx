FROM python:3.11

WORKDIR /code

COPY req.txt /code/req.txt

RUN pip install --no-cache-dir --upgrade -r /code/req.txt

COPY main.py /code/main.py
COPY static /code/static
COPY templates /code/templates

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]