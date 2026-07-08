from abc import ABC, abstractmethod
from typing import Generator

class BaseLLM(ABC):
    """Абстрактный класс для LLM провайдеров"""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Генерация ответа"""
        pass
    
    @abstractmethod
    def stream(self, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
        """Стриминг ответа"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверка доступности модели"""
        pass
