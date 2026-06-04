"""
공공데이터포털 팜맵기반 농업기상 API 원시 호출 모듈
"""

import requests
from core.config import API_KEY, BASE_URL, REQUEST_TIMEOUT


def fetch_daily(lat: float, lon: float, date: str) -> dict | None:
    """좌표 기반 일별 농업기상 조회 (원시 응답)"""
    url = f"{BASE_URL}/getCoordinateBasedDayFarmimgWeatherInfo"
    params = {
        "serviceKey": API_KEY,
        "lat": lat,
        "lon": lon,
        "stdrDe": date,
        "numOfRows": 1,
        "pageNo": 1,
        "_type": "json",
    }
    return _request(url, params)


def fetch_hourly(lat: float, lon: float, date: str) -> list[dict]:
    """좌표 기반 시간별 농업기상 조회 (원시 응답)"""
    url = f"{BASE_URL}/getCoordinateBasedHourFarmimgWeatherInfo"
    params = {
        "serviceKey": API_KEY,
        "lat": lat,
        "lon": lon,
        "stdrDe": date,
        "numOfRows": 24,
        "pageNo": 1,
        "_type": "json",
    }
    result = _request(url, params)
    if result is None:
        return []
    return result if isinstance(result, list) else [result]


def _request(url: str, params: dict) -> dict | list | None:
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        body = resp.json().get("response", {}).get("body", {})
        items = body.get("items", {}).get("item", None)
        return items
    except Exception as e:
        print(f"  ⚠️  API 호출 오류: {e}")
        return None
