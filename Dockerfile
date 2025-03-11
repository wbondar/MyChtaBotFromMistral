FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    chromium \
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
    && rm -rf /var/lib/apt/lists/*

# Копируем ChromeDriver из корня проекта в образ
COPY chromedriver /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver

# Проверяем версии Chromium и ChromeDriver (для диагностики)
RUN echo "Chromium version:" && chromium --version
RUN echo "ChromeDriver version:" && chromedriver --version

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
    PATH=${PATH}:/usr/bin

# Перед запуском удаляем lock-файл Xvfb, затем запускаем Xvfb и бота
CMD ["tini", "--", "sh", "-c", "rm -f /tmp/.X99-lock; Xvfb :99 -screen 0 1920x1080x24 & python main.py"]
