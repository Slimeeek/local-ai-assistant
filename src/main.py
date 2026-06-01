#!/usr/bin/env python3
"""
Локальный ИИ ассистент - модель сама управляет своей памятью
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

import ollama
from core.logger import logger

def load_config():
    import yaml
    config_path = Path("config/base.yaml")
    if not config_path.exists():
        return None
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class Memory:
    """Простое хранилище фактов (модель сама решает, что сюда писать)"""
    
    def __init__(self, memory_file="data/memory.json"):
        self.memory_file = Path(memory_file)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.facts = self.load()
    
    def load(self):
        if self.memory_file.exists():
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save(self):
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.facts, f, ensure_ascii=False, indent=2)
    
    def add(self, key, value):
        self.facts[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self.save()
        return True
    
    def get(self, key):
        return self.facts.get(key, {}).get("value")
    
    def get_all(self):
        return {k: v["value"] for k, v in self.facts.items()}
    
    def delete(self, key):
        if key in self.facts:
            del self.facts[key]
            self.save()
            return True
        return False
    
    def clear(self):
        self.facts = {}
        self.save()
        return True

class Assistant:
    def __init__(self, model):
        self.model = model
        self.memory = Memory()
        self.messages = []
        
        # Загружаем воспоминания в системный промпт
        memories = self.memory.get_all()
        memory_text = ""
        if memories:
            memory_text = "\n\nВот что я запомнил о пользователе:\n"
            for key, value in memories.items():
                memory_text += f"- {key}: {value}\n"
            memory_text += "\nЭто информация из прошлых разговоров. Используй её, чтобы отвечать лучше."
        
        # Системный промпт с инструкцией по работе с памятью
        self.system_prompt = f"""Ты - полезный ИИ-ассистент. Отвечай на русском языке, естественно и без лишних приветствий, если мы уже общаемся.

ВАЖНО: У тебя есть возможность запоминать информацию и использовать её в будущем.

Чтобы запомнить что-то, используй команду REMEMBER в своём ответе:
REMEMBER: ключ = значение

Например:
- REMEMBER: имя = Никита
- REMEMBER: любимое число = 42
- REMEMBER: любимая игра = Minecraft

Команду можно вставить в любое место ответа. Она не будет видна пользователю, но информация сохранится в память.

Чтобы удалить информацию, используй FORGET: ключ

Используй эту возможность, когда пользователь:
- представляется (запомни имя)
- говорит о своих предпочтениях
- просит что-то запомнить
- сообщает важную информацию о себе

Используй запомненную информацию в будущем, чтобы персонализировать ответы.

{memory_text}

Запомни: ты сам решаешь, что важно запомнить. Не запоминай каждое слово, только важные факты."""
        
        self.messages.append({"role": "system", "content": self.system_prompt})
    
    def process_memory_commands(self, response):
        """Обрабатывает команды REMEMBER и FORGET в ответе модели"""
        import re
        
        processed_response = response
        
        # Ищем REMEMBER команды
        remember_pattern = r'REMEMBER:\s*([^=]+?)\s*=\s*([^\n]+)'
        remembers = re.findall(remember_pattern, response, re.IGNORECASE)
        
        for key, value in remembers:
            key = key.strip()
            value = value.strip()
            self.memory.add(key, value)
            print(f"🧠 Запомнил: {key} = {value}")
            # Удаляем команду из ответа
            processed_response = re.sub(
                r'REMEMBER:\s*[^=]+?\s*=\s*[^\n]+\n?', 
                '', 
                processed_response, 
                flags=re.IGNORECASE
            )
        
        # Ищем FORGET команды
        forget_pattern = r'FORGET:\s*([^\n]+)'
        forgets = re.findall(forget_pattern, response, re.IGNORECASE)
        
        for key in forgets:
            key = key.strip()
            if self.memory.delete(key):
                print(f"🗑️ Забыл: {key}")
            processed_response = re.sub(
                r'FORGET:\s*[^\n]+\n?', 
                '', 
                processed_response, 
                flags=re.IGNORECASE
            )
        
        # Обновляем системный промпт, если память изменилась
        if remembers or forgets:
            self.update_system_prompt()
        
        # Чистим лишние пустые строки
        processed_response = re.sub(r'\n{3,}', '\n\n', processed_response)
        
        return processed_response.strip()
    
    def update_system_prompt(self):
        """Обновляет системный промпт с новыми воспоминаниями"""
        memories = self.memory.get_all()
        memory_text = ""
        if memories:
            memory_text = "\n\nВот что я запомнил о пользователе:\n"
            for key, value in memories.items():
                memory_text += f"- {key}: {value}\n"
            memory_text += "\nЭто информация из прошлых разговоров."
        
        new_prompt = f"""Ты - полезный ИИ-ассистент. Отвечай на русском языке, естественно и без лишних приветствий, если мы уже общаемся.

ВАЖНО: У тебя есть возможность запоминать информацию и использовать её в будущем.

Чтобы запомнить что-то, используй команду REMEMBER в своём ответе:
REMEMBER: ключ = значение

Чтобы удалить информацию, используй FORGET: ключ

{memory_text}

Запомни: ты сам решаешь, что важно запомнить."""
        
        self.messages[0] = {"role": "system", "content": new_prompt}
    
    def send(self, user_message):
        """Отправляет сообщение и обрабатывает ответ"""
        
        self.messages.append({"role": "user", "content": user_message})
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=self.messages,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                }
            )
            
            raw_response = response['message']['content']
            
            # Обрабатываем команды памяти
            clean_response = self.process_memory_commands(raw_response)
            
            # Сохраняем в историю
            self.messages.append({"role": "assistant", "content": clean_response})
            
            # Ограничиваем историю
            if len(self.messages) > 21:
                self.messages = [self.messages[0]] + self.messages[-20:]
            
            return clean_response
            
        except Exception as e:
            return f"Ошибка: {str(e)}"
    
    def get_stats(self):
        memories = self.memory.get_all()
        return {
            "messages": len(self.messages) - 1,
            "memories": len(memories),
            "memory_content": memories
        }
    
    def clear_memory(self):
        self.memory.clear()
        self.update_system_prompt()
        return "✅ Вся память очищена"

def main():
    print("\n" + "="*60)
    print("🤖 Локальный ИИ ассистент (с САМОСТОЯТЕЛЬНОЙ памятью)")
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
    
    print(f"\n💾 В памяти: {stats['memories']} фактов")
    
    if stats['memories'] > 0:
        print("\n📚 Известные факты:")
        for key, value in stats['memory_content'].items():
            print(f"   • {key}: {value}")
    
    print("\nКоманды:")
    print("  /quit      - выход")
    print("  /stats     - статистика")
    print("  /mem       - показать память")
    print("  /memclear  - очистить память")
    print("-"*60)
    print("💡 Модель САМА решает, что запомнить, и САМА использует память!")
    print("-"*60)
    
    try:
        while True:
            user_input = input("\n👤 Вы: ").strip()
            
            if not user_input:
                continue
            
            if user_input == "/quit":
                print("👋 До свидания!")
                break
            elif user_input == "/stats":
                stats = assistant.get_stats()
                print(f"\n📊 Статистика:")
                print(f"   Сообщений в диалоге: {stats['messages']}")
                print(f"   Фактов в памяти: {stats['memories']}")
                continue
            elif user_input == "/mem":
                stats = assistant.get_stats()
                if stats['memories'] > 0:
                    print("\n📚 Что я помню:")
                    for key, value in stats['memory_content'].items():
                        print(f"   • {key}: {value}")
                else:
                    print("\n📭 Память пуста")
                continue
            elif user_input == "/memclear":
                confirm = input("⚠️ Точно очистить память? (yes/no): ")
                if confirm.lower() == "yes":
                    assistant.clear_memory()
                    print("✅ Память очищена")
                continue
            
            print("🤔 Думаю...", end="", flush=True)
            response = assistant.send(user_input)
            print("\r" + " "*30 + "\r", end="")
            print(f"🤖 Ассистент: {response}")
            
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
