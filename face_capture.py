# face_capture.py

import cv2
import os
from datetime import datetime
import time

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
        # 카메라 연결
        # =========================        
        self.cap = cv2.VideoCapture(
            CAMERA_INDEX
        )

        time.sleep(2)

        if not self.cap.isOpened():

            print("=" * 50)
            print("[ERROR] 카메라 연결 실패")
            print("[EXIT] 프로그램을 종료합니다")
            print("=" * 50)

            raise Exception("카메라 연결 실패")

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
    
    def is_face_parts_visible(self, face, frame_width, frame_height, margin=5):

        if not hasattr(face, "kps") or face.kps is None:
            return False

        kps = face.kps

        if len(kps) < 5:
            return False

        for x, y in kps:
            if x < margin or y < margin:
                return False

            if x > frame_width - margin or y > frame_height - margin:
                return False

        return True

    def capture_face(
        self,
        label="face"
    ):

        # =========================
        # 얼굴 인증 간격 제한
        # =========================
        if not hasattr(self, "last_capture_time"):
            self.last_capture_time = 0

        CAPTURE_INTERVAL = 1.0

        while True:

            ret, frame = self.cap.read()

            if not ret:

                print("=" * 50)
                print("[ERROR] 카메라 프레임 읽기 실패")
                print("[EXIT] 프로그램을 종료합니다")
                print("=" * 50)

                raise Exception("카메라 프레임 읽기 실패")

            cv2.imshow("Driver Camera", frame)
            cv2.waitKey(1)

            now = time.time()

            if now - self.last_capture_time < CAPTURE_INTERVAL:
                continue

            self.last_capture_time = now

            break

        # =========================
        # [추가됨] 얼굴 탐지
        # =========================
        faces = self.app.get(frame)

        if len(faces) == 0:
            cv2.putText(
                frame,
                "NO FACE",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 0, 255),
                3
            )

            cv2.imshow("Driver Camera", frame)
            cv2.waitKey(1)

            return None, None, None
        
        print("얼굴 검출 성공")

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

        height, width = frame.shape[:2]

        if not self.is_face_parts_visible(face, width, height):
            print("[RETRY] 눈, 코, 입이 모두 보이도록 정면을 봐주세요")
            return None, None, None
        

        # =========================
        # [수정됨] 얼굴 박스 좌표 추출
        # =========================
        x1, y1, x2, y2 = face.bbox.astype(int)

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "AUTHENTICATING...",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2
        )

        cv2.imshow("Driver Camera", frame)
        cv2.waitKey(1)


        embedding = face.embedding

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


    def preview(self, duration=5):


        print("카메라 준비 중...")

        start_time = time.time()
        last_remain = None

        while time.time() - start_time < duration:

            ret, frame = self.cap.read()
            
            if not ret:
                print("카메라 읽기 실패")
                continue

            # 남은 시간 표시
            remain = int(duration - (time.time() - start_time)) + 1

            if remain != last_remain:
                print(f"{remain}초 후 얼굴 인증 시작")
                last_remain = remain

            # 비디오 출력 영상 세팅
            h, w, _ = frame.shape

            text = f"{remain}"

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 5
            thickness = 8

            (text_w, text_h), _ = cv2.getTextSize(
                text,
                font,
                font_scale,
                thickness
            )

            x = (w - text_w) // 2
            y = (h + text_h) // 2

            cv2.putText(
                frame,
                text,
                (x, y),
                font,
                font_scale,
                (0,255,0),
                thickness
            )

            cv2.imshow("Driver Camera", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        print("얼굴을 인증합니다")