import os
import re
from gtts import gTTS
from telegram import InputFile
import logging
from pydub import AudioSegment

async def send_voice_message(context, chat_id: int, text: str) -> None:
    """Конвертирует текст в речь и отправляет голосовое сообщение."""
    try:
        # Фильтруем текст, оставляя только разрешенные символы
        allowed_chars = " .,!?()@'"
        filtered_text = ''.join(c for c in text if c in allowed_chars or c.isalnum() or c.isspace())

        # Создаем объект gTTS
        tts = gTTS(text=filtered_text, lang='ru', slow=False)

        # Сохраняем аудиофайл в формате MP3
        audio_path = "/tmp/response.mp3"
        tts.save(audio_path)

        # Увеличиваем скорость воспроизведения
        audio = AudioSegment.from_mp3(audio_path)
        faster_audio = audio.speedup(playback_speed=1.5)
        faster_audio_path = "/tmp/response_faster.mp3"
        faster_audio.export(faster_audio_path, format="mp3")

        # Логируем создание аудиофайла
        logging.info(f"Audio file created at {faster_audio_path}")

        # Проверяем размер файла, чтобы убедиться, что он не пустой
        if os.path.getsize(faster_audio_path) > 0:
            logging.info(f"Audio file size: {os.path.getsize(faster_audio_path)} bytes")
        else:
            logging.error("Audio file is empty!")

        # Открываем файл для отправки
        with open(faster_audio_path, 'rb') as audio_file:
            # Отправляем голосовое сообщение
            await context.bot.send_voice(chat_id=chat_id, voice=InputFile(audio_file))

        # Логируем отправку аудиофайла
        logging.info(f"Audio file sent to chat_id {chat_id}")

        # Удаляем временный файл
        os.remove(faster_audio_path)

    except Exception as e:
        logging.error(f"Ошибка при отправке голосового сообщения: {str(e)}")
        await context.bot.send_message(chat_id=chat_id, text=f"Ошибка при отправке голосового сообщения: {str(e)}")
