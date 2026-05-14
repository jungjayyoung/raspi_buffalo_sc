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
# MQ3 설정
# =========================
MQ3_THRESHOLD = 400
BLOW_DELTA_THRESHOLD = 50
MQ3_SAMPLE_TIME = 5

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
MSG_ACK_READY = "ACK:READY"
MSG_REQ_START = "REQ:START"
MSG_DETECT_ON = "DETECT:ON"
MSG_DETECT_OFF = "DETECT:OFF"

# Raspberry Pi → STM32
MSG_ACK_START = "ACK:START"
MSG_REQ_MQ3 = "REQ:MQ3"
MSG_PASS = "PASS"
MSG_FAIL_DRUNK = "FAIL_DRUNK"
MSG_RETRY = "RETRY"
MSG_IDENTITY_FAIL = "IDENTITY_FAIL"
MSG_ERROR = "ERROR"