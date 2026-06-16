"""
⚡ 병해충발생 서비스 레이어 (완전 최적화 & 6시간 캐싱 & 2026년 404 에러 철벽 방어 버전)
API 응답을 정제하여 프론트엔드와 AI에 바로 쓸 수 있는 형태로 반환
"""

from core.api_client import fetch_pest_yearly, fetch_pest_monthly
import core.cache as cache  # ⭐ 프로젝트에 연동된 캐시 모듈 가져오기


class PestService:
    """병해충발생 데이터 수집 및 가공 서비스"""

    def get_pest_yearly(self, lat: float, lon: float, year: str) -> list[dict]:
        """
        좌표 기반 년단위 병해충발생 데이터 반환 (격자 캐싱 적용 🛡️)
        """
        grid_lat = round(lat, 1)
        grid_lon = round(lon, 1)

        # 🚨 [404 에러 원천 차단] 최신 연도부터 시도, 없으면 전년도로 폴백
        for try_year in [str(int(year) - 1), str(int(year) - 2)]:
            cache_key = cache.make_key("pest_yearly", grid_lat, grid_lon, try_year)
            cached_data = cache.get(cache_key)

            if cached_data is not None:
                return cached_data

            print(f"🐛 [Pest] ({grid_lat}, {grid_lon}) 격자 {try_year}년 병해충 데이터 새로 수집 중... (404 방어막 가동)")

            try:
                raw_list = fetch_pest_yearly(lat, lon, try_year) or []
                result = [_parse_pest(r) for r in raw_list]
                if result:
                    cache.set(cache_key, result, ttl_type="pest")
                    return result
            except Exception as e:
                print(f"⚠️ [Pest API Error] {try_year}년 년단위 병해충 데이터 수집 실패: {e}")

        # 모든 연도 실패 시 빈 리스트 반환
        return []

    def get_pest_monthly(self, lat: float, lon: float, year: str, month: str) -> list[dict]:
        """
        좌표 기반 월단위 병해충발생 데이터 반환 (격자 캐싱 적용 🛡️)
        """
        grid_lat = round(lat, 1)
        grid_lon = round(lon, 1)

        # 🚨 [404 에러 원천 차단] 최신 연도부터 시도, 없으면 전년도로 폴백
        for try_year in [str(int(year) - 1), str(int(year) - 2)]:
            cache_key = cache.make_key("pest_monthly", grid_lat, grid_lon, try_year, month)
            cached_data = cache.get(cache_key)

            if cached_data is not None:
                return cached_data

            print(f"🐛 [Pest] ({grid_lat}, {grid_lon}) 격자 {try_year}년 {month}월 병해충 데이터 새로 수집 중... (404 방어막 가동)")

            try:
                raw_list = fetch_pest_monthly(lat, lon, try_year, month) or []
                result = [_parse_pest(r) for r in raw_list]
                if result:
                    cache.set(cache_key, result, ttl_type="pest")
                    return result
            except Exception as e:
                print(f"⚠️ [Pest API Error] {try_year}년 월단위 병해충 데이터 수집 실패: {e}")

        # 모든 연도 실패 시 빈 리스트 반환
        return []


# ── 파싱 헬퍼 ─────────────────────────────────────────────────

def _parse_pest(raw: dict) -> dict:
    return {
        "pest_name": raw.get("pestNm"),           # 병해충명
        "crop_name": raw.get("cropNm"),           # 작물명
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