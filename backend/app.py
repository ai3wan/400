"""
FastAPI Backend для дашборда компаний
Простая структура с таблицей company
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

app = FastAPI(title="Company Dashboard API", version="1.0.0")

# CORS настройки (разрешаем запросы с фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://tnb_user_1_vsm400_user:password@localhost:5432/tnb_user_1_vsm400")


def get_db_connection():
    """Создание подключения к PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")


@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "message": "Company Dashboard API",
        "version": "1.0.0",
        "endpoints": {
            "/api/dashboard-data": "Получить все данные дашборда",
            "/api/health": "Проверка здоровья API и БД",
            "/api/companies": "Получить список всех компаний",
            "/api/companies/{company_id}": "Получить данные конкретной компании"
        }
    }


@app.get("/api/health")
async def health_check():
    """Проверка подключения к БД"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM company;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {
            "status": "healthy",
            "database": "connected",
            "companies_count": count
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/api/companies")
async def get_companies():
    """Получить список всех компаний"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, short_name, full_name, inn, region, address, 
                   ido, ifr, ipd, spark_risk, authorized_capital, registration_date
            FROM company 
            ORDER BY short_name
        """)
        
        companies = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {"companies": companies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/companies/{company_id}")
async def get_company(company_id: int):
    """Получить данные конкретной компании"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, short_name, full_name, inn, region, address, 
                   ido, ifr, ipd, spark_risk, authorized_capital, registration_date
            FROM company 
            WHERE id = %s
        """, (company_id,))
        
        company = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return {"company": company}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/dashboard-data")
async def get_dashboard_data() -> Dict[str, Any]:
    """
    Получить все данные для дашборда из таблицы company
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1. KPI метрики
        cursor.execute("""
            SELECT
                COUNT(*) as total_companies,
                AVG(ido) as avg_ido,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ifr) as avg_ifr,
                AVG(ipd) as avg_ipd,
                AVG(authorized_capital) as avg_capital,
                MIN(authorized_capital) as min_capital,
                MAX(authorized_capital) as max_capital,
                COUNT(CASE WHEN spark_risk = 'Низкий' THEN 1 END) as low_risk_count,
                COUNT(CASE WHEN spark_risk = 'Средний' THEN 1 END) as medium_risk_count,
                COUNT(CASE WHEN spark_risk = 'Высокий' THEN 1 END) as high_risk_count,
                COUNT(CASE WHEN spark_risk = 'Критический' THEN 1 END) as critical_risk_count
            FROM company
        """)
        kpi_data = cursor.fetchone()

        # 2. Распределение компаний по регионам
        cursor.execute("""
            SELECT region, COUNT(*) as count
            FROM company
            WHERE region IS NOT NULL
            GROUP BY region
            ORDER BY COUNT(*) DESC
        """)
        companies_by_region = cursor.fetchall()

        # 3. Распределение компаний по рискам
        cursor.execute("""
            SELECT spark_risk, COUNT(*) as count
            FROM company
            WHERE spark_risk IS NOT NULL
            GROUP BY spark_risk
            ORDER BY 
                CASE spark_risk
                    WHEN 'Низкий' THEN 1
                    WHEN 'Средний' THEN 2
                    WHEN 'Высокий' THEN 3
                    WHEN 'Критический' THEN 4
                    ELSE 5
                END
        """)
        companies_by_risk = cursor.fetchall()

        # 4. Топ компаний по уставному капиталу
        cursor.execute("""
            SELECT short_name, authorized_capital, spark_risk, region
            FROM company
            WHERE authorized_capital IS NOT NULL
            ORDER BY authorized_capital DESC
            LIMIT 10
        """)
        top_companies_by_capital = cursor.fetchall()

        # 5. Корреляция риска и капитала
        cursor.execute("""
            SELECT short_name, spark_risk, authorized_capital, ido, ifr, ipd
            FROM company
            WHERE spark_risk IS NOT NULL AND authorized_capital IS NOT NULL
            ORDER BY authorized_capital DESC
            LIMIT 15
        """)
        risk_capital_correlation = cursor.fetchall()

        # 6. Статистика по показателям ИДО, ИФР, ИПД
        cursor.execute("""
            SELECT 
                CASE
                    WHEN ido IS NULL THEN 'Не указан'
                    WHEN ido < 50 THEN 'Низкий (<50)'
                    WHEN ido < 70 THEN 'Ниже среднего (50-70)'
                    WHEN ido < 85 THEN 'Средний (70-85)'
                    ELSE 'Высокий (85+)'
                END as ido_group,
                COUNT(*) as count
            FROM company
            GROUP BY 
                CASE
                    WHEN ido IS NULL THEN 'Не указан'
                    WHEN ido < 50 THEN 'Низкий (<50)'
                    WHEN ido < 70 THEN 'Ниже среднего (50-70)'
                    WHEN ido < 85 THEN 'Средний (70-85)'
                    ELSE 'Высокий (85+)'
                END
            ORDER BY 
                CASE
                    WHEN CASE
                        WHEN ido IS NULL THEN 'Не указан'
                        WHEN ido < 50 THEN 'Низкий (<50)'
                        WHEN ido < 70 THEN 'Ниже среднего (50-70)'
                        WHEN ido < 85 THEN 'Средний (70-85)'
                        ELSE 'Высокий (85+)'
                    END = 'Не указан' THEN 0
                    WHEN CASE
                        WHEN ido IS NULL THEN 'Не указан'
                        WHEN ido < 50 THEN 'Низкий (<50)'
                        WHEN ido < 70 THEN 'Ниже среднего (50-70)'
                        WHEN ido < 85 THEN 'Средний (70-85)'
                        ELSE 'Высокий (85+)'
                    END = 'Низкий (<50)' THEN 1
                    WHEN CASE
                        WHEN ido IS NULL THEN 'Не указан'
                        WHEN ido < 50 THEN 'Низкий (<50)'
                        WHEN ido < 70 THEN 'Ниже среднего (50-70)'
                        WHEN ido < 85 THEN 'Средний (70-85)'
                        ELSE 'Высокий (85+)'
                    END = 'Ниже среднего (50-70)' THEN 2
                    WHEN CASE
                        WHEN ido IS NULL THEN 'Не указан'
                        WHEN ido < 50 THEN 'Низкий (<50)'
                        WHEN ido < 70 THEN 'Ниже среднего (50-70)'
                        WHEN ido < 85 THEN 'Средний (70-85)'
                        ELSE 'Высокий (85+)'
                    END = 'Средний (70-85)' THEN 3
                    ELSE 4
                END
        """)
        ido_distribution = cursor.fetchall()

        # 7. Распределение по размеру капитала
        cursor.execute("""
            SELECT 
                CASE
                    WHEN authorized_capital IS NULL THEN 'Не указан'
                    WHEN authorized_capital < 1000000 THEN 'До 1 млн'
                    WHEN authorized_capital < 10000000 THEN '1-10 млн'
                    WHEN authorized_capital < 100000000 THEN '10-100 млн'
                    ELSE 'Свыше 100 млн'
                END as capital_group,
                COUNT(*) as count
            FROM company
            GROUP BY 
                CASE
                    WHEN authorized_capital IS NULL THEN 'Не указан'
                    WHEN authorized_capital < 1000000 THEN 'До 1 млн'
                    WHEN authorized_capital < 10000000 THEN '1-10 млн'
                    WHEN authorized_capital < 100000000 THEN '10-100 млн'
                    ELSE 'Свыше 100 млн'
                END
            ORDER BY 
                CASE
                    WHEN CASE
                        WHEN authorized_capital IS NULL THEN 'Не указан'
                        WHEN authorized_capital < 1000000 THEN 'До 1 млн'
                        WHEN authorized_capital < 10000000 THEN '1-10 млн'
                        WHEN authorized_capital < 100000000 THEN '10-100 млн'
                        ELSE 'Свыше 100 млн'
                    END = 'Не указан' THEN 0
                    WHEN CASE
                        WHEN authorized_capital IS NULL THEN 'Не указан'
                        WHEN authorized_capital < 1000000 THEN 'До 1 млн'
                        WHEN authorized_capital < 10000000 THEN '1-10 млн'
                        WHEN authorized_capital < 100000000 THEN '10-100 млн'
                        ELSE 'Свыше 100 млн'
                    END = 'До 1 млн' THEN 1
                    WHEN CASE
                        WHEN authorized_capital IS NULL THEN 'Не указан'
                        WHEN authorized_capital < 1000000 THEN 'До 1 млн'
                        WHEN authorized_capital < 10000000 THEN '1-10 млн'
                        WHEN authorized_capital < 100000000 THEN '10-100 млн'
                        ELSE 'Свыше 100 млн'
                    END = '1-10 млн' THEN 2
                    WHEN CASE
                        WHEN authorized_capital IS NULL THEN 'Не указан'
                        WHEN authorized_capital < 1000000 THEN 'До 1 млн'
                        WHEN authorized_capital < 10000000 THEN '1-10 млн'
                        WHEN authorized_capital < 100000000 THEN '10-100 млн'
                        ELSE 'Свыше 100 млн'
                    END = '10-100 млн' THEN 3
                    ELSE 4
                END
        """)
        capital_distribution = cursor.fetchall()

        # Формируем KPI
        kpi = {
            "total_companies": kpi_data.get('total_companies', 0) or 0,
            "avg_ido": round(float(kpi_data.get('avg_ido', 0) or 0), 2),
            "avg_ifr": round(float(kpi_data.get('avg_ifr', 0) or 0), 2),  # Медианный ИФР
            "avg_ipd": round(float(kpi_data.get('avg_ipd', 0) or 0), 2),
            "avg_capital": round(float(kpi_data.get('avg_capital', 0) or 0), 2),
            "min_capital": round(float(kpi_data.get('min_capital', 0) or 0), 2),
            "max_capital": round(float(kpi_data.get('max_capital', 0) or 0), 2),
            "low_risk_count": kpi_data.get('low_risk_count', 0) or 0,
            "medium_risk_count": kpi_data.get('medium_risk_count', 0) or 0,
            "high_risk_count": kpi_data.get('high_risk_count', 0) or 0,
            "critical_risk_count": kpi_data.get('critical_risk_count', 0) or 0
        }

        # Метаданные
        meta = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "currency": "₽"
        }

        cursor.close()
        conn.close()

        return {
            "kpi": kpi,
            "companies_by_region": companies_by_region,
            "companies_by_risk": companies_by_risk,
            "top_companies_by_capital": top_companies_by_capital,
            "risk_capital_correlation": risk_capital_correlation,
            "ido_distribution": ido_distribution,
            "capital_distribution": capital_distribution,
            "meta": meta
        }

    except Exception as e:
        print(f"Database error: {e}")
        return {
            "kpi": {
                "total_companies": 0, "avg_ido": 0, "avg_ifr": 0, "avg_ipd": 0,
                "avg_capital": 0, "min_capital": 0, "max_capital": 0,
                "low_risk_count": 0, "medium_risk_count": 0, "high_risk_count": 0, "critical_risk_count": 0
            },
            "companies_by_region": [],
            "companies_by_risk": [],
            "top_companies_by_capital": [],
            "risk_capital_correlation": [],
            "ido_distribution": [],
            "capital_distribution": [],
            "meta": {"generated_at": datetime.now().isoformat(), "currency": "₽", "error": str(e)}
        }


@app.get("/api/components/metrics")
async def get_components_metrics() -> Dict[str, Any]:
    """Агрегированные метрики по таблице component"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # KPI
        cursor.execute("""
            SELECT
                COUNT(*) AS total_components,
                COALESCE(SUM(quantity), 0) AS total_quantity,
                COUNT(DISTINCT object_type) AS unique_object_types,
                COUNT(DISTINCT included_in_name) AS unique_included_in_names
            FROM component
        """)
        kpi_row = cursor.fetchone()

        # Топ-15 included_in_name по количеству компонентов
        cursor.execute("""
            SELECT included_in_name, COUNT(*) AS count
            FROM component
            WHERE included_in_name IS NOT NULL AND included_in_name <> ''
            GROUP BY included_in_name
            ORDER BY COUNT(*) DESC
            LIMIT 15
        """)
        top_included_in = cursor.fetchall()

        # Сколько групп вне топ-15
        cursor.execute("""
            SELECT COUNT(*) AS others_count
            FROM (
                SELECT included_in_name
                FROM component
                WHERE included_in_name IS NOT NULL AND included_in_name <> ''
                GROUP BY included_in_name
                ORDER BY COUNT(*) DESC
                OFFSET 15
            ) t
        """)
        others_groups = cursor.fetchone() or {"others_count": 0}

        # Распределение по типу объекта
        cursor.execute("""
            SELECT object_type, COUNT(*) AS count
            FROM component
            WHERE object_type IS NOT NULL AND object_type <> ''
            GROUP BY object_type
            ORDER BY COUNT(*) DESC
            LIMIT 12
        """)
        by_object_type = cursor.fetchall()

        # Топ-10 поставщиков
        cursor.execute("""
            SELECT supplier, COUNT(*) AS count
            FROM component
            WHERE supplier IS NOT NULL AND supplier <> ''
            GROUP BY supplier
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        top_suppliers = cursor.fetchall()

        # Топ-15 included_in_name по сумме quantity
        cursor.execute("""
            SELECT included_in_name, COALESCE(SUM(quantity), 0) AS total_quantity
            FROM component
            WHERE included_in_name IS NOT NULL AND included_in_name <> ''
            GROUP BY included_in_name
            ORDER BY COALESCE(SUM(quantity), 0) DESC
            LIMIT 15
        """)
        quantity_by_included_in = cursor.fetchall()

        # Динамика по месяцам
        cursor.execute("""
            SELECT
                DATE_TRUNC('month', created_at) AS month,
                COUNT(*) AS count
            FROM component
            WHERE created_at IS NOT NULL
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month
        """)
        timeline_by_month = cursor.fetchall()

        cursor.close()
        conn.close()

        kpi = {
            "total_components": int(kpi_row.get("total_components", 0) or 0),
            "total_quantity": int(kpi_row.get("total_quantity", 0) or 0),
            "unique_object_types": int(kpi_row.get("unique_object_types", 0) or 0),
            "unique_included_in_names": int(kpi_row.get("unique_included_in_names", 0) or 0),
        }

        meta = {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")}

        return {
            "kpi": kpi,
            "top_included_in": top_included_in,
            "others_groups": others_groups,
            "by_object_type": by_object_type,
            "top_suppliers": top_suppliers,
            "quantity_by_included_in": quantity_by_included_in,
            "timeline_by_month": timeline_by_month,
            "meta": meta
        }

    except Exception as e:
        print(f"Components metrics error: {e}")
        return {
            "kpi": {
                "total_components": 0,
                "total_quantity": 0,
                "unique_object_types": 0,
                "unique_included_in_names": 0
            },
            "top_included_in": [],
            "others_groups": {"others_count": 0},
            "by_object_type": [],
            "top_suppliers": [],
            "quantity_by_included_in": [],
            "timeline_by_month": [],
            "meta": {"generated_at": datetime.now().isoformat(), "error": str(e)}
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
