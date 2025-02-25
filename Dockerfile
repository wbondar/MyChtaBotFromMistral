# Используем Python 3.10 в качестве базового образа
FROM python:3.10

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    unzip \
    chromium \
    chromium-driver 

# Загружаем и устанавливаем последнюю версию ChromeDriver
RUN LATEST_CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | \
    jq -r '.channels.Stable.downloads.chromeDriver[] | select(.platform=="linux64") | .url') && \
    wget -O /tmp/chromedriver.zip "$LATEST_CHROMEDRIVER_URL" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем приложение
CMD ["python", "main.py"]
