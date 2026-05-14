# mouth_position_checker.py

import cv2
import numpy as np
import time

from insightface.app import FaceAnalysis

from config import (
    CAMERA_INDEX,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    FPS,
    FACE_MODEL_NAME,
    FACE_PROVIDER,
    FACE_DET_SIZE
)

# =========================
# [추가됨] MQ3 위치 설정
# 화면 기준 좌표
# 필요하면 실제 카메라 화면 보면서 조정
# =========================
MQ3_X = 50
MQ3_Y = 140

# =========================
# [추가됨] 입과 MQ3 거리 기준
# 이 값 이하이면 측정 가능
# =========================
MQ3_DISTANCE_THRESHOLD = 50

# =========================
# [추가됨] 운전자 영역
# 320x240 기준
# =========================
DRIVER_X_MIN = 0
DRIVER_X_MAX = 180

# =========================
# [추가됨] 최소 얼굴 크기
# =========================
MIN_FACE_AREA = 5000

# =========================
# [추가됨] 위치 안정화 시간
# =========================
POSITION_STABLE_TIME = 3.0


class MouthPositionChecker:

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

        # =========================
        # [추가됨] 카메라 연결
        # =========================
        # [수정됨] Windows 로컬 테스트에서 MSMF 오류 방지용
        #self.cap = cv2.VideoCapture(
        #    CAMERA_INDEX,
        #    cv2.CAP_DSHOW
        #)

        #라즈베리파이용
        self.cap = cv2.VideoCapture(
            CAMERA_INDEX
        )

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, FPS)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        print("MouthPositionChecker 준비 완료")

    def check_ready(self):

        # =========================
        # [추가됨] 입-MQ3 위치 확인 메인 루프
        # =========================
        frame_count = 0
        faces = []

        candidate_state = None
        state_start_time = None

        while True:

            ret, frame = self.cap.read()

            if not ret:
                print("카메라 프레임 읽기 실패")
                return False

            frame_count += 1

            # =========================
            # [추가됨] 운전자 영역 표시
            # =========================
            cv2.rectangle(
                frame,
                (DRIVER_X_MIN, 0),
                (DRIVER_X_MAX, FRAME_HEIGHT),
                (255, 255, 0),
                2
            )

            # =========================
            # [추가됨] MQ3 위치 표시
            # =========================
            cv2.circle(
                frame,
                (MQ3_X, MQ3_Y),
                10,
                (0, 255, 255),
                -1
            )

            cv2.putText(
                frame,
                "MQ3",
                (MQ3_X + 12, MQ3_Y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

            # =========================
            # [추가됨] AI는 3프레임마다 실행
            # =========================
            if frame_count % 3 == 0:
                faces = self.app.get(frame)

            current_state = "no_face"
            text = "No Face"
            color = (0, 0, 255)

            if len(faces) > 0:

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

                x1, y1, x2, y2 = face.bbox.astype(int)

                face_center_x = int((x1 + x2) / 2)
                face_area = (x2 - x1) * (y2 - y1)

                # =========================
                # [추가됨] 운전자 영역 확인
                # =========================
                if not (DRIVER_X_MIN <= face_center_x <= DRIVER_X_MAX):

                    current_state = "not_driver"
                    text = "Not Driver Position"
                    color = (128, 128, 128)

                elif face_area < MIN_FACE_AREA:

                    current_state = "small_face"
                    text = "Move Closer"
                    color = (100, 100, 100)

                else:

                    # =========================
                    # [추가됨] 입 위치 계산
                    # InsightFace kps:
                    # 3 = mouth left
                    # 4 = mouth right
                    # =========================
                    kps = face.kps

                    mouth_left = kps[3]
                    mouth_right = kps[4]

                    mouth_x = int((mouth_left[0] + mouth_right[0]) / 2)
                    mouth_y = int((mouth_left[1] + mouth_right[1]) / 2)

                    # =========================
                    # [추가됨] 입-MQ3 거리 계산
                    # =========================
                    distance = np.sqrt(
                        (mouth_x - MQ3_X) ** 2 +
                        (mouth_y - MQ3_Y) ** 2
                    )

                    if distance <= MQ3_DISTANCE_THRESHOLD:

                        current_state = "ready"
                        text = f"READY Dist:{int(distance)}"
                        color = (0, 255, 0)

                    else:

                        current_state = "move_to_mq3"
                        text = f"Move Mouth Dist:{int(distance)}"
                        color = (0, 255, 255)

                    # =========================
                    # [추가됨] 입 위치 표시
                    # =========================
                    cv2.circle(
                        frame,
                        (mouth_x, mouth_y),
                        5,
                        (255, 0, 0),
                        -1
                    )

                    # =========================
                    # [추가됨] 입-MQ3 연결선
                    # =========================
                    cv2.line(
                        frame,
                        (mouth_x, mouth_y),
                        (MQ3_X, MQ3_Y),
                        (255, 255, 0),
                        2
                    )

                    cv2.putText(
                        frame,
                        f"Dist: {int(distance)}",
                        (mouth_x + 10, mouth_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 0),
                        2
                    )

                # =========================
                # [추가됨] 얼굴 박스 표시
                # =========================
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2
                )

                cv2.putText(
                    frame,
                    text,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )

            # =========================
            # [추가됨] 상태 안정화
            # ready 상태가 일정 시간 유지되어야 통과
            # =========================
            if current_state != candidate_state:

                candidate_state = current_state
                state_start_time = time.time()

            else:

                elapsed = time.time() - state_start_time

                if current_state == "ready" and elapsed >= POSITION_STABLE_TIME:

                    print("입-MQ3 위치 확인 완료")

                    cv2.destroyWindow("Mouth Position Check")

                    return True

            # =========================
            # [추가됨] 상태 표시
            # =========================
            cv2.putText(
                frame,
                f"State: {current_state}",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.imshow(
                "Mouth Position Check",
                frame
            )

            # ESC 누르면 실패 처리
            if cv2.waitKey(1) == 27:

                print("입-MQ3 위치 확인 취소")

                cv2.destroyWindow("Mouth Position Check")

                return False

    def release(self):

        # =========================
        # [추가됨] 카메라 종료
        # =========================
        if self.cap is not None:
            self.cap.release()

        cv2.destroyAllWindows()