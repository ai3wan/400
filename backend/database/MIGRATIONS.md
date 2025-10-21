# Миграции базы данных

## 📝 Список миграций

### migration_001_add_inn_gorod.sql
**Дата:** 2025-10-21  
**Описание:** Добавление полей ИНН и Город в таблицу kompanii

**Изменения:**
- Добавлено поле `inn` (VARCHAR(12)) - ИНН компании
- Добавлено поле `gorod` (VARCHAR(100)) - город местонахождения
- Добавлена проверка длины ИНН (10 или 12 цифр)
- Созданы индексы для новых полей
- Заполнены данные для существующих компаний

---

## 🚀 Применение миграций

### ⚠️ ВАЖНО: Миграции применяются БЕЗ потери данных!

### На сервере:

```bash
# Подключитесь к серверу
ssh tnb_user_1@198.177.123.150

# Перейдите в папку миграций
cd /home/tnb_user_1/public_html/400/backend/database

# Примените миграцию
psql -U tnb_user_1_vsm400_user -h localhost -d tnb_user_1_vsm400 -f migration_001_add_inn_gorod.sql

# Проверьте результат
psql -U tnb_user_1_vsm400_user -h localhost -d tnb_user_1_vsm400 -c "\d kompanii"
```

### Проверка:

```sql
-- Посмотрите обновленные данные
SELECT id, nazvanie, inn, gorod, rol FROM kompanii ORDER BY id;
```

Должны увидеть заполненные ИНН и города для всех компаний.

---

## 📋 Порядок применения миграций

1. **Всегда делайте бэкап перед миграцией:**
   ```bash
   pg_dump -U tnb_user_1_vsm400_user -h localhost tnb_user_1_vsm400 > backup_before_migration.sql
   ```

2. **Применяйте миграции по порядку:**
   ```bash
   psql ... -f migration_001_add_inn_gorod.sql
   # psql ... -f migration_002_next_migration.sql
   # и т.д.
   ```

3. **Проверяйте результат после каждой миграции**

4. **Перезапустите API** (если изменилась структура данных):
   ```bash
   sudo systemctl restart dashboard-api
   ```

---

## 🔄 Откат миграции

Если что-то пошло не так:

```bash
# Восстановите из бэкапа
psql -U tnb_user_1_vsm400_user -h localhost -d tnb_user_1_vsm400 -f backup_before_migration.sql
```

Или вручную удалите колонки:

```sql
-- Откат migration_001
ALTER TABLE kompanii DROP COLUMN IF EXISTS inn;
ALTER TABLE kompanii DROP COLUMN IF EXISTS gorod;
DROP INDEX IF EXISTS idx_kompanii_inn;
DROP INDEX IF EXISTS idx_kompanii_gorod;
```

---

## 📊 Создание новой миграции

Шаблон:

```sql
-- Миграция: Описание изменений
-- Дата: YYYY-MM-DD

-- 1. Добавление полей
ALTER TABLE table_name ADD COLUMN IF NOT EXISTS new_field TYPE;

-- 2. Создание индексов
CREATE INDEX IF NOT EXISTS idx_name ON table(field);

-- 3. Обновление данных (если нужно)
UPDATE table_name SET new_field = 'value' WHERE condition;
```

---

## ✅ Best Practices

1. **Никогда не изменяйте старые миграции** - создавайте новые
2. **Всегда делайте бэкап** перед миграцией
3. **Тестируйте на копии БД** перед применением в продакшене
4. **Используйте IF NOT EXISTS** для идемпотентности
5. **Нумеруйте миграции** последовательно (001, 002, 003...)

