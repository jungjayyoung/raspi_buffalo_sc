import serial
import subprocess
import time

# =========================
# [추가됨] UART 설정
# =========================
UART_PORT = "/dev/serial0"
UART_BAUDRATE = 115200

# =========================
# [추가됨] MQ3 임시 기준값
# =========================
MQ3_THRESHOLD = 400       # 음주 판단 기준
BLOW_DELTA_THRESHOLD = 50 # 실제로 불었는지 판단하는 변화량 기준
MQ3_SAMPLE_TIME = 5       # 5초 동안 MQ3 값 수집

# =========================
# [추가됨] MQ3 값 여러 개 수집
# =========================
def collect_mq3_values(sample_time=MQ3_SAMPLE_TIME):
    values = []

    start_time = time.time()

    with serial.Serial(UART_PORT, UART_BAUDRATE, timeout=1) as ser:

        while time.time() - start_time < sample_time:

            line = ser.readline().decode(errors="ignore").strip()

            if not line:
                continue

            print(f"STM32 → Pi: {line}")

            if line.startswith("MQ3:"):

                try:
                    value = int(line.split(":")[1])
                    values.append(value)

                except ValueError:
                    print("MQ3 값 변환 실패")

    return values


# =========================
# [추가됨] UART 한 줄 읽기
# =========================
def read_uart_line():
    with serial.Serial(UART_PORT, UART_BAUDRATE, timeout=1) as ser:
        while True:
            line = ser.readline().decode(errors="ignore").strip()

            if line:
                print(f"STM32 → Pi: {line}")
                return line


# =========================
# [추가됨] UART 한 줄 전송
# =========================
def send_uart_message(message):
    with serial.Serial(UART_PORT, UART_BAUDRATE, timeout=1) as ser:
        ser.write((message + "\n").encode())
        print(f"Pi → STM32: {message}")


# =========================
# [추가됨] 파이썬 파일 실행 후 출력 확인
# =========================
def run_python_file(filename, success_keyword):
    process = subprocess.Popen(
        ["python3", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    success = False

    for line in process.stdout:
        print(line, end="")

        if success_keyword in line:
            success = True

    process.wait()

    return success


# =========================
# [추가됨] 메인 시스템 루프
# =========================
while True:

    print("시스템 대기 중... STM32 READY 대기")

    # =========================
    # [추가됨] STM32 READY 수신 대기
    # =========================
    line = read_uart_line()

    if line != "READY":
        continue

    print("READY 수신 완료")
    print("등록 사용자 인증 시작")

    # =========================
    # [추가됨] 얼굴 인증 실행
    # =========================
    auth_ok = run_python_file(
        "buffalo_sc_authentication.py",
        "UART: face_ok"
    )

    # =========================
    # [추가됨] 인증 실패 처리
    # =========================
    if not auth_ok:
        print("인증 실패")
        send_uart_message("face_fail")
        continue

    print("인증 성공")
    print("운전자 음주 검사 위치 확인 시작")

    # =========================
    # [추가됨] 알코올 체크 위치 확인 실행
    # =========================
    alcohol_ready = run_python_file(
        "buffalo_sc_alcohol_check.py",
        "UART: start_mq3"
    )

    # =========================
    # [추가됨] MQ3 시작 실패 처리
    # =========================
    if not alcohol_ready:
        print("MQ3 측정 시작 실패")
        send_uart_message("BLOCK")
        continue

    print("MQ3 측정 시작 요청 완료")
    print("STM32 MQ3 값 대기")

    # =========================
    # [추가됨] STM32에서 MQ3 값 수신
    # 예: MQ3:320
    # =========================
    # =========================
    # [수정됨] MQ3 값을 여러 번 받아서 실제로 불었는지 판단
    # =========================
    mq3_values = collect_mq3_values()

    if len(mq3_values) == 0:
        print("MQ3 값 수신 실패")
        send_uart_message("BLOCK")
        continue

    baseline = mq3_values[0]
    max_value = max(mq3_values)
    delta = max_value - baseline

    print(f"MQ3 baseline: {baseline}")
    print(f"MQ3 max: {max_value}")
    print(f"MQ3 delta: {delta}")

    # =========================
    # [추가됨] 실제로 불었는지 판단
    # =========================
    if delta < BLOW_DELTA_THRESHOLD:
        print("측정 실패: 실제 호흡 변화량 부족")
        send_uart_message("BLOCK")
        continue

    # =========================
    # [수정됨] 실제로 불었다고 판단된 경우에만 음주 여부 판단
    # =========================
    if max_value < MQ3_THRESHOLD:
        send_uart_message("ALLOW")
        print("최종 결과: ALLOW")

    else:
        send_uart_message("BLOCK")
        print("최종 결과: BLOCK")

    time.sleep(1)