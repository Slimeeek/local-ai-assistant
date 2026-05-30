"""
Долгосрочная память для ИИ ассистента
Использует ChromaDB для векторного хранения
"""

import chromadb
from chromadb.utils import embedding_functions
import hashlib
import json
from datetime import datetime
from pathlib import Path

class LongTermMemory:
    def __init__(self, persist_directory="data/chromadb"):
        """Инициализация памяти"""
        # Создаём папку для БД
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Подключаем ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Используем простое эмбеддинг-функцию (работает локально)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Создаём или получаем коллекцию
        self.collection = self.client.get_or_create_collection(
            name="conversation_memory",
            embedding_function=self.embedding_fn,
            metadata={"description": "Долгосрочная память ассистента"}
        )
        
        print(f"🧠 Память инициализирована (коллекция: conversation_memory)")
    
    def add_memory(self, user_message, assistant_response, metadata=None):
        """Сохраняет диалог в память"""
        try:
            # Создаём уникальный ID
            memory_id = hashlib.md5(
                f"{datetime.now().timestamp()}{user_message}".encode()
            ).hexdigest()
            
            # Формируем текст для хранения
            memory_text = f"Пользователь: {user_message}\nАссистент: {assistant_response}"
            
            # Метаданные
            if metadata is None:
                metadata = {}
            metadata.update({
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message[:100],
                "assistant_response": assistant_response[:100]
            })
            
            # Сохраняем
            self.collection.add(
                documents=[memory_text],
                metadatas=[metadata],
                ids=[memory_id]
            )
            
            return True
        except Exception as e:
            print(f"Ошибка сохранения памяти: {e}")
            return False
    
    def search_memories(self, query, top_k=5):
        """Ищет похожие воспоминания"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            if results['documents'] and results['documents'][0]:
                return results['documents'][0]
            return []
        except Exception as e:
            print(f"Ошибка поиска памяти: {e}")
            return []
    
    def get_recent_memories(self, limit=10):
        """Получает последние воспоминания"""
        try:
            # Получаем все записи
            all_memories = self.collection.get(limit=limit)
            if all_memories['documents']:
                return all_memories['documents']
            return []
        except Exception as e:
            print(f"Ошибка получения последних воспоминаний: {e}")
            return []
    
    def clear_all(self):
        """Очищает всю память (осторожно!)"""
        try:
            self.client.delete_collection("conversation_memory")
            # Пересоздаём коллекцию
            self.collection = self.client.create_collection(
                name="conversation_memory",
                embedding_function=self.embedding_fn
            )
            print("🧹 Память очищена")
            return True
        except Exception as e:
            print(f"Ошибка очистки: {e}")
            return False
    
    def get_stats(self):
        """Возвращает статистику памяти"""
        try:
            count = self.collection.count()
            return {
                "total_memories": count,
                "collection_name": "conversation_memory"
            }
        except Exception as e:
            return {"error": str(e)}
