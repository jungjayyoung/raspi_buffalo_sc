import cv2
import numpy as np
import serial
import time
from insightface.app import FaceAnalysis

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
# 저장된 embedding 로드
# =========================
known_embedding = np.load(
    "/home/willtek/work/umjoocut/known_embedding.npy"
)

print("임베딩 로드 완료")

# =========================
# UART 연결
# =========================
ser = serial.Serial(
    '/dev/serial0',
    115200,
    timeout=1
)

print("UART 연결 완료")
print("운전자 위치 확인 시작")

# =========================
# 코사인 유사도 함수
# =========================
def cosine_similarity(a, b):

    return np.dot(a, b) / (
        np.linalg.norm(a) *
        np.linalg.norm(b)
    )

# =========================
# MQ3 위치
# =========================
MQ3_X = 50
MQ3_Y = 140

# 입과 MQ3 거리 기준
MQ3_DISTANCE_THRESHOLD = 20

# =========================
# 얼굴 Threshold
# =========================
# 동일인 기준
SAME_THRESHOLD = 0.5

# 확실한 타인 기준
OTHER_THRESHOLD = 0.35

# =========================
# 운전자 영역
# =========================
# 320x240 기준
DRIVER_X_MIN = 0
DRIVER_X_MAX = 180

# =========================
# 최소 얼굴 크기
# =========================
MIN_FACE_AREA = 5000

# =========================
# 상태 안정화 시간
# =========================
STATE_DELAY = 5.0

# =========================
# 웹캠 실행
# =========================
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 15)

# =========================
# 변수 초기화
# =========================
frame_count = 0
last_state = ""

state_start_time = None
candidate_state = None

no_face_count = 0

faces = []

# =========================
# 메인 루프
# =========================
while True:

    ret, frame = cap.read()

    if not ret:
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
    # AI는 3프레임마다 실행
    # =========================
    if frame_count % 3 == 0:

        faces = app.get(frame)

    # =========================
    # 얼굴 없음
    # =========================
    if len(faces) == 0:

        no_face_count += 1

        if no_face_count > 10:

            current_state = "no_face"

            if current_state != candidate_state:

                candidate_state = current_state
                state_start_time = time.time()

            else:

                elapsed = time.time() - state_start_time

                if elapsed >= STATE_DELAY:

                    if last_state != "no_face":

                        ser.write(b"no_face\n")
                        print("UART: no_face")

                        last_state = "no_face"

        # MQ3 표시
        cv2.circle(
            frame,
            (MQ3_X, MQ3_Y),
            10,
            (0, 255, 255),
            -1
        )

        cv2.imshow("Face Compare", frame)

        if cv2.waitKey(1) == 27:
            break

        continue

    # =========================
    # 얼굴 있으면 카운트 초기화
    # =========================
    no_face_count = 0

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

    # 얼굴 박스
    box = face.bbox.astype(int)

    x1, y1, x2, y2 = box

    # =========================
    # 얼굴 중심 좌표
    # =========================
    face_center_x = int((x1 + x2) / 2)

    # =========================
    # 운전자 영역 밖 무시
    # =========================
    if not (DRIVER_X_MIN <= face_center_x <= DRIVER_X_MAX):

        cv2.putText(
            frame,
            "Ignored (Not Driver)",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (128, 128, 128),
            2
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (128, 128, 128),
            2
        )

        cv2.imshow("Face Compare", frame)

        if cv2.waitKey(1) == 27:
            break

        continue

    # =========================
    # 얼굴 크기 계산
    # =========================
    face_area = (
        (x2 - x1) *
        (y2 - y1)
    )

    # =========================
    # 작은 얼굴 무시
    # =========================
    if face_area < MIN_FACE_AREA:

        cv2.putText(
            frame,
            "Ignored (Small Face)",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (100, 100, 100),
            2
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (100, 100, 100),
            2
        )

        cv2.imshow("Face Compare", frame)

        if cv2.waitKey(1) == 27:
            break

        continue

    # =========================
    # 임베딩 비교
    # =========================
    embedding = face.embedding

    similarity = cosine_similarity(
        known_embedding,
        embedding
    )

    # =========================
    # 얼굴 Keypoints
    # =========================
    kps = face.kps

    mouth_left = kps[3]
    mouth_right = kps[4]

    mouth_x = int(
        (mouth_left[0] + mouth_right[0]) / 2
    )

    mouth_y = int(
        (mouth_left[1] + mouth_right[1]) / 2
    )

    # =========================
    # MQ3 거리 계산
    # =========================
    distance = np.sqrt(
        (mouth_x - MQ3_X) ** 2 +
        (mouth_y - MQ3_Y) ** 2
    )

    # =========================
    # 상태 판별
    # =========================
    current_state = None

    # SAME
    if similarity >= SAME_THRESHOLD:

        if distance < MQ3_DISTANCE_THRESHOLD:

            current_state = "start_mq3"

            text = f"Same + MQ3 ({similarity:.2f})"
            color = (0, 255, 0)

        else:

            current_state = "waiting"

            text = f"Same but far ({similarity:.2f})"
            color = (0, 255, 255)

    # UNKNOWN
    elif similarity >= OTHER_THRESHOLD:

        current_state = "unknown"

        text = f"Unknown ({similarity:.2f})"
        color = (255, 165, 0)

    # OTHERS
    else:

        current_state = "others"

        text = f"Different ({similarity:.2f})"
        color = (0, 0, 255)

    # =========================
    # 상태 안정화
    # =========================
    if current_state != candidate_state:

        candidate_state = current_state
        state_start_time = time.time()

    else:

        elapsed = time.time() - state_start_time

        if elapsed >= STATE_DELAY:

            # MQ3 시작
            if candidate_state == "start_mq3":

                if last_state != "start_mq3":

                    ser.write(b"start_mq3\n")
                    print("UART: start_mq3")

                    last_state = "start_mq3"

            # 타인
            elif candidate_state == "others":

                if last_state != "others":

                    ser.write(b"others\n")
                    print("UART: others")

                    last_state = "others"

            # 얼굴 없음
            elif candidate_state == "no_face":

                if last_state != "no_face":

                    ser.write(b"no_face\n")
                    print("UART: no_face")

                    last_state = "no_face"

    # =========================
    # 얼굴 박스
    # =========================
    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        color,
        2
    )

    # =========================
    # 텍스트 출력
    # =========================
    cv2.putText(
        frame,
        text,
        (x1, y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2
    )

    # =========================
    # 입 위치
    # =========================
    cv2.circle(
        frame,
        (mouth_x, mouth_y),
        5,
        (255, 0, 0),
        -1
    )

    # =========================
    # MQ3 위치
    # =========================
    cv2.circle(
        frame,
        (MQ3_X, MQ3_Y),
        10,
        (0, 255, 255),
        -1
    )

    # =========================
    # 연결선
    # =========================
    cv2.line(
        frame,
        (mouth_x, mouth_y),
        (MQ3_X, MQ3_Y),
        (255, 255, 0),
        2
    )

    # =========================
    # 거리 출력
    # =========================
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
    # 상태 출력
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

    # =========================
    # similarity 출력
    # =========================
    cv2.putText(
        frame,
        f"Sim: {similarity:.2f}",
        (10, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # =========================
    # 얼굴 크기 출력
    # =========================
    cv2.putText(
        frame,
        f"Area: {face_area}",
        (10, 85),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # =========================
    # 화면 출력
    # =========================
    cv2.imshow(
        "Face Compare",
        frame
    )

    # ESC 종료
    if cv2.waitKey(1) == 27:
        break

# =========================
# 종료 처리
# =========================
cap.release()

ser.close()

cv2.destroyAllWindows()