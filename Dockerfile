# Используем базовый образ с Python 3.11
FROM python:3.11-slim

# Устанавливаем необходимые зависимости
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Получаем последнюю версию ChromeDriver
RUN LATEST_VERSION=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json | jq -r '.versions | .[0].version') && \
    echo "Latest version: $LATEST_VERSION" && \
    CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json | jq -r --arg ver "$LATEST_VERSION" '.versions[] | select(.version == $ver) | .downloads.chromeDriver[] | select(.platform=="linux64") | .url') && \
    echo "ChromeDriver URL: $CHROMEDRIVER_URL" && \
    wget -O /tmp/chromedriver.zip "$CHROMEDRIVER_URL" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта
COPY . /app

# Устанавливаем рабочую директорию
WORKDIR /app

# Команда для запуска вашего приложения
CMD ["python", "main.py"]
