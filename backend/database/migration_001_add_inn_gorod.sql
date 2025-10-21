-- Миграция: Добавление полей ИНН и Город в таблицу kompanii
-- Дата: 2025-10-21

-- Удалить старое ограничение (если было)
ALTER TABLE kompanii DROP CONSTRAINT IF EXISTS check_kompanii_inn_length;

-- Добавить новые колонки (если еще нет)
ALTER TABLE kompanii ADD COLUMN IF NOT EXISTS inn VARCHAR(20);
ALTER TABLE kompanii ADD COLUMN IF NOT EXISTS gorod VARCHAR(100);

-- Создать индексы
CREATE INDEX IF NOT EXISTS idx_kompanii_inn ON kompanii(inn);
CREATE INDEX IF NOT EXISTS idx_kompanii_gorod ON kompanii(gorod);

-- Заполнить данные для существующих компаний
UPDATE kompanii SET inn = '7701001234', gorod = 'Москва' WHERE id = 1;
UPDATE kompanii SET inn = '7702002345', gorod = 'Санкт-Петербург' WHERE id = 2;
UPDATE kompanii SET inn = '7703003456', gorod = 'Москва' WHERE id = 3;
UPDATE kompanii SET inn = '5904004567', gorod = 'Пермь' WHERE id = 4;
UPDATE kompanii SET inn = '7805005678', gorod = 'Санкт-Петербург' WHERE id = 5;
UPDATE kompanii SET inn = '5006006789', gorod = 'Екатеринбург' WHERE id = 6;
UPDATE kompanii SET inn = '7707007890', gorod = 'Москва' WHERE id = 8;
UPDATE kompanii SET inn = '7708008901', gorod = 'Москва' WHERE id = 9;
UPDATE kompanii SET inn = '6309009012', gorod = 'Самара' WHERE id = 12;
UPDATE kompanii SET inn = '7710010123', gorod = 'Москва' WHERE id = 13;
UPDATE kompanii SET inn = '7711011234', gorod = 'Москва' WHERE id = 14;

-- Добавить комментарии
COMMENT ON COLUMN kompanii.inn IS 'ИНН компании (10 или 12 цифр)';
COMMENT ON COLUMN kompanii.gorod IS 'Город местонахождения компании';

