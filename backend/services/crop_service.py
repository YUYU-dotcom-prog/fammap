"""
🌱 작물재배정보 서비스
농사로 공공데이터 기반 작물별 재배 정보
"""

import requests
from core.config import CROP_INFO_API_KEY

BASE_URL = "http://api.nongsaro.go.kr/service/cropList"


class CropService:

    def get_crop_list(self, keyword: str = "") -> list[dict]:
        """작물 목록 조회"""
        url = f"{BASE_URL}/cropListSearch"
        params = {
            "apiKey": CROP_INFO_API_KEY,
            "searchWord": keyword,
            "numOfRows": 20,
            "pageNo": 1,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            items = resp.json().get("response", {}).get("body", {}).get("items", [])
            if isinstance(items, dict):
                items = items.get("item", [])
            if isinstance(items, dict):
                items = [items]
            return [self._parse_crop(i) for i in items]
        except Exception as e:
            print(f"작물 목록 조회 오류: {e}")
            return []

    def get_crop_detail(self, crop_id: str) -> dict | None:
        """작물 상세 정보 조회"""
        url = f"{BASE_URL}/cropDetail"
        params = {
            "apiKey": CROP_INFO_API_KEY,
            "cropId": crop_id,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            item = resp.json().get("response", {}).get("body", {}).get("items", {}).get("item", None)
            if not item:
                return None
            if isinstance(item, list):
                item = item[0]
            return self._parse_crop_detail(item)
        except Exception as e:
            print(f"작물 상세 조회 오류: {e}")
            return None

    def _parse_crop(self, item: dict) -> dict:
        return {
            "crop_id": item.get("cropId"),
            "name": item.get("cropNm"),
            "category": item.get("lstFileNm"),
        }

    def _parse_crop_detail(self, item: dict) -> dict:
        return {
            "crop_id": item.get("cropId"),
            "name": item.get("cropNm"),
            "growing_temp": item.get("grwTprt"),        # 생육 온도
            "soil_ph": item.get("soilPh"),              # 토양 pH
            "water_need": item.get("waterNeed"),        # 물 필요량
            "sow_time": item.get("sowTime"),            # 파종 시기
            "harvest_time": item.get("harvestTime"),    # 수확 시기
            "description": item.get("cropDesc"),        # 설명
        }