# alcohol_judge.py

from config import (
    MQ3_BASELINE_SAMPLE_COUNT,
    MQ3_MEASURE_SAMPLE_COUNT,
    MQ3_DRUNK_DELTA_THRESHOLD,
    MQ3_BLOW_DELTA_THRESHOLD,
    HUM_BLOW_DELTA_THRESHOLD
)


class AlcoholJudge:

    def __init__(self):
        pass

    def _average(self, values):
        if len(values) == 0:
            return 0

        return sum(values) / len(values)

    def judge(self, mq3_values, hum_values):
        """
        MQ3 + 습도 기반 최종 판정 로직

        측정 구조:
        - 앞 10개 샘플: baseline 구간
        - 뒤 40개 샘플: 실제 측정 구간

        판정:
        1. MQ3 변화량 작음 + 습도 변화량 작음 → RETRY
        2. MQ3 delta >= 500 → 음주 FAIL
        3. 그 외 → PASS
        """

        required_mq3_count = (
            MQ3_BASELINE_SAMPLE_COUNT +
            MQ3_MEASURE_SAMPLE_COUNT
        )

        # =========================
        # MQ3 샘플 개수 검증
        # =========================
        if len(mq3_values) < required_mq3_count:
            print("[MQ3 ERROR] MQ3 샘플 개수 부족")
            print(f"수신 MQ3 개수: {len(mq3_values)}")
            print(f"필요 MQ3 개수: {required_mq3_count}")

            return {
                "result": "RETRY",
                "is_blown": False,
                "is_drunk": False,
                "mq3_baseline": 0,
                "mq3_peak": 0,
                "mq3_delta": 0,
                "hum_baseline": 0,
                "hum_peak": 0,
                "hum_delta": 0,
                "reason": "MQ3_SAMPLE_NOT_ENOUGH"
            }

        # =========================
        # MQ3 baseline / measure 분리
        # =========================
        mq3_baseline_samples = mq3_values[
            :MQ3_BASELINE_SAMPLE_COUNT
        ]

        mq3_measure_samples = mq3_values[
            MQ3_BASELINE_SAMPLE_COUNT:
            required_mq3_count
        ]

        mq3_baseline = self._average(
            mq3_baseline_samples
        )

        mq3_peak = max(
            mq3_measure_samples
        )

        mq3_delta = (
            mq3_peak -
            mq3_baseline
        )

        # =========================
        # 습도 데이터 처리
        # DHT는 MQ3보다 샘플 수가 적을 수 있으므로
        # 앞쪽 절반을 baseline, 뒤쪽 절반을 measure로 사용
        # =========================
        if len(hum_values) >= 2:

            split_index = len(hum_values) // 2

            hum_baseline_samples = hum_values[
                :split_index
            ]

            hum_measure_samples = hum_values[
                split_index:
            ]

            hum_baseline = self._average(
                hum_baseline_samples
            )

            hum_peak = max(
                hum_measure_samples
            )

            hum_delta = (
                hum_peak -
                hum_baseline
            )

        else:
            hum_baseline = 0
            hum_peak = 0
            hum_delta = 0

        print("=" * 50)
        print("[MQ3 / HUM 판정 결과]")
        print(f"MQ3 Baseline: {mq3_baseline:.2f}")
        print(f"MQ3 Peak: {mq3_peak:.2f}")
        print(f"MQ3 Delta: {mq3_delta:.2f}")
        print(f"HUM Baseline: {hum_baseline:.2f}")
        print(f"HUM Peak: {hum_peak:.2f}")
        print(f"HUM Delta: {hum_delta:.2f}")
        print("=" * 50)

        # =========================
        # 실제 호흡 여부 판단
        # MQ3 변화량과 습도 변화량이 모두 작으면
        # 제대로 불지 않은 것으로 판단
        # =========================
        is_blown = not (
            mq3_delta < MQ3_BLOW_DELTA_THRESHOLD
            and
            hum_delta < HUM_BLOW_DELTA_THRESHOLD
        )

        if not is_blown:
            return {
                "result": "RETRY",
                "is_blown": False,
                "is_drunk": False,
                "mq3_baseline": mq3_baseline,
                "mq3_peak": mq3_peak,
                "mq3_delta": mq3_delta,
                "hum_baseline": hum_baseline,
                "hum_peak": hum_peak,
                "hum_delta": hum_delta,
                "reason": "BLOW_NOT_DETECTED"
            }

        # =========================
        # 음주 여부 판단
        # delta 기준으로만 판정
        # =========================
        is_drunk = (
            mq3_delta >=
            MQ3_DRUNK_DELTA_THRESHOLD
        )

        if is_drunk:
            result = "FAIL"
            reason = "DRUNK_DETECTED"
        else:
            result = "PASS"
            reason = "NORMAL"

        return {
            "result": result,
            "is_blown": True,
            "is_drunk": is_drunk,
            "mq3_baseline": mq3_baseline,
            "mq3_peak": mq3_peak,
            "mq3_delta": mq3_delta,
            "hum_baseline": hum_baseline,
            "hum_peak": hum_peak,
            "hum_delta": hum_delta,
            "reason": reason
        }