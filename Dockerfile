# Используем базовый образ с Python
FROM python:3.11-slim

# Устанавливаем необходимые зависимости
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    jq \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем последнюю стабильную версию ChromeDriver
RUN LATEST_VERSION=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json | jq -r '.versions | .[0].version') && \
    echo "Latest version: $LATEST_VERSION" && \
    CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json | \
    jq -r --arg ver "$LATEST_VERSION" '.versions[] | select(.version == $ver) | .downloads.chromeDriver[] | select(.platform=="linux64") | .url') && \
    echo "ChromeDriver URL: $CHROMEDRIVER_URL" && \
    wget -O /tmp/chromedriver.zip "$CHROMEDRIVER_URL" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Устанавливаем зависимость Python для Selenium
RUN pip install selenium

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем ваш код в контейнер
COPY . /app

# Команда для запуска вашего приложения (замените на вашу основную команду)
CMD ["python", "your_script.py"]
