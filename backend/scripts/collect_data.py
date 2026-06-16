"""
🌾 농업 데이터 사전 수집 스크립트
매일 새벽 실행해서 Firebase에 저장
실행: python scripts/collect_data.py
"""

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

def get_db():
    return firestore.client()

weather_service = WeatherService()
soil_service    = SoilService()
pest_service    = PestService()

# 대한민국 주요 농업지역 25개 지점
stations = [
    {"id": "seoul",      "name": "서울",   "sido": "서울", "lat": 37.5665, "lon": 126.9780},
    {"id": "incheon",    "name": "인천",   "sido": "인천", "lat": 37.4563, "lon": 126.7052},
    {"id": "suwon",      "name": "수원",   "sido": "경기", "lat": 37.2636, "lon": 127.0286},
    {"id": "yangpyeong", "name": "양평",   "sido": "경기", "lat": 37.4914, "lon": 127.4875},
    {"id": "chuncheon",  "name": "춘천",   "sido": "강원", "lat": 37.8813, "lon": 127.7298},
    {"id": "wonju",      "name": "원주",   "sido": "강원", "lat": 37.3422, "lon": 127.9201},
    {"id": "gangneung",  "name": "강릉",   "sido": "강원", "lat": 37.7519, "lon": 128.8761},
    {"id": "cheonan",    "name": "천안",   "sido": "충남", "lat": 36.8151, "lon": 127.1139},
    {"id": "cheongju",   "name": "청주",   "sido": "충북", "lat": 36.6424, "lon": 127.4890},
    {"id": "hongseong",  "name": "홍성",   "sido": "충남", "lat": 36.6010, "lon": 126.6608},
    {"id": "nonsan",     "name": "논산",   "sido": "충남", "lat": 36.1868, "lon": 127.0988},
    {"id": "jeonju",     "name": "전주",   "sido": "전북", "lat": 35.8242, "lon": 127.1480},
    {"id": "gunsan",     "name": "군산",   "sido": "전북", "lat": 35.9677, "lon": 126.7368},
    {"id": "gimje",      "name": "김제",   "sido": "전북", "lat": 35.8033, "lon": 126.8803},
    {"id": "naju",       "name": "나주",   "sido": "전남", "lat": 35.0160, "lon": 126.7108},
    {"id": "haenam",     "name": "해남",   "sido": "전남", "lat": 34.5739, "lon": 126.5990},
    {"id": "suncheon",   "name": "순천",   "sido": "전남", "lat": 34.9506, "lon": 127.4874},
    {"id": "daegu",      "name": "대구",   "sido": "경북", "lat": 35.8714, "lon": 128.6014},
    {"id": "andong",     "name": "안동",   "sido": "경북", "lat": 36.5684, "lon": 128.7294},
    {"id": "sangju",     "name": "상주",   "sido": "경북", "lat": 36.4108, "lon": 128.1591},
    {"id": "miryang",    "name": "밀양",   "sido": "경남", "lat": 35.5037, "lon": 128.7461},
    {"id": "jinju",      "name": "진주",   "sido": "경남", "lat": 35.1799, "lon": 128.1076},
    {"id": "changwon",   "name": "창원",   "sido": "경남", "lat": 35.2279, "lon": 128.6811},
    {"id": "jeju",       "name": "제주",   "sido": "제주", "lat": 33.4996, "lon": 126.5312},
    {"id": "seogwipo",   "name": "서귀포", "sido": "제주", "lat": 33.2541, "lon": 126.5600},
]


def collect_and_save():
    print("📡 collect_and_save 함수 실행!")

    date  = (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")
    year  = date[:4]
    total = len(stations)

    print(f"\n🌾 데이터 수집 시작 ({date})")
    print(f"   총 {total}개 지점\n")

    success = 0
    fail    = 0

    for i, st in enumerate(stations, 1):
        print(f"  [{i:2d}/{total}] {st['name']} 수집 중...")

        try:
            weather = weather_service.get_point_weather(st["lat"], st["lon"], date)
            time.sleep(0.2)
            soil = soil_service.get_soil(st["lat"], st["lon"])
            time.sleep(0.2)
            pest = pest_service.get_pest_yearly(st["lat"], st["lon"], year)
            time.sleep(0.2)

            doc_id = f"{st['id']}_{date}"
            get_db().collection("station_data").document(doc_id).set({
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


print("🚀 스크립트 시작!")
if __name__ == "__main__":
    collect_and_save()