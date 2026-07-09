"""
Obsidian-хранилище памяти с структурированными метаданными.
Вдохновлено: https://habr.com/ru/articles/1033746/
"""

from pathlib import Path
from datetime import datetime
from typing import Optional
import re


class ObsidianManager:
    def __init__(self, vault_path: str = "./obsidian_vault"):
        self.vault_path = Path(vault_path)
        self.memories_path = self.vault_path / "memories"
        
        # Папки по типам памяти (не по категориям!)
        for mem_type in ["core", "fact", "insight", "dialog"]:
            (self.memories_path / mem_type).mkdir(parents=True, exist_ok=True)
    
    def save_memory(
        self,
        content: str,
        mem_type: str = "fact",          # core | fact | insight | dialog
        artifact_sign: str = "факт",      # факт | гипотеза | предпочтение | событие | диалог
        title: Optional[str] = None,
        tags: list = None,
        level: int = 3,                   # 1-5 (важность)
        status: str = "active",           # active | archived
    ) -> Path:
        """
        Сохранить воспоминание с полной структурой метаданных.
        
        type (mem_type): роль в памяти
          - core: ядро личности (имя, профессия, базовые предпочтения)
          - fact: конкретный извлечённый факт
          - insight: вывод, намерение, изменение состояния
          - dialog: краткое саммари диалога (хранится, но редко используется)
        
        artifact_sign: смысловая роль материала
          - факт, гипотеза, предпочтение, событие, диалог, решение
        
        level: 1 (мелочь) — 5 (критично)
        status: active (используется) | archived (забыто)
        """
        if tags is None:
            tags = []
        
        if not title:
            title = content[:50].replace("\n", " ").strip()
            if len(content) > 50:
                title += "..."
        
        safe_title = re.sub(r'[^\w\sа-яА-ЯёЁ\-]', '', title)
        safe_title = safe_title.replace(' ', '_').lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{safe_title[:40]}.md"
        
        type_path = self.memories_path / mem_type
        file_path = type_path / filename
        
        tags_yaml = "\n".join([f"  - {tag}" for tag in tags]) if tags else "  []"
        
        frontmatter = f"""---
type: {mem_type}
artifact_sign: {artifact_sign}
title: "{title}"
created: {datetime.now().isoformat()}
level: {level}
status: {status}
tags:
{tags_yaml}
---

"""
        memory_content = f"{frontmatter}{content}\n"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(memory_content)
        
        return file_path
    
    def load_memory(self, file_path: Path) -> dict:
        """Загрузить воспоминание с парсингом frontmatter"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        metadata = {}
        body = content
        
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            body = content[frontmatter_match.end():]
            
            for line in frontmatter_text.split("\n"):
                if ":" in line and not line.strip().startswith("-") and not line.strip().startswith("tags"):
                    key, value = line.split(":", 1)
                    val = value.strip().strip('"')
                    
                    # Конвертируем числовые значения
                    if key.strip() == "level":
                        try:
                            val = int(val)
                        except ValueError:
                            val = 3
                    
                    metadata[key.strip()] = val
            
            # Парсим теги отдельно
            tags_match = re.search(r'tags:\n((?:\s+-\s+[^\n]+\n?)+)', frontmatter_text)
            if tags_match:
                tags_text = tags_match.group(1)
                tags = [t.strip().lstrip('- ').strip() for t in tags_text.strip().split('\n') if t.strip()]
                metadata["tags"] = tags
        
        return {
            "metadata": metadata,
            "content": body.strip(),
            "file_path": file_path,
            "modified": file_path.stat().st_mtime
        }
    
    def list_memories(self, mem_type: Optional[str] = None, status: str = "active") -> list:
        """Получить список воспоминаний с фильтром по статусу"""
        memories = []
        
        if mem_type:
            search_paths = [self.memories_path / mem_type]
        else:
            search_paths = [self.memories_path]
        
        for path in search_paths:
            if path.exists():
                for file_path in path.glob("*.md"):
                    try:
                        memory = self.load_memory(file_path)
                        # Фильтр по статусу
                        if memory["metadata"].get("status", "active") == status:
                            memories.append(memory)
                    except Exception as e:
                        print(f"[WARNING] Не удалось загрузить {file_path}: {e}")
        
        return memories
    
    def search(self, query: str, mem_type: Optional[str] = None, min_level: int = 1) -> list:
        """
        Умный поиск по содержимому с учётом типа и важности.
        Приоритет: high-level facts > insights > dialogs
        """
        memories = self.list_memories(mem_type=mem_type)
        results = []
        
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 2]
        
        for memory in memories:
            # Фильтр по уровню
            level = memory["metadata"].get("level", 3)
            if level < min_level:
                continue
            
            content_lower = memory["content"].lower()
            title_lower = memory["metadata"].get("title", "").lower()
            tags = memory["metadata"].get("tags", [])
            if isinstance(tags, list):
                tags_lower = " ".join(tags).lower()
            else:
                tags_lower = str(tags).lower()
            
            # Подсчёт релевантности
            score = 0
            
            # Точное вхождение
            if query_lower in content_lower:
                score += 15
            if query_lower in title_lower:
                score += 20
            if query_lower in tags_lower:
                score += 10
            
            # Вхождение отдельных слов
            for word in query_words:
                if word in content_lower:
                    score += 2
                if word in title_lower:
                    score += 3
                if word in tags_lower:
                    score += 3
            
            # Бонус за важность (level)
            score += level * 0.5
            
            # Бонус/штраф за тип
            mem_type = memory["metadata"].get("type", "fact")
            if mem_type == "core":
                score += 5    # ядро — всегда важно
            elif mem_type == "fact":
                score += 3    # факты важнее диалогов
            elif mem_type == "insight":
                score += 2
            elif mem_type == "dialog":
                score -= 5    # диалоги — в последнюю очередь
            
            if score > 3:  # минимальный порог релевантности
                memory["relevance_score"] = score
                results.append(memory)
        
        # Сортируем: сначала релевантность, потом свежесть
        results.sort(key=lambda x: (x["relevance_score"], x["modified"]), reverse=True)
        
        return results
    
    def find_similar(self, content: str, mem_type: Optional[str] = None, threshold: float = 0.7) -> list:
        """
        Найти похожие воспоминания (для дедупликации).
        Использует простое сравнение по словам.
        """
        memories = self.list_memories(mem_type=mem_type)
        similar = []
        
        content_words = set(re.findall(r'\b\w{4,}\b', content.lower()))
        if not content_words:
            return similar
        
        for memory in memories:
            mem_words = set(re.findall(r'\b\w{4,}\b', memory["content"].lower()))
            if not mem_words:
                continue
            
            # Jaccard similarity
            intersection = content_words & mem_words
            union = content_words | mem_words
            similarity = len(intersection) / len(union) if union else 0
            
            if similarity >= threshold:
                memory["similarity"] = similarity
                similar.append(memory)
        
        similar.sort(key=lambda x: x["similarity"], reverse=True)
        return similar
    
    def get_core(self) -> list:
        """Получить ядро личности (всегда active)"""
        return self.list_memories(mem_type="core")
    
    def get_stats(self) -> dict:
        stats = {
            "total_memories": 0,
            "by_type": {},
            "by_status": {"active": 0, "archived": 0},
            "total_size_bytes": 0
        }
        
        for type_path in self.memories_path.iterdir():
            if type_path.is_dir():
                files = list(type_path.glob("*.md"))
                stats["by_type"][type_path.name] = len(files)
                stats["total_memories"] += len(files)
                
                for f in files:
                    stats["total_size_bytes"] += f.stat().st_size
                    try:
                        content = f.read_text(encoding="utf-8")
                        if "status: archived" in content:
                            stats["by_status"]["archived"] += 1
                        else:
                            stats["by_status"]["active"] += 1
                    except:
                        pass
        
        return stats
