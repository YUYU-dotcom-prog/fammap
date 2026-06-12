"""
🌾 농업 데이터 사전 수집 스크립트
매일 새벽 실행해서 Firebase에 저장
실행: python scripts/collect_data.py
"""
print("🚀 스크립트 시작!")
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from core.config import FIREBASE_KEY_PATH
from services.weather_service import WeatherService
from services.soil_service import SoilService
from services.pest_service import PestService

# Firebase 초기화
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()
weather_service = WeatherService()
soil_service    = SoilService()
pest_service    = PestService()

print("📡 collect_and_save 함수 실행!")
def collect_and_save():
    date  = (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")
    year  = date[:4]
    total = len(weather_service.stations)

    print(f"\n🌾 데이터 수집 시작 ({date})")
    print(f"   총 {total}개 지점\n")

    success = 0
    fail    = 0

    for i, st in enumerate(weather_service.stations, 1):
        print(f"  [{i:2d}/{total}] {st['name']} 수집 중...")

        try:
            weather = weather_service.get_point_weather(st["lat"], st["lon"], date)
            time.sleep(0.2)
            soil = soil_service.get_soil(st["lat"], st["lon"])
            time.sleep(0.2)
            pest = pest_service.get_pest_yearly(st["lat"], st["lon"], year)
            time.sleep(0.2)

            doc_id = f"{st['id']}_{date}"
            db.collection("station_data").document(doc_id).set({
                "station_id":   st["id"],
                "station_name": st["name"],
                "sido":         st["sido"],
                "lat":          st["lat"],
                "lon":          st["lon"],
                "date":         date,
                "weather":      weather,
                "soil":         soil,
                "pest":         pest,
                "updated_at":   datetime.now().isoformat(),
            })

            print(f"         ✅ 저장 완료")
            success += 1

        except Exception as e:
            print(f"         ❌ 오류: {e}")
            fail += 1

        time.sleep(0.3)

    print(f"\n✅ 완료! 성공: {success}개 / 실패: {fail}개")


if __name__ == "__main__":
    collect_and_save()