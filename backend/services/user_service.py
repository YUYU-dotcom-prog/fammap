"""
👤 사용자 데이터 서비스
추천 기록, 즐겨찾기, 농지 위치 저장
"""

from firebase_admin import firestore
from datetime import datetime

db = firestore.client()


class UserService:
    """사용자 데이터 관리 서비스"""

    # ── 추천 기록 ─────────────────────────────────────────────

    def save_recommendation(self, uid: str, location: str, lat: float, lon: float, result: str) -> dict:
        """작물 추천 기록 저장"""
        record = {
            "uid": uid,
            "location": location,
            "lat": lat,
            "lon": lon,
            "result": result,
            "created_at": datetime.now().isoformat(),
        }
        ref = db.collection("recommendations").add(record)
        record["id"] = ref[1].id
        return record

    def get_recommendations(self, uid: str) -> list[dict]:
        """내 추천 기록 목록 조회"""
        docs = (
            db.collection("recommendations")
            .where("uid", "==", uid)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(20)
            .stream()
        )
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]

    def delete_recommendation(self, uid: str, record_id: str) -> bool:
        """추천 기록 삭제"""
        ref = db.collection("recommendations").document(record_id)
        doc = ref.get()
        if not doc.exists or doc.to_dict().get("uid") != uid:
            return False
        ref.delete()
        return True

    # ── 즐겨찾기 ──────────────────────────────────────────────

    def add_favorite(self, uid: str, crop_name: str, location: str) -> dict:
        """즐겨찾기 추가"""
        favorite = {
            "uid": uid,
            "crop_name": crop_name,
            "location": location,
            "created_at": datetime.now().isoformat(),
        }
        ref = db.collection("favorites").add(favorite)
        favorite["id"] = ref[1].id
        return favorite

    def get_favorites(self, uid: str) -> list[dict]:
        """내 즐겨찾기 목록 조회"""
        docs = (
            db.collection("favorites")
            .where("uid", "==", uid)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .stream()
        )
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]

    def delete_favorite(self, uid: str, favorite_id: str) -> bool:
        """즐겨찾기 삭제"""
        ref = db.collection("favorites").document(favorite_id)
        doc = ref.get()
        if not doc.exists or doc.to_dict().get("uid") != uid:
            return False
        ref.delete()
        return True

    # ── 농지 위치 ─────────────────────────────────────────────

    def add_location(self, uid: str, name: str, lat: float, lon: float, address: str = "") -> dict:
        """내 농지 위치 추가"""
        location = {
            "uid": uid,
            "name": name,
            "lat": lat,
            "lon": lon,
            "address": address,
            "created_at": datetime.now().isoformat(),
        }
        ref = db.collection("locations").add(location)
        location["id"] = ref[1].id
        return location

    def get_locations(self, uid: str) -> list[dict]:
        """내 농지 위치 목록 조회"""
        docs = (
            db.collection("locations")
            .where("uid", "==", uid)
            .stream()
        )
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]

    def delete_location(self, uid: str, location_id: str) -> bool:
        """농지 위치 삭제"""
        ref = db.collection("locations").document(location_id)
        doc = ref.get()
        if not doc.exists or doc.to_dict().get("uid") != uid:
            return False
        ref.delete()
        return True
