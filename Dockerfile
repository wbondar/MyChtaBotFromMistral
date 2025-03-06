# Используем официальный образ Python с Slim для минимизации размера
FROM python:3.11-slim

# Установка зависимостей для Chromium и Xvfb
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
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

# Копируем chromedriver из проекта и делаем его исполняемым
COPY chromedriver /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver

# Настройка рабочей директории
WORKDIR /app

# Копируем остальные файлы
COPY . /app

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Настройка переменных окружения
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    CHROME_BIN=/usr/bin/chromium \
    DISPLAY=:99  # Для Xvfb
ENV LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    LC_ALL=C.UTF-8

# Добавляем путь к драйверу в PATH
ENV PATH=${PATH}:/usr/bin

# Запуск Xvfb и приложения
CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 & python main.py"]
