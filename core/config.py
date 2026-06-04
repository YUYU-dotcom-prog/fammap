"""
환경설정 - API 키 및 기본값 관리
.env 파일 또는 환경변수로 주입
"""

import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 자동 로드

# ✅ 공공데이터포털 인코딩 키를 .env 파일에 넣거나 환경변수로 설정하세요
#    FARMMAP_API_KEY=여기에_인코딩_키
API_KEY: str = os.getenv("FARMMAP_API_KEY", "YOUR_API_KEY_HERE")

BASE_URL: str = (
    "http://apis.data.go.kr/B552895/rest/farmmap"
    "/getFarmmapAgricultureWeatherService"
)

# API 요청 타임아웃 (초)
REQUEST_TIMEOUT: int = 10

# 지점 간 요청 딜레이 (초) - API 과부하 방지
REQUEST_DELAY: float = 0.15
