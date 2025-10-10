# Cloud Architecture Diagram Generator

AI로 클라우드 아키텍처를 자동으로 시각화하는 웹 애플리케이션입니다. 백엔드는 FastAPI로 구현되었고, 프론트엔드는 정적 HTML/JavaScript로 구현되어 Google Cloud Platform에 배포됩니다.

## 🏗️ 프로젝트 구조

```
gcp-cloud-architecture/
├── deploy.sh              # 🚀 통합 배포 스크립트
├── .env                   # 📋 환경변수
├── README.md              # 📖 프로젝트 문서
├── backend/               # 🔧 FastAPI 백엔드
│   ├── main.py
│   ├── cloudbuild.yaml
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── ...
└── frontend/              # 🎨 웹 프론트엔드
    ├── index.html
    ├── 404.html
    └── ...
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd gcp-cloud-architecture

# 환경변수 파일 생성
cp .env.template .env

# .env 파일 편집하여 Google Cloud 프로젝트 ID 설정
nano .env
```

`.env` 파일 설정 예시:
```bash
GOOGLE_CLOUD_PROJECT=my-project-123
BUCKET_SUFFIX=cloud-architecture-frontend  # 선택사항
```

### 2. Google Cloud 설정

```bash
# Google Cloud CLI 설치 (아직 설치하지 않은 경우)
# https://cloud.google.com/sdk/docs/install

# 로그인 및 프로젝트 설정
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 필요한 API 활성화
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable storage.googleapis.com
```

### 3. 한 번에 배포

```bash
# 프로젝트 루트에서 실행
./deploy.sh
```

## ✨ 배포 과정

`./deploy.sh` 스크립트는 다음 단계를 자동으로 수행합니다:

1. **환경 검증**: 프로젝트 구조 및 환경변수 확인
2. **Cloud Storage**: 프론트엔드 호스팅용 버킷 생성 및 설정
3. **백엔드 배포**: Cloud Run으로 FastAPI 서비스 배포
4. **프론트엔드 배포**: 
   - 백엔드 URL을 자동으로 프론트엔드에 설정
   - Cloud Storage에 정적 웹사이트로 배포
5. **배포 정보 출력**: 접속 URL 및 서비스 정보 제공

## 🌐 배포 결과

배포 완료 후 다음과 같은 서비스들이 생성됩니다:

- **백엔드 API**: `https://cloud-diagram-generator-xxx.run.app`
- **프론트엔드 웹사이트**: `https://your-project-cloud-architecture-frontend.storage.googleapis.com`
- **Cloud Storage 버킷**: `gs://your-project-cloud-architecture-frontend`

## 🔧 개발 및 커스터마이징

### 로컬 개발

#### 백엔드 개발
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

#### 프론트엔드 개발
```bash
# 로컬 웹서버 실행 (Python 3)
cd frontend
python -m http.server 3000
```

### 환경변수 옵션

`.env` 파일에서 설정할 수 있는 옵션들:

- `GOOGLE_CLOUD_PROJECT`: Google Cloud 프로젝트 ID (필수)
- `BUCKET_SUFFIX`: Cloud Storage 버킷 이름 접미사 (선택)
- `DEPLOY_REGION`: 배포 리전 (기본값: asia-northeast3)
- `SERVICE_NAME`: Cloud Run 서비스명 (기본값: cloud-diagram-generator)

## 📊 주요 기능

- **AI 기반 다이어그램 생성**: Google Gemini를 사용한 자동 아키텍처 다이어그램 생성
- **다중 클라우드 지원**: GCP, AWS, Azure 아키텍처 지원
- **실시간 시각화**: Mermaid.js를 사용한 즉시 렌더링
- **다운로드 기능**: SVG/PNG 형식으로 다이어그램 다운로드
- **코드 복사**: Mermaid 코드 클립보드 복사

## 🛠️ 기술 스택

### 백엔드
- **FastAPI**: Python 웹 프레임워크
- **Google Cloud Firestore**: NoSQL 데이터베이스
- **Google Vertex AI (Gemini)**: AI 모델
- **Docker**: 컨테이너화
- **Google Cloud Run**: 서버리스 컨테이너 플랫폼

### 프론트엔드
- **HTML5/CSS3/JavaScript**: 웹 표준 기술
- **Mermaid.js**: 다이어그램 렌더링
- **Google Cloud Storage**: 정적 웹사이트 호스팅

### 인프라
- **Google Cloud Build**: CI/CD
- **Artifact Registry**: 컨테이너 이미지 저장소
- **Cloud Storage**: 정적 파일 호스팅

## 🔄 업데이트 배포

코드 변경 후 재배포하려면:

```bash
# 프로젝트 루트에서
./deploy.sh
```

기존 리소스를 재사용하여 빠르게 업데이트됩니다.

## 🗑️ 리소스 정리

배포된 리소스를 삭제하려면:

```bash
# Cloud Run 서비스 삭제
gcloud run services delete cloud-diagram-generator --region=asia-northeast3

# Cloud Storage 버킷 삭제
gsutil rm -r gs://your-project-cloud-architecture-frontend

# Artifact Registry 리포지토리 삭제 (선택사항)
gcloud artifacts repositories delete cloud-run-source-deploy --location=asia-northeast3
```

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 제공됩니다.

## 🤝 기여

프로젝트에 기여하고 싶으시다면 Pull Request를 제출해주세요!

---

**💡 문제가 발생하면?**

1. Google Cloud 계정 및 프로젝트 설정 확인
2. 필요한 API들이 활성화되어 있는지 확인
3. `.env` 파일의 환경변수 설정 확인
4. `gcloud auth list`로 인증 상태 확인

### json 파일 재배포

```bash
gsutil -m setmeta -h "Cache-Control:no-cache, no-store, must-revalidate" -h "Content-Type:application/json" gs://gleaming-modem-474701-f3-cloud-architecture-frontend/icons/*.json
```