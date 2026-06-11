"""
🤖 Gemini AI 작물 추천 서비스
팜맵 기상 + 토양 + 병해충 데이터를 분석해서
귀농인에게 맞춤 작물을 추천해줍니다.
"""

import time
import google.generativeai as genai
from core.config import GEMINI_API_KEY

# Gemini 초기화
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")


def _generate_with_retry(prompt: str, max_retries: int = 3) -> str:
    """
    429 오류 시 자동 재시도
    """
    import re
    for i in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                # 대기 시간 추출
                match = re.search(r'seconds: (\d+)', error_msg)
                wait = int(match.group(1)) if match else 20
                print(f"  ⏳ 429 오류 - {wait}초 대기 후 재시도 ({i+1}/{max_retries})")
                time.sleep(wait)
                continue
            raise e
    raise Exception("최대 재시도 횟수 초과")


class AIService:
    """Gemini AI 작물 추천 서비스"""

    def recommend_crops(
        self,
        location: str,
        weather: dict | None,
        soil: dict | None,
        pest: list | None,
    ) -> dict:
        prompt = _build_prompt(location, weather, soil, pest)
        try:
            text = _generate_with_retry(prompt)
            return {
                "status": "success",
                "location": location,
                "recommendation": text,
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
            text = _generate_with_retry(prompt)
            return {
                "status": "success",
                "question": question,
                "answer": text,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }


def _build_prompt(location, weather, soil, pest) -> str:
    
    w = f"기온:{weather.get('temperature','?')}°C, 강수:{weather.get('precipitation','?')}mm, 습도:{weather.get('humidity','?')}%" if weather else "없음"
    s = f"pH:{soil.get('ph','?')}, 유기물:{soil.get('organic_matter','?')}" if soil else "없음"
    p = ", ".join([p.get('pest_name','?') for p in pest[:3]]) if pest else "없음"

    return f"""귀농 전문가로서 아래 데이터로 작물 추천해주세요.
지역:{location} | 기상:{w} | 토양:{s} | 병해충:{p}

1. 추천작물 TOP3 (이유 포함)
2. 각 작물 재배방법 요약
3. 주의사항
4. 초보자 조언

간결하게 답변해주세요."""