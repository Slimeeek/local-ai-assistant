#!/bin/bash

# ============================================
# Local AI Assistant - Установщик
# ============================================

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ============================================
# Приветствие
# ============================================
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Local AI Assistant - Установщик                    ║"
echo "════════════════════════════════════════════════════════════╝"
echo ""
info "Начинаем установку..."
echo ""

# ============================================
# Шаг 1: Проверка Python
# ============================================
info "Проверка Python..."

if ! command -v python3 &> /dev/null; then
    error "Python 3 не найден!"
    echo "Установите Python 3.12 или выше:"
    echo "  sudo apt update && sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    error "Требуется Python 3.10 или выше (у вас $PYTHON_VERSION)"
    exit 1
fi

success "Python $PYTHON_VERSION найден"

# ============================================
# Шаг 2: Проверка tkinter
# ============================================
info "Проверка tkinter..."

if python3 -c "import tkinter" 2>/dev/null; then
    success "tkinter установлен"
else
    warning "tkinter не найден. Устанавливаю..."
    
    # Определяем пакетный менеджер
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y python3-tk python3-tk-dbg
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-tkinter
    elif command -v pacman &> /dev/null; then
        sudo pacman -S tk
    else
        error "Не удалось определить пакетный менеджер. Установите tkinter вручную:"
        echo "  Ubuntu/Debian: sudo apt install python3-tk"
        echo "  Fedora: sudo dnf install python3-tkinter"
        echo "  Arch: sudo pacman -S tk"
        exit 1
    fi
    
    success "tkinter установлен"
fi

# ============================================
# Шаг 3: Проверка Ollama
# ============================================
info "Проверка Ollama..."

if command -v ollama &> /dev/null; then
    success "Ollama установлен"
    
    # Проверяем, запущен ли сервис
    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        warning "Ollama сервис не запущен"
        echo "Запустите Ollama командой: ollama serve"
        echo "Или добавьте в автозагрузку: systemctl enable ollama"
    else
        success "Ollama сервис работает"
    fi
else
    warning "Ollama не установлен"
    echo ""
    echo "Ollama необходим для работы ассистента."
    echo "Установите его командой:"
    echo "  curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    echo "Или скачайте с сайта: https://ollama.com/download"
    echo ""
    
    read -p "Хотите установить Ollama сейчас? (y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Установка Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
        success "Ollama установлен"
        
        # Запускаем сервис
        info "Запуск Ollama сервиса..."
        ollama serve &
        sleep 3
        success "Ollama сервис запущен"
    else
        warning "Ollama не установлен. Вы можете установить его позже."
    fi
fi

# ============================================
# Шаг 4: Создание виртуального окружения
# ============================================
info "Создание виртуального окружения..."

if [ -d "venv" ]; then
    warning "Виртуальное окружение уже существует"
    read -p "Пересоздать? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        success "Виртуальное окружение пересоздано"
    else
        success "Используем существующее виртуальное окружение"
    fi
else
    python3 -m venv venv
    success "Виртуальное окружение создано"
fi

# ============================================
# Шаг 5: Установка зависимостей
# ============================================
info "Установка зависимостей Python..."

# Активируем venv
source venv/bin/activate

# Обновляем pip
pip install --upgrade pip

# Устанавливаем зависимости
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    success "Зависимости установлены"
else
    error "requirements.txt не найден!"
    exit 1
fi

# ============================================
# Шаг 6: Скачивание модели
# ============================================
echo ""
info "Проверка моделей Ollama..."

# Проверяем, есть ли уже модели
if curl -s http://localhost:11434/api/tags | grep -q "models"; then
    MODEL_COUNT=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('models', [])))" 2>/dev/null || echo "0")
    
    if [ "$MODEL_COUNT" -gt 0 ]; then
        success "Найдено $MODEL_COUNT моделей"
    else
        warning "Модели не найдены"
    fi
else
    warning "Не удалось подключиться к Ollama"
fi

echo ""
echo "Рекомендуемые модели для вашего железа (8GB RAM, RTX 3050):"
echo "  1. phi3 (3.8B) - лучший баланс скорости и качества [РЕКОМЕНДУЕТСЯ]"
echo "  2. llama3.2:3b (3B) - очень быстрая"
echo "  3. qwen2.5:7b (7B) - лучшее качество, но медленнее"
echo ""

read -p "Скачать модель phi3? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Скачивание модели phi3 (это может занять время)..."
    ollama pull phi3
    success "Модель phi3 скачана"
fi

# ============================================
# Шаг 7: Настройка прав доступа
# ============================================
info "Настройка прав доступа..."

chmod +x run.sh
chmod +x install.sh
success "Права доступа настроены"

# ============================================
# Завершение
# ============================================
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Установка завершена!                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
success "Local AI Assistant готов к использованию!"
echo ""
echo "Для запуска ассистента выполните:"
echo "  ./run.sh"
echo ""
echo "Или вручную:"
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""
info "Документация: README.md"
echo ""
