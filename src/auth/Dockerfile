FROM python:3.12.0-slim-bullseye

RUN apt-get update

RUN apt-get install libpq-dev python3-dev build-essential gcc -y

RUN mkdir /app

ENV PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

ADD src/auth auth

CMD ["python", "auth/run.py"]