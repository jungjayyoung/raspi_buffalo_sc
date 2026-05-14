# main.py

import time
import os

from config import (
    MSG_ACK_READY,
    MSG_REQ_START,
    MSG_DETECT_ON,
    MSG_ACK_START,
    MSG_REQ_MQ3,
    MSG_PASS,
    MSG_FAIL_DRUNK,
    MSG_RETRY,
    MSG_IDENTITY_FAIL,
    MSG_ERROR,
    MQ3_SAMPLE_TIME,
    MAX_RETRY,
    RETRY_DELAY,
    SESSION_FACE_CAPTURE_COUNT
)

from uart_manager import UARTManager
from logger_manager import LoggerManager
from file_manager import FileManager

from face_capture import FaceCapture
from registered_driver import RegisteredDriver
from session_driver import SessionDriver
from alcohol_judge import AlcoholJudge
from config import USE_UART

# [추가됨] 입-MQ3 위치 확인 모듈
from mouth_position_checker import MouthPositionChecker

# =========================
# [추가됨] MQ3 값 수집 함수
# =========================
def collect_mq3_values(uart):

    # =========================
    # [추가됨] 로컬 테스트용 MQ3 더미값
    # STM32 없이 테스트할 때 사용
    # =========================
    if not USE_UART:

        print("[LOCAL TEST] MQ3 더미값 사용")

        # 정상 테스트용
        return [120, 150, 190, 230]

        # 음주 테스트용으로 바꾸고 싶으면 아래 사용
        # return [120, 260, 430, 520]


    mq3_values = []
    start_time = time.time()

    while time.time() - start_time < MQ3_SAMPLE_TIME:

        message = uart.read_message()

        if not message:
            continue

        if message.startswith("MQ3:"):

            try:
                value = int(message.split(":")[1])
                mq3_values.append(value)

            except ValueError:
                print("MQ3 값 변환 실패")

    # stm32 용
    return mq3_values
    


# =========================
# [추가됨] face_A 여러 장 촬영 함수
# =========================
def capture_session_faces(face_capture):

    face_a_paths = []
    face_a_embeddings = []

    max_attempts = SESSION_FACE_CAPTURE_COUNT * 5
    attempt_count = 0

    while (
        len(face_a_paths) < SESSION_FACE_CAPTURE_COUNT
        and attempt_count < max_attempts
    ):

        attempt_count += 1

        current_count = len(face_a_paths) + 1

        image_path, embedding, _ = face_capture.capture_face(
            label=f"face_A_{current_count}"
        )

        if image_path is None or embedding is None:
            #print("face_A 촬영 실패")
            continue

        # 실제 파일 저장 여부 재확인
        if not os.path.exists(image_path):
            print(
                f"face_A {current_count}/{SESSION_FACE_CAPTURE_COUNT} "
                "파일 저장 실패 → 재촬영"
            )
            continue

        # 파일 크기가 0이면 저장 실패로 판단
        if os.path.getsize(image_path) == 0:
            print(
                f"face_A {current_count}/{SESSION_FACE_CAPTURE_COUNT} "
                "빈 파일 생성 → 재촬영"
            )
            continue

        face_a_paths.append(image_path)
        face_a_embeddings.append(embedding)

        print(
            f"face_A 촬영 성공 "
            f"{len(face_a_paths)}/{SESSION_FACE_CAPTURE_COUNT}"
        )

        time.sleep(0.5)

    return face_a_paths, face_a_embeddings


# =========================clear
# [추가됨] 대표 face_A 이미지 선택
# =========================
def get_main_face_a_path(face_a_paths):

    if len(face_a_paths) == 0:
        return None

    return face_a_paths[0]


# =========================
# [수정됨] 메인 함수
# 기존 이력자 DB 방식 → 등록 운전자 + 세션 운전자 방식
# =========================
def main():

    uart = UARTManager()
    logger = LoggerManager()
    file_manager = FileManager()

    face_capture = FaceCapture()
    registered_driver = RegisteredDriver()
    session_driver = SessionDriver()
    alcohol_judge = AlcoholJudge()


    face_capture.preview(duration=5)

    retry_count = 0

    try:
        print("[2단계] ACK:READY 대기")
        #uart.wait_for_message(MSG_ACK_READY)
        print("[LOCAL TEST] ACK:READY 자동 통과")

        while True:

            print("[3단계] REQ:START 대기")
            #uart.wait_for_message(MSG_REQ_START)
            print("[LOCAL TEST] REQ:START 자동 통과")

            uart.send_message(MSG_ACK_START)

            while True:

                print("[4단계] 운전자 감지 대기")
                #uart.wait_for_message(MSG_DETECT_ON)
                print("[LOCAL TEST] DETECT:ON 자동 통과")

                # =========================
                # [수정됨] face_A 1~3장 촬영
                # 기존: face_A 1장 촬영
                # 변경: 세션 운전자 embedding 생성을 위해 여러 장 촬영
                # =========================
                print("[5단계] face_A 세션 촬영")

                face_a_paths, face_a_embeddings = capture_session_faces(
                    face_capture
                )

                if len(face_a_embeddings) == 0:

                    #print("face_A 세션 촬영 실패")
                    uart.send_message(MSG_ERROR)

                    # [수정됨] 카메라 오류 시 무한 반복 방지
                    break

                face_a_path = get_main_face_a_path(
                    face_a_paths
                )

                # =========================
                # [추가됨] 세션 embedding 생성
                # 측정한 사람을 이번 세션 운전자로 임시 등록
                # =========================
                session_embedding = session_driver.create_session_embedding(
                    face_a_embeddings
                )

                if session_embedding is None:

                    print("세션 embedding 생성 실패")
                    uart.send_message(MSG_ERROR)
                    continue

                # =========================
                # [수정됨] 등록 운전자 여부 확인
                # 기존: 이력자 DB 1:N 매칭
                # 변경: 등록 운전자 1명과 비교
                # =========================
                registered_result = registered_driver.check_registered(
                    session_embedding
                )

                is_registered = registered_result["is_registered"]

                driver_type = "registered" if is_registered else "unregistered"
                driver_id = "registered_driver" if is_registered else "unknown"

                print(f"운전자 유형: {driver_type}")
                print(f"Registered Similarity: {registered_result['similarity']:.4f}")


                # =========================
                # [추가됨] 입-MQ3 위치 확인
                # =========================
                print("[5단계] 입-MQ3 위치 확인")

                # =========================
                # [수정됨] face_A 촬영에 사용한 카메라 해제
                # MouthPositionChecker가 같은 카메라를 다시 열 수 있도록 함
                # =========================
                face_capture.release()

                # =========================
                # [수정됨] 입-MQ3 위치 확인 객체를 이 시점에 생성
                # 기존처럼 main 시작 시 만들면 카메라 충돌 가능
                # =========================
                mouth_checker = MouthPositionChecker()
                mouth_ready = mouth_checker.check_ready()
                mouth_checker.release()

                if not mouth_ready:

                    print("입-MQ3 위치 확인 실패")
                    uart.send_message(MSG_ERROR)

                    return

                # =========================
                # [추가됨] face_B 촬영을 위해 FaceCapture 다시 생성
                # =========================
                face_capture = FaceCapture()
                # =========================
                # [추가됨] MQ3 측정 요청
                # =========================
                uart.send_message(MSG_REQ_MQ3)

                print("[5단계] MQ3 값 수집")
                mq3_values = collect_mq3_values(uart)

                alcohol_result = alcohol_judge.judge(
                    mq3_values
                )

                mq3_max = alcohol_result["max_value"]
                mq3_delta = alcohol_result["delta"]

                # =========================
                # [추가됨] 실제 호흡 실패 처리
                # =========================
                if not alcohol_result["is_blown"]:

                    print("실제 호흡 감지 실패")

                    retry_count += 1

                    logger.write_log(
                        driver_type=driver_type,
                        driver_id=driver_id,
                        mq3_max=mq3_max,
                        mq3_delta=mq3_delta,
                        alcohol_result="invalid",
                        identity_result="skip",
                        final_result=f"RETRY_{retry_count}"
                    )

                    uart.send_message(MSG_RETRY)

                    if retry_count > MAX_RETRY:
                        uart.send_message(MSG_FAIL_DRUNK)
                        print("재시도 초과: FAIL_DRUNK")

                    time.sleep(RETRY_DELAY)
                    continue

                # =========================
                # [6단계] 음주 감지 처리
                # =========================
                if alcohol_result["is_drunk"]:

                    print("[6단계] 음주 감지")

                    retry_count += 1

                    # =========================
                    # [수정됨] registered / unregistered 기준 저장
                    # =========================
                    if is_registered:
                        file_manager.save_registered_drunk(
                            face_a_path
                        )
                    else:
                        file_manager.save_unregistered_drunk(
                            face_a_path
                        )

                    logger.write_log(
                        driver_type=driver_type,
                        driver_id=driver_id,
                        mq3_max=mq3_max,
                        mq3_delta=mq3_delta,
                        alcohol_result="drunk",
                        identity_result="skip",
                        final_result=f"RETRY_{retry_count}"
                    )

                    if retry_count <= MAX_RETRY:

                        uart.send_message(MSG_RETRY)
                        print(f"{retry_count}회차 음주 감지: 30초 후 재측정")

                        time.sleep(RETRY_DELAY)
                        continue

                    else:

                        uart.send_message(MSG_FAIL_DRUNK)

                        logger.write_log(
                            driver_type=driver_type,
                            driver_id=driver_id,
                            mq3_max=mq3_max,
                            mq3_delta=mq3_delta,
                            alcohol_result="drunk",
                            identity_result="skip",
                            final_result="FAIL_DRUNK"
                        )

                        print("최종 음주 판정: FAIL_DRUNK")
                        continue

                # =========================
                # [7단계] 본인 검증
                # 시동 직전 현재 운전자 face_B 촬영
                # face_B ↔ session_embedding 비교
                # =========================
                print("[7단계] 본인 검증 face_B 촬영")

                face_b_path, face_b_embedding, _ = face_capture.capture_face(
                    label="face_B"
                )

                if face_b_path is None:

                    print("face_B 촬영 실패")
                    uart.send_message(MSG_ERROR)
                    continue

                identity_result = session_driver.verify_current_driver(
                    current_embedding=face_b_embedding,
                    session_embedding=session_embedding
                )

                # =========================
                # [수정됨] 본인 검증 실패 처리
                # 기존: face_A embedding과 face_B 비교
                # 변경: session_embedding과 face_B 비교
                # =========================
                if not identity_result["is_same_person"]:

                    print("본인 검증 실패")

                    file_manager.save_identity_fail(
                        face_a_path,
                        face_b_path
                    )

                    logger.write_log(
                        driver_type=driver_type,
                        driver_id=driver_id,
                        mq3_max=mq3_max,
                        mq3_delta=mq3_delta,
                        alcohol_result="normal",
                        identity_result="fail",
                        final_result="IDENTITY_FAIL"
                    )

                    uart.send_message(MSG_IDENTITY_FAIL)

                    continue

                # =========================
                # [9단계] 최종 PASS
                # =========================
                print("[9단계] 최종 PASS")

                uart.send_message(MSG_PASS)

                retry_count = 0

                # =========================
                # [수정됨] 정상 통과 이미지 저장 정책
                # registered / unregistered 기준
                # =========================
                if is_registered:
                    file_manager.save_registered_normal(
                        face_a_path
                    )
                else:
                    file_manager.save_unregistered_normal(
                        face_a_path
                    )

                file_manager.delete_temp_file(
                    face_b_path
                )

                logger.write_log(
                    driver_type=driver_type,
                    driver_id=driver_id,
                    mq3_max=mq3_max,
                    mq3_delta=mq3_delta,
                    alcohol_result="normal",
                    identity_result="pass",
                    final_result="PASS"
                )

                print("시퀀스 완료")

                # =========================
                # [수정됨] 로컬 테스트에서는 종료
                # 실제 차량에서는 다음 시동 요청 대기
                # =========================
                if not USE_UART:

                    print("다음 시동 요청 대기 상태")
                    return

                break
                

    except KeyboardInterrupt:
        print("사용자 종료")

    except Exception as e:
        print(f"예외 발생: {e}")
        uart.send_message(MSG_ERROR)

    finally:
        face_capture.release()
        
        uart.close()


if __name__ == "__main__":
    main()