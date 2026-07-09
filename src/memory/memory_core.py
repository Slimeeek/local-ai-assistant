"""
Главный класс памяти. Только Obsidian, без векторной БД.
"""

from .obsidian_manager import ObsidianManager
from typing import Optional


class HybridMemory:
    def __init__(self, vault_path: str = "./obsidian_vault"):
        print("[INFO] Инициализация системы памяти...")
        self.obsidian = ObsidianManager(vault_path=vault_path)
        print("[INFO] Система памяти готова")
    
    def remember(
        self,
        content: str,
        mem_type: str = "fact",
        artifact_sign: str = "факт",
        title: Optional[str] = None,
        tags: list = None,
        level: int = 3,
        check_duplicate: bool = True,
    ) -> Optional[dict]:
        """
        Сохранить воспоминание с проверкой на дубликаты.
        
        Returns:
            dict с путём файла или None (если дубликат)
        """
        if tags is None:
            tags = []
        
        # Проверка на дубликат (для core и fact)
        if check_duplicate and mem_type in ["core", "fact"]:
            similar = self.obsidian.find_similar(content, mem_type=mem_type, threshold=0.6)
            if similar:
                print(f"  ⏭️  [{mem_type}] Дубликат найден ({similar[0]['similarity']:.0%}): {similar[0]['content'][:60]}")
                return None
        
        file_path = self.obsidian.save_memory(
            content=content,
            mem_type=mem_type,
            artifact_sign=artifact_sign,
            title=title,
            tags=tags,
            level=level,
        )
        
        return {
            "file_path": file_path,
            "type": mem_type,
        }
    
    def recall_for_answer(self, query: str, n_results: int = 3) -> list:
        """
        Поиск воспоминаний ДЛЯ ОТВЕТА на вопрос пользователя.
        Ищет ТОЛЬКО в facts, insights и core.
        Диалоги НЕ включаются — они мешают боту.
        """
        results = []
        
        # 1. Core — всегда добавляем (до 2 самых важных)
        core = self.obsidian.search(query, mem_type="core", min_level=3)[:2]
        results.extend(core)
        
        # 2. Facts — главные источники для ответов
        facts = self.obsidian.search(query, mem_type="fact", min_level=2)[:n_results]
        results.extend(facts)
        
        # 3. Insights — выводы и намерения
        insights = self.obsidian.search(query, mem_type="insight", min_level=2)[:2]
        results.extend(insights)
        
        # Сортируем все вместе по score
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return results[:n_results + 2]  # максимум ~5 записей
    
    def recall_about_dialogs(self, query: str, n_results: int = 3) -> list:
        """
        Поиск ПРОШЛЫХ ДИАЛОГОВ (используется только если пользователь
        ЯВНО спрашивает "о чём мы говорили", "что мы обсуждали" и т.п.)
        """
        return self.obsidian.search(query, mem_type="dialog", min_level=1)[:n_results]
    
    def get_core(self) -> list:
        """Получить ядро личности (всегда в system prompt)"""
        return self.obsidian.get_core()
    
    def get_all_memories(self, mem_type: Optional[str] = None) -> list:
        return self.obsidian.list_memories(mem_type=mem_type)
    
    def get_stats(self) -> dict:
        return {
            "obsidian": self.obsidian.get_stats()
        }
