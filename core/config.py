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
