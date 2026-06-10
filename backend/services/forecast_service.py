"""
🌤️ 기상청 단기예보 서비스
앞으로 3일간 날씨 예측
"""

import requests
from datetime import datetime, timedelta
from core.config import WEATHER_FORECAST_API_KEY

BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"


class ForecastService:

    def get_forecast(self, lat: float, lon: float) -> list[dict]:
        """
        좌표 기반 단기예보 조회 (3일치)
        """
        nx, ny = self._coord_to_grid(lat, lon)
        now = datetime.now()
        base_date = now.strftime("%Y%m%d")
        base_time = self._get_base_time(now)

        url = f"{BASE_URL}/getVilageFcst"
        params = {
            "serviceKey": WEATHER_FORECAST_API_KEY,
            "numOfRows": 300,
            "pageNo": 1,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            items = resp.json()["response"]["body"]["items"]["item"]
            return self._parse_forecast(items)
        except Exception as e:
            print(f"기상청 단기예보 오류: {e}")
            return []

    def _parse_forecast(self, items: list) -> list[dict]:
        """예보 데이터 파싱"""
        result = {}
        for item in items:
            key = f"{item['fcstDate']}_{item['fcstTime']}"
            if key not in result:
                result[key] = {
                    "date": item["fcstDate"],
                    "time": item["fcstTime"],
                }
            category = item["category"]
            value = item["fcstValue"]

            if category == "TMP":
                result[key]["temperature"] = float(value)
            elif category == "POP":
                result[key]["rain_prob"] = float(value)
            elif category == "PTY":
                result[key]["rain_type"] = self._rain_type(value)
            elif category == "WSD":
                result[key]["wind_speed"] = float(value)
            elif category == "REH":
                result[key]["humidity"] = float(value)

        return list(result.values())

    def _get_base_time(self, now: datetime) -> str:
        """가장 최근 발표 시각 반환"""
        times = ["0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300"]
        current = now.strftime("%H%M")
        base = "2300"
        for t in times:
            if current >= t:
                base = t
        return base

    def _rain_type(self, code: str) -> str:
        types = {"0": "없음", "1": "비", "2": "비/눈", "3": "눈", "4": "소나기"}
        return types.get(code, "없음")

    def _coord_to_grid(self, lat: float, lon: float) -> tuple:
        """위경도 → 기상청 격자 변환"""
        import math
        RE = 6371.00877
        GRID = 5.0
        SLAT1 = 30.0
        SLAT2 = 60.0
        OLON = 126.0
        OLAT = 38.0
        XO = 43
        YO = 136

        DEGRAD = math.pi / 180.0
        re = RE / GRID
        slat1 = SLAT1 * DEGRAD
        slat2 = SLAT2 * DEGRAD
        olon = OLON * DEGRAD
        olat = OLAT * DEGRAD

        sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
        sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
        sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
        sf = math.pow(sf, sn) * math.cos(slat1) / sn
        ro = math.tan(math.pi * 0.25 + olat * 0.5)
        ro = re * sf / math.pow(ro, sn)

        ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
        ra = re * sf / math.pow(ra, sn)
        theta = lon * DEGRAD - olon
        if theta > math.pi:
            theta -= 2.0 * math.pi
        if theta < -math.pi:
            theta += 2.0 * math.pi
        theta *= sn

        nx = int(ra * math.sin(theta) + XO + 0.5)
        ny = int(ro - ra * math.cos(theta) + YO + 0.5)
        return nx, ny