# Используем официальный образ Python с Alpine для минимизации размера
FROM python:3.11-slim

# Установка Chromium и необходимых зависимостей
RUN apt-get update && apt-get install -y \
    chromium \
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

# Копируем chromedriver из проекта в системный путь
COPY chromedriver /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver

# Настройка рабочей директории
WORKDIR /app

# Копируем остальные файлы
COPY . /app

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Настройка переменных окружения
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    CHROMEDRIVER_VERSION=120.0.6099.224 \
    CHROME_BINARY_PATH=/usr/bin/chromium \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    LC_ALL=C.UTF-8

# Добавляем путь к драйверу в переменную PATH
ENV PATH=${PATH}:/usr/bin

# Запуск приложения
CMD ["python", "main.py"]
