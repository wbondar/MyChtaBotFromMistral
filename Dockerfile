# Используем официальный образ Python из Docker Hub
FROM python:3.11-slim

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    unzip \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем ChromeDriver
RUN CHROMEDRIVER_VERSION=114.0.5735.90 && \
    wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Устанавливаем Python-зависимости
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Проверяем версии Chromium и ChromeDriver
RUN chromium --version && \
    chromedriver --version && \
    which chromium && \
    which chromedriver

# Копируем ваш код в контейнер
COPY . /app

# Устанавливаем рабочую директорию
WORKDIR /app

# Команда для запуска вашего приложения
CMD ["python", "main.py"]
