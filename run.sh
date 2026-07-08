#!/bin/bash

# Local AI Assistant - Launcher

# Проверяем, находимся ли мы в директории проекта
if [ ! -f "requirements.txt" ]; then
    echo "❌ Ошибка: requirements.txt не найден"
    echo "Убедитесь, что вы запускаете скрипт из корня проекта"
    exit 1
fi

# Проверяем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "⚠️  Виртуальное окружение не найдено"
    echo "Запустите сначала: ./install.sh"
    exit 1
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем приложение
echo " Запуск Local AI Assistant..."
python run.py
