from abc import ABC, abstractmethod
from typing import Generator, List, Dict

class BaseLLM(ABC):
    """Абстрактный класс для LLM провайдеров"""
    
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        """Генерация ответа с историей сообщений"""
        pass
    
    @abstractmethod
    def stream(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Generator[str, None, None]:
        """Стриминг ответа"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверка доступности модели"""
        pass
