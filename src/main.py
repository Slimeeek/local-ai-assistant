import sys
import yaml
from pathlib import Path
from .ui.main_window import MainWindow  # ← добавили точку

def load_config():
    config_path = Path("config/settings.yaml")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

def main():
    config = load_config()
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
