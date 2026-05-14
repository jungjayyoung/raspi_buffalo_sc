
# Update 5/13
# 얼굴 인증 기반 음주운전 방지 시스템

## 📌 프로젝트 소개

본 프로젝트는 Raspberry Pi와 STM32를 활용한
얼굴 인증 기반 음주운전 방지 시스템입니다.

운전자의 얼굴 인증,
MQ-3 기반 음주 측정,
본인 검증,
운전자 교체 감지 기능을 통합하여
대리 측정 및 음주 운전을 방지하는 것을 목표로 합니다.

---

# 🧠 시스템 핵심 기능

## ✅ 등록 운전자 인증
- 등록 운전자 얼굴 임베딩 생성
- `known_embedding.npy` 기반 얼굴 비교
- 등록 / 미등록 운전자 판별

## ✅ 세션 기반 운전자 추적
- face_A 1~3장 촬영
- 평균 embedding 생성
- `session_embedding.npy` 생성
- 세션 운전자 임시 등록

## ✅ 본인 검증 시스템
- 시동 직전 face_B 재촬영
- session_embedding ↔ face_B 비교
- 운전자 교체 여부 판단
- 대리 측정 방지

## ✅ MQ-3 음주 측정
- MQ3 baseline / max / delta 계산
- 변화량 기반 측정 구조
- 실제 호흡 여부 확인 가능

## ✅ 입-MQ3 위치 확인
- 카메라 영상 기반 입 위치 추적
- MQ3 위치 거리 계산
- READY 상태 안정화 시간 적용
- 측정기 앞 위치 검증

## ✅ 증거 기록 시스템
- 음주 감지 이미지 저장
- 본인 검증 실패 이미지 저장
- system.log 기록
- registered / unregistered 분리 저장

---

# 🏗️ 시스템 구조

```text
STM32
- 시동 버튼 입력
- 운전자 감지 버튼 입력
- MQ-3 센서 측정
- LED 제어
- Relay 제어
- Buzzer 제어
- UART 통신

Raspberry Pi
- 얼굴 촬영
- 등록 운전자 인증
- 세션 운전자 생성
- 본인 검증
- MQ3 음주 판정
- 입-MQ3 위치 확인
- 로그 저장
- 증거 이미지 저장

# 🔄 시스템 동작 흐름

```text
1. 시동 버튼 입력
2. STM32 → Raspberry Pi 시동 요청
3. 운전자 감지
4. face_A 1~3장 촬영
5. 등록 운전자 여부 확인
6. session_embedding 생성
7. 입-MQ3 위치 확인
8. MQ3 음주 측정
9. 시동 직전 face_B 재촬영
10. face_B ↔ session_embedding 비교
11. 최종 PASS / FAIL 판정

# 📂 프로젝트 구조

```text
RASPI_BUFFALO_SC/
│
├── db/
│   ├── images/
│   │   └── registered_driver/
│   │       ├── 1.jpg
│   │       ├── 2.jpg
│   │       └── 3.jpg
│   │
│   └── known_embedding.npy
│
├── logs/
│   ├── temp/
│   │   ├── face_A_1.jpg
│   │   ├── face_A_2.jpg
│   │   ├── face_A_3.jpg
│   │   ├── face_B.jpg
│   │   └── session_embedding.npy
│   │
│   ├── registered/
│   │   ├── normal/
│   │   └── drunk/
│   │
│   ├── unregistered/
│   │   ├── normal/
│   │   └── drunk/
│   │
│   ├── identity_fail/
│   └── system.log
│
├── alcohol_judge.py
├── buffalo_sc_register.py
├── config.py
├── face_capture.py
├── file_manager.py
├── logger_manager.py
├── main.py
├── mouth_position_checker.py
├── registered_driver.py
├── session_driver.py
├── uart_manager.py
└── requirements.txt
```
# 🧪 로컬 테스트 방법

## 1. 가상환경 활성화

```bash
venv\Scripts\activate
```

## 2. 패키지 설치
```bash
pip install -r requirements.txt
```


## 3. 등록 운전자 embedding 생성
```bash
db/images/registered_driver/
```
이후 실행
```bash
python buffalo_sc_register.py
```

성공시:
```bash
db/known_embedding.npy
```
생성됨.


## 4. 메인 실행
```bash
python main.py
```

# 🖥️ UART 프로토콜

## STM32 → Raspberry Pi

```text
ACK:READY
REQ:START
DETECT:ON
DETECT:OFF
MQ3:<value>
```

## Raspberry Pi → STM32

```text
ACK:START
REQ:MQ3
PASS
FAIL_DRUNK
RETRY
IDENTITY_FAIL
ERROR
```

# ⚙️ 사용 기술

## AI / Vision
- InsightFace (buffalo_sc)
- OpenCV
- NumPy

## Hardware
- Raspberry Pi
- STM32
- MQ-3 Alcohol Sensor
- Relay Module
- Buzzer
- Camera

## Communication
- UART Serial Communication