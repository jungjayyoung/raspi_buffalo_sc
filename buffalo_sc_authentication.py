import cv2
import numpy as np
import serial
import time
from insightface.app import FaceAnalysis

# =========================
# [추가됨] 인증 설정값
# =========================
AUTH_TIME_LIMIT = 10          # 10초 안에 인증 완료해야 함
REQUIRED_DETECTIONS = 10      # 등록 사용자 검출 10번 이상이면 성공
SAME_THRESHOLD = 0.5          # 동일인 기준

# =========================
# [추가됨] 모델 로드
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
# [추가됨] 저장된 embedding 로드
# =========================
known_embedding = np.load(
    #"/home/willtek/work/umjoocut/known_embedding.npy"
    "known_embedding.npy"
)

print("임베딩 로드 완료")

# =========================
# [추가됨] UART 연결
# =========================
ser = serial.Serial(
    "/dev/serial0",
    115200,
    timeout=1
)

print("UART 연결 완료")
print("등록 사용자 인증 시작")

# =========================
# [추가됨] 코사인 유사도 함수
# =========================
def cosine_similarity(a, b):
    return np.dot(a, b) / (
        np.linalg.norm(a) *
        np.linalg.norm(b)
    )

# =========================
# [추가됨] 웹캠 실행
# =========================
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 15)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# =========================
# [추가됨] 변수 초기화
# =========================
start_time = time.time()
frame_count = 0
success_count = 0
faces = []

auth_result = "face_fail"

# =========================
# [추가됨] 메인 인증 루프
# =========================
while True:

    ret, frame = cap.read()

    if not ret:
        print("카메라 프레임 읽기 실패")
        auth_result = "face_fail"
        break

    frame_count += 1

    elapsed_time = time.time() - start_time

    # =========================
    # [추가됨] 제한 시간 초과 시 인증 실패
    # =========================
    if elapsed_time >= AUTH_TIME_LIMIT:
        print("인증 시간 초과")
        auth_result = "face_fail"
        break

    # =========================
    # [추가됨] AI는 3프레임마다 실행
    # =========================
    if frame_count % 3 == 0:
        faces = app.get(frame)

    max_similarity = 0.0
    detected_registered_user = False

    # =========================
    # [추가됨] 전체 프레임 내 모든 얼굴 검사
    # =========================
    for face in faces:

        embedding = face.embedding

        similarity = cosine_similarity(
            known_embedding,
            embedding
        )

        if similarity > max_similarity:
            max_similarity = similarity

        x1, y1, x2, y2 = face.bbox.astype(int)

        # =========================
        # [추가됨] 등록 사용자 검출
        # =========================
        if similarity >= SAME_THRESHOLD:

            detected_registered_user = True

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Registered {similarity:.2f}",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        else:

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 0, 255),
                2
            )

            cv2.putText(
                frame,
                f"Unknown {similarity:.2f}",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2
            )

    # =========================
    # [추가됨] 등록 사용자 검출 횟수 누적
    # =========================
    if detected_registered_user:
        success_count += 1
        print(f"등록 사용자 검출: {success_count}/{REQUIRED_DETECTIONS}")

    # =========================
    # [추가됨] 성공 조건 만족
    # =========================
    if success_count >= REQUIRED_DETECTIONS:
        print("등록 사용자 인증 성공")
        auth_result = "face_ok"
        break

    # =========================
    # [추가됨] 화면 상태 표시
    # =========================
    cv2.putText(
        frame,
        f"Auth Count: {success_count}/{REQUIRED_DETECTIONS}",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Time: {int(AUTH_TIME_LIMIT - elapsed_time)}",
        (10, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Max Sim: {max_similarity:.2f}",
        (10, 85),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "Authentication",
        frame
    )

    # ESC 종료 시 실패 처리
    if cv2.waitKey(1) == 27:
        print("사용자 종료")
        auth_result = "face_fail"
        break

# =========================
# [추가됨] 인증 결과 UART 전송
# =========================
if auth_result == "face_ok":
    ser.write(b"face_ok\n")
    print("UART: face_ok")
else:
    ser.write(b"face_fail\n")
    print("UART: face_fail")

# =========================
# [추가됨] 종료 처리
# =========================
cap.release()
ser.close()
cv2.destroyAllWindows()

print("등록 사용자 인증 종료")