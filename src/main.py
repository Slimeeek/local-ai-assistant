#!/usr/bin/env python3
"""
<<<<<<< HEAD
Локальный ИИ ассистент - простая версия с Ollama
"""

import sys
import subprocess
=======
Локальный ИИ ассистент с умной памятью
Сохраняет суть разговора при завершении
"""

import sys
import signal
>>>>>>> b03f3e8 (Добавлена нормальная долгосрочная память)
from pathlib import Path

# Добавляем путь для импорта
sys.path.insert(0, str(Path(__file__).parent))

<<<<<<< HEAD
from core.logger import logger, log_user_action
=======
import ollama
from memory.smart_memory import SmartMemory
>>>>>>> b03f3e8 (Добавлена нормальная долгосрочная память)

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

<<<<<<< HEAD
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
=======
class Assistant:
    def __init__(self, model):
        self.model = model
        self.memory = SmartMemory(model)
        self.messages = []
        self.is_running = True
        
        # Загружаем контекст из прошлых разговоров
        self.update_system_prompt()
        
        # Обработчик завершения
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
    
    def update_system_prompt(self):
        """Обновляет системный промпт с учётом памяти"""
        memory_context = self.memory.get_memory_context()
        
        system_prompt = f"""Ты - полезный ИИ-ассистент. Отвечай на русском языке, естественно.
{memory_context}
Если пользователь спрашивает о себе или прошлых разговорах - используй информацию из памяти.
Будь дружелюбным и внимательным."""
        
        if self.messages:
            self.messages[0] = {"role": "system", "content": system_prompt}
        else:
            self.messages = [{"role": "system", "content": system_prompt}]
    
    def handle_shutdown(self, signum, frame):
        """Обработчик завершения - сохраняем разговор в память"""
        print("\n\n🔄 Сохраняю разговор в долгосрочную память...")
        self.memory.finish_conversation()
        print("👋 До свидания!")
        sys.exit(0)
    
    def send(self, user_message):
        # Добавляем сообщение пользователя
        self.messages.append({"role": "user", "content": user_message})
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=self.messages,
                options={'temperature': 0.7}
            )
            
            assistant_response = response['message']['content']
            
            # Сохраняем в текущий разговор (временная память)
            self.memory.add_to_current(user_message, assistant_response)
            
            # Добавляем ответ в историю
            self.messages.append({"role": "assistant", "content": assistant_response})
            
            # Ограничиваем историю
            if len(self.messages) > 21:
                self.messages = [self.messages[0]] + self.messages[-20:]
            
            return assistant_response
            
        except Exception as e:
            self.messages.pop()
            return f"Ошибка: {str(e)}"
    
    def get_stats(self):
        return self.memory.get_stats()
    
    def clear_memory(self):
        self.memory.clear()
        self.update_system_prompt()

def main():
    print("\n" + "="*60)
    print("🤖 Локальный ИИ ассистент (УМНАЯ ПАМЯТЬ)")
    print("="*60)
>>>>>>> b03f3e8 (Добавлена нормальная долгосрочная память)
    
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
    
<<<<<<< HEAD
    while True:
        try:
=======
    print(f"\n💾 В памяти: {stats['past_conversations']} прошлых разговоров")
    print(f"💬 Сейчас: {stats['current_messages']} сообщений в этом диалоге")
    
    print("\nКоманды:")
    print("  /quit      - выход (разговор сохранится в память)")
    print("  /stats     - статистика")
    print("  /memclear  - очистить всю память")
    print("-"*60)
    print("💡 При завершении работы суть разговора сохранится в память!")
    print("💡 При следующем запуске я вспомню прошлые разговоры!")
    print("-"*60)
    
    try:
        while True:
>>>>>>> b03f3e8 (Добавлена нормальная долгосрочная память)
            user_input = input("\n👤 Вы: ").strip()
            
            if not user_input:
                continue
            
            if user_input == "/quit":
                print("\n🔄 Сохраняю разговор...")
                assistant.memory.finish_conversation()
                print("👋 До свидания!")
                break
<<<<<<< HEAD
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
=======
            elif user_input == "/stats":
                stats = assistant.get_stats()
                print(f"\n📊 Статистика:")
                print(f"   Прошлых разговоров: {stats['past_conversations']}")
                print(f"   Сообщений в текущем: {stats['current_messages']}")
                continue
            elif user_input == "/memclear":
                confirm = input("⚠️ Очистить ВСЮ память? (yes/no): ")
                if confirm.lower() == "yes":
                    assistant.clear_memory()
                    print("✅ Память очищена")
                continue
            
            response = assistant.send(user_input)
            print(f"🤖 Ассистент: {response}")
            
    except KeyboardInterrupt:
        assistant.handle_shutdown(None, None)
>>>>>>> b03f3e8 (Добавлена нормальная долгосрочная память)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
