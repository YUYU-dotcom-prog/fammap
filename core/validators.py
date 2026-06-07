"""
✅ 입력값 검증 모듈
잘못된 값 들어왔을 때 막기
"""

from fastapi import HTTPException


def validate_lat_lon(lat: float, lon: float) -> None:
    """위경도 범위 검증 (대한민국 범위)"""
    if not (33.0 <= lat <= 38.9):
        raise HTTPException(
            status_code=400,
            detail=f"위도 범위 오류: 대한민국 범위(33.0 ~ 38.9)를 벗어났습니다. 입력값: {lat}"
        )
    if not (124.0 <= lon <= 132.0):
        raise HTTPException(
            status_code=400,
            detail=f"경도 범위 오류: 대한민국 범위(124.0 ~ 132.0)를 벗어났습니다. 입력값: {lon}"
        )


def validate_date(date: str) -> None:
    """날짜 형식 검증 (YYYYMMDD)"""
    if not date.isdigit() or len(date) != 8:
        raise HTTPException(
            status_code=400,
            detail=f"날짜 형식 오류: YYYYMMDD 형식으로 입력하세요. 입력값: {date}"
        )
    year  = int(date[:4])
    month = int(date[4:6])
    day   = int(date[6:])
    if not (2000 <= year <= 2100):
        raise HTTPException(status_code=400, detail=f"연도 범위 오류: {year}")
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail=f"월 범위 오류: {month}")
    if not (1 <= day <= 31):
        raise HTTPException(status_code=400, detail=f"일 범위 오류: {day}")


def validate_year(year: str) -> None:
    """연도 형식 검증 (YYYY)"""
    if not year.isdigit() or len(year) != 4:
        raise HTTPException(
            status_code=400,
            detail=f"연도 형식 오류: YYYY 형식으로 입력하세요. 입력값: {year}"
        )


def validate_location_name(name: str) -> None:
    """지역명 길이 검증"""
    if len(name.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="지역명은 2글자 이상 입력하세요."
        )
    if len(name) > 50:
        raise HTTPException(
            status_code=400,
            detail="지역명은 50글자 이하로 입력하세요."
        )
