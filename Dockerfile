# Используем минимальный образ Python
FROM python:3.11-slim

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем ChromeDriver с фиксированной версией
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/115.0.5790.102/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Копируем зависимости Python
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . /app

# Указываем команду для запуска
CMD ["python", "main.py"]
