# logger_manager.py

import os
from datetime import datetime

from config import SYSTEM_LOG_PATH


class LoggerManager:

    def __init__(self):

        # =========================
        # [추가됨] 로그 폴더 자동 생성
        # =========================
        os.makedirs(
            os.path.dirname(SYSTEM_LOG_PATH),
            exist_ok=True
        )

    def write_log(
        self,
        driver_type,
        driver_id,
        mq3_max,
        mq3_delta,
        alcohol_result,
        identity_result,
        final_result
    ):

        # =========================
        # [추가됨] 현재 시간 문자열
        # =========================
        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # =========================
        # [추가됨] 로그 한 줄 생성
        # =========================
        log_line = (
            f"{now} | "
            f"driver_type={driver_type} | "
            f"driver_id={driver_id} | "
            f"mq3_max={mq3_max} | "
            f"mq3_delta={mq3_delta} | "
            f"alcohol={alcohol_result} | "
            f"identity={identity_result} | "
            f"result={final_result}\n"
        )

        # =========================
        # [추가됨] 로그 파일 저장
        # =========================
        with open(
            SYSTEM_LOG_PATH,
            "a",
            encoding="utf-8"
        ) as f:

            f.write(log_line)

        print("[SYSTEM LOG]")
        print(log_line)