"""
🗄️ Firebase station_data 조회 서비스
사전 수집된 데이터를 조회해서 API 호출 최소화
"""

import math
from firebase_admin import firestore
from datetime import datetime, timedelta

db = firestore.client()


class StationService:

    def get_nearest_station_data(self, lat: float, lon: float) -> dict | None:
        """
        가장 가까운 지점의 최신 데이터 조회
        """
        # 어제 날짜
        date = (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")

        # 모든 지점 데이터 조회
        docs = db.collection("station_data").where(
            "date", "==", date
        ).stream()

        nearest = None
        min_dist = float("inf")

        for doc in docs:
            data = doc.to_dict()
            dist = self._distance(lat, lon, data["lat"], data["lon"])
            if dist < min_dist:
                min_dist = dist
                nearest = data

        return nearest

    def get_station_data(self, station_id: str) -> dict | None:
        """특정 지점 최신 데이터 조회"""
        date = (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")
        doc_id = f"{station_id}_{date}"
        doc = db.collection("station_data").document(doc_id).get()
        return doc.to_dict() if doc.exists else None

    def get_all_stations_data(self) -> list[dict]:
        """전체 지점 최신 데이터 조회 (지도용)"""
        date = (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")
        docs = db.collection("station_data").where(
            "date", "==", date
        ).stream()
        return [doc.to_dict() for doc in docs]

    def _distance(self, lat1, lon1, lat2, lon2) -> float:
        """두 좌표 간 거리 계산 (km)"""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    