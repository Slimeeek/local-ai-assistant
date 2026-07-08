import ollama
from typing import Generator
from .base import BaseLLM

class OllamaClient(BaseLLM):
    def __init__(self, model: str = "llama3.2:3b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self.client = ollama.Client(host=host)
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat(model=self.model, messages=messages)
        return response["message"]["content"]
    
    def stream(self, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        stream = self.client.chat(model=self.model, messages=messages, stream=True)
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
            print(f"[DEBUG] Ollama response: {response}")
            
            # Пробуем разные варианты структуры ответа
            if "models" in response:
                models = response["models"]
            elif "data" in response:
                models = response["data"]
            else:
                print(f"[ERROR] Неизвестная структура ответа: {response.keys()}")
                return []
            
            model_names = []
            for m in models:
                print(f"[DEBUG] Model entry: {m}")
                # Пробуем разные ключи
                name = m.get("name") or m.get("model") or m.get("modelName")
                if name:
                    model_names.append(name)
            
            print(f"[INFO] Найдено моделей: {len(model_names)}")
            return model_names
            
        except Exception as e:
            print(f"[ERROR] Не удалось получить список моделей: {e}")
            import traceback
            traceback.print_exc()
            return []
