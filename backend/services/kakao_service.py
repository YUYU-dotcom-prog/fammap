"""
🗺️ 카카오 주소 검색 서비스
주소 → 좌표 변환, 좌표 → 주소 변환
"""

import requests
from core.config import KAKAO_API_KEY


class KakaoService:

    def address_to_coord(self, address: str) -> dict | None:
        """
        주소 → 좌표 변환
        예: "전북 군산시 미룡동" → {"lat": 35.96, "lon": 126.73}
        """
        url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
        params = {"query": address}

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            docs = resp.json().get("documents", [])
            if not docs:
                return None
            doc = docs[0]
            return {
                "address": address,
                "road_address": doc.get("road_address", {}).get("address_name", ""),
                "jibun_address": doc.get("address", {}).get("address_name", ""),
                "lat": float(doc["y"]),
                "lon": float(doc["x"]),
                "region_1": doc.get("address", {}).get("region_1depth_name", ""),
                "region_2": doc.get("address", {}).get("region_2depth_name", ""),
                "region_3": doc.get("address", {}).get("region_3depth_name", ""),
            }
        except Exception as e:
            print(f"카카오 주소 검색 오류: {e}")
            return None

    def coord_to_address(self, lat: float, lon: float) -> dict | None:
        """
        좌표 → 주소 변환
        예: (35.96, 126.73) → "전북 군산시 미룡동"
        """
        url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
        params = {"x": lon, "y": lat}

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            docs = resp.json().get("documents", [])
            if not docs:
                return None
            doc = docs[0]
            return {
                "lat": lat,
                "lon": lon,
                "road_address": doc.get("road_address", {}).get("address_name", "") if doc.get("road_address") else "",
                "jibun_address": doc.get("address", {}).get("address_name", ""),
                "region_1": doc.get("address", {}).get("region_1depth_name", ""),
                "region_2": doc.get("address", {}).get("region_2depth_name", ""),
                "region_3": doc.get("address", {}).get("region_3depth_name", ""),
            }
        except Exception as e:
            print(f"카카오 좌표 변환 오류: {e}")
            return None

    def search_keyword(self, keyword: str, lat: float = None, lon: float = None) -> list[dict]:
        """
        키워드로 장소 검색
        예: "군산 농협" 검색
        """
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
        params = {"query": keyword, "size": 10}
        if lat and lon:
            params["y"] = lat
            params["x"] = lon

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            docs = resp.json().get("documents", [])
            return [{
                "name": d.get("place_name"),
                "address": d.get("road_address_name") or d.get("address_name"),
                "lat": float(d["y"]),
                "lon": float(d["x"]),
                "phone": d.get("phone"),
                "category": d.get("category_name"),
            } for d in docs]
        except Exception as e:
            print(f"카카오 키워드 검색 오류: {e}")
            return []