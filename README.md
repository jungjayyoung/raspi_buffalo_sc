# Update 5/18

# 얼굴 인증 기반 음주운전 방지 시스템

## 📌 프로젝트 소개

본 프로젝트는 Raspberry Pi와 STM32를 활용한  
얼굴 인증 기반 음주운전 방지 시스템입니다.

운전자의 얼굴 인증,  
MQ-3 기반 음주 측정,  
DHT 기반 실제 호흡 감지,  
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
- face_A 3장 촬영
- 평균 embedding 생성
- `session_embedding.npy` 생성
- 세션 운전자 임시 등록

## ✅ 본인 검증 시스템
- 시동 직전 face_B 3장 재촬영
- 평균 embedding 생성
- session_embedding ↔ face_B 비교
- 운전자 교체 여부 판단
- 대리 측정 방지

## ✅ MQ-3 + DHT 음주 측정

- 1초 baseline 측정 (10개)
- 4초 측정 (40개)
- MQ3 peak 계산
- MQ3 delta 계산
- DHT 습도 변화량 계산

최종 판정:

```text
MQ3 변화량 작음
+
습도 변화량 작음
→ RETRY

MQ3 delta >= threshold
→ FAIL

나머지
→ PASS
```

## ✅ 입-MQ3 위치 확인

- 카메라 영상 기반 입 위치 추적
- 입 ↔ 측정기 거리 계산
- READY 상태 안정화
- 측정기 앞 위치 검증

## ✅ 증거 기록 시스템

- 음주 감지 이미지 저장
- 본인 검증 실패 이미지 저장
- registered / unregistered 분리 저장
- system.log 저장

---

# 🏗️ 시스템 구조

```text
STM32
- 버튼 입력
- MQ-3 센서 측정
- DHT 센서 측정
- LED 제어
- Relay 제어
- Buzzer 제어
- UART 통신

Raspberry Pi
- 얼굴 촬영
- 등록 운전자 인증
- 세션 운전자 생성
- 본인 검증
- MQ3/DHT 분석
- 입 위치 확인
- 로그 저장
- 증거 이미지 저장
```

# 🔄 시스템 동작 흐름

```text
1. SYSTEM_START
2. SEAT_ON
3. face_A 3장 촬영
4. 등록 운전자 여부 확인
5. session_embedding 생성
6. 입-MQ3 위치 확인
7. BLOW_START
8. MQ3/DHT 측정
9. face_B 재촬영
10. face_B ↔ session_embedding 비교
11. 최종 PASS / FAIL
```

# 📂 프로젝트 구조

```text
RASPI_MOBILEFACENET/

├── db/
│   ├── images/
│   │   └── registered_driver/
│   └── known_embedding.npy
│
├── logs/
│   ├── temp/
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
├── mobilefacenet_register.py
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

# 🖥️ UART 프로토콜

## STM32 → Raspberry Pi

```text
SYSTEM_START
SEAT_ON
SEAT_OFF
BLOW_START
MEASURE_BEGIN

MQ3:1234
HUM:52.3

MEASURE_END
```

## Raspberry Pi → STM32

```text
PASS
FAIL
RETRY
ERROR
```

# ⚙️ 사용 기술

## AI / Vision

- MobileFaceNet
- OpenCV
- NumPy

## Hardware

- Raspberry Pi 5
- STM32
- MQ-3 Alcohol Sensor
- DHT Sensor
- Relay
- Buzzer
- Camera

## Communication

- UART Serial Communication