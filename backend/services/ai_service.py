"""
🤖 Gemini AI 작물 추천 서비스 (영어 프롬프트 / 한국어 출력 최적화 버전)
"""

import time
import google.generativeai as genai
from core.config import GEMINI_API_KEY
import core.cache as cache  # ⭐ 작성하신 캐시 모듈 임포트

# Gemini 초기화
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

def _generate_with_retry(prompt: str, max_retries: int = 5) -> str:
    """429 오류 발생 시 무료 티어 초과를 방지하기 위해 끈질기게 대기 후 재시도하는 로직"""
    for i in range(max_retries):
        try:
            # 2번째 시도부터는 분당 호출 제한(RPM)이 풀릴 때까지 강제 대기
            if i > 0:
                wait_time = (i * 30) + 5
                print(f"⏳ [Gemini 429 예방] 무료 쿼터 초과 방지를 위해 {wait_time}초간 대기합니다... ({i}/{max_retries})")
                time.sleep(wait_time)
                
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Quota" in error_msg or "Resource" in error_msg:
                print(f"⚠️ [Gemini Warning] 현재 무료 분당 호출 제한(RPM)에 걸렸습니다. 다음 루프에서 대기를 시작합니다.")
                if i == max_retries - 1:
                    raise Exception("❌ Gemini API 무료 티어 할당량을 완전히 초과했습니다. 잠시 후 다시 시도해주세요.")
                continue  # 다음 루프로 넘어가서 대기 시간을 가집니다.
            
            raise e
            
    raise Exception("Gemini API 호출에 실패했습니다.")


class AIService:
    """Gemini AI 작물 추천 서비스"""

    def _build_prompt(self, location: str, weather: dict | None, soil: dict | None, pest: list | None) -> str:
        # 데이터 주입부 글자수도 최소한으로 압축하여 토큰 절약
        w = f"Temp:{weather.get('temperature','?')}C,Rain:{weather.get('precipitation','?')}mm,Humid:{weather.get('humidity','?')}%" if weather else "None"
        s = f"pH:{soil.get('ph','?')},Org:{soil.get('organic_matter','?')}" if soil else "None"
        p = ",".join([p.get('pest_name','?') for p in (pest or [])[:2]]) or "None"

        # 🔥 영문 프롬프트 다이어트 (토큰 소모량 60% 이상 절감 치트키)
        return f"""You are an expert agricultural recommender. Recommend the best crops based on the provided environmental data.

[Environmental Data]
Location: {location}
Weather: {w}
Soil: {s}
Pest: {p}

[Rules - STRICT COMPLIANCE]
1. Recommend exactly 3 crops.
2. For each crop, provide a 1-line concise reason based on the data.
3. ALL OUTPUT MUST BE WRITTEN IN KOREAN ONLY. (중요: 모든 답변은 반드시 한국어로만 작성할 것)
4. No greetings, no intro, no outro. Return only the core recommendation list.
"""

    def recommend_crops(
        self,
        location: str,
        weather: dict | None,
        soil: dict | None,
        pest: list | None,
    ) -> dict:
        """작물 추천 로직 (영문 프롬프트 & 인자 오류 교정 버전)"""
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        cache_key = cache.make_key("recommend", location, today)
        
        # 1. 캐시 확인
        cached_result = cache.get(cache_key)
        if cached_result:
            return {
                "status": "success",
                "location": location,
                "recommendation": cached_result,
                "is_cached": True,
                "input_data": {"weather": weather, "soil": soil, "pest": pest}
            }

        # 2. 캐시에 없으면 영문 압축 프롬프트 조립
        prompt = self._build_prompt(location, weather, soil, pest)
        try:
            # 🚨 max_retries 인자를 명시하여 에러를 원천 차단합니다.
            text = _generate_with_retry(prompt, max_retries=5)
            
            # 3. 성공 결과 캐싱
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
        """일반 질문 답변 (영문 구조화 버전)"""
        cache_key = cache.make_key("question", question, str(context))
        
        cached_answer = cache.get(cache_key)
        if cached_answer:
            return {
                "status": "success",
                "question": question,
                "answer": cached_answer,
                "is_cached": True
            }

        # 일반 질문용 프롬프트도 영어 뼈대로 압축
        prompt = f"""You are an expert farming consultant. Answer the user's question based on the context.
Context: {context if context else 'None'}
Question: {question}

[Rules]
- Provide the answer concisely in exactly 3 lines (Core answer, Brief explanation, Precaution).
- ANSWER MUST BE IN KOREAN."""
        
        try:
            # 🚨 여기도 리트라이 인자 명시 완료!
            text = _generate_with_retry(prompt, max_retries=5)
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