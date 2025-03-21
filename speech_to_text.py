import os
import speech_recognition as sr
from pydub import AudioSegment
import logging

async def handle_voice_to_text(context, chat_id, voice_file_path):
    """Обработчик голосовых сообщений для преобразования в текст."""
    try:
        # Конвертируем OGG в WAV
        audio = AudioSegment.from_ogg(voice_file_path)
        wav_path = f"{voice_file_path.rsplit('.', 1)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Преобразуем голосовое сообщение в текст
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")

        return text

    except sr.UnknownValueError:
        logging.error("Не удалось распознать речь.")
        raise ValueError("Не удалось распознать речь.")

    except sr.RequestError as e:
        logging.error(f"Ошибка сервиса распознавания речи: {str(e)}")
        raise RuntimeError(f"Ошибка сервиса распознавания речи: {str(e)}")

    except Exception as e:
        logging.error(f"Ошибка: {str(e)}")
        raise RuntimeError(f"Ошибка: {str(e)}")
