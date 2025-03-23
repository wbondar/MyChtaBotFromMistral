FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    tini \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Настройки окружения
ENV LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH=${PATH}:/usr/bin

# Запуск приложения
CMD ["tini", "--", "python", "main.py"]
