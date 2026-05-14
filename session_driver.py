# session_driver.py

import os
import numpy as np

from config import (
    SESSION_EMBEDDING_PATH,
    IDENTITY_VERIFY_THRESHOLD
)


class SessionDriver:

    def __init__(self):

        # =========================
        # [추가됨] 세션 embedding 저장 경로
        # =========================
        self.session_embedding_path = SESSION_EMBEDDING_PATH

    def cosine_similarity(self, a, b):

        # =========================
        # [추가됨] 코사인 유사도 계산
        # =========================
        return np.dot(a, b) / (
            np.linalg.norm(a) *
            np.linalg.norm(b)
        )

    def create_session_embedding(
        self,
        embeddings
    ):

        # =========================
        # [추가됨] face_A 1~3장 embedding 평균 생성
        # =========================
        if len(embeddings) == 0:

            print("세션 embedding 생성 실패: embedding 없음")

            return None

        session_embedding = np.mean(
            embeddings,
            axis=0
        )

        # =========================
        # [추가됨] temp 폴더 자동 생성
        # =========================
        os.makedirs(
            os.path.dirname(self.session_embedding_path),
            exist_ok=True
        )

        # =========================
        # [추가됨] session_embedding.npy 저장
        # =========================
        np.save(
            self.session_embedding_path,
            session_embedding
        )

        print("세션 embedding 저장 완료")

        return session_embedding

    def load_session_embedding(self):

        # =========================
        # [추가됨] 세션 embedding 로드
        # =========================
        if not os.path.exists(self.session_embedding_path):

            print("세션 embedding 파일 없음")

            return None

        return np.load(
            self.session_embedding_path
        )

    def verify_current_driver(
        self,
        current_embedding,
        session_embedding=None
    ):

        # =========================
        # [추가됨] session_embedding 미전달 시 파일에서 로드
        # =========================
        if session_embedding is None:

            session_embedding = self.load_session_embedding()

        if session_embedding is None:

            return {
                "is_same_person": False,
                "similarity": 0.0
            }

        # =========================
        # [추가됨] 현재 운전자 ↔ 세션 측정자 비교
        # =========================
        similarity = self.cosine_similarity(
            session_embedding,
            current_embedding
        )

        print(
            f"Session Identity Similarity: {similarity:.4f}"
        )

        print(f"[IDENTITY] threshold: {IDENTITY_VERIFY_THRESHOLD}")

        is_same_person = (
            similarity >=
            IDENTITY_VERIFY_THRESHOLD
        )

        return {
            "is_same_person": is_same_person,
            "similarity": similarity
        }