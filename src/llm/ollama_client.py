import ollama
from typing import Generator, List, Dict, Optional
from .base import BaseLLM

class OllamaClient(BaseLLM):
    def __init__(self, model: str = "llama3.2:3b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self.client = ollama.Client(host=host)
    
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str = ""
    ) -> str:
        """
        Генерация ответа с историей сообщений.
        
        Args:
            messages: Список сообщений [{"role": "user", "content": "..."}, ...]
            system_prompt: Системный промпт (опционально)
        """
        full_messages = []
        
        # Добавляем system prompt если есть
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        # Добавляем историю сообщений
        full_messages.extend(messages)
        
        response = self.client.chat(model=self.model, messages=full_messages)
        return response["message"]["content"]
    
    def stream(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str = ""
    ) -> Generator[str, None, None]:
        """Стриминг ответа с историей"""
        full_messages = []
        
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        full_messages.extend(messages)
        
        stream = self.client.chat(model=self.model, messages=full_messages, stream=True)
        for chunk in stream:
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]
    
    def is_available(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception:
            return False
    
    def list_models(self) -> list:
        """Получить список доступных моделей"""
        try:
            response = self.client.list()
            
            # Новый формат ответа ollama (объект с полем models)
            if hasattr(response, 'models'):
                models = response.models
            elif isinstance(response, dict):
                models = response.get("models", [])
            else:
                print(f"[ERROR] Неизвестный формат ответа: {type(response)}")
                return []
            
            model_names = []
            for m in models:
                # Поддержка разных форматов
                if hasattr(m, 'model'):
                    name = m.model
                elif isinstance(m, dict):
                    name = m.get("name") or m.get("model") or m.get("modelName")
                else:
                    name = str(m)
                
                if name:
                    model_names.append(name)
            
            print(f"[INFO] Найдено моделей: {len(model_names)}")
            return model_names
            
        except Exception as e:
            print(f"[ERROR] Не удалось получить список моделей: {e}")
            import traceback
            traceback.print_exc()
            return []
