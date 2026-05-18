# config.py

# =========================
# UART 설정
# =========================
UART_PORT = "/dev/serial0"
UART_BAUDRATE = 115200
UART_TIMEOUT = 1

# =========================
# 카메라 설정
# =========================
CAMERA_INDEX = 0
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
FPS = 15

# =========================
# InsightFace 모델 설정
# =========================
FACE_MODEL_NAME = "buffalo_sc"
FACE_PROVIDER = ["CPUExecutionProvider"]
FACE_DET_SIZE = (320, 320)

# =========================
# [수정됨] 세션 본인 검증 Threshold
# face_A 평균 embedding ↔ face_B 비교
# =========================
IDENTITY_VERIFY_THRESHOLD = 0.5

# =========================
# [추가됨] 세션 얼굴 촬영 개수
# 등록 운전자가 아닌 경우에도 1~3장 촬영해서 임시 embedding 생성
# =========================
SESSION_FACE_CAPTURE_COUNT = 3

# =========================
# MQ3 측정 설정
# =========================

# baseline 측정 시간
# BLOW_START 이후 처음 1초 동안 기준값 측정
MQ3_BASELINE_TIME = 1.0

# 실제 음주 측정 시간
# baseline 이후 4초 동안 측정값 수집
MQ3_MEASURE_TIME = 4.0

# MQ3 샘플링 간격
# STM32가 100ms마다 MQ3 값을 송신한다고 가정
MQ3_SAMPLE_INTERVAL = 0.1

# baseline 샘플 개수
# 1초 / 0.1초 = 10개
MQ3_BASELINE_SAMPLE_COUNT = 10

# 측정 샘플 개수
# 4초 / 0.1초 = 40개
MQ3_MEASURE_SAMPLE_COUNT = 40

# 최종 음주 판정 기준
# delta = peak - baseline
# delta >= 500 이면 음주 판정
MQ3_DRUNK_DELTA_THRESHOLD = 500   # 음주 판정 기준
MQ3_BLOW_DELTA_THRESHOLD = 50     # MQ3 호흡 감지 최소 변화량
HUM_BLOW_DELTA_THRESHOLD = 3.0    # 습도 호흡 감지 최소 변화량(%)

# =========================
# 재측정 정책
# =========================
MAX_RETRY = 3
RETRY_DELAY = 30


# =========================
# [수정됨] DB 경로
# 기존 history_embeddings.npy / history_metadata.json 제거
# =========================
DB_DIR = "db"
REGISTERED_EMBEDDING_PATH = "db/known_embedding.npy"

# =========================
# 로그 경로
# =========================
LOG_DIR = "logs"
TEMP_DIR = "logs/temp"



# =========================
# [수정됨] 이력자/비이력자 → 등록/미등록 운전자 기준
# =========================
REGISTERED_NORMAL_DIR = "logs/registered/normal"
REGISTERED_DRUNK_DIR = "logs/registered/drunk"

REGISTERED_MATCH_THRESHOLD = 0.5

UNREGISTERED_NORMAL_DIR = "logs/unregistered/normal"
UNREGISTERED_DRUNK_DIR = "logs/unregistered/drunk"

IDENTITY_FAIL_DIR = "logs/identity_fail"
SYSTEM_LOG_PATH = "logs/system.log"


# =========================
# [추가됨] 세션 임시 embedding 저장 경로
# =========================
SESSION_EMBEDDING_PATH = "logs/temp/session_embedding.npy"


# =========================
# [추가됨] 로컬 테스트 모드
# =========================
USE_UART = False


# =========================
# UART 메시지
# =========================


# STM32 → Raspberry Pi

# STM32 시스템 시작 완료
MSG_SYSTEM_START = "SYSTEM_START"

# 운전석 감지 ON
MSG_SEAT_ON = "SEAT_ON"

# 운전석 감지 OFF
MSG_SEAT_OFF = "SEAT_OFF"

# BLOW 버튼 눌림
# STM32가 MQ3 스트리밍 시작 전에 Pi에 알림
MSG_BLOW_START = "BLOW_START"

# MQ3 측정 시작
# 이후 MQ3:<value> 메시지가 연속 수신됨
MSG_MEASURE_BEGIN = "MEASURE_BEGIN"

# MQ3 측정 종료
# Pi는 이 시점까지 받은 MQ3 값으로 baseline/peak/delta 계산
MSG_MEASURE_END = "MEASURE_END"

# MQ3 센서값 prefix
# 예: MQ3:1234
MSG_MQ3_PREFIX = "MQ3:"

# Raspberry Pi → STM32


# Raspberry Pi가 시퀀스를 시작하겠다는 응답
MSG_ACK_START = "ACK:START"

# MQ3 측정 시작 요청
# 얼굴 인증 및 위치 검증 완료 후 전송
# STM32는 이 메시지를 받으면 MQ3 측정 시작
MSG_REQ_MQ3 = "REQ:MQ3"

# 최종 정상 통과
# STM32는 릴레이 ON / Green LED 처리
MSG_PASS = "PASS"

# 최종 실패
# STM32는 릴레이 OFF / Red LED / Buzzer 처리
MSG_FAIL = "FAIL"

# 재측정 요청
MSG_RETRY = "RETRY"

# 오류 발생
MSG_ERROR = "ERROR"
