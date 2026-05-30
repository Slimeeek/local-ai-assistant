#!/usr/bin/env python3
"""
Локальный ИИ ассистент с долгосрочной памятью
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.logger import logger, log_user_action
from memory.vector_memory import LongTermMemory

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

def build_prompt_with_memory(user_input, memories):
    """Строит промпт с учётом памяти"""
    if not memories:
        return user_input
    
    # Формируем контекст из воспоминаний
    context = "Вот что мы обсуждали ранее:\n\n"
    for i, memory in enumerate(memories, 1):
        context += f"{i}. {memory}\n"
    
    context += f"\nТеперь пользователь спрашивает: {user_input}\n\nОтветь, учитывая предыдущий контекст:"
    
    return context

def main():
    """Главная функция"""
    print("\n" + "="*55)
    print("🤖 Локальный ИИ ассистент с ДОЛГОСРОЧНОЙ ПАМЯТЬЮ")
    print("="*55)
    
    # Загружаем конфиг
    config = load_config()
    if not config:
        print("❌ Ошибка: не найден config/base.yaml")
        return 1
    
    model = config['llm']['model']
    print(f"📦 Модель: {model}")
    
    # Проверяем модель
    if not check_model_exists(model):
        print(f"⚠️ Модель {model} не найдена")
        print(f"📥 Скачайте: ollama pull {model}")
        return 1
    
    # Инициализируем память
    memory = LongTermMemory()
    stats = memory.get_stats()
    print(f"🧠 Память: {stats['total_memories']} воспоминаний")
    
    print("\nКоманды:")
    print("  /quit     - выход")
    print("  /help     - помощь")
    print("  /stats    - статистика памяти")
    print("  /clear    - очистить память (осторожно!)")
    print("-"*55)
    
    while True:
        try:
            user_input = input("\n👤 Вы: ").strip()
            
            if not user_input:
                continue
            
            # Обработка команд
            if user_input == "/quit":
                print("👋 До свидания!")
                break
            elif user_input == "/help":
                print("\nДоступные команды:")
                print("  /quit  - выход")
                print("  /help  - помощь")
                print("  /stats - показать статистику памяти")
                print("  /clear - очистить всю память")
                continue
            elif user_input == "/stats":
                stats = memory.get_stats()
                print(f"\n📊 Статистика памяти:")
                print(f"   Всего воспоминаний: {stats['total_memories']}")
                continue
            elif user_input == "/clear":
                confirm = input("⚠️ Точно очистить всю память? (yes/no): ")
                if confirm.lower() == "yes":
                    memory.clear_all()
                    print("✅ Память очищена")
                else:
                    print("❌ Отменено")
                continue
            
            # Ищем похожие воспоминания
            print("🔍 Ищу в памяти...", end="", flush=True)
            memories = memory.search_memories(user_input, top_k=3)
            print("\r" + " " * 30 + "\r", end="")
            
            if memories:
                print(f"📚 Найдено {len(memories)} воспоминаний")
            
            # Строим промпт с памятью
            prompt = build_prompt_with_memory(user_input, memories)
            
            # Отправляем запрос
            print("🤔 Думаю...", end="", flush=True)
            response = ask_ollama(model, prompt)
            print("\r🤖 Ассистент: " + response)
            
            # Сохраняем в память
            memory.add_memory(user_input, response)
            print("💾 Диалог сохранён в память")
            
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
