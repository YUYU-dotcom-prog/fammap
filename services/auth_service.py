"""
🔐 Firebase 인증 서비스
회원가입, 로그인, 구글 로그인, 토큰 검증
"""

import firebase_admin
from firebase_admin import credentials, auth, firestore
from core.config import FIREBASE_KEY_PATH
from datetime import datetime

# Firebase 초기화 (한 번만 실행)
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()


class AuthService:
    """Firebase 인증 서비스"""

    def verify_token(self, id_token: str) -> dict | None:
        """
        프론트엔드에서 받은 Firebase ID 토큰 검증
        → 유효하면 사용자 정보 반환
        """
        try:
            decoded = auth.verify_id_token(id_token)
            return {
                "uid": decoded["uid"],
                "email": decoded.get("email"),
                "name": decoded.get("name"),
                "picture": decoded.get("picture"),
            }
        except Exception as e:
            print(f"토큰 검증 실패: {e}")
            return None

    def get_or_create_user(self, uid: str, email: str, name: str = None, picture: str = None) -> dict:
        """
        Firestore에 사용자 정보 저장 (없으면 생성, 있으면 조회)
        """
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()

        if user_doc.exists:
            return user_doc.to_dict()

        # 신규 사용자 생성
        user_data = {
            "uid": uid,
            "email": email,
            "name": name or "",
            "picture": picture or "",
            "created_at": datetime.now().isoformat(),
            "locations": [],  # 내 농지 위치 목록
        }
        user_ref.set(user_data)
        return user_data

    def get_user(self, uid: str) -> dict | None:
        """사용자 정보 조회"""
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        return user_doc.to_dict() if user_doc.exists else None
