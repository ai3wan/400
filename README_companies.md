# Дашборд компаний

Простой дашборд для анализа данных компаний с PostgreSQL базой данных.

## Структура проекта

```
backend/
├── database/
│   ├── schema_companies.sql    # Схема БД с таблицей company
│   └── seed_companies.sql      # Тестовые данные
├── app_companies.py            # FastAPI backend
└── requirements.txt
index_companies.html            # Frontend дашборд
```

## Структура таблицы company

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL PRIMARY KEY | Уникальный идентификатор |
| short_name | VARCHAR(200) | Наименование |
| full_name | VARCHAR(500) | Полное наименование |
| inn | VARCHAR(20) | ИНН (текст, может начинаться с нуля) |
| region | VARCHAR(100) | Регион |
| address | TEXT | Адрес |
| ido | DECIMAL(5,2) | ИДО (цифра) |
| ifr | DECIMAL(5,2) | ИФР (цифра) |
| ipd | DECIMAL(5,2) | ИПД (цифра) |
| spark_risk | VARCHAR(50) | Спарк_риск (текст) |
| authorized_capital | DECIMAL(15,2) | Уставный Капитал |
| registration_date | DATE | Дата регистрации |
| created_at | TIMESTAMP | Дата создания записи |
| updated_at | TIMESTAMP | Дата обновления записи |

## Развертывание

### 1. Создание базы данных

```bash
# Подключение к PostgreSQL
psql -U tnb_user_1_vsm400_user -h localhost -d tnb_user_1_vsm400

# Выполнение схемы
\i backend/database/schema_companies.sql

# Загрузка тестовых данных
\i backend/database/seed_companies.sql
```

### 2. Настройка backend

```bash
# Копирование нового API
cp backend/app_companies.py backend/app.py

# Установка зависимостей (если нужно)
pip install -r requirements.txt

# Запуск API
python backend/app.py
```

### 3. Настройка frontend

```bash
# Копирование нового frontend
cp index_companies.html index.html
```

### 4. Проверка работы

- API: `http://localhost:8000/api/health`
- Дашборд: `http://your-domain.com/400/`

## API Endpoints

- `GET /` - Информация об API
- `GET /api/health` - Проверка здоровья API и БД
- `GET /api/companies` - Список всех компаний
- `GET /api/companies/{id}` - Данные конкретной компании
- `GET /api/dashboard-data` - Все данные для дашборда

## Дашборд включает

1. **KPI метрики:**
   - Общее количество компаний
   - Средние значения ИДО, ИФР, ИПД
   - Средний размер капитала
   - Количество компаний с низким риском

2. **Графики:**
   - Распределение компаний по регионам (pie chart)
   - Распределение по рискам (pie chart)
   - Топ-10 компаний по капиталу (bar chart)
   - Корреляция риск-капитал (scatter plot)
   - Распределение по ИДО (bar chart)
   - Распределение по размеру капитала (bar chart)

## Особенности

- ✅ Безопасная обработка null значений
- ✅ Индивидуальные try-catch блоки для каждой функции
- ✅ Адаптивный дизайн
- ✅ Темная/светлая тема
- ✅ Автоматическое обновление размеров графиков
- ✅ Детальное логирование для отладки
