"""
🌾 귀농인을 위한 AI 작물 추천 시스템 - FastAPI 백엔드
팜맵기반 농업기상 / 토양검정 / 병해충발생 조회 서비스
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

from services.weather_service import WeatherService
from services.soil_service import SoilService
from services.pest_service import PestService

app = FastAPI(
    title="귀농 AI 작물 추천 시스템 API",
    description="팜맵기반 농업기상 / 토양검정 / 병해충발생 데이터 제공",
    version="2.0.0",
)

# ── CORS 설정 (프론트엔드 어디서든 호출 가능) ─────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

weather_service = WeatherService()
soil_service    = SoilService()
pest_service    = PestService()


# ── 헬스체크 ─────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "귀농 AI 작물 추천 시스템 API 서버가 실행 중입니다."}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ════════════════════════════════════════════
# 🌤️  농업기상 API
# ════════════════════════════════════════════

@app.get("/api/weather/korea", tags=["농업기상"])
def get_korea_weather(
    date: str = Query(default=None, description="기준일자 YYYYMMDD (미입력 시 어제)", example="20240601")
):
    """대한민국 주요 농업지역 25개 지점 일별 기상 데이터 (지도 마커용)"""
    date = _resolve_date(date)
    try:
        data = weather_service.get_korea_weather(date)
        return {"status": "success", "date": date, "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/weather/point", tags=["농업기상"])
def get_point_weather(
    lat: float = Query(..., description="위도", example=35.9677),
    lon: float = Query(..., description="경도", example=126.7368),
    date: str = Query(default=None, description="기준일자 YYYYMMDD"),
):
    """특정 좌표 일별 기상 데이터"""
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


@app.get("/api/weather/hourly", tags=["농업기상"])
def get_hourly_weather(
    lat: float = Query(..., description="위도", example=35.9677),
    lon: float = Query(..., description="경도", example=126.7368),
    date: str = Query(default=None, description="기준일자 YYYYMMDD"),
):
    """특정 좌표 시간별 기상 데이터 (24시간, 차트용)"""
    date = _resolve_date(date)
    try:
        data = weather_service.get_hourly_weather(lat, lon, date)
        return {"status": "success", "date": date, "lat": lat, "lon": lon, "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════
# 🌱  토양검정 API
# ════════════════════════════════════════════

@app.get("/api/soil/point", tags=["토양검정"])
def get_soil(
    lat: float = Query(..., description="위도", example=35.9677),
    lon: float = Query(..., description="경도", example=126.7368),
):
    """
    특정 좌표 토양검정 데이터 반환.
    pH, 유기물, 유효인산, 칼륨/칼슘/마그네슘 등 포함.
    작물 추천 AI 분석에 활용.
    """
    try:
        data = soil_service.get_soil(lat, lon)
        if data is None:
            raise HTTPException(status_code=404, detail="해당 좌표의 토양 데이터가 없습니다.")
        return {"status": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════
# 🐛  병해충발생 API
# ════════════════════════════════════════════

@app.get("/api/pest/yearly", tags=["병해충발생"])
def get_pest_yearly(
    lat: float = Query(..., description="위도", example=35.9677),
    lon: float = Query(..., description="경도", example=126.7368),
    year: str = Query(default=None, description="기준연도 YYYY (미입력 시 올해)", example="2024"),
):
    """특정 좌표 년단위 병해충발생 데이터"""
    year = year or str(datetime.today().year)
    try:
        data = pest_service.get_pest_yearly(lat, lon, year)
        return {"status": "success", "year": year, "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pest/monthly", tags=["병해충발생"])
def get_pest_monthly(
    lat: float = Query(..., description="위도", example=35.9677),
    lon: float = Query(..., description="경도", example=126.7368),
    year: str = Query(default=None, description="기준연도 YYYY", example="2024"),
    month: str = Query(default=None, description="기준월 MM", example="06"),
):
    """특정 좌표 월단위 병해충발생 데이터"""
    year  = year  or str(datetime.today().year)
    month = month or f"{datetime.today().month:02d}"
    try:
        data = pest_service.get_pest_monthly(lat, lon, year, month)
        return {"status": "success", "year": year, "month": month, "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════
# 📍  지점 목록
# ════════════════════════════════════════════

@app.get("/api/stations", tags=["지점목록"])
def get_stations():
    """전국 25개 농업 지점 목록 (지도 초기 렌더링용)"""
    return {
        "status": "success",
        "count": len(weather_service.stations),
        "data": weather_service.stations,
    }


# ── 유틸 ─────────────────────────────────────────────────────
def _resolve_date(date: str | None) -> str:
    if date:
        if len(date) != 8 or not date.isdigit():
            raise HTTPException(status_code=400, detail="날짜 형식 오류: YYYYMMDD (예: 20240601)")
        return date
    return (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")


# ════════════════════════════════════════════
# 🤖  AI 작물 추천 API
# ════════════════════════════════════════════

from services.ai_service import AIService
from services.weather_service import WeatherService as _WS
from services.soil_service import SoilService as _SS
from services.pest_service import PestService as _PS

ai_service = AIService()


@app.get("/api/ai/recommend", tags=["AI 작물추천"])
def recommend_crops(
    lat: float = Query(..., description="위도", example=35.9677),
    lon: float = Query(..., description="경도", example=126.7368),
    location: str = Query(..., description="지역명", example="전북 군산"),
    date: str = Query(default=None, description="기준일자 YYYYMMDD"),
):
    """
    🌾 귀농인 맞춤 작물 추천
    기상 + 토양 + 병해충 데이터를 AI가 분석해서 작물을 추천합니다.
    """
    date = _resolve_date(date)
    year = date[:4]

    # 데이터 수집
    weather = weather_service.get_point_weather(lat, lon, date)
    soil    = soil_service.get_soil(lat, lon)
    pest    = pest_service.get_pest_yearly(lat, lon, year)

    # AI 분석
    result = ai_service.recommend_crops(location, weather, soil, pest)
    return result


@app.get("/api/ai/question", tags=["AI 작물추천"])
def ask_question(
    question: str = Query(..., description="귀농 관련 질문", example="고구마 키우는 방법 알려줘"),
    location: str = Query(default=None, description="지역명 (선택)", example="전북 군산"),
):
    """
    🤖 귀농 관련 자유 질문
    작물 재배법, 귀농 준비 등 무엇이든 물어보세요!
    """
    context = {"location": location} if location else None
    result = ai_service.ask_farming_question(question, context)
    return result
