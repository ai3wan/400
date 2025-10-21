"""
FastAPI Backend для дашборда КУПЭ
Подключение к PostgreSQL и API endpoints
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

app = FastAPI(title="Dashboard KUPE API", version="1.0.0")

# CORS настройки (разрешаем запросы с фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/dashboard_db")


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
        "message": "Dashboard KUPE API",
        "version": "1.0.0",
        "endpoints": {
            "/api/dashboard-data": "Получить все данные дашборда",
            "/api/health": "Проверка здоровья API и БД"
        }
    }


@app.get("/api/health")
async def health_check():
    """Проверка подключения к БД"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {
            "status": "healthy",
            "database": "connected",
            "db_version": db_version
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/api/dashboard-data")
async def get_dashboard_data() -> Dict[str, Any]:
    """
    Получить все данные для дашборда из PostgreSQL
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. KPI данные
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE period = 'current') as komponenty_count_curr,
                COUNT(*) FILTER (WHERE period = 'previous') as komponenty_count_prev,
                AVG(progress) FILTER (WHERE period = 'current') as avg_progress_curr,
                AVG(progress) FILTER (WHERE period = 'previous') as avg_progress_prev,
                COUNT(*) FILTER (WHERE period = 'current' AND is_risk = true) as risks_open_curr,
                COUNT(*) FILTER (WHERE period = 'previous' AND is_risk = true) as risks_open_prev
            FROM komponenty
        """)
        kpi_raw = cursor.fetchone()
        
        kpi = {
            "komponenty_count_curr": kpi_raw.get('komponenty_count_curr', 0) or 0,
            "komponenty_count_prev": kpi_raw.get('komponenty_count_prev', 0) or 0,
            "avg_progress_curr": float(kpi_raw.get('avg_progress_curr', 0) or 0),
            "avg_progress_prev": float(kpi_raw.get('avg_progress_prev', 0) or 0),
            "risks_open_curr": kpi_raw.get('risks_open_curr', 0) or 0,
            "risks_open_prev": kpi_raw.get('risks_open_prev', 0) or 0,
        }
        
        # 2. Статусы компонентов (для pie chart)
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM komponenty
            WHERE period = 'current'
            GROUP BY status
            ORDER BY count DESC
        """)
        pie_status = cursor.fetchall()
        
        # 3. Выпуск КД по месяцам (для line chart)
        cursor.execute("""
            SELECT 
                DATE_TRUNC('month', data_vypuska) as data_vypuska,
                COUNT(*) as count,
                SUM(COUNT(*)) OVER (ORDER BY DATE_TRUNC('month', data_vypuska)) as cum
            FROM konstruktorskie_dokumenty
            GROUP BY DATE_TRUNC('month', data_vypuska)
            ORDER BY data_vypuska
        """)
        kdocs_month_raw = cursor.fetchall()
        kdocs_month = [
            {
                "data_vypuska": row['data_vypuska'].strftime('%Y-%m-%d'),
                "count": row['count'],
                "cum": row['cum']
            }
            for row in kdocs_month_raw
        ]
        
        # 4. Топ поставщики (для bar chart)
        cursor.execute("""
            SELECT 
                k.kompaniya_id,
                ko.nazvanie as nazvanie_kompanii,
                COUNT(*) as components
            FROM komponenty k
            JOIN kompanii ko ON k.kompaniya_id = ko.id
            WHERE k.period = 'current'
            GROUP BY k.kompaniya_id, ko.nazvanie
            ORDER BY components DESC
            LIMIT 7
        """)
        top_suppliers = cursor.fetchall()
        
        # 5. Heatmap данные (риски)
        cursor.execute("""
            SELECT DISTINCT rol FROM kompanii ORDER BY rol
        """)
        roles = [row['rol'] for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT DISTINCT kategoriya FROM riski ORDER BY kategoriya
        """)
        categories = [row['kategoriya'] for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT 
                ko.rol,
                r.kategoriya as kategoriya_riska,
                COUNT(*) as cnt
            FROM riski r
            JOIN komponenty k ON r.komponent_id = k.id
            JOIN kompanii ko ON k.kompaniya_id = ko.id
            WHERE r.veroyatnost > 0.3
            GROUP BY ko.rol, r.kategoriya
        """)
        heat_cells = cursor.fetchall()
        
        heat = {
            "roles": roles,
            "categories": categories,
            "cells": heat_cells
        }
        
        # 6. Gantt данные
        cursor.execute("""
            SELECT 
                CONCAT('T', k.id, '_', ko.id, '_', ko.rol) as id,
                CONCAT(k.nazvanie, ' #', k.id, ' — ', ko.rol) as name,
                k.data_start::text as start,
                k.data_end::text as end,
                k.progress,
                CASE 
                    WHEN k.progress = 100 THEN 'Done'
                    WHEN k.progress > 50 THEN 'In Progress'
                    ELSE 'At Risk'
                END as status,
                ko.nazvanie as owner
            FROM komponenty k
            JOIN kompanii ko ON k.kompaniya_id = ko.id
            WHERE k.period = 'current' AND k.data_start IS NOT NULL
            ORDER BY k.data_start
        """)
        gantt = cursor.fetchall()
        
        # 7. Поставщики по странам (для pie chart)
        cursor.execute("""
            SELECT 
                strana,
                COUNT(*) as count
            FROM postavshchiki
            WHERE aktivnyj = true
            GROUP BY strana
            ORDER BY count DESC
        """)
        suppliers_by_country = cursor.fetchall()
        
        # 8. Риски по категориям (для bar chart)
        cursor.execute("""
            SELECT 
                kategoriya,
                COUNT(*) FILTER (WHERE status = 'Открыт') as open_count,
                COUNT(*) FILTER (WHERE status = 'В работе') as in_progress_count,
                COUNT(*) FILTER (WHERE status = 'Закрыт') as closed_count,
                COUNT(*) as total_count
            FROM riski
            GROUP BY kategoriya
            ORDER BY total_count DESC
        """)
        risks_by_category = cursor.fetchall()
        
        # 9. Матрица рисков (для scatter plot)
        cursor.execute("""
            SELECT 
                r.id,
                r.kategoriya,
                r.opisanie,
                r.veroyatnost,
                r.vliyanie,
                r.status,
                k.nazvanie as komponent_nazvanie
            FROM riski r
            JOIN komponenty k ON r.komponent_id = k.id
            WHERE r.status != 'Закрыт'
            ORDER BY r.veroyatnost DESC, r.vliyanie DESC
        """)
        risks_matrix = cursor.fetchall()
        
        # 10. Риски по уровню влияния (для pie chart)
        cursor.execute("""
            SELECT 
                vliyanie,
                COUNT(*) as count
            FROM riski
            WHERE status != 'Закрыт'
            GROUP BY vliyanie
            ORDER BY 
                CASE vliyanie
                    WHEN 'Критическое' THEN 1
                    WHEN 'Высокое' THEN 2
                    WHEN 'Среднее' THEN 3
                    WHEN 'Низкое' THEN 4
                END
        """)
        risks_by_impact = cursor.fetchall()
        
        # 11. Топ критичных рисков
        cursor.execute("""
            SELECT 
                r.kategoriya,
                r.opisanie,
                r.veroyatnost,
                r.vliyanie,
                k.nazvanie as komponent_nazvanie,
                (r.veroyatnost * 
                    CASE r.vliyanie
                        WHEN 'Критическое' THEN 4
                        WHEN 'Высокое' THEN 3
                        WHEN 'Среднее' THEN 2
                        WHEN 'Низкое' THEN 1
                    END
                ) as risk_score
            FROM riski r
            JOIN komponenty k ON r.komponent_id = k.id
            WHERE r.status != 'Закрыт'
            ORDER BY risk_score DESC
            LIMIT 5
        """)
        top_risks = cursor.fetchall()
        
        # 12. Компании по ролям (для pie chart)
        cursor.execute("""
            SELECT 
                rol,
                COUNT(*) as count
            FROM kompanii
            GROUP BY rol
            ORDER BY count DESC
        """)
        companies_by_role = cursor.fetchall()
        
        # Метаданные
        meta = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "currency": "₽"
        }
        
        cursor.close()
        conn.close()
        
        return {
            "kpi": kpi,
            "pie_status": pie_status,
            "kdocs_month": kdocs_month,
            "top_suppliers": top_suppliers,
            "heat": heat,
            "gantt": gantt,
            "suppliers_by_country": suppliers_by_country,
            "risks_by_category": risks_by_category,
            "risks_matrix": risks_matrix,
            "risks_by_impact": risks_by_impact,
            "top_risks": top_risks,
            "companies_by_role": companies_by_role,
            "meta": meta
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

