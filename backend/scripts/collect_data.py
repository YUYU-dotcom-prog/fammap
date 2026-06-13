"""
🚀 전국 농업기상 데이터 수집 및 Firebase 원샷 백업 스크립트
"""

import sys
import os
from datetime import datetime
import time

# 프로젝트 루트 경로 주입
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.weather_service import WeatherService
from firebase_admin import firestore
import firebase_admin

# Firebase 안전 초기화
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()


def collect_and_save():
    print("📡 [Batch] 전국 기상 데이터 수집 및 Firebase 원샷 패키징 시작...")

    weather_service = WeatherService()
    today_str = datetime.now().strftime("%Y%m%d")

    korea_weather_payload = {}
    stations_list = getattr(weather_service, "stations", [])

    if not stations_list:
        print("❌ [Error] weather_service에서 stations 리스트를 참조할 수 없습니다.")
        return

    total = len(stations_list)
    print(f"📊 총 {total}개 지점 데이터를 수집합니다.")

    for idx, st in enumerate(stations_list, 1):
        st_id = st["id"]
        print(f"🔄 [{idx}/{total}] {st['name']} 데이터 수집 중...")

        # 공공 API 연동 호출
        point_weather = weather_service.get_point_weather(
            st["lat"], st["lon"], today_str
        )

        if point_weather:
            # 원샷 패키징을 위한 데이터 경량화 (부모 레벨에 이미 명시되므로 제외)
            point_weather.pop("lat", None)
            point_weather.pop("lon", None)

            korea_weather_payload[st_id] = {
                "name": st["name"],
                "sido": st["sido"],
                **point_weather,
            }
        
        # 외부 API 과부하 방지 딜레이
        time.sleep(0.3)

    # 🔥 [최적화 핵심] 수집 완료된 데이터를 단 1개의 문서에 몽땅 압축하여 원샷 저장
    if korea_weather_payload:
        doc_ref = db.collection("weather_data").document("korea_summary")
        doc_ref.set(
            {
                "date": today_str,
                "updated_at": int(datetime.now().timestamp()),
                "stations": korea_weather_payload,
            }
        )
        print("✨ [Firebase Success] 단 1회의 쓰기 비용으로 전국 날씨 요약본 저장 완료!")
    else:
        print("⚠️ [Warning] 수집된 데이터가 없어 Firebase 업데이트를 생략합니다.")


if __name__ == "__main__":
    print("🚀 스크립트 가동")
    collect_and_save()
    print("🏁 스크립트 종료")