#!/bin/bash

echo "Запуск скрипта download_chromedriver.sh"

# Получаем версию Chromium
CHROMIUM_VERSION=$(chromium --version | awk '{print $2}' | sed 's/-stable//' | awk -F. '{print $1"."$2"."$3}')
echo "Версия Chromium: ${CHROMIUM_VERSION}"

# Базовый URL
BASE_URL="https://storage.googleapis.com/chrome-for-testing-public"

# Пытаемся найти точную версию
FULL_VERSION=$(chromium --version | awk '{print $2}' | sed 's/-stable//')
DOWNLOAD_URL="${BASE_URL}/${FULL_VERSION}/linux64/chromedriver-linux64.zip"
echo "Пробуем скачать точную версию ChromeDriver по URL: ${DOWNLOAD_URL}"

# Проверяем, существует ли файл
if ! wget --spider -q "$DOWNLOAD_URL"; then
    echo "Точная версия ChromeDriver не найдена, используем версию ${CHROMIUM_VERSION}"
    DOWNLOAD_URL="${BASE_URL}/${CHROMIUM_VERSION}/linux64/chromedriver-linux64.zip"

    # Повторная проверка
    if ! wget --spider -q "$DOWNLOAD_URL"; then
        echo "Ошибка: Не удалось найти подходящую версию ChromeDriver."
        exit 1
    fi
fi

echo "Скачиваем ChromeDriver по URL: ${DOWNLOAD_URL}"
wget -q -O /tmp/chromedriver.zip "$DOWNLOAD_URL"

# Распаковываем
echo "Распаковываем ChromeDriver"
unzip -o /tmp/chromedriver.zip -d /tmp/

# Перемещаем
echo "Перемещаем ChromeDriver в /usr/bin"
mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver

# Устанавливаем права
chmod +x /usr/bin/chromedriver

# Проверяем версии
echo "Chromium version:" && chromium --version
echo "ChromeDriver version:" && chromedriver --version

# Чистим
rm /tmp/chromedriver.zip
rm -rf /tmp/chromedriver-linux64

echo "Скрипт download_chromedriver.sh завершен"
