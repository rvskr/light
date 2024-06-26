import os
import hashlib
from gtts import gTTS
from playsound import playsound

class Notifier:
    def __init__(self, config_manager):
        self.config_manager = config_manager

    def generate_notification_filename(self, message):
        try:
            hash_object = hashlib.md5(message.encode())
            return f"notification_{hash_object.hexdigest()}.mp3"
        except Exception as e:
            print(f"Ошибка при генерации имени файла: {e}")
            return "notification_error.mp3"

    def send_notification(self):
        config = self.config_manager.config
        message = config["message"]
        filename = config.get("audio_file", "")
        if not filename or not os.path.exists(filename):
            filename = self.generate_notification_filename(message)
            try:
                tts = gTTS(text=message, lang='ru')
                tts.save(filename)
                config["audio_file"] = filename
                self.config_manager.save_config(config)
            except Exception as e:
                print(f"Ошибка при создании аудио файла: {e}")
        try:
            playsound(filename)
        except Exception as e:
            print(f"Ошибка при воспроизведении звука: {e}")
            print(message)
