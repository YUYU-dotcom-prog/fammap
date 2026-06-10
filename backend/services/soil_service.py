"""
토양검정 서비스 레이어
"""

from core.api_client import fetch_soil


class SoilService:
    """토양검정 데이터 수집 및 가공 서비스"""

    def get_soil(self, lat: float, lon: float) -> dict | None:
        """
        단일 좌표 토양검정 데이터 반환

        주요 항목:
        - 토성 (모래/미사/점토 비율)
        - pH (산도)
        - 유기물 함량
        - 유효인산
        - 치환성 양이온 (칼륨/칼슘/마그네슘)
        - 전기전도도 (EC)
        """
        raw = fetch_soil(lat, lon)
        if raw is None:
            return None

        if isinstance(raw, list):
            raw = raw[0]

        return {
            "lat": lat,
            "lon": lon,
            "soil_type": raw.get("soilType"),          # 토성
            "ph": _f(raw.get("ph")),                   # 산도 (pH)
            "organic_matter": _f(raw.get("om")),       # 유기물 (g/kg)
            "available_p": _f(raw.get("avlP2O5")),     # 유효인산 (mg/kg)
            "potassium": _f(raw.get("exK")),            # 칼륨 (cmol+/kg)
            "calcium": _f(raw.get("exCa")),             # 칼슘 (cmol+/kg)
            "magnesium": _f(raw.get("exMg")),           # 마그네슘 (cmol+/kg)
            "ec": _f(raw.get("ec")),                    # 전기전도도 (dS/m)
        }


def _f(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
