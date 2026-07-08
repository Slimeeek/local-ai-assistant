import customtkinter as ctk
from tkinter import scrolledtext
import threading
from ..llm.ollama_client import OllamaClient

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Настройки окна
        self.title("Local AI Assistant")
        self.geometry("800x600")
        
        # Инициализация LLM
        self.llm = OllamaClient()
        
        # Создание UI
        self._create_widgets()
        
        # Проверка доступности
        self._check_ollama_connection()
    
    def _check_ollama_connection(self):
        """Проверяет подключение к Ollama"""
        try:
            if self.llm.is_available():
                models = self.llm.list_models()
                if models:
                    self.status_label.configure(text=f"✅ Ollama подключена ({len(models)} моделей)", text_color="green")
                else:
                    self.status_label.configure(text="⚠️ Ollama подключена, но моделей нет", text_color="orange")
            else:
                self.status_label.configure(text="❌ Ollama не доступна", text_color="red")
        except Exception as e:
            self.status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="red")
    
    def _create_widgets(self):
        # Верхняя панель с настройками
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        # Выбор модели
        ctk.CTkLabel(top_frame, text="Модель:").pack(side="left", padx=5)
        self.model_combo = ctk.CTkComboBox(
            top_frame, 
            values=[],
            width=200,
            state="readonly"  # Делаем readonly, чтобы нельзя было вписать ерунду
        )
        self.model_combo.pack(side="left", padx=5)
        self.model_combo.set("Выберите модель")  # Устанавливаем placeholder
        
        # Кнопка обновления списка моделей
        self.refresh_btn = ctk.CTkButton(
            top_frame, 
            text="🔄", 
            width=40, 
            command=self._refresh_models
        )
        self.refresh_btn.pack(side="left", padx=5)
        
        # Статус
        self.status_label = ctk.CTkLabel(top_frame, text="Проверка...")
        self.status_label.pack(side="right", padx=5)
        
        # Область чата
        self.chat_area = scrolledtext.ScrolledText(
            self, 
            wrap=ctk.WORD,
            font=("Arial", 12),
            bg="#2b2b2b",
            fg="#ffffff"
        )
        self.chat_area.pack(fill="both", expand=True, padx=10, pady=5)
        self.chat_area.configure(state="disabled")
        
        # Поле ввода
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Введите сообщение...",
            font=("Arial", 12)
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.input_entry.bind("<Return>", lambda e: self._send_message())
        
        self.send_btn = ctk.CTkButton(
            input_frame,
            text="Отправить",
            command=self._send_message,
            width=100,
            state="disabled"  # Изначально кнопка disabled
        )
        self.send_btn.pack(side="right", padx=5)

    def _refresh_models(self):
        """Обновляет список доступных моделей"""
        try:
            # Проверяем подключение
            if not self.llm.is_available():
                self.status_label.configure(text="❌ Ollama не доступна", text_color="red")
                return
            
            # Получаем свежий список
            models = self.llm.list_models()
            
            if not models:
                self.status_label.configure(text="⚠️ Модели не найдены. Скачай: ollama pull llama3.2", text_color="orange")
                self.model_combo.configure(values=[])
                self.model_combo.set("Выберите модель")
                self.send_btn.configure(state="disabled")
                return
            
            # Обновляем выпадающий список
            self.model_combo.configure(values=models)
            self.model_combo.set(models[0])  # Выбираем первую модель
            self.llm.model = models[0]
            
            # Включаем кнопку отправки
            self.send_btn.configure(state="normal")
            
            self.status_label.configure(text=f"✅ Загружено {len(models)} моделей", text_color="green")
        except Exception as e:
            error_msg = str(e)
            self.status_label.configure(text=f"❌ Ошибка: {error_msg}", text_color="red")
            print(f"[ERROR] При обновлении моделей: {error_msg}")
            import traceback
            traceback.print_exc()
    
    def _send_message(self):
        message = self.input_entry.get()
        if not message.strip():
            return
        
        # Проверяем подключение перед отправкой
        if not self.llm.is_available():
            self._append_message("Ошибка", " Ollama не доступна. Убедитесь, что сервер запущен (ollama serve)")
            return
        
        # Проверяем, выбрана ли модель
        selected_model = self.model_combo.get()
        if not selected_model or selected_model == "Выберите модель":
            self._append_message("Ошибка", "⚠️ Сначала выберите модель из списка!")
            return
        
        # Очистка поля ввода
        self.input_entry.delete(0, "end")
        
        # Добавление сообщения пользователя
        self._append_message("Вы", message)
        
        # Отправка в отдельном потоке
        threading.Thread(target=self._get_response, args=(message,), daemon=True).start()
    
    def _get_response(self, prompt: str):
        try:
            # Обновление модели если изменилась
            selected_model = self.model_combo.get()
            if selected_model and selected_model != self.llm.model:
                print(f"[INFO] Смена модели: {self.llm.model} -> {selected_model}")
                self.llm.model = selected_model
            
            print(f"[INFO] Используемая модель: {self.llm.model}")
            
            # Получение ответа
            response = self.llm.generate(prompt)
            self._append_message("Ассистент", response)
        except Exception as e:
            error_msg = str(e)
            self._append_message("Ошибка", f"Не удалось получить ответ:\n{error_msg}")
            print(f"[ERROR] При генерации ответа: {error_msg}")
            import traceback
            traceback.print_exc()
    
    def _append_message(self, sender: str, message: str):
        self.chat_area.configure(state="normal")
        self.chat_area.insert("end", f"\n{sender}:\n{message}\n")
        self.chat_area.configure(state="disabled")
        self.chat_area.see("end")
