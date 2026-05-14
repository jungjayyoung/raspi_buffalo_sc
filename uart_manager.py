# uart_manager.py

import serial
import time
from config import USE_UART


class UARTManager:

    def __init__(self):
        # =========================
        # [추가됨] UART 연결 객체
        # =========================
        # =========================
        # [수정됨] 로컬 테스트 모드 지원
        # =========================
        if USE_UART:

            self.ser = serial.Serial(
                UART_PORT,
                UART_BAUDRATE,
                timeout=UART_TIMEOUT
            )

            print("UART 연결 완료")

        else:

            self.ser = None

            print("UART 비활성화 (로컬 테스트 모드)")

    def read_message(self):

        if not USE_UART:
            return ""
        # =========================
        # [추가됨] UART 메시지 1줄 읽기
        # =========================
        line = self.ser.readline().decode(errors="ignore").strip()

        if line:
            print(f"STM32 → RPi: {line}")

        return line

    def wait_for_message(self, target_message):
        # =========================
        # [추가됨] 특정 메시지 수신까지 대기
        # =========================
        while True:
            message = self.read_message()

            if message == target_message:
                return message

            time.sleep(0.05)

    def send_message(self, message):


        if not USE_UART:

            print(f"[LOCAL UART] {message}")
            return
        # =========================
        # [추가됨] UART 메시지 전송
        # =========================
        self.ser.write((message + "\n").encode())
        print(f"RPi → STM32: {message}")

    def close(self):
        # =========================
        # [추가됨] UART 종료
        # =========================
        if self.ser is not None:
            self.ser.close()
            print("UART 연결 종료")