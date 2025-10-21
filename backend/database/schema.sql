-- SQL Schema для дашборда КУПЭ
-- PostgreSQL Database Schema

-- 1. Таблица компаний
CREATE TABLE IF NOT EXISTS kompanii (
    id SERIAL PRIMARY KEY,
    nazvanie VARCHAR(255) NOT NULL,
    inn VARCHAR(12),
    gorod VARCHAR(100),
    rol VARCHAR(50) NOT NULL CHECK (rol IN ('Заказчик', 'Исполнитель', 'Поставщик', 'Проектировщик', 'Сервис', 'Разработчик')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Проверки
    CONSTRAINT check_kompanii_inn_length CHECK (inn IS NULL OR LENGTH(inn) IN (10, 12))
);

-- 2. Таблица компонентов
CREATE TABLE IF NOT EXISTS komponenty (
    id SERIAL PRIMARY KEY,
    nazvanie VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('Тестирование', 'Поставка', 'Проектирование', 'Изготовление', 'Интеграция', 'В эксплуатации', 'Закупка')),
    progress DECIMAL(5,2) DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    kompaniya_id INTEGER REFERENCES kompanii(id) ON DELETE CASCADE,
    data_start DATE,
    data_end DATE,
    period VARCHAR(20) DEFAULT 'current' CHECK (period IN ('current', 'previous')),
    is_risk BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Таблица конструкторских документов
CREATE TABLE IF NOT EXISTS konstruktorskie_dokumenty (
    id SERIAL PRIMARY KEY,
    nomer VARCHAR(100) NOT NULL,
    nazvanie VARCHAR(255),
    data_vypuska DATE NOT NULL,
    komponent_id INTEGER REFERENCES komponenty(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Таблица рисков
CREATE TABLE IF NOT EXISTS riski (
    id SERIAL PRIMARY KEY,
    komponent_id INTEGER REFERENCES komponenty(id) ON DELETE CASCADE,
    kategoriya VARCHAR(50) NOT NULL CHECK (kategoriya IN ('Поставки', 'Сроки', 'Технический', 'Финансовый', 'Юридический')),
    opisanie TEXT,
    veroyatnost DECIMAL(3,2) CHECK (veroyatnost >= 0 AND veroyatnost <= 1),
    vliyanie VARCHAR(20) CHECK (vliyanie IN ('Низкое', 'Среднее', 'Высокое', 'Критическое')),
    status VARCHAR(20) DEFAULT 'Открыт' CHECK (status IN ('Открыт', 'Закрыт', 'В работе')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Таблица поставщиков
CREATE TABLE IF NOT EXISTS postavshchiki (
    id SERIAL PRIMARY KEY,
    nazvanie VARCHAR(255) NOT NULL,
    inn VARCHAR(12) NOT NULL UNIQUE,
    tip_postavki VARCHAR(100) NOT NULL,
    strana VARCHAR(100) NOT NULL,
    
    -- Дополнительные поля
    kontaktnoe_litso VARCHAR(255),
    telefon VARCHAR(50),
    email VARCHAR(255),
    adres TEXT,
    aktivnyj BOOLEAN DEFAULT TRUE,
    
    -- Служебные поля
    data_sozdaniya TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_obnovleniya TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Проверки
    CONSTRAINT check_inn_length CHECK (LENGTH(inn) IN (10, 12)),
    CONSTRAINT check_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' OR email IS NULL)
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_kompanii_inn ON kompanii(inn);
CREATE INDEX IF NOT EXISTS idx_kompanii_gorod ON kompanii(gorod);
CREATE INDEX IF NOT EXISTS idx_komponenty_period ON komponenty(period);
CREATE INDEX IF NOT EXISTS idx_komponenty_status ON komponenty(status);
CREATE INDEX IF NOT EXISTS idx_komponenty_kompaniya ON komponenty(kompaniya_id);
CREATE INDEX IF NOT EXISTS idx_riski_komponent ON riski(komponent_id);
CREATE INDEX IF NOT EXISTS idx_riski_veroyatnost ON riski(veroyatnost);
CREATE INDEX IF NOT EXISTS idx_kdocs_data ON konstruktorskie_dokumenty(data_vypuska);
CREATE INDEX IF NOT EXISTS idx_postavshchiki_inn ON postavshchiki(inn);
CREATE INDEX IF NOT EXISTS idx_postavshchiki_strana ON postavshchiki(strana);
CREATE INDEX IF NOT EXISTS idx_postavshchiki_tip ON postavshchiki(tip_postavki);
CREATE INDEX IF NOT EXISTS idx_postavshchiki_aktivnyj ON postavshchiki(aktivnyj);

-- Комментарии к таблицам
COMMENT ON TABLE kompanii IS 'Компании-участники проекта';
COMMENT ON TABLE komponenty IS 'Компоненты железнодорожного состава';
COMMENT ON TABLE konstruktorskie_dokumenty IS 'Конструкторские документы (КД)';
COMMENT ON TABLE riski IS 'Риски проекта';
COMMENT ON TABLE postavshchiki IS 'Поставщики';

COMMENT ON COLUMN komponenty.period IS 'Период: current (текущий) или previous (предыдущий) для расчета дельты';
COMMENT ON COLUMN komponenty.progress IS 'Готовность в процентах (0-100)';
COMMENT ON COLUMN riski.veroyatnost IS 'Вероятность риска от 0 до 1 (например, 0.3 = 30%)';
COMMENT ON COLUMN postavshchiki.inn IS 'ИНН (10 или 12 цифр)';
COMMENT ON COLUMN postavshchiki.aktivnyj IS 'Активен ли поставщик (TRUE/FALSE)';

-- Триггер для автоматического обновления data_obnovleniya
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_obnovleniya = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_postavshchiki_modtime
    BEFORE UPDATE ON postavshchiki
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

