#!/bin/bash

# Скрипт для деплоя дашборда на сервер
# Использование: ./deploy.sh user@your-server.com /var/www/html/dashboard

if [ $# -lt 2 ]; then
    echo "Использование: $0 USER@SERVER REMOTE_PATH"
    echo "Пример: $0 user@server.com public_html/400"
    exit 1
fi

SERVER=$1
REMOTE_PATH=$2

echo "🚀 Деплой на сервер: $SERVER"
echo "📁 Путь: $REMOTE_PATH"
echo ""

# Подключаемся к серверу и клонируем/обновляем репозиторий
ssh $SERVER << EOF
    echo "📦 Проверка наличия Git..."
    if ! command -v git &> /dev/null; then
        echo "❌ Git не установлен. Установите: sudo apt install git"
        exit 1
    fi

    echo "📂 Переход в директорию..."
    if [ -d "$REMOTE_PATH" ]; then
        echo "♻️  Обновление существующего репозитория..."
        cd $REMOTE_PATH
        git pull origin main
    else
        echo "📥 Клонирование репозитория..."
        git clone https://github.com/ai3wan/400.git $REMOTE_PATH
    fi

    echo "✅ Деплой завершён!"
    echo "🌐 Доступно по адресу: http://\$(hostname -I | awk '{print \$1}')"
EOF

echo ""
echo "✨ Готово!"

