"""
환경설정 - API 키 및 기본값 관리
.env 파일 또는 환경변수로 주입
"""

import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 자동 로드

# ✅ 공공데이터포털 인코딩 키를 .env 파일에 넣거나 환경변수로 설정하세요

# 농업기상 API 키
WEATHER_API_KEY: str = os.getenv("FARMMAP_WEATHER_API_KEY", "YOUR_WEATHER_API_KEY_HERE")

# 토양검정 API 키
SOIL_API_KEY: str = os.getenv("FARMMAP_SOIL_API_KEY", "YOUR_SOIL_API_KEY_HERE")

# 병해충발생 API 키
PEST_API_KEY: str = os.getenv("FARMMAP_PEST_API_KEY", "YOUR_PEST_API_KEY_HERE")

# 각 API BASE URL
WEATHER_BASE_URL: str = (
    "http://apis.data.go.kr/B552895/rest/farmmap"
    "/getFarmmapAgricultureWeatherService"
)

SOIL_BASE_URL: str = (
    "http://apis.data.go.kr/B552895/rest/farmmap"
    "/getFarmmapSoilAnalysisService"
)

PEST_BASE_URL: str = (
    "http://apis.data.go.kr/B552895/rest/farmmap"
    "/getFarmmapPestOccrrncService"
)

# API 요청 타임아웃 (초)
REQUEST_TIMEOUT: int = 10

# 지점 간 요청 딜레이 (초) - API 과부하 방지
REQUEST_DELAY: float = 0.15

# Gemini AI API 키
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

# Firebase 키 파일 경로
FIREBASE_KEY_PATH: str = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")

# 카카오 REST API 키
KAKAO_API_KEY: str = os.getenv("KAKAO_API_KEY", "YOUR_KAKAO_API_KEY_HERE")

# 토스페이먼츠
TOSS_CLIENT_KEY: str = os.getenv("TOSS_CLIENT_KEY", "")
TOSS_SECRET_KEY: str = os.getenv("TOSS_SECRET_KEY", "")

# 카카오페이
KAKAO_PAY_CLIENT_ID: str = os.getenv("KAKAO_PAY_CLIENT_ID", "")
KAKAO_PAY_SECRET_KEY: str = os.getenv("KAKAO_PAY_SECRET_KEY", "")

# 기상청 단기예보 API 키
WEATHER_FORECAST_API_KEY: str = os.getenv("WEATHER_FORECAST_API_KEY", "")

# 작물재배정보 API 키
CROP_INFO_API_KEY: str = os.getenv("CROP_INFO_API_KEY", "")