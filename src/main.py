#!/usr/bin/env python3
"""
Локальный ИИ ассистент с сохранением контекста через официальный API
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import ollama
from core.logger import logger
from memory.vector_memory import LongTermMemory

def load_config():
    import yaml
    config_path = Path("config/base.yaml")
    if not config_path.exists():
        return None
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class OllamaChat:
    """Использует официальный API Ollama с сохранением контекста"""
    
    def __init__(self, model):
        self.model = model
        self.messages = []
        # Системный промпт
        self.messages.append({
            "role": "system",
            "content": """Ты - полезный ИИ-ассистент. 
Ты общаешься с пользователем на русском языке.
Не здоровайся в каждом сообщении - просто продолжай разговор.
Не используй китайские иероглифы.
Отвечай естественно, как в нормальном диалоге."""
        })
    
    def send(self, user_message):
        """Отправляет сообщение и возвращает ответ с сохранением контекста"""
        self.messages.append({"role": "user", "content": user_message})
        
        response = ollama.chat(
            model=self.model,
            messages=self.messages
        )
        
        assistant_message = response['message']['content']
        self.messages.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
    
    def clear_context(self):
        """Очищает контекст диалога (но оставляет системный промпт)"""
        system_prompt = self.messages[0] if self.messages else None
        self.messages = [system_prompt] if system_prompt else []
        print("🗑️ Контекст диалога очищен")
    
    def get_context_length(self):
        return len(self.messages)

def main():
    print("\n" + "="*60)
    print("🤖 Локальный ИИ ассистент - ПОЛНЫЙ КОНТЕКСТ ДИАЛОГА")
    print("="*60)
    
    config = load_config()
    if not config:
        print("❌ Ошибка: не найден config/base.yaml")
        return 1
    
    model = config['llm']['model']
    print(f"📦 Модель: {model}")
    
    # Проверяем наличие модели
    try:
        ollama.list()
    except Exception as e:
        print(f"❌ Ollama не запущен: {e}")
        print("Запустите: ollama serve")
        return 1
    
    # Инициализация чата с сохранением контекста
    chat = OllamaChat(model)
    
    # Долгосрочная память
    long_memory = LongTermMemory()
    stats = long_memory.get_stats()
    print(f"💾 Долгосрочная память: {stats['total_memories']} воспоминаний")
    
    print("\nКоманды:")
    print("  /quit     - выход")
    print("  /clear    - очистить контекст текущего диалога")
    print("  /stats    - статистика памяти")
    print("-"*60)
    print("💡 Модель ПОМНИТ ВСЕ предыдущие сообщения в этой сессии!")
    print("-"*60)
    
    try:
        while True:
            user_input = input("\n👤 Вы: ").strip()
            
            if not user_input:
                continue
            
            if user_input == "/quit":
                print("👋 До свидания!")
                break
            elif user_input == "/clear":
                chat.clear_context()
                continue
            elif user_input == "/stats":
                stats = long_memory.get_stats()
                print(f"📊 Статистика:")
                print(f"   Текущий контекст: {chat.get_context_length() - 1} сообщений")
                print(f"   Долгосрочная память: {stats['total_memories']} воспоминаний")
                continue
            
            print("🤔 Думаю...", end="", flush=True)
            response = chat.send(user_input)
            print("\r" + " "*30 + "\r", end="")
            print(f"🤖 Ассистент: {response}")
            
            # Сохраняем в долгосрочную память (асинхронно)
            long_memory.add_memory(user_input, response)
            
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
