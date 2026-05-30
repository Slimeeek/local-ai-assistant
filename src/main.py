#!/usr/bin/env python3
"""
Локальный ИИ ассистент - простая версия с Ollama
"""

import sys
import subprocess
from pathlib import Path

# Добавляем путь для импорта
sys.path.insert(0, str(Path(__file__).parent))

from core.logger import logger, log_user_action

def load_config():
    """Загружает конфигурацию"""
    import yaml
    
    config_path = Path("config/base.yaml")
    
    if not config_path.exists():
        logger.error(f"Конфиг не найден: {config_path}")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Конфиг загружен, модель: {config['llm']['model']}")
    return config

def check_model_exists(model_name):
    """Проверяет, скачана ли модель локально"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        return model_name in result.stdout
    except:
        return False

def ask_ollama(model, prompt):
    """Отправляет запрос к Ollama"""
    try:
        # Запускаем ollama
        cmd = ['ollama', 'run', model, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Ошибка: {result.stderr[:100]}"
    except subprocess.TimeoutExpired:
        return "Превышено время ожидания"
    except Exception as e:
        return f"Ошибка: {str(e)[:100]}"

def main():
    """Главная функция"""
    print("\n" + "="*50)
    print("🤖 Локальный ИИ ассистент")
    print("="*50)
    
    # Загружаем конфиг
    config = load_config()
    if not config:
        print("❌ Ошибка: не найден config/base.yaml")
        return 1
    
    model = config['llm']['model']
    print(f"📦 Модель: {model}")
    
    # Проверяем, существует ли модель
    if not check_model_exists(model):
        print(f"⚠️ Модель {model} не найдена локально")
        print(f"📥 Скачайте её командой: ollama pull {model}")
        return 1
    
    print("✅ Модель готова к работе")
    print("\nКоманды: /quit - выход, /help - помощь")
    print("-"*50)
    
    while True:
        try:
            user_input = input("\n👤 Вы: ").strip()
            
            if not user_input:
                continue
            
            if user_input == "/quit":
                print("👋 До свидания!")
                break
            elif user_input == "/help":
                print("\nДоступные команды:")
                print("  /quit - выход")
                print("  /help - помощь")
                continue
            
            # Отправляем запрос
            print("🤔 Думаю...", end="", flush=True)
            response = ask_ollama(model, user_input)
            print("\r🤖 Ассистент: " + response)
            
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
