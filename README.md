# UmjooCut

AI 기반 얼굴 인증 및 음주운전 방지 시스템

## 📌 프로젝트 소개

UmjooCut은 등록 사용자 얼굴 인증과 음주 측정을 기반으로 차량 시동 가능 여부를 판단하는 시스템입니다.

InsightFace의 `buffalo_sc` 모델을 활용한 얼굴 인증,  
MQ3 센서를 활용한 음주 감지,  
Raspberry Pi와 STM32 간 UART 통신을 통해 차량 접근 및 시동을 제어합니다.

---

# 🧩 시스템 구조

```text
USB Webcam
    ↓
Raspberry Pi 5
 ├─ 얼굴 인증
 ├─ 운전자 위치 확인
 ├─ MQ3 측정 제어
 └─ UART 통신
    ↓
STM32F411RE
 ├─ MQ3 센서
 ├─ LED 제어
 ├─ LCD 출력
 ├─ Relay 제어
 └─ Buzzer 제어
```

---

# ⚙️ 주요 기능

## ✅ 등록 사용자 얼굴 인증

- InsightFace buffalo_sc 모델 사용
- 등록된 사용자 얼굴 임베딩 생성
- 실시간 얼굴 인증 수행
- 일정 횟수 이상 검출 시 인증 성공

## ✅ 운전자 위치 확인

- 운전자 영역(ROI) 검사
- 가장 큰 얼굴 추적
- 얼굴 크기 필터링

## ✅ 입 위치 기반 MQ3 측정 시작

- 입 위치 Keypoint 추적
- MQ3 센서 위치와 거리 계산
- 일정 거리 이하일 때 측정 시작

## ✅ 실제 호흡 여부 판단

- STM32가 MQ3 값을 연속 전송
- Raspberry Pi가 MQ3 변화량 분석
- 실제로 숨을 불었는지 판단

## ✅ 차량 시동 제어

- 음주 여부에 따라
  - ALLOW
  - BLOCK
  전송
- STM32가 Relay 제어 수행

---

# 🔄 시스템 흐름

```text
READY
↓
등록 사용자 얼굴 인증
↓
face_ok
↓
운전자 위치 확인
↓
입-MQ3 거리 확인
↓
start_mq3
↓
STM32가 MQ3 값 연속 송신
↓
Raspberry Pi가 변화량 분석
↓
실제 호흡 여부 판단
↓
ALLOW / BLOCK
↓
STM32 출력 제어
```

---

# 📂 프로젝트 구조

```text
umjoocut/
│
├── main.py
├── buffalo_sc_register.py
├── buffalo_sc_authentication.py
├── buffalo_sc_alcohol_check.py
├── known_embedding.npy
└── requirements.txt
```

---

# 📄 파일 설명

## main.py

전체 시스템 상태 머신 및 UART 통신 제어

- READY 수신
- 얼굴 인증 실행
- 음주 측정 실행
- MQ3 값 수신
- ALLOW / BLOCK 판단

## buffalo_sc_register.py

등록 사용자 얼굴 임베딩 생성

- 얼굴 embedding 추출
- 평균 embedding 생성
- known_embedding.npy 저장

## buffalo_sc_authentication.py

등록 사용자 얼굴 인증

- 전체 프레임 얼굴 검사
- cosine similarity 비교
- 인증 성공 시 face_ok 전송

## buffalo_sc_alcohol_check.py

운전자 위치 및 입 위치 검사

- 운전자 ROI 검사
- 입 위치 추적
- MQ3 거리 계산
- start_mq3 전송

---

# 🖥️ 사용 기술

## AI / Vision

- Python
- OpenCV
- InsightFace
- buffalo_sc
- ONNX Runtime

## Embedded

- Raspberry Pi 5
- STM32F411RE
- UART Communication
- MQ3 Alcohol Sensor

---

# 📦 설치

## requirements.txt

```text
opencv-python==4.9.0.80
numpy==1.26.4
insightface
onnxruntime==1.17.0
pyserial
```

설치:

```bash
pip install -r requirements.txt
```

---

# ▶️ 실행 방법

## 1. 얼굴 임베딩 생성

```bash
python buffalo_sc_register.py
```

## 2. 전체 시스템 실행

```bash
python main.py
```

---

# 📡 UART 프로토콜

## STM32 → Raspberry Pi

```text
READY
MQ3:320
```

## Raspberry Pi → STM32

```text
face_ok
face_fail
start_mq3
ALLOW
BLOCK
```

---

# 🚧 향후 개선 예정

- STM32 펌웨어 구현
- MQ3 센서 실제 측정 로직 구현
- MQ3 기준값 및 호흡 변화량 튜닝
- Relay Module 기반 차량 시동 제어 구현
- Green / Red / Yellow LED 상태 출력 구현
- Buzzer 경고 출력 구현
- I2C LCD 상태 메시지 출력 구현
- Raspberry Pi와 STM32 간 UART 통신 실기기 테스트
- 전체 하드웨어 회로 연결 및 통합 테스트
- 실제 시연 환경에서 얼굴 인증 및 음주 측정 안정화

---

# 👥 Team

- 박종빈, 정재영: Face Authentication
- 정재영, 박세연: Alcohol Detection
- 박세연: Raspberry Pi Integration
- 박종빈: STM32 Embedded System