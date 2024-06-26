import json

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
