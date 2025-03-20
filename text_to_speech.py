import os
from gtts import gTTS
from telegram import InputFile

async def send_voice_message(context, chat_id: int, text: str) -> None:
    """Конвертирует текст в речь и отправляет голосовое сообщение."""
    try:
        # Создаем объект gTTS
        tts = gTTS(text=text, lang='ru')

        # Сохраняем аудиофайл
        audio_path = "/tmp/response.ogg"
        tts.save(audio_path)

        # Отправляем голосовое сообщение
        await context.bot.send_voice(chat_id=chat_id, voice=InputFile(audio_path))

        # Удаляем временный файл
        os.remove(audio_path)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Ошибка при отправке голосового сообщения: {str(e)}")
