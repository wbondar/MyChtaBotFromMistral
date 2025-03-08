FROM python:3.11-slim

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    chromium \
    tzdata \
    xvfb \
    tini \
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
    wget \
    && rm -rf /var/lib/apt/lists/*

# Установка ChromeDriver
RUN CHROME_VERSION=$(chromium --version | awk '{print $2}' | awk -F. '{print $1}') && \
    wget https://chromedriver.storage.googleapis.com/${CHROME_VERSION}.0.0/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver

# Настройка часового пояса
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Проверка версий
RUN echo "Chromium version: $(chromium --version)" && \
    echo "ChromeDriver version: $(chromedriver --version)"

WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Настройки окружения
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    CHROME_BIN=/usr/bin/chromium \
    DISPLAY=:99 \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    LC_ALL=C.UTF-8

# Запуск
CMD ["tini", "--", "sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & python main.py"]
