import cv2
import numpy as np
import glob
from insightface.app import FaceAnalysis

# 모델 로드
app = FaceAnalysis(
    name='buffalo_sc',
    providers=['CPUExecutionProvider']
)

app.prepare(ctx_id=0)

# 이미지 읽기
image_paths = glob.glob(
    "/home/willtek/work/umjoocut/files/person/*.jpg"
)

embeddings = []

for path in image_paths:

    img = cv2.imread(path)

    faces = app.get(img)

    if len(faces) == 0:
        continue

    embedding = faces[0].embedding

    embeddings.append(embedding)

# 평균 임베딩 생성
known_embedding = np.mean(
    embeddings,
    axis=0
)

# 파일 저장
np.save(
    "known_embedding.npy",
    known_embedding
)

print("임베딩 저장 완료")