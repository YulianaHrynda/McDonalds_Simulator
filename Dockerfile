# syntax=docker/dockerfile:1.4
FROM python:3.12-slim

RUN apt-get update && apt-get install -y build-essential libffi-dev && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install poetry

WORKDIR /app

COPY . .

ENV PYTHONPATH=/app

RUN poetry config virtualenvs.create false \
 && poetry install --no-root --only main

CMD ["poetry", "run", "python", "bot/main.py"]
