"""
⚡ 토양검정 서비스 레이어 (완전 최적화 & 24시간 캐싱 버전)
API 응답을 정제하여 프론트엔드와 AI에 바로 쓸 수 있는 형태로 반환
"""

from core.api_client import fetch_soil
import core.cache as cache  # ⭐ 프로젝트에 연동된 캐시 모듈 가져오기


class SoilService:
    """토양검정 데이터 수집 및 가공 서비스"""

    def get_soil(self, lat: float, lon: float) -> dict | None:
        """
        단일 좌표 토양검정 데이터 반환 (대한민국 전체 격자 캐싱 적용 🛡️)
        """
        # 11km 격자 단위 반올림으로 대한민국 전체 구역을 묶어 캐시 효율 극대화
        grid_lat = round(lat, 1)
        grid_lon = round(lon, 1)
        
        # 🛡️ 1. 캐시 키 생성 및 확인
        cache_key = cache.make_key("soil_grid", grid_lat, grid_lon)
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data

        # 2. 캐시에 없으면 딱 한 번만 외부 API 호출
        print(f"🌱 [Soil DB] ({grid_lat}, {grid_lon}) 격자 토양 데이터 새로 수집 중...")

        try:
            raw = fetch_soil(lat, lon)
        except Exception as e:
            print(f"⚠️ [Soil API Error] 토양 데이터 수집 실패: {e}")
            return None

        # 3. 빈 응답 체크
        if not raw:
            print(f"⚠️ [Soil API Error] 빈 응답 수신 ({grid_lat}, {grid_lon})")
            return None

        if isinstance(raw, list):
            raw = raw[0]

        # 4. 데이터 정제 (기존 포맷 100% 유지)
        result = {
            "lat": lat,
            "lon": lon,
            "soil_type": raw.get("soilType"),           # 토성
            "ph": _f(raw.get("ph")),                    # 산도 (pH)
            "organic_matter": _f(raw.get("om")),        # 유기물 (g/kg)
            "available_p": _f(raw.get("avlP2O5")),      # 유효인산 (mg/kg)
            "potassium": _f(raw.get("exK")),            # 칼륨 (cmol+/kg)
            "calcium": _f(raw.get("exCa")),             # 칼슘 (cmol+/kg)
            "magnesium": _f(raw.get("exMg")),           # 마그네슘 (cmol+/kg)
            "ec": _f(raw.get("ec")),                    # 전기전도도 (dS/m)
        }
        
        # 🛡️ 5. 토양은 변동성이 극도로 낮으므로 작성하신 'soil' TTL (24시간) 동안 캐싱 봉인
        cache.set(cache_key, result, ttl_type="soil")
        return result


# ── 파싱 헬퍼 ─────────────────────────────────────────────────

def _f(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None