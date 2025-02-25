# Используем Python 3.10 в качестве базового образа
FROM python:3.10

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    chromium \
    chromium-driver 

# Получаем последнюю версию ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -sS https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json | \
    grep -o '"linux64".*?https://[^"]*' | head -1 | cut -d '"' -f 4) && \
    wget -O /tmp/chromedriver.zip "$CHROMEDRIVER_VERSION" && \
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
