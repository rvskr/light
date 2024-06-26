import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from config_manager import ConfigManager
from wifi_scanner import WindowsWiFiScanner
from notifier import Notifier
from updater import Updater  # Импорт класса Updater из updater.py

class ElectricityMonitorApp:
    def __init__(self, master):
        self.master = master
        master.title("Electricity Monitor")

        self.config_manager = ConfigManager()
        self.config = self.config_manager.config

        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 12), padding=5)
        self.style.configure('TEntry', font=('Arial', 12), padding=5)
        self.style.configure('TLabel', font=('Arial', 12))

        self.create_widgets()
        self.monitoring = False
        self.monitoring_thread = None
        self.scanner = WindowsWiFiScanner()
        self.notifier = Notifier(self.config_manager)
        self.last_status = "Unknown"

        self.repo_url = "https://api.github.com/repos/rvskr/light"  # Замените на ваш URL репозитория
        self.current_version = "1.32"  # Укажите текущую версию вашего приложения
        self.exe_name = "electricity_monitor_app.exe"
        self.updater = Updater(self.repo_url, self.exe_name, self.current_version)

        # Handle window closing event
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Configure grid layout
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)
        self.master.rowconfigure(2, weight=1)
        self.master.rowconfigure(3, weight=1)
        self.master.rowconfigure(4, weight=1)
        self.master.rowconfigure(5, weight=1)
        self.master.rowconfigure(6, weight=1)

    def create_widgets(self):
        self.num_networks_label = ttk.Label(self.master, text="Количество доступных Wi-Fi:")
        self.num_networks_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.num_networks_entry = ttk.Entry(self.master)
        self.num_networks_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.num_networks_entry.insert(0, self.config["num_networks"])

        self.interval_label = ttk.Label(self.master, text="Интервал проверки(сек):")
        self.interval_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.interval_entry = ttk.Entry(self.master)
        self.interval_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.interval_entry.insert(0, self.config["interval"])

        self.message_label = ttk.Label(self.master, text="Power Status Message:")
        self.message_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.message_entry = ttk.Entry(self.master)
        self.message_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.message_entry.insert(0, self.config["message"])

        self.status_label = ttk.Label(self.master, text="Power Status:")
        self.status_label.grid(row=3, column=0, sticky="w", padx=10, pady=5)

        self.status_var = tk.StringVar(value="Unknown")
        self.status_value_label = ttk.Label(self.master, textvariable=self.status_var)
        self.status_value_label.grid(row=3, column=1, sticky="w", padx=10, pady=5)

        self.networks_found_label = ttk.Label(self.master, text="Wi-Fi Networks Found:")
        self.networks_found_label.grid(row=4, column=0, sticky="w", padx=10, pady=5)

        self.networks_found_var = tk.StringVar(value="Unknown")
        self.networks_found_value_label = ttk.Label(self.master, textvariable=self.networks_found_var)
        self.networks_found_value_label.grid(row=4, column=1, sticky="w", padx=10, pady=5)

        self.start_stop_button = ttk.Button(self.master, text="Start", command=self.toggle_monitoring)
        self.start_stop_button.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")

        self.update_button = ttk.Button(self.master, text="Check for Updates", command=self.check_for_updates)
        self.update_button.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")

    def check_electricity(self):
        try:
            num_networks = self.scanner.scan_wifi_networks()
            self.master.after(0, self.networks_found_var.set, str(num_networks))  # update via after
            current_status = "Power On" if num_networks >= int(self.config["num_networks"]) else "Power Off"

            if current_status == "Power On":
                self.notifier.send_notification()

            self.master.after(0, self.status_var.set, current_status)  # update via after
            self.last_status = current_status

        except Exception as e:
            self.master.after(0, self.status_var.set, f"Error: {e}")  # update via after


    def start_monitoring(self):
        try:
            new_message = self.message_entry.get()
            old_message = self.config["message"]

            self.config["num_networks"] = int(self.num_networks_entry.get())
            self.config["interval"] = int(self.interval_entry.get())
            self.config["message"] = new_message

            # Удаление старого аудиофайла, если сообщение изменилось
            if new_message != old_message:
                old_audio_file = self.config.get("audio_file", "")
                if old_audio_file and os.path.exists(old_audio_file):
                    os.remove(old_audio_file)
                self.config["audio_file"] = ""

            self.config_manager.save_config(self.config)

            self.monitoring = True
            self.start_stop_button.config(text="Stop")
            self.monitoring_thread = threading.Thread(target=self.monitoring_task)
            self.monitoring_thread.start()
        except Exception as e:
            print(f"Error starting monitoring: {e}")


    def stop_monitoring(self):
        self.monitoring = False
        self.start_stop_button.config(text="Start")

    def toggle_monitoring(self):
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def monitoring_task(self):
        while self.monitoring:
            self.check_electricity()
            time.sleep(int(self.config["interval"]))

            if not self.monitoring:
                break

            # Check if thread has finished
            if not self.monitoring_thread.is_alive():
                self.master.after(0, self.on_thread_finished)

    def on_thread_finished(self):
        self.stop_monitoring()  # Stop monitoring
        self.master.destroy()   # Close the application window

    def on_closing(self):
        self.stop_monitoring()  # Stop monitoring and wait for thread to finish
        self.master.after(0, self.master.destroy)  # Close window after monitoring finishes

    def check_for_updates(self):
        latest_release = self.updater.check_for_update(self.current_version)
        if latest_release:
            self.updater.notify_update(self.master, latest_release)
        else:
            messagebox.showinfo("Updates", "You have the latest version.")

def main():
    try:
        root = tk.Tk()
        app = ElectricityMonitorApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")

if __name__ == "__main__":
    main()
