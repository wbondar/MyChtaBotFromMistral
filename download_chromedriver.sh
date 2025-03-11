#!/bin/bash

# Получаем версию Chromium, удаляем "-stable" и берем только мажорную, минорную и билд версии.
CHROMIUM_VERSION=$(chromium --version | awk '{print $2}' | sed 's/-stable//' | awk -F. '{print $1"."$2"."$3}')

# Базовый URL для скачивания
BASE_URL="https://storage.googleapis.com/chrome-for-testing-public"

# Пытаемся найти точную версию
FULL_VERSION=$(chromium --version | awk '{print $2}' | sed 's/-stable//')
DOWNLOAD_URL="${BASE_URL}/${FULL_VERSION}/linux64/chromedriver-linux64.zip"

# Проверяем, существует ли файл по этому URL.  Если нет, используем урезанную версию.
if ! wget --spider -q "$DOWNLOAD_URL"; then
    echo "Точная версия ChromeDriver не найдена, используем версию ${CHROMIUM_VERSION}"
    DOWNLOAD_URL="${BASE_URL}/${CHROMIUM_VERSION}/linux64/chromedriver-linux64.zip"

  # Повторная проверка (на случай, если и такой версии нет)
  if ! wget --spider -q "$DOWNLOAD_URL"; then
      echo "Ошибка: Не удалось найти подходящую версию ChromeDriver."
      exit 1  # Выходим с ошибкой
  fi
fi

# Скачиваем
wget -q -O /tmp/chromedriver.zip "$DOWNLOAD_URL"

# Распаковываем
unzip -o /tmp/chromedriver.zip -d /tmp/

# Перемещаем chromedriver в /usr/bin
mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver

# Устанавливаем права
chmod +x /usr/bin/chromedriver

# Проверяем версии (для диагностики)
echo "Chromium version:" && chromium --version
echo "ChromeDriver version:" && chromedriver --version

# Чистим за собой
rm /tmp/chromedriver.zip
rm -rf /tmp/chromedriver-linux64
