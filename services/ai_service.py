"""
🤖 Gemini AI 작물 추천 서비스
팜맵 기상 + 토양 + 병해충 데이터를 분석해서
귀농인에게 맞춤 작물을 추천해줍니다.
"""

import google.generativeai as genai
from core.config import GEMINI_API_KEY

# Gemini 초기화
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


class AIService:
    """Gemini AI 작물 추천 서비스"""

    def recommend_crops(
        self,
        location: str,
        weather: dict | None,
        soil: dict | None,
        pest: list | None,
    ) -> dict:
        """
        수집된 농업 데이터를 바탕으로 작물 추천

        Args:
            location : 사용자 입력 지역명 (예: "전북 군산")
            weather  : 농업기상 데이터
            soil     : 토양검정 데이터
            pest     : 병해충 발생 데이터

        Returns:
            AI 추천 결과 dict
        """
        prompt = _build_prompt(location, weather, soil, pest)

        try:
            response = model.generate_content(prompt)
            return {
                "status": "success",
                "location": location,
                "recommendation": response.text,
                "input_data": {
                    "weather": weather,
                    "soil": soil,
                    "pest": pest,
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def ask_farming_question(self, question: str, context: dict | None = None) -> dict:
        """
        귀농 관련 자유 질문에 AI가 답변

        Args:
            question : 사용자 질문 (예: "고구마 키우는 방법 알려줘")
            context  : 추가 컨텍스트 (지역, 계절 등)
        """
        prompt = f"""
당신은 대한민국 귀농 전문가 AI입니다.
처음 귀농하는 사람들을 위해 쉽고 친절하게 답변해주세요.

{f"사용자 지역/상황: {context}" if context else ""}

질문: {question}

답변은 아래 형식으로 해주세요:
- 핵심 답변을 먼저 간단히
- 그 다음 자세한 설명
- 주의사항이 있으면 마지막에
        """

        try:
            response = model.generate_content(prompt)
            return {
                "status": "success",
                "question": question,
                "answer": response.text,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }


# ── 프롬프트 생성 ─────────────────────────────────────────────

def _build_prompt(
    location: str,
    weather: dict | None,
    soil: dict | None,
    pest: list | None,
) -> str:

    # 기상 정보 텍스트
    weather_text = "데이터 없음"
    if weather:
        weather_text = f"""
- 기온: {weather.get('temperature', 'N/A')}°C
- 강수량: {weather.get('precipitation', 'N/A')}mm
- 습도: {weather.get('humidity', 'N/A')}%
- 풍속: {weather.get('wind_speed', 'N/A')}m/s
        """.strip()

    # 토양 정보 텍스트
    soil_text = "데이터 없음"
    if soil:
        soil_text = f"""
- 토성: {soil.get('soil_type', 'N/A')}
- pH(산도): {soil.get('ph', 'N/A')}
- 유기물: {soil.get('organic_matter', 'N/A')}g/kg
- 유효인산: {soil.get('available_p', 'N/A')}mg/kg
- 칼륨: {soil.get('potassium', 'N/A')}cmol+/kg
- 칼슘: {soil.get('calcium', 'N/A')}cmol+/kg
- 마그네슘: {soil.get('magnesium', 'N/A')}cmol+/kg
- 전기전도도(EC): {soil.get('ec', 'N/A')}dS/m
        """.strip()

    # 병해충 정보 텍스트
    pest_text = "데이터 없음"
    if pest and len(pest) > 0:
        pest_list = "\n".join([
            f"- {p.get('pest_name', 'N/A')} ({p.get('crop_name', 'N/A')}): 발생수준 {p.get('occrrnc_level', 'N/A')}"
            for p in pest[:5]
        ])
        pest_text = pest_list

    return f"""
당신은 대한민국 귀농 전문가 AI입니다.
처음 귀농하는 사람을 위해 아래 농업 데이터를 분석해서 작물을 추천해주세요.

📍 지역: {location}

🌤️ 농업기상 데이터:
{weather_text}

🌱 토양검정 데이터:
{soil_text}

🐛 병해충 발생 현황:
{pest_text}

위 데이터를 바탕으로 아래 형식으로 답변해주세요:

1. 추천 작물 TOP 3
   - 작물명, 추천 이유 (데이터 근거 포함)

2. 각 작물별 재배 방법 요약
   - 파종 시기, 수확 시기, 주요 관리 포인트

3. 주의사항
   - 이 지역에서 키우기 어려운 작물
   - 병해충 관련 주의사항

4. 귀농 초보자를 위한 한마디 조언

쉽고 친절하게, 초보 귀농인도 이해할 수 있게 설명해주세요.
    """.strip()
