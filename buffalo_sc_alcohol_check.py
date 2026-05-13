import cv2
import numpy as np
import serial
import time
from insightface.app import FaceAnalysis



# =========================
# [추가됨] 로컬 테스트 여부
# =========================
USE_UART = False

# =========================
# 모델 로드
# =========================
app = FaceAnalysis(
    name='buffalo_sc',
    providers=['CPUExecutionProvider']
)

app.prepare(
    ctx_id=0,
    det_size=(320, 320)
)

# =========================
# UART 연결
# =========================
if USE_UART:

    ser = serial.Serial(
        '/dev/serial0',
        115200,
        timeout=1
    )

    print("UART 연결 완료")

else:

    ser = None
    print("UART 비활성화 (로컬 테스트 모드)")

print("UART 연결 완료")
print("운전자 위치 확인 시작")

# =========================
# MQ3 위치
# =========================
MQ3_X = 50
MQ3_Y = 140

MQ3_DISTANCE_THRESHOLD = 20

# =========================
# 운전자 영역
# 320x240 기준
# =========================
DRIVER_X_MIN = 0
DRIVER_X_MAX = 180

# =========================
# 최소 얼굴 크기
# =========================
MIN_FACE_AREA = 5000

# =========================
# 상태 안정화 시간
# =========================
STATE_DELAY = 3.0

# =========================
# 웹캠 실행
# =========================
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 15)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# =========================
# 변수 초기화
# =========================
frame_count = 0
faces = []

candidate_state = None
state_start_time = None

last_sent_state = None

# =========================
# 메인 루프
# =========================
while True:

    ret, frame = cap.read()

    if not ret:
        print("카메라 프레임 읽기 실패")
        break

    frame_count += 1

    # =========================
    # 운전자 영역 표시
    # =========================
    cv2.rectangle(
        frame,
        (DRIVER_X_MIN, 0),
        (DRIVER_X_MAX, 240),
        (255, 255, 0),
        2
    )

    # =========================
    # MQ3 위치 표시
    # =========================
    cv2.circle(
        frame,
        (MQ3_X, MQ3_Y),
        10,
        (0, 255, 255),
        -1
    )

    # =========================
    # AI는 3프레임마다 실행
    # =========================
    if frame_count % 3 == 0:
        faces = app.get(frame)

    current_state = "waiting"
    text = "Waiting driver position"
    color = (255, 255, 255)

    # =========================
    # 얼굴 없음
    # =========================
    if len(faces) == 0:

        current_state = "no_face"
        text = "No Face"
        color = (0, 0, 255)

    else:
        # =========================
        # 가장 큰 얼굴 선택
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
        # 운전자 영역 밖
        # =========================
        if not (DRIVER_X_MIN <= face_center_x <= DRIVER_X_MAX):

            current_state = "not_driver"
            text = "Not Driver Position"
            color = (128, 128, 128)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

        # =========================
        # 얼굴이 너무 작음
        # =========================
        elif face_area < MIN_FACE_AREA:

            current_state = "small_face"
            text = "Move Closer"
            color = (100, 100, 100)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

        else:
            # =========================
            # 입 위치 계산
            # insightface kps:
            # 3 = mouth left
            # 4 = mouth right
            # =========================
            kps = face.kps

            mouth_left = kps[3]
            mouth_right = kps[4]

            mouth_x = int((mouth_left[0] + mouth_right[0]) / 2)
            mouth_y = int((mouth_left[1] + mouth_right[1]) / 2)

            # =========================
            # MQ3와 입 거리 계산
            # =========================
            distance = np.sqrt(
                (mouth_x - MQ3_X) ** 2 +
                (mouth_y - MQ3_Y) ** 2
            )

            if distance <= MQ3_DISTANCE_THRESHOLD:

                current_state = "start_mq3"
                text = f"MQ3 Ready Dist:{int(distance)}"
                color = (0, 255, 0)

            else:

                current_state = "waiting"
                text = f"Move mouth to MQ3 Dist:{int(distance)}"
                color = (0, 255, 255)

            # 얼굴 박스
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            # 입 위치
            cv2.circle(
                frame,
                (mouth_x, mouth_y),
                5,
                (255, 0, 0),
                -1
            )

            # 입 - MQ3 연결선
            cv2.line(
                frame,
                (mouth_x, mouth_y),
                (MQ3_X, MQ3_Y),
                (255, 255, 0),
                2
            )

            # 거리 출력
            cv2.putText(
                frame,
                f"Dist: {int(distance)}",
                (mouth_x + 10, mouth_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
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
    # 상태 안정화
    # =========================
    if current_state != candidate_state:

        candidate_state = current_state
        state_start_time = time.time()

    else:

        elapsed = time.time() - state_start_time

        if elapsed >= STATE_DELAY:

            if candidate_state == "start_mq3":

                if last_sent_state != "start_mq3":

                    # =========================
                    # [수정됨] UART 전송
                    # =========================
                    if USE_UART:
                        ser.write(b"start_mq3\n")

                    print("UART: start_mq3")

                    last_sent_state = "start_mq3"

                    break

    # =========================
    # 현재 상태 출력
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
        "Alcohol Check",
        frame
    )

    # ESC 종료
    if cv2.waitKey(1) == 27:
        break

# =========================
# 종료 처리
# =========================
cap.release()
# =========================
# [수정됨] UART 종료
# =========================
if ser is not None:
    ser.close()
cv2.destroyAllWindows()

print("알코올 위치 확인 종료")