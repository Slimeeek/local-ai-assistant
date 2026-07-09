import customtkinter as ctk
from tkinter import scrolledtext, messagebox
import threading
import json
import re
from datetime import datetime
from ..llm.ollama_client import OllamaClient
from ..memory import HybridMemory

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Local AI Assistant")
        self.geometry("1200x700")
        
        self.llm = OllamaClient()
        self.memory = HybridMemory()
        
        self.current_session_history = []
        self.is_saving = False
        
        self.base_system_prompt = """Ты полезный ИИ-ассистент с долговременной памятью. 
ОТВЕЧАЙ СТРОГО НА РУССКОМ ЯЗЫКЕ.
Будь естественным и дружелюбным.

ПРАВИЛА РАБОТЫ С ПАМЯТЬЮ:
- Информация о пользователе (core) — всегда актуальна, используй естественно.
- Факты (facts) — конкретные вещи, которые пользователь говорил. Используй если относятся к вопросу.
- Инсайты (insights) — выводы и намерения. Используй для персонализации.
- Прошлые диалоги (dialogs) — только если пользователь ЯВНО спрашивает "о чём мы говорили", "помнишь тот разговор".
- НИКОГДА не перечисляй всё подряд. Отвечай кратко и по существу.
- Не говори "я помню, что..." или "согласно моей памяти..." — используй информацию естественно."""
        
        self._create_widgets()
        self._check_ollama_connection()
        self._load_initial_memory()
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _on_closing(self):
        if self.current_session_history:
            if messagebox.askyesno("Сохранение", "Сохранить текущий диалог в память перед закрытием?"):
                self._end_session_and_save()
        self.destroy()
    
    def _load_initial_memory(self):
        print("\n" + "="*60)
        print("🧠 ЗАГРУЗКА ПАМЯТИ ПРИ СТАРТЕ")
        print("="*60)
        
        stats = self.memory.get_stats()
        obsidian_stats = stats["obsidian"]
        print(f"📊 Всего воспоминаний: {obsidian_stats['total_memories']}")
        print(f"   По типам: {obsidian_stats['by_type']}")
        
        core = self.memory.get_core()
        if core:
            print(f"\n👤 ЯДРО (core):")
            for item in core:
                level = item["metadata"].get("level", 3)
                print(f"  [lvl {level}] {item['content'][:80]}")
        
        print("="*60 + "\n")
        self._refresh_memory_list()
    
    def _check_ollama_connection(self):
        try:
            if self.llm.is_available():
                models = self.llm.list_models()
                if models:
                    self.status_label.configure(text=f"✅ Ollama ({len(models)} моделей)", text_color="green")
                else:
                    self.status_label.configure(text="⚠️ Нет моделей", text_color="orange")
            else:
                self.status_label.configure(text="❌ Ollama не доступна", text_color="red")
        except Exception as e:
            self.status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="red")
    
    def _create_widgets(self):
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        chat_frame = ctk.CTkFrame(main_container)
        chat_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        memory_frame = ctk.CTkFrame(main_container, width=350)
        memory_frame.pack(side="right", fill="both", padx=5)
        memory_frame.pack_propagate(False)
        
        self._create_chat_panel(chat_frame)
        self._create_memory_panel(memory_frame)
    
    def _create_chat_panel(self, parent):
        top_frame = ctk.CTkFrame(parent)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(top_frame, text="Модель:").pack(side="left", padx=5)
        self.model_combo = ctk.CTkComboBox(top_frame, values=[], width=200, state="readonly")
        self.model_combo.pack(side="left", padx=5)
        self.model_combo.set("Выберите модель")
        
        self.refresh_btn = ctk.CTkButton(top_frame, text="🔄", width=40, command=self._refresh_models)
        self.refresh_btn.pack(side="left", padx=5)
        
        self.end_session_btn = ctk.CTkButton(
            top_frame, text="✅ Завершить и сохранить", width=160,
            command=self._end_session_and_save, fg_color="green"
        )
        self.end_session_btn.pack(side="left", padx=5)
        
        self.status_label = ctk.CTkLabel(top_frame, text="Проверка...")
        self.status_label.pack(side="right", padx=5)
        
        self.chat_area = scrolledtext.ScrolledText(parent, wrap=ctk.WORD, font=("Arial", 12), bg="#2b2b2b", fg="#ffffff")
        self.chat_area.pack(fill="both", expand=True, padx=10, pady=5)
        self.chat_area.configure(state="disabled")
        
        input_frame = ctk.CTkFrame(parent)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        self.input_entry = ctk.CTkEntry(input_frame, placeholder_text="Введите сообщение...", font=("Arial", 12))
        self.input_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.input_entry.bind("<Return>", lambda e: self._send_message())
        
        self.send_btn = ctk.CTkButton(input_frame, text="Отправить", command=self._send_message, width=100, state="disabled")
        self.send_btn.pack(side="right", padx=5)
    
    def _create_memory_panel(self, parent):
        ctk.CTkLabel(parent, text="🧠 Память", font=("Arial", 16, "bold")).pack(pady=10)
        
        filter_frame = ctk.CTkFrame(parent)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Тип:").pack(side="left", padx=5)
        self.memory_filter = ctk.CTkComboBox(
            filter_frame, values=["все", "core", "fact", "insight", "dialog"],
            width=120, state="readonly"
        )
        self.memory_filter.pack(side="left", padx=5)
        self.memory_filter.set("все")
        
        search_frame = ctk.CTkFrame(parent)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        self.memory_search = ctk.CTkEntry(search_frame, placeholder_text="Поиск...", font=("Arial", 11))
        self.memory_search.pack(side="left", fill="x", expand=True, padx=5)
        self.memory_search.bind("<Return>", lambda e: self._search_memory())
        
        ctk.CTkButton(search_frame, text="🔍", width=40, command=self._search_memory).pack(side="right", padx=5)
        
        self.memory_list = scrolledtext.ScrolledText(parent, wrap=ctk.WORD, font=("Arial", 10), bg="#1e1e1e", fg="#ffffff", height=15)
        self.memory_list.pack(fill="both", expand=True, padx=10, pady=5)
        self.memory_list.configure(state="disabled")
        
        btn_frame = ctk.CTkFrame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(btn_frame, text="📊 Статистика", command=self._show_memory_stats, width=150).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(btn_frame, text="🔄 Обновить", command=self._refresh_memory_list, width=150).pack(side="right", padx=5, pady=5)
        
        self._refresh_memory_list()
    
    def _refresh_models(self):
        try:
            if not self.llm.is_available():
                self.status_label.configure(text="❌ Ollama не доступна", text_color="red")
                return
            
            models = self.llm.list_models()
            if not models:
                self.status_label.configure(text="⚠️ Модели не найдены", text_color="orange")
                self.model_combo.configure(values=[])
                self.model_combo.set("Выберите модель")
                self.send_btn.configure(state="disabled")
                return
            
            self.model_combo.configure(values=models)
            self.model_combo.set(models[0])
            self.llm.model = models[0]
            self.send_btn.configure(state="normal")
            self.status_label.configure(text=f"✅ {len(models)} моделей", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="red")
    
    def _build_system_prompt(self) -> str:
        """Строит системный промпт. Core — ВСЕГДА."""
        prompt = self.base_system_prompt
        
        core_memories = self.memory.get_core()
        if core_memories:
            prompt += "\n\n=== ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ (ядро личности, всегда актуально) ===\n"
            for mem in core_memories:
                prompt += f"- {mem['content']}\n"
            prompt += "=== КОНЕЦ ===\n"
        
        return prompt
    
    def _is_asking_about_past_dialogs(self, query: str) -> bool:
        """Проверяет, спрашивает ли пользователь о прошлых разговорах"""
        keywords = [
            "о чём мы говорили", "что мы обсуждали", "помнишь разговор",
            "прошлый раз", "в прошлый раз", "раньше говорили",
            "мы обсуждали", "говорили про", "помнишь, мы", "во что играли",
            "что делали", "что было", "как было", "помнишь, как"
        ]
        query_lower = query.lower()
        return any(kw in query_lower for kw in keywords)
    
    def _end_session_and_save(self):
        if not self.current_session_history:
            self._append_message("Система", "⚠️ Нет сообщений для сохранения")
            return
        
        if self.is_saving:
            return
        
        self.is_saving = True
        self.end_session_btn.configure(state="disabled", text="⏳ Сохранение...")
        
        threading.Thread(target=self._analyze_and_save_session, daemon=True).start()
    
    def _analyze_and_save_session(self):
        try:
            print(f"\n{'='*60}")
            print(f"🧠 НАЧАЛО АНАЛИЗА ДИАЛОГА")
            print(f"{'='*60}")
            
            self.after(0, lambda: self._append_message("Система", "📝 Формирую текст диалога..."))
            
            full_conversation = ""
            for msg in self.current_session_history:
                role = "Пользователь" if msg["role"] == "user" else "Ассистент"
                full_conversation += f"{role}: {msg['content']}\n\n"
            
            print(f"✅ Текст готов ({len(full_conversation)} символов)")
            self.after(0, lambda: self._append_message("Система", "🤖 Отправляю в LLM для анализа (1-3 минуты)..."))
            
            # КРИТИЧЕСКИ ВАЖНО: промпт разделяет сырой диалог и извлечённые факты
            analysis_prompt = f"""Проанализируй диалог и извлеки ЗНАНИЯ в структурированной форме.

ДИАЛОГ (СЫРОЙ МАТЕРИАЛ — это "артефакт", не факт):
{full_conversation}

Верни JSON в этом формате:
{{
  "core": [
    {{"content": "ТОЛЬКО факт о личности (имя, возраст, профессия, базовое предпочтение)", "artifact_sign": "факт|предпочтение", "level": 5, "tags": ["тег"]}}
  ],
  "facts": [
    {{"content": "ИЗВЛЕЧЁННЫЙ ФАКТ в форме утверждения (не цитата, не пересказ)", "artifact_sign": "факт|событие|предпочтение", "level": 1-5, "tags": ["тег"]}}
  ],
  "insights": [
    {{"content": "ВЫВОД, намерение или изменение состояния пользователя", "artifact_sign": "гипотеза|решение", "level": 1-5, "tags": ["тег"]}}
  ],
  "dialog_summary": {{
    "content": "Краткое саммари диалога (2-3 предложения) + ключевые моменты",
    "artifact_sign": "диалог",
    "level": 2,
    "tags": ["тег"]
  }}
}}

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:

1. CORE — только БАЗОВАЯ информация о личности:
   ✅ "Имя пользователя: Никита", "Пользователь — программист", "Пользователь любит кофе"
   ❌ "Пользователь сказал, что играет в шахматы" — это не ядро, это факт
   level всегда 5

2. FACTS — ИЗВЛЕЧЁННЫЕ ФАКТЫ в форме УТВЕРЖДЕНИЙ:
   ✅ "Пользователь играет в Dota 2", "У пользователя есть кот Барсик", "Пользователь выиграл в камень-ножницы-бумага 2 из 3"
   ❌ "Пользователь сказал, что играет в Dota 2" — это пересказ, не факт
   ❌ Весь диалог или длинная история
   level: 3 для обычных, 4 для важных, 5 для критичных

3. INSIGHTS — выводы и намерения:
   ✅ "Пользователь хочет сменить работу", "Пользователь устал от проекта"
   artifact_sign: гипотеза (если не уверен) или решение (если явно сказал)

4. DIALOG_SUMMARY — одно короткое саммари:
   "Обсуждали игры. Пользователь рассказал про победу в камень-ножницы-бумага над другом."

5. КАЖДЫЙ элемент — одна короткая мысль. Не делай длинные абзацы!

6. Если в слое нет данных — верни пустой массив [].

7. Отвечай ТОЛЬКО валидным JSON на русском языке, без markdown."""
            
            print("🤖 Отправляю запрос в LLM...")
            
            analysis_response = self.llm.generate(
                messages=[{"role": "user", "content": analysis_prompt}],
                system_prompt="Ты эксперт по извлечению знаний. Превращай сырые диалоги в чёткие факты. Отвечай ТОЛЬКО валидным JSON на русском."
            )
            
            print(f"\n📥 Ответ получен ({len(analysis_response)} символов)")
            self.after(0, lambda: self._append_message("Система", "💾 Сохраняю извлеченные знания..."))
            
            try:
                json_match = re.search(r'\{.*\}', analysis_response, re.DOTALL)
                
                if json_match:
                    data = json.loads(json_match.group())
                    print(f"✅ JSON распарсен")
                    
                    saved = {"core": 0, "fact": 0, "insight": 0, "dialog": 0}
                    
                    # CORE
                    for item in data.get("core", []):
                        if item.get("content"):
                            result = self.memory.remember(
                                content=item["content"], mem_type="core",
                                artifact_sign=item.get("artifact_sign", "факт"),
                                tags=item.get("tags", []),
                                level=5,
                                check_duplicate=True,
                            )
                            if result:
                                saved["core"] += 1
                                print(f"  ✅ [core] {item['content']}")
                    
                    # FACTS
                    for item in data.get("facts", []):
                        if item.get("content"):
                            result = self.memory.remember(
                                content=item["content"], mem_type="fact",
                                artifact_sign=item.get("artifact_sign", "факт"),
                                tags=item.get("tags", []),
                                level=item.get("level", 3),
                                check_duplicate=True,
                            )
                            if result:
                                saved["fact"] += 1
                                print(f"  ✅ [fact] {item['content']}")
                    
                    # INSIGHTS
                    for item in data.get("insights", []):
                        if item.get("content"):
                            result = self.memory.remember(
                                content=item["content"], mem_type="insight",
                                artifact_sign=item.get("artifact_sign", "гипотеза"),
                                tags=item.get("tags", []),
                                level=item.get("level", 3),
                                check_duplicate=True,
                            )
                            if result:
                                saved["insight"] += 1
                                print(f"  ✅ [insight] {item['content']}")
                    
                    # DIALOG SUMMARY
                    ds = data.get("dialog_summary", {})
                    if ds.get("content"):
                        result = self.memory.remember(
                            content=ds["content"], mem_type="dialog",
                            artifact_sign="диалог",
                            title=f"Диалог {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                            tags=ds.get("tags", []),
                            level=ds.get("level", 2),
                            check_duplicate=False,
                        )
                        if result:
                            saved["dialog"] += 1
                            print(f"  ✅ [dialog] {ds['content'][:80]}")
                    
                    print(f"\n📊 Итого: {saved}")
                    
                    msg = f"✅ Сохранено: core={saved['core']}, facts={saved['fact']}, insights={saved['insight']}, dialogs={saved['dialog']}"
                    self.after(0, lambda m=msg: self._append_message("Система", m))
                    self.after(0, self._refresh_memory_list)
                    self.after(0, self._clear_session_history)
                    
                else:
                    print(f"❌ JSON не найден")
                    self.after(0, lambda: self._append_message("Система", "❌ Модель не вернула JSON"))
                    
            except json.JSONDecodeError as e:
                error_msg = str(e)
                print(f"❌ Ошибка парсинга: {error_msg}")
                print(f"📄 Ответ: {analysis_response}")
                self.after(0, lambda msg=error_msg: self._append_message("Система", f"❌ Ошибка JSON: {msg}"))
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Ошибка: {error_msg}")
            import traceback
            traceback.print_exc()
            self.after(0, lambda msg=error_msg: self._append_message("Система", f"❌ {msg}"))
        finally:
            self.is_saving = False
            self.after(0, lambda: self.end_session_btn.configure(state="normal", text="✅ Завершить и сохранить"))
    
    def _clear_session_history(self):
        self.current_session_history = []
        self.chat_area.configure(state="normal")
        self.chat_area.delete("1.0", "end")
        self.chat_area.configure(state="disabled")
        self._append_message("Система", "📝 Новая сессия. Воспоминания сохранены.")
    
    def _send_message(self):
        message = self.input_entry.get()
        if not message.strip():
            return
        
        if not self.llm.is_available():
            self._append_message("Ошибка", "❌ Ollama не доступна")
            return
        
        selected_model = self.model_combo.get()
        if not selected_model or selected_model == "Выберите модель":
            self._append_message("Ошибка", "⚠️ Выберите модель!")
            return
        
        self.input_entry.delete(0, "end")
        self._append_message("Вы", message)
        
        self.current_session_history.append({"role": "user", "content": message})
        
        threading.Thread(target=self._get_response, args=(message,), daemon=True).start()
    
    def _get_response(self, prompt: str):
        try:
            selected_model = self.model_combo.get()
            if selected_model and selected_model != self.llm.model:
                self.llm.model = selected_model
            
            self.after(0, lambda: self.status_label.configure(text="⏳ Думаю...", text_color="yellow"))
            
            system_prompt = self._build_system_prompt()
            
            # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: разный поиск для разных типов вопросов
            asking_about_dialogs = self._is_asking_about_past_dialogs(prompt)
            
            if asking_about_dialogs:
                print(f"\n🔍 ВОПРОС О ПРОШЛЫХ РАЗГОВОРАХ: '{prompt}'")
                # Ищем в диалогах + фактах
                relevant = self.memory.recall_for_answer(prompt)
                dialogs = self.memory.recall_about_dialogs(prompt, n_results=2)
                all_relevant = relevant + dialogs
            else:
                print(f"\n🔍 ОБЫЧНЫЙ ВОПРОС: '{prompt}'")
                # Ищем ТОЛЬКО facts и insights (без диалогов!)
                all_relevant = self.memory.recall_for_answer(prompt)
            
            print(f"📊 Найдено релевантных: {len(all_relevant)}")
            
            if all_relevant:
                system_prompt += "\n\n=== РЕЛЕВАНТНЫЕ ВОСПОМИНАНИЯ ===\n"
                
                for mem in all_relevant:
                    mem_type = mem["metadata"].get("type", "unknown")
                    level = mem["metadata"].get("level", 3)
                    sign = mem["metadata"].get("artifact_sign", "")
                    score = mem.get("relevance_score", 0)
                    
                    icon = {"core": "👤", "fact": "📝", "insight": "💡", "dialog": "💬"}.get(mem_type, "")
                    system_prompt += f"{icon} [{mem_type}|{sign}|lvl{level}|score{score:.1f}]: {mem['content']}\n"
                    
                    print(f"  {icon} [{mem_type}|lvl{level}|{score:.1f}] {mem['content'][:80]}")
                
                system_prompt += "\n=== КОНЕЦ ===\n"
                
                if asking_about_dialogs:
                    system_prompt += "\nПользователь спрашивает о прошлых разговорах. Ответь конкретно, что обсуждали.\n"
                else:
                    system_prompt += "\nИспользуй воспоминания естественно. НЕ перечисляй всё подряд. Отвечай кратко и по делу.\n"
            
            response = self.llm.generate(
                messages=self.current_session_history,
                system_prompt=system_prompt
            )
            
            self.after(0, lambda: self.status_label.configure(text="✅ Готов", text_color="green"))
            
            self._append_message("Ассистент", response)
            self.current_session_history.append({"role": "assistant", "content": response})
            
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self.status_label.configure(text="❌ Ошибка", text_color="red"))
            self._append_message("Ошибка", f"Не удалось получить ответ:\n{error_msg}")
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
    
    def _search_memory(self):
        query = self.memory_search.get()
        if not query.strip():
            return
        
        mem_type = self.memory_filter.get()
        if mem_type == "все":
            mem_type = None
        
        print(f"\n🔍 ПОИСК: '{query}' (тип: {mem_type or 'все'})")
        
        self.memory_list.configure(state="normal")
        self.memory_list.delete("1.0", "end")
        self.memory_list.insert("end", f"🔍 Поиск: {query}\n\n")
        
        results = self.memory.obsidian.search(query, mem_type=mem_type, min_level=1)
        
        if not results:
            self.memory_list.insert("end", "❌ Ничего не найдено\n")
        else:
            for i, mem in enumerate(results[:20], 1):
                score = mem.get("relevance_score", 0)
                content = mem['content']
                cat = mem["metadata"].get("type", "unknown")
                level = mem["metadata"].get("level", 3)
                sign = mem["metadata"].get("artifact_sign", "")
                
                icon = {"core": "👤", "fact": "📝", "insight": "💡", "dialog": "💬"}.get(cat, "📄")
                
                self.memory_list.insert("end", f"{i}. {icon} [{cat}|{sign}|lvl{level}|{score:.1f}]\n")
                self.memory_list.insert("end", f"   {content}\n\n")
        
        self.memory_list.configure(state="disabled")
    
    def _refresh_memory_list(self):
        self.memory_list.configure(state="normal")
        self.memory_list.delete("1.0", "end")
        
        stats = self.memory.get_stats()
        obsidian_stats = stats["obsidian"]
        
        self.memory_list.insert("end", f"📚 Всего: {obsidian_stats['total_memories']}\n")
        for cat, count in obsidian_stats.get("by_type", {}).items():
            icon = {"core": "👤", "fact": "📝", "insight": "💡", "dialog": "💬"}.get(cat, "📄")
            self.memory_list.insert("end", f"  {icon} {cat}: {count}\n")
        self.memory_list.insert("end", "\n")
        
        all_memories = self.memory.get_all_memories()
        all_memories.sort(key=lambda x: x.get("modified", 0), reverse=True)
        
        for mem in all_memories[:20]:
            cat = mem["metadata"].get("type", "unknown")
            level = mem["metadata"].get("level", 3)
            icon = {"core": "👤", "fact": "📝", "insight": "💡", "dialog": "💬"}.get(cat, "📄")
            content = mem["content"][:100]
            self.memory_list.insert("end", f"{icon} [lvl{level}] {content}\n\n")
        
        self.memory_list.configure(state="disabled")
    
    def _show_memory_stats(self):
        stats = self.memory.get_stats()
        obsidian_stats = stats["obsidian"]
        
        self.memory_list.configure(state="normal")
        self.memory_list.delete("1.0", "end")
        
        self.memory_list.insert("end", "📊 Статистика\n")
        self.memory_list.insert("end", "=" * 40 + "\n\n")
        
        self.memory_list.insert("end", f"Всего: {obsidian_stats['total_memories']}\n")
        self.memory_list.insert("end", f"Размер: {obsidian_stats['total_size_bytes']} байт\n\n")
        
        self.memory_list.insert("end", "По типам:\n")
        for cat, count in obsidian_stats["by_type"].items():
            icon = {"core": "👤", "fact": "📝", "insight": "💡", "dialog": "💬"}.get(cat, "📄")
            self.memory_list.insert("end", f"  {icon} {cat}: {count}\n")
        
        self.memory_list.insert("end", "\nПо статусам:\n")
        for status, count in obsidian_stats["by_status"].items():
            self.memory_list.insert("end", f"  {status}: {count}\n")
        
        self.memory_list.configure(state="disabled")
    
    def _append_message(self, sender: str, message: str):
        self.chat_area.configure(state="normal")
        self.chat_area.insert("end", f"\n{sender}:\n{message}\n")
        self.chat_area.configure(state="disabled")
        self.chat_area.see("end")
