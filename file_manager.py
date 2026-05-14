# file_manager.py

import os
import shutil
from datetime import datetime

from config import (
    TEMP_DIR,
    REGISTERED_NORMAL_DIR,
    REGISTERED_DRUNK_DIR,
    UNREGISTERED_NORMAL_DIR,
    UNREGISTERED_DRUNK_DIR,
    IDENTITY_FAIL_DIR
)


class FileManager:

    def __init__(self):

        # =========================
        # [수정됨] 새 로그 폴더 구조 생성
        # 기존 history/non_history → registered/unregistered
        # =========================
        os.makedirs(TEMP_DIR, exist_ok=True)

        os.makedirs(REGISTERED_NORMAL_DIR, exist_ok=True)
        os.makedirs(REGISTERED_DRUNK_DIR, exist_ok=True)

        os.makedirs(UNREGISTERED_NORMAL_DIR, exist_ok=True)
        os.makedirs(UNREGISTERED_DRUNK_DIR, exist_ok=True)

        os.makedirs(IDENTITY_FAIL_DIR, exist_ok=True)

    def get_timestamp(self):

        # =========================
        # [추가됨] 파일명용 시간 문자열
        # =========================
        return datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

    def move_file(self, src_path, dst_dir, filename):

        # =========================
        # [추가됨] 파일 이동 공통 함수
        # =========================
        if src_path is None:
            return None

        if not os.path.exists(src_path):
            print(f"[파일 없음] {src_path}")
            return None

        os.makedirs(dst_dir, exist_ok=True)

        dst_path = os.path.join(
            dst_dir,
            filename
        )

        shutil.move(
            src_path,
            dst_path
        )

        print(f"[저장 완료] {dst_path}")

        return dst_path

    def save_registered_normal(self, image_path):

        # =========================
        # [수정됨] 등록 운전자 정상 저장
        # 기존 save_history_normal 대체
        # =========================
        timestamp = self.get_timestamp()

        return self.move_file(
            image_path,
            REGISTERED_NORMAL_DIR,
            f"{timestamp}_registered_normal.jpg"
        )

    def save_registered_drunk(self, image_path):

        # =========================
        # [수정됨] 등록 운전자 음주 저장
        # 기존 save_history_drunk 대체
        # =========================
        timestamp = self.get_timestamp()

        return self.move_file(
            image_path,
            REGISTERED_DRUNK_DIR,
            f"{timestamp}_registered_drunk.jpg"
        )

    def save_unregistered_normal(self, image_path):

        # =========================
        # [추가됨] 미등록 운전자 정상 저장
        # 저장이 부담되면 나중에 delete_temp_file로 바꿔도 됨
        # =========================
        timestamp = self.get_timestamp()

        return self.move_file(
            image_path,
            UNREGISTERED_NORMAL_DIR,
            f"{timestamp}_unregistered_normal.jpg"
        )

    def save_unregistered_drunk(self, image_path):

        # =========================
        # [수정됨] 미등록 운전자 음주 저장
        # 기존 save_non_history_drunk 대체
        # =========================
        timestamp = self.get_timestamp()

        return self.move_file(
            image_path,
            UNREGISTERED_DRUNK_DIR,
            f"{timestamp}_unregistered_drunk.jpg"
        )

    def save_identity_fail(self, face_a_path, face_b_path):

        # =========================
        # [수정됨] 본인 검증 실패 저장
        # face_A / face_B 모두 저장
        # =========================
        timestamp = self.get_timestamp()

        saved_a = self.move_file(
            face_a_path,
            IDENTITY_FAIL_DIR,
            f"{timestamp}_identity_fail_face_A.jpg"
        )

        saved_b = self.move_file(
            face_b_path,
            IDENTITY_FAIL_DIR,
            f"{timestamp}_identity_fail_face_B.jpg"
        )

        print("[저장 완료] Identity Fail")

        return saved_a, saved_b

    def delete_temp_file(self, image_path):

        # =========================
        # [추가됨] temp 이미지 삭제
        # =========================
        if image_path is None:
            return

        if os.path.exists(image_path):

            os.remove(image_path)

            print(f"[삭제 완료] {image_path}")