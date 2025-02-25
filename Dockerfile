# Используем официальный образ Python из Docker Hub
FROM python:3.11-slim

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем ChromeDriver
RUN wget -O /usr/local/bin/chromedriver https://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip \
    && unzip /usr/local/bin/chromedriver -d /usr/local/bin/ \
    && rm /usr/local/bin/chromedriver.zip

# Устанавливаем Python-зависимости
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ваш код в контейнер
COPY . /app

# Устанавливаем рабочую директорию
WORKDIR /app

# Команда для запуска вашего приложения
CMD ["python", "main.py"]
