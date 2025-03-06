# Используйте более новую версию Debian (Bullseye) вместо Buster
FROM python:3.10-slim-bullseye

# Установите Chromium и зависимости
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgl1 \
    libglu1-mesa \
    libpango-1.0-0 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrender1 \
    libxtst6 \
    --no-install-recommends

# Установите Xvfb для headless-режима (если нужно)
RUN apt-get install -y xvfb

# Установите зависимости проекта
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем файлы проекта
COPY . /app
WORKDIR /app

# Запускаем скрипт перед основным приложением
CMD ["sh", "-c", "python3 testsyschrom.py && python3 main.py"]
