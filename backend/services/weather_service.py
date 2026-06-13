"""
⚡ 농업기상 서비스 레이어 (배치 수집 호환 및 격자 최적화 버전)
"""

import time
from core.api_client import fetch_daily, fetch_hourly
from core.config import REQUEST_DELAY
import core.cache as cache


class WeatherService:
    """농업기상 데이터 수집 및 가공 서비스"""

    # 수집 스크립트가 참조할 대한민국 주요 농업지역 25개 대표 지점
    stations: list[dict] = [
        {"id": "seoul",    "name": "서울",   "sido": "서울",  "lat": 37.5665, "lon": 126.9780},
        {"id": "incheon",  "name": "인천",   "sido": "인천",  "lat": 37.4563, "lon": 126.7052},
        {"id": "suwon",    "name": "수원",   "sido": "경기",  "lat": 37.2636, "lon": 127.0286},
        {"id": "yangpyeong","name": "양평",  "sido": "경기",  "lat": 37.4914, "lon": 127.4875},
        {"id": "chuncheon","name": "춘천",   "sido": "강원",  "lat": 37.8813, "lon": 127.7298},
        {"id": "wonju",    "name": "원주",   "sido": "강원",  "lat": 37.3422, "lon": 127.9201},
        {"id": "gangneung","name": "강릉",   "sido": "강원",  "lat": 37.7519, "lon": 128.8761},
        {"id": "cheonan",  "name": "천안",   "sido": "충남",  "lat": 36.8151, "lon": 127.1139},
        {"id": "cheongju", "name": "청주",   "sido": "충북",  "lat": 36.6424, "lon": 127.4890},
        {"id": "hongseong","name": "홍성",   "sido": "충남",  "lat": 36.6010, "lon": 126.6608},
        {"id": "nonsan",   "name": "논산",   "sido": "충남",  "lat": 36.1868, "lon": 127.0988},
        {"id": "jeonju",   "name": "전주",   "sido": "전북",  "lat": 35.8242, "lon": 127.1480},
        {"id": "gunsan",   "name": "군산",   "sido": "전북",  "lat": 35.9677, "lon": 126.7368},
        {"id": "gimje",    "name": "김제",   "sido": "전북",  "lat": 35.8033, "lon": 126.8803},
        {"id": "naju",     "name": "나주",   "sido": "전남",  "lat": 35.0160, "lon": 126.7108},
        {"id": "haenam",   "name": "해남",   "sido": "전남",  "lat": 34.5739, "lon": 126.5990},
        {"id": "suncheon", "name": "순천",   "sido": "전남",  "lat": 34.9506, "lon": 127.4874},
        {"id": "daegu",    "name": "대구",   "sido": "경북",  "lat": 35.8714, "lon": 128.6014},
        {"id": "andong",   "name": "안동",   "sido": "경북",  "lat": 36.5684, "lon": 128.7294},
        {"id": "sangju",   "name": "상주",   "sido": "경북",  "lat": 36.4108, "lon": 128.1591},
        {"id": "miryang",  "name": "밀양",   "sido": "경남",  "lat": 35.5037, "lon": 128.7461},
        {"id": "jinju",    "name": "진주",   "sido": "경남",  "lat": 35.1799, "lon": 128.1076},
        {"id": "changwon", "name": "창원",   "sido": "경남",  "lat": 35.2279, "lon": 128.6811},
        {"id": "jeju",     "name": "제주",   "sido": "제주",  "lat": 33.4996, "lon": 126.5312},
        {"id": "seogwipo", "name": "서귀포", "sido": "제주",  "lat": 33.2541, "lon": 126.5600},
    ]

    def get_korea_weather(self, date: str) -> list[dict]:
        """전국 25개 지점 날씨 패키지 반환 (메모리 캐싱 적용 🛡️)"""
        cache_key = cache.make_key("weather_korea_all", date)
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        results = []
        for st in self.stations:
            raw = fetch_daily(st["lat"], st["lon"], date)
            if raw:
                results.append({**st, **_parse_daily(raw)})
            time.sleep(REQUEST_DELAY)
            
        cache.set(cache_key, results, ttl_type="weather")
        return results

    def get_point_weather(self, lat: float, lon: float, date: str) -> dict | None:
        """단일 좌표 일별 기상 데이터 (격자 캐싱 및 실시간 조회 폴백 🛡️)"""
        grid_lat = round(lat, 1)
        grid_lon = round(lon, 1)
        
        cache_key = cache.make_key("weather_grid", grid_lat, grid_lon, date)
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        raw = fetch_daily(lat, lon, date)
        if raw is None:
            return None
            
        result = {
            "lat": lat,
            "lon": lon,
            **_parse_daily(raw),
        }
        cache.set(cache_key, result, ttl_type="weather")
        return result

    def get_hourly_weather(self, lat: float, lon: float, date: str) -> list[dict]:
        """단일 좌표 시간별 기상 데이터 (격자 캐싱)"""
        grid_lat = round(lat, 1)
        grid_lon = round(lon, 1)
        
        cache_key = cache.make_key("weather_hourly_grid", grid_lat, grid_lon, date)
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        raw_list = fetch_hourly(lat, lon, date)
        result = [_parse_hourly(r) for r in raw_list]
        cache.set(cache_key, result, ttl_type="weather")
        return result


# ── 파싱 헬퍼 ─────────────────────────────────────────────────

def _parse_daily(raw: dict) -> dict:
    return {
        "temperature": _f(raw.get("tmpr")),
        "precipitation": _f(raw.get("rn")),
        "humidity": _f(raw.get("hm")),
        "wind_speed": _f(raw.get("ws")),
        "date": raw.get("stdrDe"),
    }

def _parse_hourly(raw: dict) -> dict:
    return {
        "hour": raw.get("stdrHour"),
        "temperature": _f(raw.get("tmpr")),
        "precipitation": _f(raw.get("rn")),
        "humidity": _f(raw.get("hm")),
    }

def _f(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None