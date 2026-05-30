"""
Единая система логирования для всего проекта
Все логи пишутся в data/logs/assistant.log
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Создаём папку для логов если её нет
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Имя файла лога с датой
LOG_FILE = LOG_DIR / f"assistant_{datetime.now().strftime('%Y%m%d')}.log"

def setup_logger(name="assistant", level=logging.INFO):
    """Настраивает логгер с выводом в файл и консоль"""
    
    # Создаём логгер
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Очищаем старые обработчики (если есть)
    logger.handlers.clear()
    
    # Формат логов (время - имя - уровень - сообщение)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для файла
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Обработчик для консоли (чтобы видеть ошибки сразу)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Создаём глобальный логгер
logger = setup_logger()

# Функция для быстрого логирования ошибок
def log_error(error, context=""):
    """Логирует ошибку с контекстом"""
    logger.error(f"{context}: {str(error)}" if context else str(error))

# Функция для логирования действий пользователя
def log_user_action(action, details=""):
    """Логирует действия пользователя"""
    logger.info(f"USER ACTION: {action} | {details}")

# Функция для получения последних N строк лога (для отладки)
def get_recent_logs(lines=50):
    """Возвращает последние строки лога"""
    if not LOG_FILE.exists():
        return "Лог-файл ещё не создан"
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        return ''.join(all_lines[-lines:])
