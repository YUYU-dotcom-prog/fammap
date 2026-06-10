# 🌾 농업기상 GIS - FastAPI 백엔드

팜맵기반 농업기상 조회 서비스를 래핑한 REST API 서버입니다.  
프론트엔드(React, Vue 등)와 완전 분리된 JSON API 구조입니다.

---

## 📁 프로젝트 구조

```
farmmap_api/
├── main.py                  # FastAPI 앱 + 라우터
├── requirements.txt
├── .env.example             # 환경변수 예시
├── core/
│   ├── config.py            # API 키 · 설정
│   └── api_client.py        # 공공데이터포털 원시 API 호출
└── services/
    └── weather_service.py   # 비즈니스 로직 · 데이터 파싱
```

---

## 🚀 시작하기

### 1. 설치
```bash
pip install -r requirements.txt
```

### 2. API 키 설정
```bash
cp .env.example .env
# .env 파일을 열어 FARMMAP_API_KEY=발급받은_키 입력
```

### 3. 서버 실행
```bash
uvicorn main:app --reload --port 8000
```

### 4. API 문서 확인
브라우저에서 → http://localhost:8000/docs

---

## 📡 API 엔드포인트

| Method | URL | 설명 |
|--------|-----|------|
| GET | `/` | 헬스체크 |
| GET | `/health` | 서버 상태 |
| GET | `/api/stations` | 전국 25개 지점 목록 |
| GET | `/api/weather/korea?date=YYYYMMDD` | 전국 기상 데이터 (지도용) |
| GET | `/api/weather/point?lat=&lon=&date=` | 특정 좌표 일별 기상 |
| GET | `/api/weather/hourly?lat=&lon=&date=` | 특정 좌표 시간별 기상 |

---

## 📦 응답 예시

### `GET /api/weather/korea`
```json
{
  "status": "success",
  "date": "20240601",
  "count": 25,
  "data": [
    {
      "id": "gunsan",
      "name": "군산",
      "sido": "전북",
      "lat": 35.9677,
      "lon": 126.7368,
      "temperature": 22.5,
      "precipitation": 0.0,
      "humidity": 68.0,
      "wind_speed": 2.3,
      "solar_radiation": 18.4,
      "date": "20240601"
    }
  ]
}
```

### `GET /api/weather/hourly`
```json
{
  "status": "success",
  "date": "20240601",
  "lat": 35.9677,
  "lon": 126.7368,
  "count": 24,
  "data": [
    { "hour": "00", "temperature": 18.2, "precipitation": 0.0, "humidity": 75.0, ... },
    { "hour": "01", "temperature": 17.8, ... }
  ]
}
```
