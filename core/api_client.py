"""
공공데이터포털 팜맵기반 API 원시 호출 모듈
- 농업기상
- 토양검정
- 병해충발생
"""

import requests
from core.config import (
    WEATHER_API_KEY, SOIL_API_KEY, PEST_API_KEY,
    WEATHER_BASE_URL, SOIL_BASE_URL, PEST_BASE_URL,
    REQUEST_TIMEOUT,
)


# ── 농업기상 ──────────────────────────────────────────────────

def fetch_daily(lat: float, lon: float, date: str) -> dict | None:
    """좌표 기반 일별 농업기상 조회"""
    url = f"{WEATHER_BASE_URL}/getCoordinateBasedDayFarmimgWeatherInfo"
    params = {
        "serviceKey": WEATHER_API_KEY,
        "lat": lat,
        "lon": lon,
        "stdrDe": date,
        "numOfRows": 1,
        "pageNo": 1,
        "_type": "json",
    }
    return _request(url, params)


def fetch_hourly(lat: float, lon: float, date: str) -> list[dict]:
    """좌표 기반 시간별 농업기상 조회 (24시간)"""
    url = f"{WEATHER_BASE_URL}/getCoordinateBasedHourFarmimgWeatherInfo"
    params = {
        "serviceKey": WEATHER_API_KEY,
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


# ── 토양검정 ──────────────────────────────────────────────────

def fetch_soil(lat: float, lon: float) -> dict | None:
    """좌표 기반 토양검정 상세조회"""
    url = f"{SOIL_BASE_URL}/getCoordinateBasedSoilAnalsInfo"
    params = {
        "serviceKey": SOIL_API_KEY,
        "lat": lat,
        "lon": lon,
        "numOfRows": 1,
        "pageNo": 1,
        "_type": "json",
    }
    return _request(url, params)


# ── 병해충발생 ────────────────────────────────────────────────

def fetch_pest_yearly(lat: float, lon: float, year: str) -> list[dict]:
    """좌표 기반 년단위 병해충발생 상세조회"""
    url = f"{PEST_BASE_URL}/getCoordinateBasedYearPestOccrrncInfo"
    params = {
        "serviceKey": PEST_API_KEY,
        "lat": lat,
        "lon": lon,
        "stdrYear": year,
        "numOfRows": 10,
        "pageNo": 1,
        "_type": "json",
    }
    result = _request(url, params)
    if result is None:
        return []
    return result if isinstance(result, list) else [result]


def fetch_pest_monthly(lat: float, lon: float, year: str, month: str) -> list[dict]:
    """좌표 기반 월단위 병해충발생 상세조회"""
    url = f"{PEST_BASE_URL}/getCoordinateBasedMonthPestOccrrncInfo"
    params = {
        "serviceKey": PEST_API_KEY,
        "lat": lat,
        "lon": lon,
        "stdrYear": year,
        "stdrMonth": month,
        "numOfRows": 10,
        "pageNo": 1,
        "_type": "json",
    }
    result = _request(url, params)
    if result is None:
        return []
    return result if isinstance(result, list) else [result]


# ── 공통 요청 ─────────────────────────────────────────────────

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
