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
from services.kakao_service import KakaoService
from services.payment_service import PaymentService
from services.station_service import StationService

app = FastAPI(
    title="귀농 AI 작물 추천 시스템 API",
    description="팜맵기반 농업기상 / 토양검정 / 병해충발생 데이터 + Gemini AI 작물 추천",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

weather_service = WeatherService()
soil_service    = SoilService()
pest_service    = PestService()
ai_service      = AIService()
auth_service    = AuthService()
user_service    = UserService()
kakao_service   = KakaoService()
payment_service = PaymentService()
station_service = StationService()

STATIONS = [
    {"id": "seoul",     "name": "서울",   "sido": "서울",  "lat": 37.5665, "lon": 126.9780},
    {"id": "incheon",   "name": "인천",   "sido": "인천",  "lat": 37.4563, "lon": 126.7052},
    {"id": "suwon",     "name": "수원",   "sido": "경기",  "lat": 37.2636, "lon": 127.0286},
    {"id": "yangpyeong","name": "양평",   "sido": "경기",  "lat": 37.4914, "lon": 127.4875},
    {"id": "chuncheon", "name": "춘천",   "sido": "강원",  "lat": 37.8813, "lon": 127.7298},
    {"id": "wonju",     "name": "원주",   "sido": "강원",  "lat": 37.3422, "lon": 127.9201},
    {"id": "gangneung", "name": "강릉",   "sido": "강원",  "lat": 37.7519, "lon": 128.8761},
    {"id": "cheonan",   "name": "천안",   "sido": "충남",  "lat": 36.8151, "lon": 127.1139},
    {"id": "cheongju",  "name": "청주",   "sido": "충북",  "lat": 36.6424, "lon": 127.4890},
    {"id": "hongseong", "name": "홍성",   "sido": "충남",  "lat": 36.6010, "lon": 126.6608},
    {"id": "nonsan",    "name": "논산",   "sido": "충남",  "lat": 36.1868, "lon": 127.0988},
    {"id": "jeonju",    "name": "전주",   "sido": "전북",  "lat": 35.8242, "lon": 127.1480},
    {"id": "gunsan",    "name": "군산",   "sido": "전북",  "lat": 35.9677, "lon": 126.7368},
    {"id": "gimje",     "name": "김제",   "sido": "전북",  "lat": 35.8033, "lon": 126.8803},
    {"id": "naju",      "name": "나주",   "sido": "전남",  "lat": 35.0160, "lon": 126.7108},
    {"id": "haenam",    "name": "해남",   "sido": "전남",  "lat": 34.5739, "lon": 126.5990},
    {"id": "suncheon",  "name": "순천",   "sido": "전남",  "lat": 34.9506, "lon": 127.4874},
    {"id": "daegu",     "name": "대구",   "sido": "경북",  "lat": 35.8714, "lon": 128.6014},
    {"id": "andong",    "name": "안동",   "sido": "경북",  "lat": 36.5684, "lon": 128.7294},
    {"id": "sangju",    "name": "상주",   "sido": "경북",  "lat": 36.4108, "lon": 128.1591},
    {"id": "miryang",   "name": "밀양",   "sido": "경남",  "lat": 35.5037, "lon": 128.7461},
    {"id": "jinju",     "name": "진주",   "sido": "경남",  "lat": 35.1799, "lon": 128.1076},
    {"id": "changwon",  "name": "창원",   "sido": "경남",  "lat": 35.2279, "lon": 128.6811},
    {"id": "jeju",      "name": "제주",   "sido": "제주",  "lat": 33.4996, "lon": 126.5312},
    {"id": "seogwipo",  "name": "서귀포", "sido": "제주",  "lat": 33.2541, "lon": 126.5600},
]


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = round((time.time() - start) * 1000)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({elapsed}ms)")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"예상치 못한 오류: {exc} | {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}
    )


def _resolve_date(date: str | None) -> str:
    if date:
        validate_date(date)
        return date
    return (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")


def _get_uid(authorization: str) -> str:
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
    return {"status": "ok", "message": "귀농 AI 작물 추천 시스템 API 서버가 실행 중입니다."}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ════════════════════════════════════════════
# 🌤️  농업기상 API
# ════════════════════════════════════════════

@app.get("/api/weather/korea", tags=["농업기상"])
def get_korea_weather(date: str = Query(default=None)):
    date = _resolve_date(date)
    cache_key = cache.make_key("weather_korea", date)
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = weather_service.get_korea_weather(date)
    result = {"status": "success", "date": date, "count": len(data), "data": data}
    cache.set(cache_key, result, "weather")
    return result


@app.get("/api/weather/point", tags=["농업기상"])
def get_point_weather(
    lat: float = Query(...),
    lon: float = Query(...),
    date: str = Query(default=None),
):
    validate_lat_lon(lat, lon)
    date = _resolve_date(date)
    cache_key = cache.make_key("weather_point", lat, lon, date)
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = weather_service.get_point_weather(lat, lon, date)
    if data is None:
        raise HTTPException(status_code=404, detail="해당 좌표의 데이터가 없습니다.")
    result = {"status": "success", "date": date, "data": data}
    cache.set(cache_key, result, "weather")
    return result


@app.get("/api/weather/hourly", tags=["농업기상"])
def get_hourly_weather(
    lat: float = Query(...),
    lon: float = Query(...),
    date: str = Query(default=None),
):
    validate_lat_lon(lat, lon)
    date = _resolve_date(date)
    cache_key = cache.make_key("weather_hourly", lat, lon, date)
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = weather_service.get_hourly_weather(lat, lon, date)
    result = {"status": "success", "date": date, "lat": lat, "lon": lon, "count": len(data), "data": data}
    cache.set(cache_key, result, "weather")
    return result


# ════════════════════════════════════════════
# 🌱  토양검정 API
# ════════════════════════════════════════════

@app.get("/api/soil/point", tags=["토양검정"])
def get_soil(lat: float = Query(...), lon: float = Query(...)):
    validate_lat_lon(lat, lon)
    cache_key = cache.make_key("soil", lat, lon)
    cached = cache.get(cache_key)
    if cached:
        return cached
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
    lat: float = Query(...),
    lon: float = Query(...),
    year: str = Query(default=None),
):
    validate_lat_lon(lat, lon)
    year = year or str(datetime.today().year)
    validate_year(year)
    cache_key = cache.make_key("pest_yearly", lat, lon, year)
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = pest_service.get_pest_yearly(lat, lon, year)
    result = {"status": "success", "year": year, "count": len(data), "data": data}
    cache.set(cache_key, result, "pest")
    return result


@app.get("/api/pest/monthly", tags=["병해충발생"])
def get_pest_monthly(
    lat: float = Query(...),
    lon: float = Query(...),
    year: str = Query(default=None),
    month: str = Query(default=None),
):
    validate_lat_lon(lat, lon)
    year  = year  or str(datetime.today().year)
    month = month or f"{datetime.today().month:02d}"
    validate_year(year)
    cache_key = cache.make_key("pest_monthly", lat, lon, year, month)
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = pest_service.get_pest_monthly(lat, lon, year, month)
    result = {"status": "success", "year": year, "month": month, "count": len(data), "data": data}
    cache.set(cache_key, result, "pest")
    return result


# ════════════════════════════════════════════
# 🤖  AI 작물추천 API
# ════════════════════════════════════════════

@app.get("/api/ai/recommend", tags=["AI 작물추천"])
def recommend_crops(
    lat: float = Query(...),
    lon: float = Query(...),
    location: str = Query(...),
    date: str = Query(default=None),
    authorization: str = Header(default=None),
):
    """🌾 귀농인 맞춤 작물 추천 (Firebase 사전수집 데이터 활용)"""
    validate_lat_lon(lat, lon)
    validate_location_name(location)
    date = _resolve_date(date)
    year = date[:4]

    if authorization:
        token = authorization.replace("Bearer ", "")
        user = auth_service.verify_token(token)
        if user:
            limit = payment_service.check_ai_limit(user["uid"])
            if not limit["can_use"]:
                raise HTTPException(
                    status_code=429,
                    detail=f"이번 달 AI 추천 횟수({limit['limit']}회)를 초과했습니다."
                )
            payment_service.increment_ai_usage(user["uid"])

    logger.info(f"AI 작물 추천 요청: {location} ({lat},{lon})")

    station_data = station_service.get_nearest_station_data(lat, lon)

    if station_data:
        weather = station_data.get("weather")
        soil    = station_data.get("soil")
        pest    = station_data.get("pest")
        logger.info(f"Firebase 데이터 사용: {station_data.get('station_name')}")
    else:
        logger.info("Firebase 데이터 없음 → 직접 API 호출")
        weather = weather_service.get_point_weather(lat, lon, date)
        soil    = soil_service.get_soil(lat, lon)
        pest    = pest_service.get_pest_yearly(lat, lon, year)

    return ai_service.recommend_crops(location, weather, soil, pest)


@app.get("/api/ai/question", tags=["AI 작물추천"])
def ask_question(
    question: str = Query(...),
    location: str = Query(default=None),
):
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
    uid = _get_uid(authorization)
    data = user_service.get_recommendations(uid)
    return {"status": "success", "count": len(data), "data": data}


@app.post("/api/user/recommendations", tags=["사용자 데이터"])
def save_recommendation(
    location: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...),
    result: str = Query(...),
    authorization: str = Header(...),
):
    validate_lat_lon(lat, lon)
    validate_location_name(location)
    uid = _get_uid(authorization)
    data = user_service.save_recommendation(uid, location, lat, lon, result)
    return {"status": "success", "data": data}


@app.delete("/api/user/recommendations/{record_id}", tags=["사용자 데이터"])
def delete_recommendation(record_id: str, authorization: str = Header(...)):
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
    uid = _get_uid(authorization)
    data = user_service.get_favorites(uid)
    return {"status": "success", "count": len(data), "data": data}


@app.post("/api/user/favorites", tags=["사용자 데이터"])
def add_favorite(
    crop_name: str = Query(...),
    location: str = Query(...),
    authorization: str = Header(...),
):
    if len(crop_name.strip()) < 1:
        raise HTTPException(status_code=400, detail="작물명을 입력하세요.")
    uid = _get_uid(authorization)
    data = user_service.add_favorite(uid, crop_name, location)
    return {"status": "success", "data": data}


@app.delete("/api/user/favorites/{favorite_id}", tags=["사용자 데이터"])
def delete_favorite(favorite_id: str, authorization: str = Header(...)):
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
    uid = _get_uid(authorization)
    data = user_service.get_locations(uid)
    return {"status": "success", "count": len(data), "data": data}


@app.post("/api/user/locations", tags=["사용자 데이터"])
def add_location(
    name: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...),
    address: str = Query(default=""),
    authorization: str = Header(...),
):
    validate_lat_lon(lat, lon)
    validate_location_name(name)
    uid = _get_uid(authorization)
    data = user_service.add_location(uid, name, lat, lon, address)
    return {"status": "success", "data": data}


@app.delete("/api/user/locations/{location_id}", tags=["사용자 데이터"])
def delete_location(location_id: str, authorization: str = Header(...)):
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
    return {"status": "success", "count": len(STATIONS), "data": STATIONS}


# ════════════════════════════════════════════
# 🗺️  카카오 주소 검색 API
# ════════════════════════════════════════════

@app.get("/api/kakao/address", tags=["카카오 지도"])
def address_to_coord(address: str = Query(...)):
    validate_location_name(address)
    logger.info(f"주소 검색: {address}")
    data = kakao_service.address_to_coord(address)
    if data is None:
        raise HTTPException(status_code=404, detail="해당 주소를 찾을 수 없습니다.")
    return {"status": "success", "data": data}


@app.get("/api/kakao/coord", tags=["카카오 지도"])
def coord_to_address(lat: float = Query(...), lon: float = Query(...)):
    validate_lat_lon(lat, lon)
    data = kakao_service.coord_to_address(lat, lon)
    if data is None:
        raise HTTPException(status_code=404, detail="해당 좌표의 주소를 찾을 수 없습니다.")
    return {"status": "success", "data": data}


@app.get("/api/kakao/search", tags=["카카오 지도"])
def search_keyword(
    keyword: str = Query(...),
    lat: float = Query(default=None),
    lon: float = Query(default=None),
):
    data = kakao_service.search_keyword(keyword, lat, lon)
    return {"status": "success", "count": len(data), "data": data}


# ════════════════════════════════════════════
# 💳  결제 API
# ════════════════════════════════════════════

@app.get("/api/payment/plans", tags=["결제"])
def get_plans():
    return {
        "status": "success",
        "data": {
            "free":    {"name": "무료",     "price": 0,    "ai_count": 10},
            "basic":   {"name": "베이직",   "price": 3900, "ai_count": 30},
            "premium": {"name": "프리미엄", "price": 9900, "ai_count": 999},
        }
    }


@app.get("/api/payment/usage", tags=["결제"])
def get_ai_usage(authorization: str = Header(...)):
    uid = _get_uid(authorization)
    data = payment_service.check_ai_limit(uid)
    return {"status": "success", "data": data}


@app.post("/api/payment/toss/confirm", tags=["결제"])
def toss_confirm(
    payment_key: str = Query(...),
    order_id: str = Query(...),
    amount: int = Query(...),
    plan_id: str = Query(...),
    authorization: str = Header(...),
):
    uid = _get_uid(authorization)
    result = payment_service.toss_confirm_payment(payment_key, order_id, amount)
    if result["status"] == "success":
        payment_service.save_subscription(uid, plan_id, result["data"])
    return result


@app.post("/api/payment/kakao/ready", tags=["결제"])
def kakao_ready(
    plan_id: str = Query(...),
    order_id: str = Query(...),
    authorization: str = Header(...),
):
    uid = _get_uid(authorization)
    return payment_service.kakao_ready_payment(uid, plan_id, order_id)


@app.post("/api/payment/kakao/approve", tags=["결제"])
def kakao_approve(
    tid: str = Query(...),
    pg_token: str = Query(...),
    order_id: str = Query(...),
    plan_id: str = Query(...),
    authorization: str = Header(...),
):
    uid = _get_uid(authorization)
    result = payment_service.kakao_approve_payment(uid, tid, pg_token, order_id)
    if result["status"] == "success":
        payment_service.save_subscription(uid, plan_id, result["data"])
    return result


# ════════════════════════════════════════════
# 🗄️  Firebase 사전수집 데이터 API
# ════════════════════════════════════════════

@app.get("/api/station/nearest", tags=["사전수집 데이터"])
def get_nearest_station(lat: float = Query(...), lon: float = Query(...)):
    validate_lat_lon(lat, lon)
    cache_key = cache.make_key("station_nearest", lat, lon)
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = station_service.get_nearest_station_data(lat, lon)
    if data is None:
        raise HTTPException(status_code=404, detail="데이터가 없습니다.")
    result = {"status": "success", "data": data}
    cache.set(cache_key, result, "weather")
    return result


@app.get("/api/station/all", tags=["사전수집 데이터"])
def get_all_stations():
    cache_key = cache.make_key("station_all")
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = station_service.get_all_stations_data()
    result = {"status": "success", "count": len(data), "data": data}
    cache.set(cache_key, result, "weather")
    return result