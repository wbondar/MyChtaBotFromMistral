# Используем Python 3.10 в качестве базового образа
FROM python:3.10

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    chromium \
    chromium-driver \
    jq

# Получаем последнюю доступную версию ChromeDriver
RUN CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build.json | \
    jq -r '.["stable"]' | \
    awk '{print "https://storage.googleapis.com/chrome-for-testing-public/" $1 "/linux64/chromedriver-linux64.zip"}') && \
    wget -O /tmp/chromedriver.zip "$CHROMEDRIVER_URL" && \
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
