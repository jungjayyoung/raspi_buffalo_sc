# Umjoo-Cut Face Recognition System

## 프로젝트 개요

차량 내부에서 운전자 얼굴을 인식하고,
등록된 사용자와 동일 인물인지 확인한 뒤
MQ3 센서를 이용한 음주 측정을 시작하는 시스템입니다.

시스템은 다음 기능을 수행합니다:

* 실시간 얼굴 검출
* 등록 사용자 얼굴 비교
* 운전자 영역 필터링
* 작은 얼굴 제거
* MQ3 센서 위치 기반 거리 계산
* 상태 안정화(State Stabilization)
* UART 기반 STM32 통신

---

# 시스템 구성

## Hardware

* Raspberry Pi 5
* USB Webcam
* STM32F446RE
* MQ3 Alcohol Sensor

---

## Software

* Python
* OpenCV
* InsightFace
* ONNX Runtime
* UART Serial Communication

---

# 전체 동작 흐름

```text
카메라 입력
    ↓
얼굴 검출
    ↓
가장 큰 얼굴 선택
    ↓
운전자 영역 확인
    ↓
얼굴 크기 필터
    ↓
등록 얼굴과 similarity 비교
    ↓
입 위치 검출
    ↓
MQ3와 거리 계산
    ↓
상태 결정
    ↓
상태 안정화(5초)
    ↓
UART 전송
```

---

# 핵심 개선 사항

## 1. 가장 큰 얼굴 선택

### 문제점

차량 내부에서 뒷좌석 사람이 먼저 검출되면
타인(OTHERS) 상태로 잘못 판별되는 문제가 발생.

### 해결 방법

검출된 얼굴들 중 가장 큰 얼굴만 선택.

```python
face = max(
    faces,
    key=lambda f: (
        (f.bbox[2] - f.bbox[0]) *
        (f.bbox[3] - f.bbox[1])
    )
)
```

### 효과

* 운전자 우선 인식 가능
* 뒷좌석 얼굴 영향 감소
* 안정성 향상

---

# 2. 운전자 영역 제한

## 문제점

차량 내부 전체를 검사하면
조수석/뒷좌석 얼굴까지 인식될 수 있음.

## 해결 방법

운전자 영역만 유효하도록 제한.

```python
DRIVER_X_MIN = 0
DRIVER_X_MAX = 180
```

```python
if not (
    DRIVER_X_MIN <= face_center_x <= DRIVER_X_MAX
):
    continue
```

## 효과

* 운전자 외 얼굴 무시
* 오검출 감소
* 성능 향상

---

# 3. 최소 얼굴 크기 필터

## 문제점

멀리 있는 작은 얼굴도 검출되어
잘못된 판별이 발생.

## 해결 방법

얼굴 면적 기준 적용.

```python
MIN_FACE_AREA = 5000
```

```python
face_area = (
    (x2 - x1) *
    (y2 - y1)
)
```

```python
if face_area < MIN_FACE_AREA:
    continue
```

## 효과

* 먼 거리 얼굴 제거
* 안정성 증가
* 뒤 좌석 간섭 감소

---

# 4. 상태 안정화(State Stabilization)

## 문제점

얼굴 인식은 프레임마다 결과가 변동될 수 있음.

예시:

```text
same
same
others
same
same
```

이 경우 UART가 반복 전송되며
오동작 가능성이 발생.

---

## 해결 방법

동일 상태가 일정 시간 유지될 때만
UART 전송 수행.

```python
STATE_DELAY = 5.0
```

```python
if current_state != candidate_state:

    candidate_state = current_state
    state_start_time = time.time()
```

```python
elapsed = time.time() - state_start_time

if elapsed >= STATE_DELAY:
```

---

## 효과

* 상태 튐 방지
* UART 스팸 방지
* 차량 환경 안정성 향상

---

# 5. UART 중복 전송 방지

## 문제점

같은 상태가 반복 전송되면
STM32 처리 부담 증가.

## 해결 방법

마지막 상태 저장 후 비교.

```python
last_state = ""
```

```python
if last_state != "start_mq3":

    ser.write(b"start_mq3\n")
```

## 효과

* UART 통신 최적화
* STM32 안정성 향상

---

# 6. AI 연산 최적화

## 문제점

라즈베리파이에서 매 프레임 AI 수행 시
CPU 사용량 증가.

## 해결 방법

3프레임마다 얼굴 분석 수행.

```python
if frame_count % 3 == 0:

    faces = app.get(frame)
```

## 효과

* CPU 사용량 감소
* FPS 안정화
* 발열 감소

---

# 얼굴 판별 기준

## SAME

등록된 사용자와 동일 인물.

```python
similarity >= 0.5
```

---

## UNKNOWN

애매한 유사도 영역.

```python
0.35 <= similarity < 0.5
```

---

## OTHERS

등록되지 않은 타인.

```python
similarity < 0.35
```

---

# MQ3 연동 구조

## 입 위치 계산

InsightFace Keypoints 사용.

```python
mouth_left = kps[3]
mouth_right = kps[4]
```

---

## 입 중심 계산

```python
mouth_x = int(
    (mouth_left[0] + mouth_right[0]) / 2
)

mouth_y = int(
    (mouth_left[1] + mouth_right[1]) / 2
)
```

---

## MQ3 거리 계산

```python
distance = np.sqrt(
    (mouth_x - MQ3_X) ** 2 +
    (mouth_y - MQ3_Y) ** 2
)
```

---

## MQ3 시작 조건

```text
1. SAME 상태
2. 입과 MQ3 거리 조건 만족
```

---

# UART 프로토콜

## Raspberry Pi → STM32

| Command   | Description |
| --------- | ----------- |
| start_mq3 | MQ3 측정 시작   |
| others    | 타인 감지       |
| no_face   | 얼굴 없음       |

---

# 실행 환경

## Camera Resolution

```python
320 x 240
```

---

## FPS

```python
15 FPS
```

---

## InsightFace Model

```python
buffalo_sc
```

---

# 주요 변수

| Variable               | Description  |
| ---------------------- | ------------ |
| SAME_THRESHOLD         | 동일인 기준       |
| OTHER_THRESHOLD        | 타인 기준        |
| MIN_FACE_AREA          | 최소 얼굴 크기     |
| STATE_DELAY            | 상태 안정화 시간    |
| MQ3_DISTANCE_THRESHOLD | 입과 MQ3 거리 기준 |

---

# 향후 개선 예정

* Multi-face tracking
* 야간 조도 보정
* MQ3 실측값 기반 음주 판별
* STM32 상태 머신 연동
* ONNX Runtime 최적화
* TensorRT/NPU 가속
* 얼굴 추적 기반 안정화
* 음주 측정 완료 프로토콜 추가

---

# 프로젝트 목표

차량 내부에서:

* 운전자 본인 확인
* 타인 운전 감지
* 음주 측정 자동화
* 임베디드 환경 실시간 처리

를 수행하는 경량 AI 기반 스마트 음주운전 방지 시스템 개발.
