"""
병해충발생 서비스 레이어
"""

from core.api_client import fetch_pest_yearly, fetch_pest_monthly


class PestService:
    """병해충발생 데이터 수집 및 가공 서비스"""

    def get_pest_yearly(self, lat: float, lon: float, year: str) -> list[dict]:
        """
        좌표 기반 년단위 병해충발생 데이터 반환
        """
        raw_list = fetch_pest_yearly(lat, lon, year)
        return [_parse_pest(r) for r in raw_list]

    def get_pest_monthly(self, lat: float, lon: float, year: str, month: str) -> list[dict]:
        """
        좌표 기반 월단위 병해충발생 데이터 반환
        """
        raw_list = fetch_pest_monthly(lat, lon, year, month)
        return [_parse_pest(r) for r in raw_list]


def _parse_pest(raw: dict) -> dict:
    return {
        "pest_name": raw.get("pestNm"),          # 병해충명
        "crop_name": raw.get("cropNm"),          # 작물명
        "occrrnc_level": raw.get("occrrncLevel"), # 발생 수준
        "occrrnc_area": _f(raw.get("occrrncArea")), # 발생 면적
        "year": raw.get("stdrYear"),             # 기준 연도
        "month": raw.get("stdrMonth"),           # 기준 월
    }


def _f(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
