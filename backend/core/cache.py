"""
⚡ 캐싱 모듈
같은 데이터 반복 요청 시 빠르게 응답
메모리 기반 캐시 (서버 재시작 시 초기화)
"""

import time
from typing import Any

# 캐시 저장소
_cache: dict[str, dict] = {}

# 캐시 유효 시간 (초)
CACHE_TTL = {
    "weather": 60 * 30,    # 기상 데이터: 30분
    "soil":    60 * 60 * 24,  # 토양 데이터: 24시간 (잘 안 바뀜)
    "pest":    60 * 60 * 6,   # 병해충: 6시간
    "default": 60 * 10,    # 기본: 10분
}


def get(key: str) -> Any | None:
    """캐시에서 값 가져오기. 만료됐거나 없으면 None 반환"""
    if key not in _cache:
        return None
    item = _cache[key]
    if time.time() > item["expires_at"]:
        del _cache[key]
        return None
    return item["value"]


def set(key: str, value: Any, ttl_type: str = "default") -> None:
    """캐시에 값 저장"""
    ttl = CACHE_TTL.get(ttl_type, CACHE_TTL["default"])
    _cache[key] = {
        "value": value,
        "expires_at": time.time() + ttl,
    }


def delete(key: str) -> None:
    """캐시에서 값 삭제"""
    _cache.pop(key, None)


def clear() -> None:
    """캐시 전체 초기화"""
    _cache.clear()


def make_key(*args) -> str:
    """캐시 키 생성"""
    return ":".join(str(a) for a in args)
