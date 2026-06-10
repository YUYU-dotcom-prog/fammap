"""
농업기상 서비스 레이어
API 응답을 정제하여 프론트엔드에 바로 쓸 수 있는 JSON 형태로 반환
"""

import time
from core.api_client import fetch_daily, fetch_hourly
from core.config import REQUEST_DELAY


class WeatherService:
    """농업기상 데이터 수집 및 가공 서비스"""

    # 대한민국 주요 농업지역 25개 대표 지점
    stations: list[dict] = [
        # 수도권
        {"id": "seoul",    "name": "서울",   "sido": "서울",  "lat": 37.5665, "lon": 126.9780},
        {"id": "incheon",  "name": "인천",   "sido": "인천",  "lat": 37.4563, "lon": 126.7052},
        {"id": "suwon",    "name": "수원",   "sido": "경기",  "lat": 37.2636, "lon": 127.0286},
        {"id": "yangpyeong","name": "양평",  "sido": "경기",  "lat": 37.4914, "lon": 127.4875},
        # 강원
        {"id": "chuncheon","name": "춘천",   "sido": "강원",  "lat": 37.8813, "lon": 127.7298},
        {"id": "wonju",    "name": "원주",   "sido": "강원",  "lat": 37.3422, "lon": 127.9201},
        {"id": "gangneung","name": "강릉",   "sido": "강원",  "lat": 37.7519, "lon": 128.8761},
        # 충청
        {"id": "cheonan",  "name": "천안",   "sido": "충남",  "lat": 36.8151, "lon": 127.1139},
        {"id": "cheongju", "name": "청주",   "sido": "충북",  "lat": 36.6424, "lon": 127.4890},
        {"id": "hongseong","name": "홍성",   "sido": "충남",  "lat": 36.6010, "lon": 126.6608},
        {"id": "nonsan",   "name": "논산",   "sido": "충남",  "lat": 36.1868, "lon": 127.0988},
        # 전라
        {"id": "jeonju",   "name": "전주",   "sido": "전북",  "lat": 35.8242, "lon": 127.1480},
        {"id": "gunsan",   "name": "군산",   "sido": "전북",  "lat": 35.9677, "lon": 126.7368},
        {"id": "gimje",    "name": "김제",   "sido": "전북",  "lat": 35.8033, "lon": 126.8803},
        {"id": "naju",     "name": "나주",   "sido": "전남",  "lat": 35.0160, "lon": 126.7108},
        {"id": "haenam",   "name": "해남",   "sido": "전남",  "lat": 34.5739, "lon": 126.5990},
        {"id": "suncheon", "name": "순천",   "sido": "전남",  "lat": 34.9506, "lon": 127.4874},
        # 경상
        {"id": "daegu",    "name": "대구",   "sido": "경북",  "lat": 35.8714, "lon": 128.6014},
        {"id": "andong",   "name": "안동",   "sido": "경북",  "lat": 36.5684, "lon": 128.7294},
        {"id": "sangju",   "name": "상주",   "sido": "경북",  "lat": 36.4108, "lon": 128.1591},
        {"id": "miryang",  "name": "밀양",   "sido": "경남",  "lat": 35.5037, "lon": 128.7461},
        {"id": "jinju",    "name": "진주",   "sido": "경남",  "lat": 35.1799, "lon": 128.1076},
        {"id": "changwon", "name": "창원",   "sido": "경남",  "lat": 35.2279, "lon": 128.6811},
        # 제주
        {"id": "jeju",     "name": "제주",   "sido": "제주",  "lat": 33.4996, "lon": 126.5312},
        {"id": "seogwipo", "name": "서귀포", "sido": "제주",  "lat": 33.2541, "lon": 126.5600},
    ]

    def get_korea_weather(self, date: str) -> list[dict]:
        """
        전국 25개 지점 일별 기상 데이터 수집
        → 지도 마커 렌더링용 JSON 리스트 반환
        """
        results = []
        for st in self.stations:
            raw = fetch_daily(st["lat"], st["lon"], date)
            if raw:
                results.append({
                    **st,
                    **_parse_daily(raw),
                })
            time.sleep(REQUEST_DELAY)
        return results

    def get_point_weather(self, lat: float, lon: float, date: str) -> dict | None:
        """단일 좌표 일별 기상 데이터"""
        raw = fetch_daily(lat, lon, date)
        if raw is None:
            return None
        return {
            "lat": lat,
            "lon": lon,
            **_parse_daily(raw),
        }

    def get_hourly_weather(self, lat: float, lon: float, date: str) -> list[dict]:
        """단일 좌표 시간별 기상 데이터 (24시간)"""
        raw_list = fetch_hourly(lat, lon, date)
        return [_parse_hourly(r) for r in raw_list]


# ── 파싱 헬퍼 ─────────────────────────────────────────────────

def _parse_daily(raw: dict) -> dict:
    return {
        "temperature": _f(raw.get("tmpr")),       # 기온 (°C)
        "precipitation": _f(raw.get("rn")),        # 강수량 (mm)
        "humidity": _f(raw.get("hm")),             # 상대습도 (%)
        "wind_speed": _f(raw.get("ws")),           # 풍속 (m/s)
        "solar_radiation": _f(raw.get("sr")),      # 일사량
        "date": raw.get("stdrDe"),
    }


def _parse_hourly(raw: dict) -> dict:
    return {
        "hour": raw.get("stdrHour"),               # 시각
        "temperature": _f(raw.get("tmpr")),
        "precipitation": _f(raw.get("rn")),
        "humidity": _f(raw.get("hm")),
        "wind_speed": _f(raw.get("ws")),
        "solar_radiation": _f(raw.get("sr")),
    }


def _f(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
