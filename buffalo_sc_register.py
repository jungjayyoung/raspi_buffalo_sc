import cv2
import numpy as np
import glob
import os

from insightface.app import FaceAnalysis

from config import (
    FACE_MODEL_NAME,
    FACE_PROVIDER,
    FACE_DET_SIZE,
    REGISTERED_EMBEDDING_PATH,
    DB_DIR
)

# =========================
# [수정됨] 등록 운전자 이미지 폴더
# 기존 person 폴더 대신 db/images/registered_driver 사용
# =========================
REGISTERED_IMAGE_DIR = "db/images/registered_driver"

# =========================
# [추가됨] DB 폴더 생성
# =========================
os.makedirs(DB_DIR, exist_ok=True)

# =========================
# 모델 로드
# =========================
app = FaceAnalysis(
    name=FACE_MODEL_NAME,
    providers=FACE_PROVIDER
)

app.prepare(
    ctx_id=0,
    det_size=FACE_DET_SIZE
)

# =========================
# [수정됨] 등록 운전자 이미지 읽기
# =========================
image_paths = glob.glob(
    os.path.join(REGISTERED_IMAGE_DIR, "*.jpg")
)

if len(image_paths) == 0:

    print("등록 운전자 이미지가 없습니다.")
    print(f"이미지 폴더: {REGISTERED_IMAGE_DIR}")
    exit()

embeddings = []

for path in image_paths:

    img = cv2.imread(path)

    if img is None:

        print(f"이미지 읽기 실패: {path}")
        continue

    faces = app.get(img)

    if len(faces) == 0:

        print(f"얼굴 검출 실패: {path}")
        continue

    # =========================
    # [수정됨] 가장 큰 얼굴 선택
    # 이미지에 여러 얼굴이 있을 경우 가장 큰 얼굴 사용
    # =========================
    face = max(
        faces,
        key=lambda f: (
            (f.bbox[2] - f.bbox[0]) *
            (f.bbox[3] - f.bbox[1])
        )
    )

    embedding = face.embedding

    embeddings.append(embedding)

    print(f"등록 이미지 처리 완료: {path}")

if len(embeddings) == 0:

    print("사용 가능한 얼굴 embedding이 없습니다.")
    exit()

# =========================
# [수정됨] 평균 임베딩 생성
# =========================
registered_embedding = np.mean(
    embeddings,
    axis=0
)

# =========================
# [수정됨] db/known_embedding.npy 저장
# =========================
np.save(
    REGISTERED_EMBEDDING_PATH,
    registered_embedding
)

print("등록 운전자 embedding 저장 완료")
print(f"저장 경로: {REGISTERED_EMBEDDING_PATH}")