import subprocess

class WindowsWiFiScanner:
    def __init__(self):
        pass

    def scan_wifi_networks(self):
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks"],
                capture_output=True, text=True, check=True, encoding="cp866",
                creationflags=subprocess.CREATE_NO_WINDOW  # Добавляем этот параметр для скрытия консоли
            )
            networks = [line for line in result.stdout.split('\n') if "SSID" in line]
            return len(networks)
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при выполнении команды netsh: {e}")
            return 0
        except Exception as e:
            print(f"Общая ошибка: {e}")
            return 0
