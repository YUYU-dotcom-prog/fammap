"""
🌾 귀농인을 위한 AI 작물 추천 시스템 - FastAPI 백엔드
팜맵기반 농업기상 / 토양검정 / 병해충발생 / Gemini AI / Firebase
"""

import time
from fastapi import FastAPI, HTTPException, Query, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

from core.logger import logger
from core import cache
from core.validators import validate_lat_lon, validate_date, validate_year, validate_location_name
from services.weather_service import WeatherService
from services.soil_service import SoilService
from services.pest_service import PestService
from services.ai_service import AIService
from services.auth_service import AuthService
from services.user_service import UserService

app = FastAPI(
    title="귀농 AI 작물 추천 시스템 API",
    description="팜맵기반 농업기상 / 토양검정 / 병해충발생 데이터 + Gemini AI 작물 추천",
    version="3.0.0",
)

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 서비스 인스턴스 ───────────────────────────────────────────
weather_service = WeatherService()
soil_service    = SoilService()
pest_service    = PestService()
ai_service      = AIService()
auth_service    = AuthService()
user_service    = UserService()


# ── 요청/응답 로깅 미들웨어 ───────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = round((time.time() - start) * 1000)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({elapsed}ms)")
    return response


# ── 전역 에러 핸들러 ──────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"예상치 못한 오류: {exc} | {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}
    )


# ── 유틸 ─────────────────────────────────────────────────────
def _resolve_date(date: str | None) -> str:
    if date:
        validate_date(date)
        return date
    return (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")


def _get_uid(authorization: str = Header(...)) -> str:
    token = authorization.replace("Bearer ", "")
    user = auth_service.verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    return user["uid"]


# ════════════════════════════════════════════
# ❤️  헬스체크
# ════════════════════════════════════════════

@app.get("/", tags=["Health"])
def root():
    logger.info("헬스체크 요청")
    return {"status": "ok", "message": "귀농 AI 작물 추천 시스템 API 서버가 실행 중입니다."}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ════════════════════════════════════════════
# 🌤️  농업기상 API
# ════════════════════════════════════════════

@app.get("/api/weather/korea", tags=["농업기상"])
def get_korea_weather(
    date: str = Query(default=None, description="기준일자 YYYYMMDD")
):
    """대한민국 주요 농업지역 25개 지점 일별 기상 데이터"""
    date = _resolve_date(date)
    cache_key = cache.make_key("weather_korea", date)
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"캐시 히트: weather_korea {date}")
        return cached

    logger.info(f"농업기상 전국 조회: {date}")
    data = weather_service.get_korea_weather(date)
    result = {"status": "success", "date": date, "count": len(data), "data": data}
    cache.set(cache_key, result, "weather")
    return result


@app.get("/api/weather/point", tags=["농업기상"])
def get_point_weather(
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"),
    date: str = Query(default=None, description="기준일자 YYYYMMDD"),
):
    """특정 좌표 일별 기상 데이터"""
    validate_lat_lon(lat, lon)
    date = _resolve_date(date)
    cache_key = cache.make_key("weather_point", lat, lon, date)
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"캐시 히트: weather_point {lat},{lon} {date}")
        return cached

    logger.info(f"농업기상 단일 좌표 조회: {lat},{lon} {date}")
    data = weather_service.get_point_weather(lat, lon, date)
    if data is None:
        raise HTTPException(status_code=404, detail="해당 좌표의 데이터가 없습니다.")
    result = {"status": "success", "date": date, "data": data}
    cache.set(cache_key, result, "weather")
    return result


@app.get("/api/weather/hourly", tags=["농업기상"])
def get_hourly_weather(
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"),
    date: str = Query(default=None, description="기준일자 YYYYMMDD"),
):
    """특정 좌표 시간별 기상 데이터 (24시간)"""
    validate_lat_lon(lat, lon)
    date = _resolve_date(date)
    cache_key = cache.make_key("weather_hourly", lat, lon, date)
    cached = cache.get(cache_key)
    if cached:
        return cached

    logger.info(f"농업기상 시간별 조회: {lat},{lon} {date}")
    data = weather_service.get_hourly_weather(lat, lon, date)
    result = {"status": "success", "date": date, "lat": lat, "lon": lon, "count": len(data), "data": data}
    cache.set(cache_key, result, "weather")
    return result


# ════════════════════════════════════════════
# 🌱  토양검정 API
# ════════════════════════════════════════════

@app.get("/api/soil/point", tags=["토양검정"])
def get_soil(
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"),
):
    """특정 좌표 토양검정 데이터"""
    validate_lat_lon(lat, lon)
    cache_key = cache.make_key("soil", lat, lon)
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"캐시 히트: soil {lat},{lon}")
        return cached

    logger.info(f"토양검정 조회: {lat},{lon}")
    data = soil_service.get_soil(lat, lon)
    if data is None:
        raise HTTPException(status_code=404, detail="해당 좌표의 토양 데이터가 없습니다.")
    result = {"status": "success", "data": data}
    cache.set(cache_key, result, "soil")
    return result


# ════════════════════════════════════════════
# 🐛  병해충발생 API
# ════════════════════════════════════════════

@app.get("/api/pest/yearly", tags=["병해충발생"])
def get_pest_yearly(
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"),
    year: str = Query(default=None, description="기준연도 YYYY"),
):
    """특정 좌표 년단위 병해충발생 데이터"""
    validate_lat_lon(lat, lon)
    year = year or str(datetime.today().year)
    validate_year(year)
    cache_key = cache.make_key("pest_yearly", lat, lon, year)
    cached = cache.get(cache_key)
    if cached:
        return cached

    logger.info(f"병해충 연간 조회: {lat},{lon} {year}")
    data = pest_service.get_pest_yearly(lat, lon, year)
    result = {"status": "success", "year": year, "count": len(data), "data": data}
    cache.set(cache_key, result, "pest")
    return result


@app.get("/api/pest/monthly", tags=["병해충발생"])
def get_pest_monthly(
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"),
    year: str = Query(default=None, description="기준연도 YYYY"),
    month: str = Query(default=None, description="기준월 MM"),
):
    """특정 좌표 월단위 병해충발생 데이터"""
    validate_lat_lon(lat, lon)
    year  = year  or str(datetime.today().year)
    month = month or f"{datetime.today().month:02d}"
    validate_year(year)
    cache_key = cache.make_key("pest_monthly", lat, lon, year, month)
    cached = cache.get(cache_key)
    if cached:
        return cached

    logger.info(f"병해충 월간 조회: {lat},{lon} {year}-{month}")
    data = pest_service.get_pest_monthly(lat, lon, year, month)
    result = {"status": "success", "year": year, "month": month, "count": len(data), "data": data}
    cache.set(cache_key, result, "pest")
    return result


# ════════════════════════════════════════════
# 🤖  AI 작물추천 API
# ════════════════════════════════════════════

@app.get("/api/ai/recommend", tags=["AI 작물추천"])
def recommend_crops(
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"),
    location: str = Query(..., description="지역명"),
    date: str = Query(default=None, description="기준일자 YYYYMMDD"),
):
    """🌾 귀농인 맞춤 작물 추천 (기상+토양+병해충 데이터 AI 분석)"""
    validate_lat_lon(lat, lon)
    validate_location_name(location)
    date = _resolve_date(date)
    year = date[:4]

    logger.info(f"AI 작물 추천 요청: {location} ({lat},{lon})")
    weather = weather_service.get_point_weather(lat, lon, date)
    soil    = soil_service.get_soil(lat, lon)
    pest    = pest_service.get_pest_yearly(lat, lon, year)
    result  = ai_service.recommend_crops(location, weather, soil, pest)
    return result


@app.get("/api/ai/question", tags=["AI 작물추천"])
def ask_question(
    question: str = Query(..., description="귀농 관련 질문"),
    location: str = Query(default=None, description="지역명 (선택)"),
):
    """🤖 귀농 관련 자유 질문"""
    if len(question.strip()) < 2:
        raise HTTPException(status_code=400, detail="질문은 2글자 이상 입력하세요.")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="질문은 500글자 이하로 입력하세요.")

    logger.info(f"AI 질문: {question[:50]}")
    context = {"location": location} if location else None
    return ai_service.ask_farming_question(question, context)


# ════════════════════════════════════════════
# 🔐  인증 API
# ════════════════════════════════════════════

@app.post("/api/auth/login", tags=["인증"])
def login(authorization: str = Header(...)):
    """Firebase 토큰으로 로그인 (구글 로그인 포함)"""
    token = authorization.replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=400, detail="토큰이 없습니다.")

    user_info = auth_service.verify_token(token)
    if not user_info:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    logger.info(f"로그인: {user_info.get('email')}")
    user = auth_service.get_or_create_user(
        uid=user_info["uid"],
        email=user_info.get("email", ""),
        name=user_info.get("name"),
        picture=user_info.get("picture"),
    )
    return {"status": "success", "user": user}


@app.get("/api/auth/me", tags=["인증"])
def get_me(authorization: str = Header(...)):
    """내 프로필 조회"""
    uid = _get_uid(authorization)
    user = auth_service.get_user(uid)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return {"status": "success", "user": user}


# ════════════════════════════════════════════
# 📋  추천 기록 API
# ════════════════════════════════════════════

@app.get("/api/user/recommendations", tags=["사용자 데이터"])
def get_recommendations(authorization: str = Header(...)):
    """내 작물 추천 기록 목록"""
    uid = _get_uid(authorization)
    logger.info(f"추천 기록 조회: {uid}")
    data = user_service.get_recommendations(uid)
    return {"status": "success", "count": len(data), "data": data}


@app.post("/api/user/recommendations", tags=["사용자 데이터"])
def save_recommendation(
    location: str = Query(..., description="지역명"),
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"),
    result: str = Query(..., description="AI 추천 결과"),
    authorization: str = Header(...),
):
    """작물 추천 기록 저장"""
    validate_lat_lon(lat, lon)
    validate_location_name(location)
    uid = _get_uid(authorization)
    data = user_service.save_recommendation(uid, location, lat, lon, result)
    return {"status": "success", "data": data}


@app.delete("/api/user/recommendations/{record_id}", tags=["사용자 데이터"])
def delete_recommendation(record_id: str, authorization: str = Header(...)):
    """추천 기록 삭제"""
    uid = _get_uid(authorization)
    ok = user_service.delete_recommendation(uid, record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    return {"status": "success"}


# ════════════════════════════════════════════
# ⭐  즐겨찾기 API
# ════════════════════════════════════════════

@app.get("/api/user/favorites", tags=["사용자 데이터"])
def get_favorites(authorization: str = Header(...)):
    """내 즐겨찾기 목록"""
    uid = _get_uid(authorization)
    data = user_service.get_favorites(uid)
    return {"status": "success", "count": len(data), "data": data}


@app.post("/api/user/favorites", tags=["사용자 데이터"])
def add_favorite(
    crop_name: str = Query(..., description="작물명"),
    location: str = Query(..., description="지역명"),
    authorization: str = Header(...),
):
    """즐겨찾기 추가"""
    if len(crop_name.strip()) < 1:
        raise HTTPException(status_code=400, detail="작물명을 입력하세요.")
    uid = _get_uid(authorization)
    data = user_service.add_favorite(uid, crop_name, location)
    return {"status": "success", "data": data}


@app.delete("/api/user/favorites/{favorite_id}", tags=["사용자 데이터"])
def delete_favorite(favorite_id: str, authorization: str = Header(...)):
    """즐겨찾기 삭제"""
    uid = _get_uid(authorization)
    ok = user_service.delete_favorite(uid, favorite_id)
    if not ok:
        raise HTTPException(status_code=404, detail="즐겨찾기를 찾을 수 없습니다.")
    return {"status": "success"}


# ════════════════════════════════════════════
# 📍  농지 위치 API
# ════════════════════════════════════════════

@app.get("/api/user/locations", tags=["사용자 데이터"])
def get_locations(authorization: str = Header(...)):
    """내 농지 위치 목록"""
    uid = _get_uid(authorization)
    data = user_service.get_locations(uid)
    return {"status": "success", "count": len(data), "data": data}


@app.post("/api/user/locations", tags=["사용자 데이터"])
def add_location(
    name: str = Query(..., description="위치 이름"),
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"),
    address: str = Query(default="", description="주소"),
    authorization: str = Header(...),
):
    """농지 위치 추가"""
    validate_lat_lon(lat, lon)
    validate_location_name(name)
    uid = _get_uid(authorization)
    data = user_service.add_location(uid, name, lat, lon, address)
    return {"status": "success", "data": data}


@app.delete("/api/user/locations/{location_id}", tags=["사용자 데이터"])
def delete_location(location_id: str, authorization: str = Header(...)):
    """농지 위치 삭제"""
    uid = _get_uid(authorization)
    ok = user_service.delete_location(uid, location_id)
    if not ok:
        raise HTTPException(status_code=404, detail="위치를 찾을 수 없습니다.")
    return {"status": "success"}


# ════════════════════════════════════════════
# 📍  지점 목록
# ════════════════════════════════════════════

@app.get("/api/stations", tags=["지점목록"])
def get_stations():
    """전국 25개 농업 지점 목록"""
    return {
        "status": "success",
        "count": len(weather_service.stations),
        "data": weather_service.stations,
    }
