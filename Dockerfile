# Используем официальный образ Python из Docker Hub
FROM python:3.11-slim

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    unzip \
    wget \
    curl \
    gnupg \
    && apt-get remove -y chromium chromium-driver \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем ChromeDriver
RUN CHROMEDRIVER_VERSION=114.0.5735.90 && \
    wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Устанавливаем Python-зависимости
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Проверяем версии Google Chrome и ChromeDriver
RUN google-chrome --version && \
    chromedriver --version && \
    which google-chrome && \
    which chromedriver

# Копируем ваш код в контейнер
COPY . /app

# Устанавливаем рабочую директорию
WORKDIR /app

# Команда для запуска вашего приложения
CMD ["python", "main.py"]
