"""
📝 로깅 모듈
누가 언제 뭘 요청했는지 기록
"""

import logging
import sys
from datetime import datetime

# 로그 포맷 설정
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 로거 생성
logger = logging.getLogger("farmmap")
logger.setLevel(logging.INFO)

# 콘솔 출력
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
logger.addHandler(console_handler)

# 파일 출력 (logs 폴더에 날짜별 저장)
import os
os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler(
    f"logs/{datetime.now().strftime('%Y-%m-%d')}.log",
    encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
logger.addHandler(file_handler)
