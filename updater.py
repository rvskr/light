import requests
import os
import shutil
from tkinter import messagebox, Toplevel, Label, Button
import subprocess
import time  # Для добавления задержки перед попыткой замены файла

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

        download_button = Button(top, text="Скачать", command=lambda: self.download_and_replace(latest_release, top))
        download_button.pack(pady=10)

        close_button = Button(top, text="Закрыть", command=top.destroy)
        close_button.pack(pady=10)

    def download_and_replace(self, latest_release, window):
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

            new_exe_path = self.exe_name + ".new"
            with open(new_exe_path, 'wb') as file:
                shutil.copyfileobj(response.raw, file)

            current_exe_path = os.path.abspath(self.exe_name)
            backup_exe_path = self.exe_name + ".bak"

            # Проверяем существование текущего исполняемого файла
            if not os.path.exists(current_exe_path):
                messagebox.showerror("Ошибка", f"Не удалось найти текущий исполняемый файл: {self.exe_name}")
                return

            # Закрываем текущее приложение, если оно открыто
            self.close_application()

            # Даем время на закрытие приложения
            time.sleep(2)  # Увеличить время при необходимости

            # Повторно проверяем, не открыто ли приложение
            if self.is_application_running():
                messagebox.showerror("Ошибка", "Не удалось закрыть текущее приложение. Закройте его вручную перед обновлением.")
                return

            # Создаем резервную копию текущего исполняемого файла
            shutil.copyfile(current_exe_path, backup_exe_path)

            # Заменяем текущий исполняемый файл новым
            os.replace(new_exe_path, current_exe_path)

            messagebox.showinfo("Успех", "Приложение обновлено. Перезапустите его для применения изменений.")
            window.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скачать и заменить файл: {e}")

    def close_application(self):
        try:
            subprocess.call(['taskkill', '/F', '/IM', os.path.basename(self.exe_name)])
        except Exception as e:
            print(f"Ошибка при закрытии приложения: {e}")

    def is_application_running(self):
        try:
            output = subprocess.check_output(['tasklist', '/FI', f'IMAGENAME eq {os.path.basename(self.exe_name)}'], shell=True, stderr=subprocess.STDOUT)
            output_decoded = output.decode('utf-8', errors='ignore')
            return True if os.path.basename(self.exe_name) in output_decoded else False
        except Exception as e:
            print(f"Ошибка при проверке запущенного приложения: {e}")
            return False


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

    return 0  # версии равны
