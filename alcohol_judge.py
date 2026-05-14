# alcohol_judge.py

from config import (
    MQ3_THRESHOLD,
    BLOW_DELTA_THRESHOLD
)


class AlcoholJudge:

    def __init__(self):

        pass

    def judge(self, mq3_values):

        # =========================
        # [추가됨] MQ3 값이 비어 있으면 실패 처리
        # =========================
        if len(mq3_values) == 0:

            return {
                "is_blown": False,
                "is_drunk": False,
                "baseline": 0,
                "max_value": 0,
                "delta": 0
            }

        # =========================
        # [추가됨] MQ3 기준값 계산
        # =========================
        baseline = mq3_values[0]

        max_value = max(
            mq3_values
        )

        delta = (
            max_value -
            baseline
        )

        print(f"MQ3 Baseline: {baseline}")
        print(f"MQ3 Max: {max_value}")
        print(f"MQ3 Delta: {delta}")

        # =========================
        # [추가됨] 실제로 불었는지 판단
        # =========================
        is_blown = (
            delta >=
            BLOW_DELTA_THRESHOLD
        )

        # =========================
        # [추가됨] 음주 여부 판단
        # =========================
        is_drunk = (
            max_value >=
            MQ3_THRESHOLD
        )

        return {
            "is_blown": is_blown,
            "is_drunk": is_drunk,
            "baseline": baseline,
            "max_value": max_value,
            "delta": delta
        }