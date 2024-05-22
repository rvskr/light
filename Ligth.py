import tkinter as tk
from tkinter import ttk, messagebox
import time
import pyttsx3
import json
import threading
from pywifi import PyWiFi, const

class ElectricityMonitorApp:
    def __init__(self, master):
        self.master = master
        master.title("Монитор электричества")

        self.load_config()

        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 12), padding=5)
        self.style.configure('TEntry', font=('Arial', 12), padding=5)
        self.style.configure('TLabel', font=('Arial', 12))

        self.num_networks_label = ttk.Label(master, text="Количество Wi-Fi сетей:")
        self.num_networks_label.grid(row=0, column=0, sticky="w")

        self.num_networks_entry = ttk.Entry(master)
        self.num_networks_entry.grid(row=0, column=1)
        self.num_networks_entry.insert(0, self.config["num_networks"])

        self.interval_label = ttk.Label(master, text="Интервал проверки (сек):")
        self.interval_label.grid(row=1, column=0, sticky="w")

        self.interval_entry = ttk.Entry(master)
        self.interval_entry.grid(row=1, column=1)
        self.interval_entry.insert(0, self.config["interval"])

        self.message_label = ttk.Label(master, text="Сообщение о состоянии света:")
        self.message_label.grid(row=2, column=0, sticky="w")

        self.message_entry = ttk.Entry(master)
        self.message_entry.grid(row=2, column=1)
        self.message_entry.insert(0, self.config["message"])

        self.status_label = ttk.Label(master, text="Статус света:")
        self.status_label.grid(row=3, column=0, sticky="w")

        self.status_var = tk.StringVar()
        self.status_var.set("Неизвестно")
        self.status_value_label = ttk.Label(master, textvariable=self.status_var)
        self.status_value_label.grid(row=3, column=1, sticky="w")

        self.start_stop_button = ttk.Button(master, text="Старт", command=self.toggle_monitoring)
        self.start_stop_button.grid(row=4, columnspan=2)

        self.monitoring = False
        self.monitoring_thread = None

    def load_config(self):
        try:
            with open("config.json", "r") as file:
                self.config = json.load(file)
        except FileNotFoundError:
            self.config = {"num_networks": 1, "interval": 60, "message": "Кажется появился свет."}
        except KeyError as e:
            # Если ключ отсутствует в файле конфигурации, используйте значение по умолчанию
            self.config = {"num_networks": 1, "interval": 60, "message": "Кажется появился свет."}


    def save_config(self):
        with open("config.json", "w") as file:
            json.dump(self.config, file)

    def scan_wifi_networks(self):
        wifi = PyWiFi()
        iface = wifi.interfaces()[0]  # Получаем первый Wi-Fi интерфейс
        iface.scan()  # Сканируем Wi-Fi сети
        time.sleep(3)  # Даем время на сканирование
        return len(iface.scan_results())  # Возвращаем количество найденных сетей

    def check_electricity(self):
        try:
            num_networks = self.scan_wifi_networks()
            if num_networks is not None and num_networks >= int(self.config["num_networks"]):
                self.status_var.set("Включен")
                self.master.update()
                self.send_notification()
            else:
                self.status_var.set("Выключен")
                self.master.update()
        except Exception as e:
            print("Ошибка при проверке наличия электричества:", e)

    def send_notification(self):
        message = self.config["message"]
        engine = pyttsx3.init()
        engine.say(message)
        engine.runAndWait()

    def start_monitoring_thread(self):
        try:
            interval = self.config["interval"]
            while self.monitoring:
                self.check_electricity()
                time.sleep(interval)
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите корректные значения.")

    def start_monitoring(self):
        self.config["num_networks"] = int(self.num_networks_entry.get())
        self.config["interval"] = int(self.interval_entry.get())
        self.config["message"] = self.message_entry.get()
        self.save_config()

        self.monitoring = True
        self.start_stop_button.config(text="Стоп")
        self.monitoring_thread = threading.Thread(target=self.start_monitoring_thread)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        self.monitoring = False
        self.start_stop_button.config(text="Старт")
    def toggle_monitoring(self):
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()

def main():
    root = tk.Tk()
    app = ElectricityMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

