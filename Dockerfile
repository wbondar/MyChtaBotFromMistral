FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    xvfb \
    tini \
    wget \
    unzip \
    fonts-liberation2 \
    libatk-bridge2.0-0 \
    libgbm1 \
    libnss3 \
    libx11-6 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Устанавливаем Python зависимости
RUN pip install --no-install-recommends -r requirements.txt

# Копируем скрипт для скачивания chromedriver
COPY download_chromedriver.sh /app/

# Настройки окружения
ENV DISPLAY=:99 \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    LC_ALL=C.UTF-8

# Запуск приложения: сначала скачиваем chromedriver, потом запускаем бота
CMD ["tini", "--", "sh", "-c", "/app/download_chromedriver.sh && Xvfb :99 -screen 0 1024x768x24 & python main.py"]
