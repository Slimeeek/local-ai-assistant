#!/usr/bin/env python3
"""
Локальный ИИ ассистент с умной памятью
Сохраняет суть разговора при завершении
"""

import sys
import signal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import ollama
from memory.smart_memory import SmartMemory

def load_config():
    import yaml
    config_path = Path("config/base.yaml")
    if not config_path.exists():
        return None
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

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
    
    config = load_config()
    if not config:
        print("❌ Ошибка: не найден config/base.yaml")
        return 1
    
    model = config['llm']['model']
    print(f"📦 Модель: {model}")
    
    try:
        ollama.list()
    except Exception as e:
        print(f"❌ Ollama не запущен: {e}")
        return 1
    
    assistant = Assistant(model)
    stats = assistant.get_stats()
    
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
            user_input = input("\n👤 Вы: ").strip()
            
            if not user_input:
                continue
            
            if user_input == "/quit":
                print("\n🔄 Сохраняю разговор...")
                assistant.memory.finish_conversation()
                print("👋 До свидания!")
                break
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
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
