-- Создание новой структуры БД с таблицей компаний
-- Дата: 2025-01-22

-- Удаляем все существующие таблицы и объекты
DROP TABLE IF EXISTS company CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;

-- Создаем таблицу company
CREATE TABLE company (
    id SERIAL PRIMARY KEY,
    short_name VARCHAR(200) NOT NULL,                    -- Наименование
    full_name VARCHAR(500),                             -- Полное наименование
    inn VARCHAR(20),                                    -- ИНН (текст, может начинаться с нуля)
    region VARCHAR(100),                                -- Регион
    address TEXT,                                       -- Адрес
    ido DECIMAL(5,2),                                  -- ИДО (цифра)
    ifr DECIMAL(5,2),                                  -- ИФР (цифра)
    ipd DECIMAL(5,2),                                  -- ИПД (цифра)
    spark_risk VARCHAR(50),                            -- Спарк_риск (текст)
    authorized_capital DECIMAL(15,2),                   -- Уставный Капитал
    registration_date DATE,                             -- Дата регистрации
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаем индексы для быстрого поиска
CREATE INDEX idx_company_short_name ON company(short_name);
CREATE INDEX idx_company_inn ON company(inn);
CREATE INDEX idx_company_region ON company(region);
CREATE INDEX idx_company_spark_risk ON company(spark_risk);
CREATE INDEX idx_company_authorized_capital ON company(authorized_capital);
CREATE INDEX idx_company_registration_date ON company(registration_date);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для автоматического обновления updated_at
CREATE TRIGGER update_company_updated_at
    BEFORE UPDATE ON company
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Комментарии к таблице и полям
COMMENT ON TABLE company IS 'Таблица компаний с основными характеристиками';
COMMENT ON COLUMN company.short_name IS 'Краткое наименование компании';
COMMENT ON COLUMN company.full_name IS 'Полное наименование компании';
COMMENT ON COLUMN company.inn IS 'ИНН компании (текстовое поле)';
COMMENT ON COLUMN company.region IS 'Регион компании';
COMMENT ON COLUMN company.address IS 'Адрес компании';
COMMENT ON COLUMN company.ido IS 'Индекс деловой активности (0-100)';
COMMENT ON COLUMN company.ifr IS 'Индекс финансового риска (0-100)';
COMMENT ON COLUMN company.ipd IS 'Индекс платежной дисциплины (0-100)';
COMMENT ON COLUMN company.spark_risk IS 'Спарк риск (текстовое описание)';
COMMENT ON COLUMN company.authorized_capital IS 'Уставный капитал в рублях';
COMMENT ON COLUMN company.registration_date IS 'Дата регистрации компании';
