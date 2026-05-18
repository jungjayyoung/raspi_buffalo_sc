# main.py

import time
import os

from config import (
    MSG_SYSTEM_START,
    MSG_SEAT_ON,
    MSG_SEAT_OFF,
    MSG_BLOW_START,
    MSG_MEASURE_BEGIN,
    MSG_MEASURE_END,
    MSG_MQ3_PREFIX,
    MSG_HUM_PREFIX,
    MSG_PASS,
    MSG_FAIL,
    MSG_RETRY,
    MSG_ERROR,
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
def collect_sensor_values(uart):
    if not USE_UART:
        print("[LOCAL TEST] MQ3/HUM 더미값 사용")

        # 정상 호흡 + 정상 판정 예시
        mq3_values = [1100] * 10 + [1120, 1140, 1160, 1180] + [1180] * 36
        hum_values = [52.0, 52.1, 52.0, 55.0, 57.0, 58.0]

        return mq3_values, hum_values

        # 음주 테스트 예시
        # mq3_values = [1100] * 10 + [1300, 1450, 1650, 1700] + [1700] * 36
        # hum_values = [52.0, 52.1, 52.0, 55.0, 57.0, 58.0]
        # return mq3_values, hum_values

        # 제대로 안 분 경우 RETRY 예시
        # mq3_values = [1100] * 10 + [1110] * 40
        # hum_values = [52.0, 52.0, 52.1, 52.1]
        # return mq3_values, hum_values

    mq3_values = []
    hum_values = []

    is_measuring = False

    while True:
        message = uart.read_message()

        if not message:
            continue

        if message == MSG_MEASURE_BEGIN:
            print("[UART] 측정 시작")
            is_measuring = True
            mq3_values.clear()
            hum_values.clear()
            continue

        if message == MSG_MEASURE_END:
            print("[UART] 측정 종료")
            break

        if not is_measuring:
            continue

        if message.startswith(MSG_MQ3_PREFIX):
            try:
                value = int(message.split(":")[1])
                mq3_values.append(value)
            except ValueError:
                print("MQ3 값 변환 실패")

        elif message.startswith(MSG_HUM_PREFIX):
            try:
                value = float(message.split(":")[1])
                hum_values.append(value)
            except ValueError:
                print("HUM 값 변환 실패")

    return mq3_values, hum_values 
    


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

def capture_verify_faces(face_capture):

    face_b_paths = []
    face_b_embeddings = []

    while len(face_b_paths) < SESSION_FACE_CAPTURE_COUNT:

        current_count = len(face_b_paths) + 1

        image_path, embedding, _ = face_capture.capture_face(
            label=f"face_B_{current_count}"
        )

        if image_path is None or embedding is None:

            print(
                f"face_B {current_count}/{SESSION_FACE_CAPTURE_COUNT} "
                "촬영 실패 → 재시도"
            )

            continue

        face_b_paths.append(image_path)
        face_b_embeddings.append(embedding)

        print(
            f"face_B 촬영 성공 "
            f"{len(face_b_paths)}/{SESSION_FACE_CAPTURE_COUNT}"
        )

        time.sleep(0.5)

    return face_b_paths, face_b_embeddings

def get_main_face_b_path(face_b_paths):

    if len(face_b_paths) == 0:
        return None

    return face_b_paths[0]

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
        print("[1단계] SYSTEM_START 대기")
        if USE_UART:
            uart.wait_for_message(MSG_SYSTEM_START)
        else:
            print("[LOCAL TEST] SYSTEM_START 자동 통과")

        while True:

            print("[2단계] SEAT_ON 대기")
            if USE_UART:
                uart.wait_for_message(MSG_SEAT_ON)
            else:
                print("[LOCAL TEST] SEAT_ON 자동 통과")


            while True:

                # =========================
                # [수정됨] face_A 1~3장 촬영
                # 기존: face_A 1장 촬영
                # 변경: 세션 운전자 embedding 생성을 위해 여러 장 촬영
                # =========================
                print("[3단계] face_A 세션 촬영")
                print("=" * 50)
                print("👤 얼굴 인증을 시작합니다")
                print("📸 face_A 세션 촬영 시작")
                print("=" * 50)

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

                print("🧠 세션 운전자 embedding 생성 완료")
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

                print(f"👤 운전자 유형: {driver_type}")
                print(f"📊 Registered Similarity: {registered_result['similarity']:.4f}")


                # =========================
                # [추가됨] 입-MQ3 위치 확인
                # =========================
                print("📍 입-MQ3 위치 확인 시작")

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
                mouth_ready = mouth_checker.check_ready(driver_type=driver_type)
                mouth_checker.release()

                if not mouth_ready:

                    print("입-MQ3 위치 확인 실패")
                    uart.send_message(MSG_ERROR)

                    return
                
                print("✅ 입-MQ3 위치 확인 완료")

                # =========================
                # [추가됨] face_B 촬영을 위해 FaceCapture 다시 생성
                # =========================
                face_capture = FaceCapture()
                # =========================
                # [추가됨] MQ3 측정 요청
                # =========================

                print("🌬️ 음주 측정 시작")

                print("[4단계][측정 대기 단계] BLOW_START 대기")

                if USE_UART:
                    uart.wait_for_message(MSG_BLOW_START)
                else:
                    print("[LOCAL TEST] BLOW_START 자동 통과")


                print("[5단계] MQ3 값, DHT 값  수집")
                mq3_values, hum_values = collect_sensor_values(uart)

                alcohol_result = alcohol_judge.judge(
                    mq3_values,
                    hum_values
                )

                mq3_max = alcohol_result["mq3_peak"]
                mq3_delta = alcohol_result["mq3_delta"]
                hum_delta = alcohol_result["hum_delta"]

                # =========================
                # [추가됨] 실제 호흡 실패 처리
                # =========================
                if not alcohol_result["is_blown"]:

                    print("실제 호흡 감지 실패")
                    print(f"🔄 다시 측정해주세요 ({retry_count + 1}/{MAX_RETRY})")

                    retry_count += 1

                    logger.write_log(
                    driver_type=driver_type,
                    driver_id=driver_id,
                    mq3_max=mq3_max,
                    mq3_delta=mq3_delta,
                    hum_delta=hum_delta,
                    alcohol_result="invalid",
                    identity_result="skip",
                    final_result=f"RETRY_{retry_count}",
                    reason=alcohol_result["reason"]
                )

                    uart.send_message(MSG_RETRY)

                    if retry_count > MAX_RETRY:
                        uart.send_message(MSG_FAIL)
                        print("재시도 초과: FAIL_DRUNK")

                    time.sleep(RETRY_DELAY)
                    continue

                # =========================
                # [6단계] 음주 감지 처리
                # =========================
                if alcohol_result["is_drunk"]:

                    print("=" * 50)
                    print("🚫 음주 감지")
                    print(f"📈 MQ3 최대값: {mq3_max}")
                    print(f"📈 MQ3 변화량(delta): {mq3_delta}")
                    print("=" * 50)

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

                        hum_delta=hum_delta,

                        alcohol_result="invalid",
                        identity_result="skip",
                        final_result=f"RETRY_{retry_count}",
                        reason=alcohol_result["reason"]
                    )

                    if retry_count <= MAX_RETRY:

                        uart.send_message(MSG_RETRY)
                        print(f"{retry_count}회차 음주 감지: 30초 후 재측정")

                        time.sleep(RETRY_DELAY)
                        continue

                    else:

                        uart.send_message(MSG_FAIL)

                        logger.write_log(
                            driver_type=driver_type,
                            driver_id=driver_id,
                            mq3_max=mq3_max,
                            mq3_delta=mq3_delta,
                            hum_delta=hum_delta,
                            alcohol_result="drunk",
                            identity_result="skip",
                            final_result="FAIL_DRUNK",
                            reason=alcohol_result["reason"]
                        )

                        print("최종 음주 판정: FAIL_DRUNK")
                        continue

                # =========================
                # [7단계] 본인 검증
                # 시동 직전 현재 운전자 face_B 3장 촬영
                # face_B 평균 embedding ↔ session_embedding 비교
                # =========================
                print("👤 최종 운전자 확인 중...")
                print("📸 face_B 세션 촬영 시작")

                face_b_paths, face_b_embeddings = capture_verify_faces(
                    face_capture
                )

                if len(face_b_embeddings) == 0:

                    print("[ERROR] face_B 촬영 실패")
                    uart.send_message(MSG_ERROR)
                    continue

                face_b_path = get_main_face_b_path(
                    face_b_paths
                )

                face_b_embedding = session_driver.create_session_embedding(
                    face_b_embeddings
                )

                if face_b_embedding is None:

                    print("[ERROR] face_B 평균 embedding 생성 실패")
                    uart.send_message(MSG_ERROR)
                    continue

                print("🧠 face_B 평균 embedding 생성 완료")

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
                        hum_delta=hum_delta,

                        alcohol_result="normal",
                        identity_result="fail",
                        final_result="IDENTITY_FAIL",
                        reason=alcohol_result["reason"]
                    )
                    uart.send_message(MSG_FAIL)

                    print("=" * 50)
                    print("⚠️ 측정자와 현재 운전자가 다릅니다")
                    print("🚫 시동 차단")
                    print("🔄 처음부터 다시 측정합니다")
                    print("=" * 50)

                    time.sleep(3)

                    continue

                # =========================
                # [9단계] 최종 PASS
                # =========================
                print("=" * 50)
                print("✅ 최종 PASS")
                print("🚗 시동 허용")
                print("=" * 50)

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
                    hum_delta=hum_delta,

                    alcohol_result="normal",
                    identity_result="pass",

                    final_result="PASS",
                    reason=alcohol_result["reason"]
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