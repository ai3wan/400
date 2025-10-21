# База данных дашборда КУПЭ

## 📁 Файлы

- `schema.sql` - Схема базы данных (таблицы, индексы, триггеры)
- `seed_data.sql` - Тестовые данные для начальной загрузки
- `update_data.sql` - Шаблон для безопасного обновления данных

## ⚠️ ВАЖНО: Работа с данными

### 🔴 НЕ ДЕЛАЙТЕ ЭТО в продакшене:

```bash
# ❌ Это УДАЛИТ все ваши данные!
psql -U tnb_user_1_vsm400_user -h localhost -d tnb_user_1_vsm400 -f seed_data.sql
```

Файл `seed_data.sql` содержит `TRUNCATE TABLE` - команду полного удаления данных!

---

## ✅ Первоначальная установка (ОДИН РАЗ):

```bash
# Шаг 1: Создать таблицы
psql -U tnb_user_1_vsm400_user -h localhost -d tnb_user_1_vsm400 -f schema.sql

# Шаг 2: Загрузить тестовые данные (ТОЛЬКО ОДИН РАЗ)
psql -U tnb_user_1_vsm400_user -h localhost -d tnb_user_1_vsm400 -f seed_data.sql
```

---

## 📝 Работа с данными в продакшене:

### Вариант 1: Через DBeaver (GUI) - РЕКОМЕНДУЕТСЯ ⭐

1. Установите DBeaver на вашем Mac
2. Подключитесь через SSH туннель к БД
3. Редактируйте таблицы визуально:
   - Добавляйте строки
   - Обновляйте значения
   - Удаляйте ненужное
4. Изменения сохраняются сразу в БД

### Вариант 2: SQL запросы напрямую

```bash
# Подключитесь к БД
psql -U tnb_user_1_vsm400_user -h localhost -d tnb_user_1_vsm400
```

```sql
-- Добавить новый риск
INSERT INTO riski (komponent_id, kategoriya, opisanie, veroyatnost, vliyanie, status) 
VALUES (5, 'Технический', 'Новая проблема с интеграцией', 0.6, 'Высокое', 'Открыт');

-- Обновить статус риска
UPDATE riski SET status = 'Закрыт' WHERE id = 15;

-- Изменить вероятность
UPDATE riski SET veroyatnost = 0.3 WHERE id = 10;

-- Добавить новый компонент
INSERT INTO komponenty (nazvanie, status, progress, kompaniya_id, period)
VALUES ('Система освещения', 'Проектирование', 25.0, 5, 'current');

-- Обновить прогресс компонента
UPDATE komponenty SET progress = 85.5 WHERE id = 1;
```

### Вариант 3: Через API (будущее развитие)

Можно добавить POST/PUT/DELETE endpoints в FastAPI для редактирования данных через веб-интерфейс.

---

## 🔄 Обновление схемы БД (миграции):

Если нужно добавить новую колонку или таблицу:

```sql
-- Пример: добавить поле к таблице
ALTER TABLE riski ADD COLUMN prioritet INTEGER DEFAULT 1;

-- Создать новую таблицу
CREATE TABLE novaya_tablica (...);
```

---

## 📊 Полезные запросы:

```sql
-- Количество записей в каждой таблице
SELECT 'kompanii' as table_name, COUNT(*) FROM kompanii
UNION ALL SELECT 'komponenty', COUNT(*) FROM komponenty
UNION ALL SELECT 'riski', COUNT(*) FROM riski;

-- Открытые критические риски
SELECT * FROM riski 
WHERE status = 'Открыт' AND vliyanie = 'Критическое' 
ORDER BY veroyatnost DESC;

-- Компоненты с рисками
SELECT k.nazvanie, COUNT(r.id) as risks_count
FROM komponenty k
LEFT JOIN riski r ON r.komponent_id = k.id
GROUP BY k.nazvanie
ORDER BY risks_count DESC;
```

---

## 💾 Резервное копирование:

```bash
# Создать бэкап БД
pg_dump -U tnb_user_1_vsm400_user -h localhost tnb_user_1_vsm400 > backup_$(date +%Y%m%d).sql

# Восстановить из бэкапа
psql -U tnb_user_1_vsm400_user -h localhost -d tnb_user_1_vsm400 -f backup_20251021.sql
```

---

**Используйте DBeaver для удобного редактирования данных!** 🚀

