"""
🤖 Gemini AI 작물 추천 서비스 (작성하신 캐시 모듈 연동 버전)
"""

import time
import google.generativeai as genai
from core.config import GEMINI_API_KEY
import core.cache as cache  # ⭐ 작성하신 캐시 모듈 임포트

# Gemini 초기화
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")


def _generate_with_retry(prompt: str, max_retries: int = 3) -> str:
    """429 오류 시 무료 티어 기준 확실한 대기 후 재시도 (지수 백오프)"""
    for i in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Quota" in error_msg:
                wait = (i + 1) * 30 
                print(f"   ⏳ 429 쿼터 초과 - {wait}초 대기 후 재시도합니다. ({i+1}/{max_retries})")
                time.sleep(wait)
                continue
            raise e
    raise Exception("Gemini API 무료 할당량을 초과했습니다. 잠시 후 다시 시도해주세요.")


class AIService:
    """Gemini AI 작물 추천 서비스"""

    def _build_prompt(self, location: str, weather: dict | None, soil: dict | None, pest: list | None) -> str:
        w = f"기온:{weather.get('temperature','?')}°C 강수:{weather.get('precipitation','?')}mm 습도:{weather.get('humidity','?')}%" if weather else "없음"
        s = f"pH:{soil.get('ph','?')} 유기물:{soil.get('organic_matter','?')}" if soil else "없음"
        p = ",".join([p.get('pest_name','?') for p in (pest or [])[:2]]) or "없음"

        return f"""당신은 귀농 전문가입니다. 아래 농업 데이터를 기반으로 맞춤 작물을 추천하세요.

[농업 데이터]
지역: {location}
기상: {w}
토양: {s}
병해충: {p}

[작성 규칙 - 필수]
1. 추천 작물은 딱 3개만 선정할 것.
2. 모든 대답은 줄바꿈을 포함해 핵심만 최대 4줄 이내로 극도로 간결하게 작성할 것.
3. 친절한 인사말이나 서론, 결론은 절대 생략할 것.
"""

    def recommend_crops(
        self,
        location: str,
        weather: dict | None,
        soil: dict | None,
        pest: list | None,
    ) -> dict:
        """작물 추천 로직 (기존 캐시 모듈 완벽 적용)"""
        
        # 🛡️ 1. 작성하신 함수로 유니크한 캐시 키 생성 (예: "recommend:전북완주")
        cache_key = cache.make_key("recommend", location)
        
        # 🛡️ 2. 캐시 확인
        cached_result = cache.get(cache_key)
        if cached_result:
            return {
                "status": "success",
                "location": location,
                "recommendation": cached_result,
                "is_cached": True,
                "input_data": {"weather": weather, "soil": soil, "pest": pest}
            }

        # 3. 캐시에 없으면 프롬프트 조립 후 Gemini 호출
        prompt = self._build_prompt(location, weather, soil, pest)
        try:
            text = _generate_with_retry(prompt)
            
            # 🛡️ 4. 성공한 결과는 작성하신 캐싱 시스템에 세팅
            # 유효시간 타입을 'default'(10분) 혹은 원하시면 다른 걸로 지정 가능합니다.
            cache.set(cache_key, text, ttl_type="default")
            
            return {
                "status": "success",
                "location": location,
                "recommendation": text,
                "is_cached": False,
                "input_data": {"weather": weather, "soil": soil, "pest": pest}
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def ask_farming_question(self, question: str, context: dict | None = None) -> dict:
        """일반 질문 답변 (질문도 반복되면 서버 자원을 아끼기 위해 캐싱 처리)"""
        cache_key = cache.make_key("question", question, str(context))
        
        cached_answer = cache.get(cache_key)
        if cached_answer:
            return {
                "status": "success",
                "question": question,
                "answer": cached_answer,
                "is_cached": True
            }

        prompt = f"""당신은 귀농 전문가입니다. 
지역 컨텍스트: {context if context else '없음'}
질문: {question}

핵심 답변, 간단한 설명, 주의사항을 각각 딱 한 줄씩만 선언문 형태로 간결하게 작성하세요."""
        
        try:
            text = _generate_with_retry(prompt)
            cache.set(cache_key, text, ttl_type="default")
            return {
                "status": "success",
                "question": question,
                "answer": text,
                "is_cached": False
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }