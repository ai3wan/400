# Backend API для дашборда КУПЭ

FastAPI приложение для работы с PostgreSQL и предоставления данных дашборду.

## 🚀 Быстрый старт

### 1. Установите зависимости

```bash
cd backend
pip install -r requirements.txt
```

### 2. Настройте .env файл

```bash
cp config.env.example .env
nano .env
```

Укажите ваш DATABASE_URL:
```env
DATABASE_URL=postgresql://tnb_user_1_vsm400_user:ВАШ_ПАРОЛЬ@localhost:5432/tnb_user_1_vsm400
```

### 3. Примените SQL схему

На сервере в psql:
```sql
-- Подключитесь к БД
\c tnb_user_1_vsm400

-- Примените схему (скопируйте содержимое database/schema.sql)
-- Затем примените тестовые данные (database/seed_data.sql)
```

Или через файл:
```bash
psql -U tnb_user_1_vsm400_user -h localhost -d tnb_user_1_vsm400 -f database/schema.sql
psql -U tnb_user_1_vsm400_user -h localhost -d tnb_user_1_vsm400 -f database/seed_data.sql
```

### 4. Запустите API

```bash
python app.py
```

API будет доступно на `http://localhost:8000`

## 📡 API Endpoints

### `GET /`
Информация об API

### `GET /api/health`
Проверка здоровья API и подключения к БД

```json
{
  "status": "healthy",
  "database": "connected",
  "db_version": "PostgreSQL 16.2"
}
```

### `GET /api/dashboard-data`
Получить все данные для дашборда

**Response:**
```json
{
  "kpi": {
    "komponenty_count_curr": 28,
    "avg_progress_curr": 65.2,
    "risks_open_curr": 13
  },
  "pie_status": [...],
  "kdocs_month": [...],
  "top_suppliers": [...],
  "heat": {...},
  "gantt": [...],
  "suppliers_by_country": [...],
  "meta": {...}
}
```

## 📚 Документация API

После запуска доступна автоматическая документация:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🗄️ Структура БД

- **kompanii** — компании-участники
- **komponenty** — компоненты проекта
- **konstruktorskie_dokumenty** — КД
- **riski** — риски проекта
- **postavshchiki** — поставщики

См. `database/schema.sql` для деталей.

