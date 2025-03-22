FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    chromium \
    xvfb \
    tini \
    fonts-liberation \
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
    ffmpeg \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE_$(google-chrome --version | grep -oE '[0-9]+.[0-9]+.[0-9]+.[0-9]+' | cut -d '.' -f 1)) \
    && wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

# Копируем ChromeDriver из корня проекта в образ
COPY chromedriver /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver

WORKDIR /app
COPY . /app

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Настройки окружения
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    CHROME_BIN=/usr/bin/chromium \
    DISPLAY=:99 \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH=${PATH}:/usr/local/bin

# Удаляем файл блокировки перед запуском Xvfb
RUN rm -f /tmp/.X99-lock

# Запуск приложения
CMD ["tini", "--", "sh", "-c", "Xvfb :99 -screen 0 1024x768x24 & python main.py"]
