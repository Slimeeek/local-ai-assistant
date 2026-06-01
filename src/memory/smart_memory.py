"""
Умная память - сохраняет суть всего разговора при завершении
"""

import json
import re
from pathlib import Path
from datetime import datetime
import ollama

class SmartMemory:
    def __init__(self, model, memory_file="data/memory.json"):
        self.model = model
        self.memory_file = Path(memory_file)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Текущий разговор (временный)
        self.current_conversation = []
        
        # Загружаем прошлые разговоры
        self.past_conversations = self.load()
    
    def load(self):
        """Загружает прошлые разговоры из файла"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("conversations", [])
            except:
                pass
        return []
    
    def save(self):
        """Сохраняет все разговоры в файл"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump({
                "conversations": self.past_conversations,
                "last_updated": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def add_to_current(self, user_msg, assistant_msg):
        """Добавляет сообщение в текущий разговор"""
        self.current_conversation.append({
            "user": user_msg,
            "assistant": assistant_msg,
            "timestamp": datetime.now().isoformat()
        })
    
    def summarize_conversation(self, conversation):
        """Извлекает суть разговора с помощью LLM"""
        if not conversation:
            return None
        
        # Формируем текст разговора
        conv_text = ""
        for msg in conversation:
            conv_text += f"Пользователь: {msg['user']}\n"
            conv_text += f"Ассистент: {msg['assistant']}\n\n"
        
        prompt = f"""Проанализируй этот разговор и извлеки ВАЖНУЮ информацию о пользователе.
Также кратко опиши, о чём был разговор.

Разговор:
{conv_text}

Ответь в формате JSON:
{{
    "summary": "краткая суть разговора (1-2 предложения)",
    "facts": {{
        "имя": "имя пользователя (если называлось)",
        "хобби": "хобби (если упоминалось)",
        "интересы": "интересы (если упоминались)",
        "предпочтения": "предпочтения (если упоминались)",
        "важно": "другая важная информация"
    }}
}}

Если информация не упоминалась, оставляй поле пустым.
Только JSON, без лишнего текста:"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={'temperature': 0.3, 'num_predict': 500}
            )
            
            text = response['message']['content']
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
        except Exception as e:
            print(f"⚠️ Ошибка извлечения сути: {e}")
        
        return None
    
    def finish_conversation(self):
        """Завершает текущий разговор - извлекает суть и сохраняет в память"""
        if not self.current_conversation:
            return
        
        print("\n🧠 Анализирую разговор для сохранения в память...")
        
        # Извлекаем суть разговора
        summary_data = self.summarize_conversation(self.current_conversation)
        
        if summary_data:
            # Сохраняем в список прошлых разговоров
            self.past_conversations.append({
                "id": len(self.past_conversations),
                "timestamp": datetime.now().isoformat(),
                "summary": summary_data.get("summary", ""),
                "facts": summary_data.get("facts", {}),
                "length": len(self.current_conversation)
            })
            
            # Ограничиваем количество сохраняемых разговоров (последние 20)
            if len(self.past_conversations) > 20:
                self.past_conversations = self.past_conversations[-20:]
            
            self.save()
            print(f"✅ Разговор сохранён в память!")
            if summary_data.get("summary"):
                print(f"   📝 Суть: {summary_data['summary'][:100]}...")
        else:
            print("⚠️ Не удалось извлечь суть разговора")
        
        # Очищаем текущий разговор
        self.current_conversation = []
    
    def get_memory_context(self, query=""):
        """Возвращает контекст из прошлых разговоров"""
        if not self.past_conversations:
            return ""
        
        context = "\n\n[ИЗ ПРОШЛЫХ РАЗГОВОРОВ]:\n"
        
        # Собираем все факты и суть из прошлых разговоров
        all_facts = {}
        all_summaries = []
        
        for conv in self.past_conversations[-5:]:  # последние 5 разговоров
            facts = conv.get("facts", {})
            for key, value in facts.items():
                if value and value != "None" and value != "":
                    all_facts[key] = value
            
            summary = conv.get("summary", "")
            if summary:
                all_summaries.append(summary)
        
        # Добавляем факты
        if all_facts:
            context += "\n[ЧТО Я ЗНАЮ О ПОЛЬЗОВАТЕЛЕ]:\n"
            for key, value in all_facts.items():
                context += f"- {key}: {value}\n"
        
        # Добавляем суть прошлых разговоров
        if all_summaries:
            context += "\n[СУТЬ ПРОШЛЫХ РАЗГОВОРОВ]:\n"
            for i, summary in enumerate(all_summaries[-3:], 1):
                context += f"{i}. {summary}\n"
        
        return context
    
    def get_stats(self):
        return {
            "past_conversations": len(self.past_conversations),
            "current_messages": len(self.current_conversation),
            "saved_facts": len(self.past_conversations)  # приблизительно
        }
    
    def clear(self):
        """Очищает всю память"""
        self.past_conversations = []
        self.current_conversation = []
        self.save()
        print("🗑️ Вся память очищена")
