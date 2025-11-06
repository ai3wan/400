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
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from datetime import date

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
async def get_components_metrics(included_in_name: Optional[str] = None, supplier: Optional[str] = None, company_id: Optional[int] = None) -> Dict[str, Any]:
    """Агрегированные метрики по таблице component"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Подготовка WHERE и параметров
        where_clauses: List[str] = []
        params: List[Any] = []
        if included_in_name:
            where_clauses.append("comp.included_in_name = %s")
            params.append(included_in_name)
        if supplier:
            where_clauses.append("comp.supplier = %s")
            params.append(supplier)
        if company_id is not None:
            where_clauses.append("comp.company_id = %s")
            params.append(company_id)
        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # KPI
        cursor.execute(
            f"""
            SELECT
                COUNT(*) AS total_components,
                COALESCE(SUM(quantity), 0) AS total_quantity,
                COUNT(DISTINCT object_type) AS unique_object_types,
                COUNT(DISTINCT included_in_name) AS unique_included_in_names
            FROM component{where_sql}
            """,
            params,
        )
        kpi_row = cursor.fetchone()

        # Топ-15 included_in_name по количеству компонентов (при фильтре вернётся соответствующая группа)
        cursor.execute(
            f"""
            SELECT included_in_name, COUNT(*) AS count
            FROM component
            {('WHERE' if not where_sql else where_sql + ' AND')} included_in_name IS NOT NULL AND included_in_name <> ''
            GROUP BY included_in_name
            ORDER BY COUNT(*) DESC
            LIMIT 15
            """,
            params,
        )
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
        cursor.execute(
            f"""
            SELECT comp.object_type, COUNT(*) AS count
            FROM component comp
            {('WHERE' if not where_sql else where_sql + ' AND')} comp.object_type IS NOT NULL AND comp.object_type <> ''
            GROUP BY comp.object_type
            ORDER BY COUNT(*) DESC
            LIMIT 12
            """,
            params,
        )
        by_object_type = cursor.fetchall()

        # Распределение по системам (included_in_object_type)
        cursor.execute(
            f"""
            SELECT comp.included_in_object_type AS system, COUNT(*) AS count
            FROM component comp
            {('WHERE' if not where_sql else where_sql + ' AND')} comp.included_in_object_type IS NOT NULL AND comp.included_in_object_type <> ''
            GROUP BY comp.included_in_object_type
            ORDER BY COUNT(*) DESC
            LIMIT 12
            """,
            params,
        )
        by_systems = cursor.fetchall()

        # Топ-10 поставщиков
        cursor.execute(
            f"""
            SELECT comp.supplier, COUNT(*) AS count
            FROM component comp
            {('WHERE' if not where_sql else where_sql + ' AND')} comp.supplier IS NOT NULL AND comp.supplier <> ''
            GROUP BY comp.supplier
            ORDER BY COUNT(*) DESC
            LIMIT 10
            """,
            params,
        )
        top_suppliers = cursor.fetchall()

        # Топ-10 компаний по числу компонентов (через FK company_id → company.id)
        cursor.execute(
            f"""
            SELECT COALESCE(c.short_name, 'Не указано') AS company_short_name, COUNT(*) AS count, c.id AS company_id
            FROM component comp
            LEFT JOIN company c ON c.id = comp.company_id
            {where_sql}
            GROUP BY COALESCE(c.short_name, 'Не указано'), c.id
            ORDER BY COUNT(*) DESC
            LIMIT 10
            """,
            params,
        )
        top_companies = cursor.fetchall()

        # Топ-15 included_in_name по сумме quantity
        cursor.execute(
            f"""
            SELECT comp.included_in_name, COALESCE(SUM(comp.quantity), 0) AS total_quantity
            FROM component comp
            {('WHERE' if not where_sql else where_sql + ' AND')} comp.included_in_name IS NOT NULL AND comp.included_in_name <> ''
            GROUP BY comp.included_in_name
            ORDER BY COALESCE(SUM(comp.quantity), 0) DESC
            LIMIT 15
            """,
            params,
        )
        quantity_by_included_in = cursor.fetchall()

        # Динамика по месяцам
        cursor.execute(
            f"""
            SELECT
                DATE_TRUNC('month', comp.created_at) AS month,
                COUNT(*) AS count
            FROM component comp
            {('WHERE' if not where_sql else where_sql + ' AND')} comp.created_at IS NOT NULL
            GROUP BY DATE_TRUNC('month', comp.created_at)
            ORDER BY month
            """,
            params,
        )
        timeline_by_month = cursor.fetchall()

        cursor.close()
        conn.close()

        kpi = {
            "total_components": int(kpi_row.get("total_components", 0) or 0),
            "total_quantity": int(kpi_row.get("total_quantity", 0) or 0),
            "unique_object_types": int(kpi_row.get("unique_object_types", 0) or 0),
            "unique_included_in_names": int(kpi_row.get("unique_included_in_names", 0) or 0),
        }

        meta = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "filter": {"included_in_name": included_in_name} if included_in_name else {}
        }

        return {
            "kpi": kpi,
            "top_included_in": top_included_in,
            "others_groups": others_groups,
            "by_object_type": by_object_type,
            "by_systems": by_systems,
            "top_suppliers": top_suppliers,
            "top_companies": top_companies,
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
            "by_systems": [],
            "top_suppliers": [],
            "top_companies": [],
            "quantity_by_included_in": [],
            "timeline_by_month": [],
            "meta": {"generated_at": datetime.now().isoformat(), "error": str(e)}
        }


@app.get("/api/components/included-in-list")
async def get_included_in_list(q: Optional[str] = None, limit: int = 1000) -> Dict[str, Any]:
    """Вернуть список включений (included_in_name), упорядоченный по частоте.
    Параметры:
      - q: фильтр по подстроке (ILIKE)
      - limit: максимальное число записей (по умолчанию 1000)
    """
    try:
        limit = max(1, min(limit, 5000))
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        if q:
            cursor.execute(
                """
                SELECT included_in_name, COUNT(*) AS count
                FROM component
                WHERE included_in_name IS NOT NULL AND included_in_name <> '' AND included_in_name ILIKE %s
                GROUP BY included_in_name
                ORDER BY COUNT(*) DESC, included_in_name ASC
                LIMIT %s
                """,
                (f"%{q}%", limit),
            )
        else:
            cursor.execute(
                """
                SELECT included_in_name, COUNT(*) AS count
                FROM component
                WHERE included_in_name IS NOT NULL AND included_in_name <> ''
                GROUP BY included_in_name
                ORDER BY COUNT(*) DESC, included_in_name ASC
                LIMIT %s
                """,
                (limit,),
            )

        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"items": rows, "total": len(rows)}
    except Exception as e:
        print(f"Included-in list error: {e}")
        return {"items": [], "total": 0, "error": str(e)}


@app.get("/api/components/suppliers-list")
async def get_suppliers_list(q: Optional[str] = None, limit: int = 1000) -> Dict[str, Any]:
    """Вернуть список поставщиков, упорядоченный по частоте."""
    try:
        limit = max(1, min(limit, 5000))
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        if q:
            cursor.execute(
                """
                SELECT supplier, COUNT(*) AS count
                FROM component
                WHERE supplier IS NOT NULL AND supplier <> '' AND supplier ILIKE %s
                GROUP BY supplier
                ORDER BY COUNT(*) DESC, supplier ASC
                LIMIT %s
                """,
                (f"%{q}%", limit),
            )
        else:
            cursor.execute(
                """
                SELECT supplier, COUNT(*) AS count
                FROM component
                WHERE supplier IS NOT NULL AND supplier <> ''
                GROUP BY supplier
                ORDER BY COUNT(*) DESC, supplier ASC
                LIMIT %s
                """,
                (limit,),
            )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"items": rows, "total": len(rows)}
    except Exception as e:
        print(f"Suppliers list error: {e}")
        return {"items": [], "total": 0, "error": str(e)}


@app.get("/api/components/companies-list")
async def get_companies_list(q: Optional[str] = None, limit: int = 1000) -> Dict[str, Any]:
    try:
        limit = max(1, min(limit, 5000))
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        if q:
            cursor.execute(
                """
                SELECT c.id AS company_id, c.short_name, COUNT(*) AS count
                FROM component comp
                JOIN company c ON c.id = comp.company_id
                WHERE c.short_name ILIKE %s
                GROUP BY c.id, c.short_name
                ORDER BY COUNT(*) DESC, c.short_name ASC
                LIMIT %s
                """,
                (f"%{q}%", limit),
            )
        else:
            cursor.execute(
                """
                SELECT c.id AS company_id, c.short_name, COUNT(*) AS count
                FROM component comp
                JOIN company c ON c.id = comp.company_id
                GROUP BY c.id, c.short_name
                ORDER BY COUNT(*) DESC, c.short_name ASC
                LIMIT %s
                """,
                (limit,),
            )
        rows = cursor.fetchall()
        cursor.close(); conn.close()
        return {"items": rows, "total": len(rows)}
    except Exception as e:
        print(f"Companies list error: {e}")
        return {"items": [], "total": 0, "error": str(e)}

@app.get("/api/okr/operational-summary")
async def okr_operational_summary() -> Dict[str, Any]:
    """
    Оперативный сводный дашборд по таблице okr_status с lookup-таблицами:
      - KPI: всего в работе; всего выполнено (когда-либо); горящие (в работе и end_plan_date < today);
             средний % выполнения по задачам в работе
      - Воронка по фазам: количество задач по каждой фазе (ТЗ/ОО/ПИ)
      - Статус по фазам (stacked): по каждой фазе разбивка по статусам (не начато/в работе/выполнено)
      - Топ-5 горящих задач: самые просроченные (в работе и end_plan_date < today)
    """
    try:
        today = date.today()
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Получим id статусов по именам для точного сравнения (на случай различий регистра)
        cursor.execute("SELECT id, name FROM work_statuses")
        status_rows = cursor.fetchall()
        name_to_status = { (r["name"].strip().lower() if r["name"] else ""): r["id"] for r in status_rows }
        st_not_started = name_to_status.get("не начато")
        st_in_progress = name_to_status.get("в работе")
        st_done = name_to_status.get("выполнено")

        # KPI: количество уникальных систем (строк в system_okr)
        cursor.execute("SELECT COUNT(*) AS cnt FROM system_okr")
        total_in_work = int((cursor.fetchone() or {}).get("cnt", 0))

        # KPI: всего выполнено (когда-либо)
        cursor.execute("""
            SELECT COUNT(*) AS cnt
            FROM okr_status
            WHERE status_id = %s
        """, (st_done,))
        total_done = int((cursor.fetchone() or {}).get("cnt", 0))

        # KPI: горящие (в работе и плановая дата окончания < today)
        cursor.execute("""
            SELECT COUNT(*) AS cnt
            FROM okr_status
            WHERE status_id = %s AND end_plan_date IS NOT NULL AND end_plan_date < %s
        """, (st_in_progress, today))
        overdue_now = int((cursor.fetchone() or {}).get("cnt", 0))

        # KPI: средний % выполнения по задачам в работе
        cursor.execute("""
            SELECT AVG(progress_percentage)::float AS avg_progress
            FROM okr_status
            WHERE status_id = %s
        """, (st_in_progress,))
        avg_progress = float((cursor.fetchone() or {}).get("avg_progress", 0.0) or 0.0)

        # KPI: полностью выполнено ОКР — количество строк во вью okr_ready
        try:
            cursor.execute("SELECT COUNT(*) AS cnt FROM okr_ready")
            total_ready = int((cursor.fetchone() or {}).get("cnt", 0))
        except Exception:
            total_ready = 0

        kpi = {
            "total_in_work": total_in_work,
            "total_done": total_done,
            "overdue_now": overdue_now,
            "avg_progress_in_work": round(avg_progress, 2),
            "total_ready": total_ready,
        }

        # Воронка по фазам: общее количество задач на каждую фазу
        cursor.execute("""
            SELECT wp.name AS phase, COUNT(*) AS count
            FROM okr_status os
            JOIN work_phases wp ON wp.id = os.work_phase_id
            GROUP BY wp.name
            ORDER BY wp.name
        """)
        funnel_by_phase = cursor.fetchall()

        # Статус по фазам (stacked): counts по статусам внутри каждой фазы
        cursor.execute("""
            SELECT wp.name AS phase, ws.name AS status, COUNT(*) AS count
            FROM okr_status os
            JOIN work_phases wp ON wp.id = os.work_phase_id
            JOIN work_statuses ws ON ws.id = os.status_id
            GROUP BY wp.name, ws.name
            ORDER BY wp.name, ws.name
        """)
        rows = cursor.fetchall()
        # нормализуем в структуру: { phase: { status: count } }
        stacked_by_phase_status: Dict[str, Dict[str, int]] = {}
        for r in rows:
            phase = r.get("phase") or "—"
            status = r.get("status") or "—"
            count = int(r.get("count") or 0)
            if phase not in stacked_by_phase_status:
                stacked_by_phase_status[phase] = {}
            stacked_by_phase_status[phase][status] = count

        # Топ-5 горящих задач с максимальной просрочкой
        cursor.execute("""
            SELECT 
                os.id,
                so.name AS system_name,
                COALESCE(c.short_name, '—') AS supplier,
                wp.name AS work_phase,
                os.end_plan_date,
                (CURRENT_DATE - os.end_plan_date) AS days_overdue
            FROM okr_status os
            JOIN system_okr so ON so.id = os.system_id
            JOIN work_phases wp ON wp.id = os.work_phase_id
            LEFT JOIN company c ON c.id = os.supplier_id
            WHERE os.status_id = %s 
              AND os.end_plan_date IS NOT NULL 
              AND os.end_plan_date < CURRENT_DATE
            ORDER BY (CURRENT_DATE - os.end_plan_date) DESC
            LIMIT 5
        """, (st_in_progress,))
        top_overdue = cursor.fetchall()

        cursor.close(); conn.close()

        return {
            "kpi": kpi,
            "funnel_by_phase": funnel_by_phase,
            "stacked_by_phase_status": stacked_by_phase_status,
            "top_overdue": top_overdue,
            "meta": {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")}
        }
    except Exception as e:
        try:
            cursor.close(); conn.close()
        except Exception:
            pass
        return {
            "kpi": {"total_in_work": 0, "total_done": 0, "overdue_now": 0, "avg_progress_in_work": 0},
            "funnel_by_phase": [],
            "stacked_by_phase_status": {},
            "top_overdue": [],
            "meta": {"generated_at": datetime.now().isoformat(), "error": str(e)}
        }


@app.get("/api/okr/summary-by-phase")
async def okr_summary_by_phase() -> Dict[str, Any]:
    """
    Агрегация из представления okr_summary: количество текущих ОКР:
      - ТЗ
      - ОО
      - ПИ (не выполнено, progress < 100)
      - Выполнено (ПИ с progress = 100)
    Возвращает массив [{phase, count}].
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT phase, count FROM (
              SELECT 'ТЗ'::text AS phase, COUNT(*)::bigint AS count
              FROM okr_summary WHERE current_phase = 'ТЗ'
            UNION ALL
              SELECT 'ОО'::text AS phase, COUNT(*)::bigint AS count
              FROM okr_summary WHERE current_phase = 'ОО'
            UNION ALL
              SELECT 'ПИ'::text AS phase, COUNT(*)::bigint AS count
              FROM okr_summary WHERE current_phase = 'ПИ' AND COALESCE(current_progress, 0) < 100
            UNION ALL
              SELECT 'Выполнено'::text AS phase, COUNT(*)::bigint AS count
              FROM okr_summary WHERE current_phase = 'ПИ' AND COALESCE(current_progress, 0) = 100
            ) t
            """
        )
        rows = cursor.fetchall()
        cursor.close(); conn.close()

        # Упорядочим: ТЗ -> ОО -> ПИ -> Выполнено
        order = {"ТЗ": 1, "ОО": 2, "ПИ": 3, "Выполнено": 4}
        rows_sorted = sorted(rows, key=lambda r: order.get((r.get("phase") or ""), 99))
        return {"items": rows_sorted, "meta": {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")}}
    except Exception as e:
        return {"items": [], "error": str(e)}


@app.get("/api/okr/funnel")
async def okr_funnel() -> Dict[str, Any]:
    """
    Фанел из представления okr_summary, группировка по current_phase и current_progress.
    Порядок слоёв сверху вниз: ТЗ -> ОО -> ПИ; внутри фазы прогресс по возрастанию.
    Возвращает items: [{phase, progress, count}] уже в нужном порядке.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT current_phase AS phase, COALESCE(current_progress, 0) AS progress, COUNT(*) AS count
            FROM okr_summary
            GROUP BY current_phase, COALESCE(current_progress, 0)
            ORDER BY 
              CASE current_phase
                WHEN 'ТЗ' THEN 1
                WHEN 'ОО' THEN 2
                WHEN 'ПИ' THEN 3
                ELSE 99
              END,
              COALESCE(current_progress, 0) ASC
            """
        )
        rows = cursor.fetchall()
        cursor.close(); conn.close()
        return {"items": rows, "meta": {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")}}
    except Exception as e:
        return {"items": [], "error": str(e)}


@app.get("/api/okr/details-by-phase")
async def okr_details_by_phase(phase: str) -> Dict[str, Any]:
    """
    Детали ОКР по выбранной фазе. Возвращает:
    system_name, supplier_name, end_plan_date, current_progress (progress_percentage).
    Сортировка по system_name (алфавит).
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT 
                so.name AS system_name,
                COALESCE(c.short_name, '—') AS supplier_name,
                os.end_plan_date,
                COALESCE(os.progress_percentage, 0) AS current_progress
            FROM okr_status os
            JOIN system_okr so ON so.id = os.system_id
            LEFT JOIN company c ON c.id = os.supplier_id
            JOIN work_phases wp ON wp.id = os.work_phase_id
            WHERE wp.name = %s AND COALESCE(os.progress_percentage, 0) < 100
            ORDER BY os.end_plan_date ASC NULLS LAST, COALESCE(os.progress_percentage, 0) ASC, so.name ASC
            """,
            (phase,)
        )
        rows = cursor.fetchall()
        cursor.close(); conn.close()
        return {"items": rows, "meta": {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), "phase": phase}}
    except Exception as e:
        return {"items": [], "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
