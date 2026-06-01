"""
Долгосрочная память на базе Mem0 + EMBEDDED Qdrant
Адаптировано под mem0ai 2.0.4
"""

from mem0 import Memory
from pathlib import Path
import uuid

def create_embedded_config(project_path):
    """Создаёт конфигурацию Mem0 с embedded Qdrant (без Docker)"""
    
    data_dir = Path(project_path) / "data"
    data_dir.mkdir(exist_ok=True)
    
    config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "path": str(data_dir / "qdrant_mem0"),
                "embedding_model_dims": 768,
                "on_disk": True,
            }
        },
        "llm": {
            "provider": "ollama",
            "config": {
                "model": "llama3.2:3b",
                "ollama_base_url": "http://localhost:11434",
                "temperature": 0.1
            }
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": "nomic-embed-text",
                "ollama_base_url": "http://localhost:11434",
            }
        },
        "version": "v1.1"
    }
    
    return config

class Mem0Memory:
    def __init__(self, project_path=None):
        if project_path is None:
            project_path = Path(__file__).parent.parent.parent
        
        self.user_id = "default_user"
        self.config = create_embedded_config(project_path)
        
        print("🧠 Инициализация Mem0 (embedded Qdrant, без Docker)...")
        self.memory = Memory.from_config(self.config)
        print("✅ Mem0 готова! Данные хранятся в папке проекта.")
    
    def add_conversation(self, user_message, assistant_response):
        """Сохраняет диалог — Mem0 сама извлечёт факты"""
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_response}
        ]
        
        result = self.memory.add(
            messages,
            user_id=self.user_id,
            metadata={"timestamp": "now"}
        )
        print("🧠 Диалог сохранён в память")
        return result
    
    def search(self, query, limit=5):
        """Ищет релевантные воспоминания"""
        results = self.memory.search(
            query,
            filters={"user_id": self.user_id},
            limit=limit
        )
        
        if results and "results" in results:
            return results["results"]
        return []
    
    def format_for_context(self, query):
        """Форматирует воспоминания для контекста"""
        memories = self.search(query)
        
        if not memories:
            return ""
        
        context = "\n\n[Из прошлых разговоров я помню]:\n"
        for i, mem in enumerate(memories, 1):
            memory_text = mem.get('memory', '')
            if memory_text:
                context += f"{i}. {memory_text}\n"
        context += "\n"
        return context
    
    def get_all_memories(self):
        """Получает все воспоминания"""
        try:
            return self.memory.get_all(filters={"user_id": self.user_id})
        except Exception as e:
            print(f"Ошибка получения воспоминаний: {e}")
            return []
    
    def clear_all(self):
        """Очищает все воспоминания"""
        try:
            self.memory.delete_all(filters={"user_id": self.user_id})
            print("🗑️ Вся память очищена")
            return True
        except Exception as e:
            print(f"Ошибка очистки: {e}")
            return False
    
    def get_stats(self):
        """Статистика памяти"""
        memories = self.get_all_memories()
        return {
            "total_memories": len(memories) if memories else 0
        }
