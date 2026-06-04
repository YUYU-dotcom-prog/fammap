"""
🌾 대한민국 농업기상 GIS - FastAPI 백엔드
농림수산식품교육문화정보원 팜맵기반 농업기상 조회 서비스
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

from services.weather_service import WeatherService

app = FastAPI(
    title="농업기상 GIS API",
    description="팜맵기반 농업기상 조회 서비스 - 대한민국 주요 농업지역 기상 데이터",
    version="1.0.0",
)

# ── CORS 설정 (프론트엔드 어디서든 호출 가능) ─────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 운영 시 프론트 도메인으로 제한 권장
    allow_methods=["GET"],
    allow_headers=["*"],
)

weather_service = WeatherService()


# ── 헬스체크 ─────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "농업기상 GIS API 서버가 실행 중입니다."}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ── 전국 기상 데이터 (지도용) ─────────────────────────────────
@app.get("/api/weather/korea", tags=["Weather"])
def get_korea_weather(
    date: str = Query(
        default=None,
        description="기준일자 YYYYMMDD (미입력 시 어제)",
        example="20240601",
    )
):
    """
    대한민국 주요 농업지역 25개 지점의 일별 기상 데이터 반환.
    GIS 지도 마커 렌더링용.
    """
    date = _resolve_date(date)
    try:
        data = weather_service.get_korea_weather(date)
        return {
            "status": "success",
            "date": date,
            "count": len(data),
            "data": data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 단일 좌표 조회 ────────────────────────────────────────────
@app.get("/api/weather/point", tags=["Weather"])
def get_point_weather(
    lat: float = Query(..., description="위도", example=35.9677),
    lon: float = Query(..., description="경도", example=126.7368),
    date: str = Query(default=None, description="기준일자 YYYYMMDD"),
):
    """
    특정 좌표의 일별 기상 데이터 반환.
    지도 클릭 이벤트 등에 활용.
    """
    date = _resolve_date(date)
    try:
        data = weather_service.get_point_weather(lat, lon, date)
        if data is None:
            raise HTTPException(status_code=404, detail="해당 좌표의 데이터가 없습니다.")
        return {"status": "success", "date": date, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 시간별 조회 ───────────────────────────────────────────────
@app.get("/api/weather/hourly", tags=["Weather"])
def get_hourly_weather(
    lat: float = Query(..., description="위도", example=35.9677),
    lon: float = Query(..., description="경도", example=126.7368),
    date: str = Query(default=None, description="기준일자 YYYYMMDD"),
):
    """
    특정 좌표의 시간별 기상 데이터 반환 (24시간).
    차트/그래프 렌더링용.
    """
    date = _resolve_date(date)
    try:
        data = weather_service.get_hourly_weather(lat, lon, date)
        return {
            "status": "success",
            "date": date,
            "lat": lat,
            "lon": lon,
            "count": len(data),
            "data": data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 지점 목록 ─────────────────────────────────────────────────
@app.get("/api/stations", tags=["Stations"])
def get_stations():
    """
    조회 대상 농업 지점 목록 (이름, 시도, 위경도) 반환.
    지도 초기 마커 렌더링용.
    """
    return {
        "status": "success",
        "count": len(weather_service.stations),
        "data": weather_service.stations,
    }


# ── 유틸 ─────────────────────────────────────────────────────
def _resolve_date(date: str | None) -> str:
    if date:
        if len(date) != 8 or not date.isdigit():
            raise HTTPException(
                status_code=400,
                detail="날짜 형식 오류: YYYYMMDD (예: 20240601)",
            )
        return date
    # 당일 데이터는 미확보 케이스가 많으므로 어제 기본값
    return (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")
