FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tini \
    ffmpeg \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH=${PATH}:/usr/bin

CMD ["tini", "--", "python", "main.py"]
