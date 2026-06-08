"""
💳 결제 서비스
토스페이먼츠 + 카카오페이 연동
AI 추천 횟수 제한 + 결제 처리
"""

import requests
import base64
from firebase_admin import firestore
from core.config import TOSS_SECRET_KEY, KAKAO_PAY_CLIENT_ID, KAKAO_PAY_SECRET_KEY
from datetime import datetime

db = firestore.client()

# 플랜 정보
PLANS = {
    "basic": {
        "name": "베이직",
        "price": 3900,
        "ai_count": 30,
    },
    "premium": {
        "name": "프리미엄",
        "price": 9900,
        "ai_count": 999,  # 무제한
    },
}

FREE_AI_COUNT = 10  # 무료 월 횟수


class PaymentService:

    # ── AI 횟수 관리 ──────────────────────────────────────────

    def get_ai_usage(self, uid: str) -> dict:
        """이번 달 AI 사용 횟수 조회"""
        month = datetime.now().strftime("%Y-%m")
        ref = db.collection("ai_usage").document(f"{uid}_{month}")
        doc = ref.get()

        if not doc.exists:
            return {"used": 0, "month": month}
        return doc.to_dict()

    def check_ai_limit(self, uid: str) -> dict:
        """AI 사용 가능 여부 확인"""
        usage = self.get_ai_usage(uid)
        used = usage.get("used", 0)

        # 구독 플랜 확인
        plan = self._get_user_plan(uid)
        limit = plan.get("ai_count", FREE_AI_COUNT)

        return {
            "can_use": used < limit,
            "used": used,
            "limit": limit,
            "remaining": max(0, limit - used),
            "plan": plan.get("name", "무료"),
        }

    def increment_ai_usage(self, uid: str) -> None:
        """AI 사용 횟수 1 증가"""
        month = datetime.now().strftime("%Y-%m")
        ref = db.collection("ai_usage").document(f"{uid}_{month}")
        doc = ref.get()

        if doc.exists:
            ref.update({"used": firestore.Increment(1)})
        else:
            ref.set({"uid": uid, "used": 1, "month": month})

    def _get_user_plan(self, uid: str) -> dict:
        """사용자 구독 플랜 조회"""
        ref = db.collection("subscriptions").document(uid)
        doc = ref.get()
        if not doc.exists:
            return {"name": "무료", "ai_count": FREE_AI_COUNT}
        data = doc.to_dict()
        plan_id = data.get("plan_id", "free")
        return PLANS.get(plan_id, {"name": "무료", "ai_count": FREE_AI_COUNT})

    # ── 토스페이먼츠 ──────────────────────────────────────────

    def toss_confirm_payment(self, payment_key: str, order_id: str, amount: int) -> dict:
        """토스페이먼츠 결제 승인"""
        url = "https://api.tosspayments.com/v1/payments/confirm"
        secret = base64.b64encode(f"{TOSS_SECRET_KEY}:".encode()).decode()
        headers = {
            "Authorization": f"Basic {secret}",
            "Content-Type": "application/json",
        }
        body = {
            "paymentKey": payment_key,
            "orderId": order_id,
            "amount": amount,
        }
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=10)
            data = resp.json()
            if resp.status_code == 200:
                return {"status": "success", "data": data}
            return {"status": "error", "message": data.get("message", "결제 실패")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ── 카카오페이 ────────────────────────────────────────────

    def kakao_ready_payment(self, uid: str, plan_id: str, order_id: str) -> dict:
        """카카오페이 결제 준비"""
        plan = PLANS.get(plan_id)
        if not plan:
            return {"status": "error", "message": "잘못된 플랜입니다."}

        url = "https://open-api.kakaopay.com/online/v1/payment/ready"
        headers = {
            "Authorization": f"SECRET_KEY {KAKAO_PAY_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "cid": KAKAO_PAY_CLIENT_ID,
            "partner_order_id": order_id,
            "partner_user_id": uid,
            "item_name": f"팜맵 {plan['name']} 플랜",
            "quantity": 1,
            "total_amount": plan["price"],
            "tax_free_amount": 0,
            "approval_url": "http://localhost:3000/payment/success",
            "fail_url": "http://localhost:3000/payment/fail",
            "cancel_url": "http://localhost:3000/payment/cancel",
        }
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=10)
            data = resp.json()
            if resp.status_code == 200:
                return {"status": "success", "data": data}
            return {"status": "error", "message": data.get("msg", "결제 준비 실패")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def kakao_approve_payment(self, uid: str, tid: str, pg_token: str, order_id: str) -> dict:
        """카카오페이 결제 승인"""
        url = "https://open-api.kakaopay.com/online/v1/payment/approve"
        headers = {
            "Authorization": f"SECRET_KEY {KAKAO_PAY_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "cid": KAKAO_PAY_CLIENT_ID,
            "tid": tid,
            "partner_order_id": order_id,
            "partner_user_id": uid,
            "pg_token": pg_token,
        }
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=10)
            data = resp.json()
            if resp.status_code == 200:
                return {"status": "success", "data": data}
            return {"status": "error", "message": data.get("msg", "결제 승인 실패")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def save_subscription(self, uid: str, plan_id: str, payment_data: dict) -> None:
        """결제 완료 후 구독 정보 저장"""
        db.collection("subscriptions").document(uid).set({
            "uid": uid,
            "plan_id": plan_id,
            "payment_data": payment_data,
            "started_at": datetime.now().isoformat(),
        })