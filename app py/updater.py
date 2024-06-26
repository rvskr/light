import os
import requests
import shutil
from tkinter import messagebox, Toplevel, Label, Button
import sys  

class Updater:
    def __init__(self, repo_url, exe_name, current_version):
        self.repo_url = repo_url
        self.exe_name = exe_name
        self.current_version = current_version

    def get_latest_release(self):
        try:
            response = requests.get(f"{self.repo_url}/releases/latest")
            response.raise_for_status()
            latest_release = response.json()
            return latest_release
        except requests.RequestException as e:
            print(f"Ошибка при проверке обновлений: {e}")
            return None

    def check_for_update(self, current_version):
        latest_release = self.get_latest_release()
        if latest_release:
            latest_version = latest_release.get("tag_name")
            if latest_version and compare_versions(latest_version, self.current_version) > 0:
                return latest_release
        return None

    def notify_update(self, master, latest_release):
        top = Toplevel(master)
        top.title("Доступно обновление")

        Label(top, text=f"Доступна новая версия: {latest_release['tag_name']}").pack(pady=10)
        Label(top, text=f"Описание:\n{latest_release['body']}").pack(pady=10)

        download_button = Button(top, text="Скачать", command=lambda: self.download_new_file(latest_release))
        download_button.pack(pady=10)

        close_button = Button(top, text="Закрыть", command=top.destroy)
        close_button.pack(pady=10)

    def download_new_file(self, latest_release):
        assets = latest_release.get('assets', [])
        if not assets:
            messagebox.showerror("Ошибка", "Не удалось найти исполняемый файл для скачивания.")
            return

        exe_url = None
        for asset in assets:
            if asset['name'].endswith('.exe'):
                exe_url = asset['browser_download_url']
                break

        if not exe_url:
            messagebox.showerror("Ошибка", "Не удалось найти исполняемый файл для скачивания.")
            return

        try:
            response = requests.get(exe_url, stream=True)
            response.raise_for_status()

            new_exe_path = "temp_" + self.exe_name
            with open(new_exe_path, 'wb') as file:
                shutil.copyfileobj(response.raw, file)

            messagebox.showinfo("Успех", f"Новый файл скачан: {new_exe_path}")
            self.create_and_run_bat_file()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скачать файл: {e}")

    def create_and_run_bat_file(self):
        bat_content = f"""@echo off
setlocal

set oldFile=temp_{self.exe_name}
set newFile={self.exe_name}
set batFile=%~f0

rem Проверяем существование файла {self.exe_name} и удаляем его, если он существует
if exist "%newFile%" (
    del "%newFile%"
    echo Удален файл %newFile%.
)
rem Добавляем задержку перед началом выполнения на 3 секунды
timeout /t 3 >nul

rem Переименовываем temp_{self.exe_name} в {self.exe_name}
ren "%oldFile%" "%newFile%"
if errorlevel 1 (
    echo Ошибка при переименовании файла.
) else (
    echo Замена файла завершена.
    start "" "%newFile%"
    del "%batFile%"
)

pause >nul
"""
        bat_path = "update.bat"
        with open(bat_path, 'w') as bat_file:
            bat_file.write(bat_content)

        try:
            os.startfile(bat_path)  # Запуск батника
            sys.exit()  # Завершение программы
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить файл обновления: {e}")

def compare_versions(version1, version2):
    v1_parts = list(map(int, version1.split('.')))
    v2_parts = list(map(int, version2.split('.')))

    for i in range(max(len(v1_parts), len(v2_parts))):
        v1_part = v1_parts[i] if i < len(v1_parts) else 0
        v2_part = v2_parts[i] if i < len(v2_parts) else 0

        if v1_part < v2_part:
            return -1
        elif v1_part > v2_part:
            return 1

    return 0
