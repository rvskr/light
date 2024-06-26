import os
import hashlib
from gtts import gTTS
from playsound import playsound
import tkinter as tk

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
        
    def show_notification_window(self, message):
        notification_window = tk.Toplevel()
        notification_window.overrideredirect(True)  # Убираем рамку и заголовок окна
        notification_window.attributes("-topmost", True)  # Окно поверх всех остальных окон
        notification_window.attributes("-alpha", 0.9)  # Прозрачность окна (0 - полностью прозрачно, 1 - полностью непрозрачно)

        screen_width = notification_window.winfo_screenwidth()
        screen_height = notification_window.winfo_screenheight()

        # Размеры и положение окна уведомления
        window_width = 300
        window_height = 100
        x = screen_width - window_width
        y_offset_percent = 5  # Смещение на 5% от высоты экрана
        y_offset_pixels = int(screen_height * y_offset_percent / 100)
        y = screen_height - window_height - y_offset_pixels

        notification_window.geometry(f"{window_width}x{window_height}+{x}+{y}")  # Положение в правом нижнем углу

        notification_window.configure(bg="#333333")  # Цвет фона в темных тонах

        close_button = tk.Button(notification_window, text="Закрыть", command=notification_window.destroy, bg="#555555", fg="white", bd=0)
        close_button.pack(side=tk.TOP, anchor=tk.NE, padx=10, pady=10)  # Размещаем кнопку в правом верхнем углу

        label = tk.Label(notification_window, text=message, font=("Arial", 14), fg="white", bg="#333333", wraplength=280, justify=tk.CENTER)
        label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)  # Размещаем текст по центру, занимая все доступное пространство

        notification_window.after(5000, notification_window.destroy)  # Закрытие окна через 5 секунд

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
            # Показать окно уведомления и воспроизвести звук одновременно
            self.show_notification_window(message)
            playsound(filename)
            
        except Exception as e:
            print(f"Ошибка при воспроизведении звука: {e}")
            print(message)
