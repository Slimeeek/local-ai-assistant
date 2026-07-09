"""
Менеджер личностей (personas).
Загружает личности из Markdown файлов с YAML frontmatter.
"""

from pathlib import Path
from typing import Optional
import re


class PersonaManager:
    def __init__(self, personas_dir: str = "./personas"):
        self.personas_dir = Path(personas_dir)
        self.personas_dir.mkdir(parents=True, exist_ok=True)
        
        self.personas = {}  # id -> persona data
        self.current_persona_id = "default"
        
        self._load_all_personas()
    
    def _load_all_personas(self):
        """Загружает все личности из папки personas/"""
        for file_path in self.personas_dir.glob("*.md"):
            try:
                persona = self._load_persona_file(file_path)
                if persona:
                    self.personas[persona["id"]] = persona
                    print(f"  ✅ Загружена личность: {persona['name']} ({persona['id']})")
            except Exception as e:
                print(f"  ❌ Ошибка загрузки {file_path}: {e}")
        
        # Если нет ни одной личности — создаём дефолтную
        if not self.personas:
            print("  ⚠️ Личности не найдены, создаю дефолтную...")
            self._create_default_persona()
            self._load_all_personas()
        
        print(f"📊 Всего загружено личностей: {len(self.personas)}")
    
    def _load_persona_file(self, file_path: Path) -> Optional[dict]:
        """Загружает одну личность из MD файла"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Парсим frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
        if not frontmatter_match:
            print(f"  ⚠️ Нет frontmatter в {file_path}")
            return None
        
        frontmatter_text = frontmatter_match.group(1)
        system_prompt = frontmatter_match.group(2).strip()
        
        # Парсим поля
        metadata = self._parse_frontmatter(frontmatter_text)
        
        # Обязательные поля
        if "id" not in metadata:
            metadata["id"] = file_path.stem
        if "name" not in metadata:
            metadata["name"] = metadata["id"].title()
        
        metadata["system_prompt"] = system_prompt
        metadata["file_path"] = file_path
        
        return metadata
    
    def _parse_frontmatter(self, text: str) -> dict:
        """Парсит YAML frontmatter (упрощённый парсер)"""
        result = {}
        current_key = None
        current_list = None
        
        for line in text.split("\n"):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Начало списка
            if line_stripped.startswith("- ") and current_key:
                if current_list is None:
                    current_list = []
                current_list.append(line_stripped[2:].strip())
                result[current_key] = current_list
                continue
            
            # Ключ: значение
            if ":" in line_stripped and not line_stripped.startswith("-"):
                # Сохраняем предыдущий список если был
                current_list = None
                
                key, value = line_stripped.split(":", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                current_key = key
                
                if value:
                    # Попытка преобразовать в число
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                    result[key] = value
                else:
                    # Пустое значение — возможно начало списка
                    result[key] = []
                    current_list = result[key]
        
        return result
    
    def _create_default_persona(self):
        """Создаёт дефолтную личность если папка пуста"""
        default_content = """---
id: default
name: Обычный Ассистент
description: Стандартный дружелюбный ИИ-ассистент
emoji: 🤖
style: дружелюбный, нейтральный
traits:
  - helpful
  - friendly
  - polite
greeting: "Привет! Я твой ИИ-ассистент. Чем могу помочь?"
---

Ты полезный ИИ-ассистент. Отвечай на русском языке.
Будь дружелюбным, вежливым и помогай пользователю.
Используй информацию из воспоминаний естественно, не упоминая явно "я помню что...".
"""
        file_path = self.personas_dir / "default.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(default_content)
    
    def list_personas(self) -> list:
        """Возвращает список всех доступных личностей"""
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "emoji": p.get("emoji", "🤖"),
                "description": p.get("description", ""),
            }
            for p in self.personas.values()
        ]
    
    def get_persona(self, persona_id: str) -> Optional[dict]:
        """Получить личность по ID"""
        return self.personas.get(persona_id)
    
    def get_current(self) -> dict:
        """Получить текущую личность"""
        return self.personas.get(self.current_persona_id, self.personas.get("default"))
    
    def set_current(self, persona_id: str) -> bool:
        """Сменить текущую личность"""
        if persona_id in self.personas:
            self.current_persona_id = persona_id
            return True
        return False
    
    def build_system_prompt(self, base_prompt: str = "") -> str:
        """
        Строит итоговый системный промпт с учётом текущей личности.
        Личность переопределяет базовый промпт.
        """
        persona = self.get_current()
        if not persona:
            return base_prompt
        
        persona_prompt = persona.get("system_prompt", "")
        
        # Объединяем: базовый промпт + промпт личности
        if base_prompt and persona_prompt:
            return f"{base_prompt}\n\n{persona_prompt}"
        elif persona_prompt:
            return persona_prompt
        else:
            return base_prompt
    
    def get_greeting(self) -> str:
        """Получить приветствие текущей личности"""
        persona = self.get_current()
        if persona and persona.get("greeting"):
            return persona["greeting"]
        return ""
