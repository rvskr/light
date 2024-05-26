import tkinter as tk
from tkinter import ttk, messagebox
import time
import json
import threading
from pywifi import PyWiFi, const
from gtts import gTTS
from playsound import playsound
import os
import hashlib

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            return {"num_networks": 1, "interval": 60, "message": "Кажется появился свет.", "audio_file": ""}

    def save_config(self, config):
        try:
            with open(self.config_file, "w", encoding="utf-8") as file:
                json.dump(config, file, ensure_ascii=False, indent=4)
            self.config = config
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")

class ElectricityMonitor:
    def __init__(self):
        self.wifi = PyWiFi()
        self.iface = self.get_wireless_interface()

    def get_wireless_interface(self):
        try:
            for iface in self.wifi.interfaces():
                if iface.name() and iface.status() in [const.IFACE_DISCONNECTED, const.IFACE_SCANNING, const.IFACE_CONNECTING, const.IFACE_CONNECTED]:
                    return iface
            raise Exception("Не найден беспроводной интерфейс")
        except Exception as e:
            print(f"Ошибка при получении интерфейса: {e}")
            return None

    def scan_wifi_networks(self):
        try:
            if self.iface:
                if self.iface.status() == const.IFACE_DISCONNECTED:
                    return 0
                self.iface.scan()
                time.sleep(3)
                results = self.iface.scan_results()
                if results:
                    return len(results)
            return 0
        except Exception as e:
            print(f"Ошибка при сканировании сетей Wi-Fi: {e}")
            return 0

class ElectricityMonitorApp:
    def __init__(self, master):
        self.master = master
        master.title("Монитор электричества")

        self.config_manager = ConfigManager()
        self.config = self.config_manager.config

        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 12), padding=5)
        self.style.configure('TEntry', font=('Arial', 12), padding=5)
        self.style.configure('TLabel', font=('Arial', 12))

        self.create_widgets()
        self.monitoring = False
        self.monitor = ElectricityMonitor()
        self.update_interface_status()

    def create_widgets(self):
        self.num_networks_label = ttk.Label(self.master, text="Количество Wi-Fi сетей:")
        self.num_networks_label.grid(row=0, column=0, sticky="w")

        self.num_networks_entry = ttk.Entry(self.master)
        self.num_networks_entry.grid(row=0, column=1)
        self.num_networks_entry.insert(0, self.config["num_networks"])

        self.interval_label = ttk.Label(self.master, text="Интервал проверки (сек):")
        self.interval_label.grid(row=1, column=0, sticky="w")

        self.interval_entry = ttk.Entry(self.master)
        self.interval_entry.grid(row=1, column=1)
        self.interval_entry.insert(0, self.config["interval"])

        self.message_label = ttk.Label(self.master, text="Сообщение о состоянии света:")
        self.message_label.grid(row=2, column=0, sticky="w")

        self.message_entry = ttk.Entry(self.master)
        self.message_entry.grid(row=2, column=1)
        self.message_entry.insert(0, self.config["message"])

        self.status_label = ttk.Label(self.master, text="Статус света:")
        self.status_label.grid(row=3, column=0, sticky="w")

        self.status_var = tk.StringVar()
        self.status_var.set("Неизвестно")
        self.status_value_label = ttk.Label(self.master, textvariable=self.status_var)
        self.status_value_label.grid(row=3, column=1, sticky="w")

        self.interface_label = ttk.Label(self.master, text="Ваш интерфейс:")
        self.interface_label.grid(row=4, column=0, sticky="w")

        self.interface_var = tk.StringVar()
        self.interface_var.set("Неизвестно")
        self.interface_value_label = ttk.Label(self.master, textvariable=self.interface_var)
        self.interface_value_label.grid(row=4, column=1, sticky="w")

        self.networks_found_label = ttk.Label(self.master, text="Найдено сетей Wi-Fi:")
        self.networks_found_label.grid(row=5, column=0, sticky="w")

        self.networks_found_var = tk.StringVar()
        self.networks_found_var.set("Неизвестно")
        self.networks_found_value_label = ttk.Label(self.master, textvariable=self.networks_found_var)
        self.networks_found_value_label.grid(row=5, column=1, sticky="w")

        self.start_stop_button = ttk.Button(self.master, text="Старт", command=self.toggle_monitoring)
        self.start_stop_button.grid(row=6, columnspan=2)

    def update_interface_status(self):
        try:
            if self.monitor.iface:
                interface_name = self.monitor.iface.name()
                interface_status = self.monitor.iface.status()
                if interface_status == const.IFACE_CONNECTED:
                    self.interface_var.set(f"{interface_name}: Подключен")
                elif interface_status == const.IFACE_DISCONNECTED:
                    self.interface_var.set(f"{interface_name}: Отключен")
                else:
                    self.interface_var.set("Неизвестно")
            else:
                self.interface_var.set("Не найден")
        except Exception as e:
            self.interface_var.set(f"Ошибка: {e}")

    def generate_notification_filename(self, message):
        try:
            hash_object = hashlib.md5(message.encode())
            return f"notification_{hash_object.hexdigest()}.mp3"
        except Exception as e:
            print(f"Ошибка при генерации имени файла: {e}")
            return "notification_error.mp3"

    def send_notification(self):
        message = self.config["message"]
        filename = self.config.get("audio_file", "")
        if not filename or not os.path.exists(filename):
            filename = self.generate_notification_filename(message)
            try:
                tts = gTTS(text=message, lang='ru')
                tts.save(filename)
                self.config["audio_file"] = filename
                self.config_manager.save_config(self.config)
            except Exception as e:
                print(f"Ошибка при создании аудио файла: {e}")
        try:
            playsound(filename)
        except Exception as e:
            print(f"Ошибка при воспроизведении звука: {e}")
            print(message)

    def check_electricity(self):
        try:
            num_networks = self.monitor.scan_wifi_networks()
            self.networks_found_var.set(str(num_networks))
            if num_networks >= int(self.config["num_networks"]):
                self.status_var.set("Включен")
                self.send_notification()
            else:
                self.status_var.set("Выключен")
            self.update_interface_status()
            self.master.update()
        except Exception as e:
            self.status_var.set(f"Ошибка: {e}")

    def start_monitoring(self):
        try:
            new_message = self.message_entry.get()
            old_message = self.config["message"]

            self.config["num_networks"] = int(self.num_networks_entry.get())
            self.config["interval"] = int(self.interval_entry.get())
            self.config["message"] = new_message

            if new_message != old_message:
                old_audio_file = self.config.get("audio_file", "")
                if old_audio_file and os.path.exists(old_audio_file):
                    os.remove(old_audio_file)
                self.config["audio_file"] = ""

            self.config_manager.save_config(self.config)

            self.monitoring = True
            self.start_stop_button.config(text="Стоп")
            threading.Thread(target=self.monitoring_task).start()
        except Exception as e:
            print(f"Ошибка при запуске мониторинга: {e}")

    def stop_monitoring(self):
        self.monitoring = False
        self.start_stop_button.config(text="Старт")

    def toggle_monitoring(self):
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def monitoring_task(self):
        while self.monitoring:
            self.check_electricity()
            time.sleep(int(self.config["interval"]))

def main():
    try:
        root = tk.Tk()
        app = ElectricityMonitorApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")

if __name__ == "__main__":
    main()
