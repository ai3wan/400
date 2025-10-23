#!/usr/bin/env python3
"""
Простой тест API для проверки работы с базой данных
"""
import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("🔍 Тестирование API...")
    
    # 1. Проверка health endpoint
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Статус: {data.get('status')}")
            print(f"   Количество компаний: {data.get('companies_count')}")
        else:
            print(f"   Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # 2. Проверка companies endpoint
    try:
        response = requests.get(f"{base_url}/api/companies")
        print(f"✅ Companies endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            companies = data.get('companies', [])
            print(f"   Найдено компаний: {len(companies)}")
            if companies:
                print(f"   Первая компания: {companies[0].get('short_name')}")
        else:
            print(f"   Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Companies endpoint failed: {e}")
    
    # 3. Проверка dashboard-data endpoint
    try:
        response = requests.get(f"{base_url}/api/dashboard-data")
        print(f"✅ Dashboard data: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            kpi = data.get('kpi', {})
            print(f"   KPI данные получены: {bool(kpi)}")
            print(f"   Всего компаний в KPI: {kpi.get('total_companies')}")
        else:
            print(f"   Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Dashboard data failed: {e}")

if __name__ == "__main__":
    test_api()
