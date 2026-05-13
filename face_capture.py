# face_capture.py

import cv2
import os
from datetime import datetime

from insightface.app import FaceAnalysis

from config import (
    CAMERA_INDEX,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    FPS,
    FACE_MODEL_NAME,
    FACE_PROVIDER,
    FACE_DET_SIZE,
    TEMP_DIR
)


class FaceCapture:

    def __init__(self):

        # =========================
        # [추가됨] InsightFace 모델 로드
        # =========================
        self.app = FaceAnalysis(
            name=FACE_MODEL_NAME,
            providers=FACE_PROVIDER
        )

        self.app.prepare(
            ctx_id=0,
            det_size=FACE_DET_SIZE
        )

        print("Face Model 로드 완료")

        # =========================
        # [추가됨] 카메라 연결
        # =========================
        # [수정됨] Windows 로컬 테스트에서 MSMF 오류 방지용
        self.cap = cv2.VideoCapture(
            CAMERA_INDEX,
            cv2.CAP_DSHOW
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            FRAME_WIDTH
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            FRAME_HEIGHT
        )

        self.cap.set(
            cv2.CAP_PROP_FPS,
            FPS
        )

        self.cap.set(
            cv2.CAP_PROP_BUFFERSIZE,
            1
        )

        print("카메라 연결 완료")

        # =========================
        # [추가됨] temp 폴더 생성
        # =========================
        os.makedirs(
            TEMP_DIR,
            exist_ok=True
        )

    def get_timestamp(self):

        # =========================
        # [추가됨] 파일명용 시간 문자열
        # =========================
        return datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

    def capture_face(
        self,
        label="face"
    ):

        # =========================
        # [추가됨] 프레임 읽기
        # =========================
        ret, frame = self.cap.read()

        if not ret:

            print("카메라 프레임 읽기 실패")

            return None, None, None

        # =========================
        # [추가됨] 얼굴 탐지
        # =========================
        faces = self.app.get(frame)

        if len(faces) == 0:

            print("얼굴 검출 실패")

            return None, None, None

        # =========================
        # [추가됨] 가장 큰 얼굴 선택
        # =========================
        face = max(
            faces,
            key=lambda f: (
                (f.bbox[2] - f.bbox[0]) *
                (f.bbox[3] - f.bbox[1])
            )
        )

        embedding = face.embedding

        # =========================
        # [수정됨] 얼굴 박스 좌표 추출
        # =========================
        x1, y1, x2, y2 = face.bbox.astype(int)

        # =========================
        # [추가됨] 얼굴 박스 좌표 화면 범위 보정
        # 얼굴 박스가 화면 밖으로 나가면 crop 이미지가 비어질 수 있어서 보정
        # =========================
        height, width = frame.shape[:2]

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(width, x2)
        y2 = min(height, y2)

        # =========================
        # [추가됨] 잘못된 crop 영역 방지
        # =========================
        if x2 <= x1 or y2 <= y1:

            print("얼굴 crop 영역 오류")

            return None, None, None

        # =========================
        # [수정됨] 보정된 좌표로 얼굴 Crop
        # =========================
        face_crop = frame[y1:y2, x1:x2]

        timestamp = self.get_timestamp()

        image_path = os.path.join(
            TEMP_DIR,
            f"{timestamp}_{label}.jpg"
        )

        # =========================
        # [추가됨] 이미지 저장
        # =========================
        cv2.imwrite(
            image_path,
            face_crop
        )

        print(f"얼굴 저장 완료: {image_path}")

        return (
            image_path,
            embedding,
            face_crop
        )

    def release(self):

        # =========================
        # [추가됨] 카메라 종료
        # =========================
        if self.cap is not None:

            self.cap.release()

            print("카메라 종료")

        cv2.destroyAllWindows()