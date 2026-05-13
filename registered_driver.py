# registered_driver.py

import os
import numpy as np

from config import (
    REGISTERED_EMBEDDING_PATH,
    REGISTERED_MATCH_THRESHOLD
)


class RegisteredDriver:

    def __init__(self):

        # =========================
        # [추가됨] 등록 운전자 embedding 경로
        # =========================
        self.embedding_path = REGISTERED_EMBEDDING_PATH

        # =========================
        # [추가됨] 등록 운전자 embedding 로드
        # =========================
        self.registered_embedding = self.load_embedding()

    def load_embedding(self):

        # =========================
        # [추가됨] 등록 운전자 embedding 파일 확인
        # =========================
        if not os.path.exists(self.embedding_path):

            print("등록 운전자 embedding 파일 없음")
            print(f"경로: {self.embedding_path}")

            return None

        embedding = np.load(
            self.embedding_path
        )

        print("등록 운전자 embedding 로드 완료")

        return embedding

    def cosine_similarity(self, a, b):

        # =========================
        # [추가됨] 코사인 유사도 계산
        # =========================
        return np.dot(a, b) / (
            np.linalg.norm(a) *
            np.linalg.norm(b)
        )

    def check_registered(
        self,
        face_embedding
    ):

        # =========================
        # [추가됨] 등록 embedding 없으면 미등록 처리
        # =========================
        if self.registered_embedding is None:

            return {
                "is_registered": False,
                "similarity": 0.0
            }

        # =========================
        # [추가됨] face_A ↔ 등록 운전자 embedding 비교
        # =========================
        similarity = self.cosine_similarity(
            self.registered_embedding,
            face_embedding
        )

        print(
            f"Registered Similarity: {similarity:.4f}"
        )

        # =========================
        # [추가됨] 등록 운전자 여부 판단
        # =========================
        is_registered = (
            similarity >=
            REGISTERED_MATCH_THRESHOLD
        )

        return {
            "is_registered": is_registered,
            "similarity": similarity
        }