# 🏗️ Cloud Architecture Diagram Generator

AI 기반 클라우드 아키텍처 다이어그램 자동 생성 웹 애플리케이션입니다. Google Vertex AI (Gemini 2.5-flash)를 활용하여 자연어 설명을 Mermaid architecture-beta 다이어그램으로 변환합니다.

## ✨ 주요 기능

- **🤖 AI 기반 다이어그램 생성**: Google Gemini를 사용한 자동 아키텍처 다이어그램 생성
- **☁️ 다중 클라우드 지원**: GCP, AWS, Azure 아키텍처 지원
- **📊 실시간 시각화**: Mermaid.js architecture-beta 기반 즉시 렌더링
- 📥 다운로드 기능: SVG/PNG 형식으로 다이어그램 내보내기
- 📋 코드 복사: Mermaid 코드 클립보드 복사
- 🎨 클라우드 아이콘: 각 클라우드 제공자별 공식 아이콘 지원
- ~~💾 다이어그램 관리: Firestore를 통한 다이어그램 저장/조회/수정/삭제~~

## 🏗️ 프로젝트 구조

```text
gcp-cloud-architecture/
├── .env                        # � 환경변수 설정
├── .gitignore                  # � Git 제외 파일
├── README.md                   # 📖 프로젝트 문서 (이 파일)
├── deploy-backend.sh           # 🚀 백엔드 배포 스크립트
├── deploy-frontend.sh          # 🚀 프론트엔드 배포 스크립트
├── backend/                    # 🔧 FastAPI 백엔드 서비스
│   ├── main.py                 # 📡 메인 API 서버 (FastAPI)
│   ├── pyproject.toml          # 📦 Python 패키지 설정 (uv 사용)
│   ├── Dockerfile              # 🐳 컨테이너 이미지 설정
│   ├── cloudbuild.yaml         # ⚙️ Google Cloud Build 설정
│   ├── .dockerignore           # 🚫 Docker 제외 파일
│   ├── .gcloudignore           # 🚫 Cloud Build 제외 파일
│   ├── .python-version         # 🐍 Python 버전 설정
│   └── uv.lock                 # 🔒 의존성 잠금 파일
├── frontend/                   # 🎨 웹 프론트엔드
│   ├── index.html              # 🏠 메인 웹 페이지
│   ├── 404.html                # 📄 404 에러 페이지
│   ├── app.js                  # ⚡ JavaScript 애플리케이션 로직
│   ├── styles.css              # 🎨 CSS 스타일시트
│   └── icons/                  # 🎯 클라우드 아이콘 JSON 파일
│       ├── gcp.json            # Google Cloud Platform 아이콘
│       ├── aws.json            # Amazon Web Services 아이콘
│       └── azr.json            # Microsoft Azure 아이콘
└── utils/                      # 🛠️ 유틸리티 도구
    ├── convert_icons.py        # 🔧 SVG → JSON 아이콘 변환기
    └── icons/                  # 📁 원본 SVG 아이콘 파일
        └── gcp/                # Google Cloud Platform SVG 아이콘
            ├── cloud_run.svg
            ├── cloud_storage.svg
            ├── firestore.svg
            └── ... (100+ 아이콘)
```

## 🚀 빠른 시작

### 📋 사전 요구사항

- **Google Cloud Platform 계정** 및 프로젝트
- **Google Cloud CLI** (`gcloud`) 설치 및 로그인
- **bash 셸** (Linux/macOS/WSL)

### 1️⃣ 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd gcp-cloud-architecture

# .env 파일 생성 및 편집
cp .env.template .env  # (템플릿이 있는 경우)
nano .env
```

**`.env` 파일 설정**:
```text
GOOGLE_CLOUD_PROJECT=your-project-id
```

### 2️⃣ Google Cloud 설정

```bash
# Google Cloud CLI 로그인
gcloud auth login

# 프로젝트 설정
gcloud config set project YOUR_PROJECT_ID

# 필요한 API 활성화
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### 3️⃣ Firestore 데이터베이스 설정

```bash
# Firestore 네이티브 모드 데이터베이스 생성
gcloud firestore databases create --region=asia-northeast3
```

### 4️⃣ 배포 실행

```bash
# 백엔드 코드 수정 후 빠른 재배포
./deploy-backend.sh

# 프론트엔드 코드 수정 후 빠른 재배포  
./deploy-frontend.sh
```

## 🛠️ 기술 스택

### 백엔드 (FastAPI)

- **🐍 Python 3.12+**: 최신 Python 기능 활용
- **⚡ FastAPI**: 고성능 웹 프레임워크
- **🤖 Google Vertex AI (Gemini 2.5-flash)**: AI 모델
- **🗄️ Google Cloud Firestore**: NoSQL 데이터베이스
- **📦 uv**: 빠른 Python 패키지 관리자
- **🐳 Docker**: 컨테이너화
- **☁️ Google Cloud Run**: 서버리스 컨테이너 플랫폼

### 프론트엔드 (Vanilla JavaScript)

- **🌐 HTML5/CSS3/JavaScript**: 웹 표준 기술
- **📊 Mermaid.js**: 다이어그램 렌더링 엔진
- **🎯 Custom Icon Packs**: 클라우드 서비스별 아이콘
- **☁️ Google Cloud Storage**: 정적 웹사이트 호스팅

### 인프라 (Google Cloud Platform)

- **🏗️ Google Cloud Build**: CI/CD 파이프라인
- **📦 Artifact Registry**: 컨테이너 이미지 저장소
- **🌐 Cloud Storage**: 정적 파일 호스팅
- **🔧 Cloud Run**: 서버리스 컨테이너 실행
- **🗄️ Firestore**: 문서형 NoSQL 데이터베이스

## 📊 주요 구성 요소

### 🔧 백엔드 API (`backend/main.py`)

**주요 엔드포인트**:
- `POST /generate-diagram`: AI 기반 다이어그램 생성
- `GET /diagrams/{id}`: 특정 다이어그램 조회
- `GET /diagrams`: 다이어그램 목록 조회
- `PUT /diagrams/{id}`: 다이어그램 수정
- `DELETE /diagrams/{id}`: 다이어그램 삭제
- `GET /health`: 서비스 상태 확인

**주요 기능**:
- **🧠 AI 프롬프트 엔지니어링**: Mermaid architecture-beta 구문 생성
- **🔍 코드 검증 및 정리**: 생성된 Mermaid 코드 후처리
- **💾 데이터 영속성**: Firestore를 통한 다이어그램 저장
- **⚡ 에러 처리**: 상세한 오류 메시지 및 로깅

### 🎨 프론트엔드 (`frontend/`)

**주요 기능**:
- **📝 사용자 입력**: 아키텍처 설명 및 클라우드 제공자 선택
- **🎯 예시 템플릿**: 일반적인 아키텍처 패턴 템플릿
- **📊 실시간 렌더링**: Mermaid.js 기반 다이어그램 시각화
- **💾 다운로드**: SVG/PNG 형식 내보내기
- **📋 코드 복사**: Mermaid 소스 코드 클립보드 복사

### 🛠️ 유틸리티 (`utils/convert_icons.py`)

**기능**:
- **🔄 SVG → JSON 변환**: 클라우드 아이콘 SVG를 Mermaid용 JSON으로 변환
- **📏 자동 크기 조정**: viewBox 기반 아이콘 크기 추출
- **🧹 코드 정리**: SVG 내용 최적화 및 정리
- **📦 배치 처리**: 여러 아이콘 파일 일괄 변환

## 🌐 배포 아키텍처

배포 완료 후 다음과 같은 GCP 리소스들이 생성됩니다:

### 🏗️ 백엔드 인프라

- **Cloud Run 서비스**: `cloud-diagram-generator`
  - 리전: `asia-northeast3`
  - URL: `https://cloud-diagram-generator-xxx.run.app`
- **Artifact Registry**: Docker 이미지 저장소
- **Firestore Database**: 다이어그램 데이터 저장

### 🎨 프론트엔드 인프라  

- **Cloud Storage 버킷**: `{PROJECT_ID}-cloud-architecture-frontend`
- **정적 웹사이트 호스팅**: `https://storage.googleapis.com/{BUCKET_NAME}/index.html`

## 💻 로컬 개발

### 🔧 백엔드 개발 환경

```bash
cd backend

uv sync --frozen

uvicorn main:app --reload --port 8080
```

**환경변수 설정** (`.env` 파일):

```text
GOOGLE_CLOUD_PROJECT=your-project-id
# 로컬 개발 시에는 Google Application Default Credentials 사용
# gcloud auth application-default login
```

### 🎨 프론트엔드 개발 환경

**API 연결 설정**:
- 로컬 개발 시 `app.js`에서 자동으로 `localhost:8080` 감지
- 또는 `index.html`에 메타 태그 추가:
```html
<meta name="api-base-url" content="http://localhost:8080">
```

## 🔧 고급 설정

### 🎯 아이콘 시스템 관리

새로운 클라우드 아이콘 추가:
```bash
cd utils

# 1. SVG 파일을 icons/gcp/ 폴더에 추가
# 2. 변환 스크립트 실행
python convert_icons.py

# 3. 생성된 JSON 파일을 frontend/icons/로 복사
cp gcp.json ../frontend/icons/

# 4. 프론트엔드 재배포
cd ..
./deploy-frontend.sh
```

## � 업데이트 및 관리

### 📈 모니터링 및 로그

```bash
# Cloud Run 로그 확인
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cloud-diagram-generator" --limit=50

# Cloud Run 메트릭 확인  
gcloud run services describe cloud-diagram-generator --region=asia-northeast3
```

### 🔧 트러블슈팅

**일반적인 문제와 해결방법**:

1. **Firestore 연결 오류**
   ```bash
   # Firestore 데이터베이스 생성 확인
   gcloud firestore databases list
   
   # 없으면 생성
   gcloud firestore databases create --region=asia-northeast3
   ```

2. **API 권한 오류**
   ```bash
   # 필요한 API 재활성화
   gcloud services enable aiplatform.googleapis.com firestore.googleapis.com
   ```

3. **프론트엔드 API 연결 실패**
   ```bash
   # 백엔드 URL 확인
   gcloud run services describe cloud-diagram-generator --region=asia-northeast3 --format="value(status.url)"
   
   # 프론트엔드 재배포 (API URL 자동 설정)
   ./deploy-frontend.sh
   ```

### 🗑️ 리소스 정리

모든 배포된 리소스 삭제:
```bash
# Cloud Run 서비스 삭제
gcloud run services delete cloud-diagram-generator --region=asia-northeast3

# Cloud Storage 버킷 삭제  
gsutil rm -r gs://${GOOGLE_CLOUD_PROJECT}-cloud-architecture-frontend

# Artifact Registry 리포지토리 삭제 (선택사항)
gcloud artifacts repositories delete cloud-run-source-deploy --location=asia-northeast3

# Firestore 데이터 삭제 (데이터베이스는 유지)
# 주의: 이 명령은 모든 다이어그램 데이터를 삭제합니다
gcloud firestore indexes composite delete --collection-group=diagrams
```

## 📄 API 문서

### 🔍 OpenAPI/Swagger 문서

배포 후 다음 URL에서 API 문서 확인:
- **Swagger UI**: `https://your-backend-url/docs`
- **ReDoc**: `https://your-backend-url/redoc`

### 📊 주요 API 엔드포인트

```http
POST /generate-diagram
Content-Type: application/json

{
  "description": "FastAPI 앱을 Cloud Run으로 배포하고...",
  "cloud_provider": "gcp",
  "diagram_type": "architecture-beta"
}
```

응답:
```json
{
  "id": "diagram-id",
  "mermaid_code": "architecture-beta\n    group vpc(gcp:vpc)...",
  "description": "...",
  "cloud_provider": "gcp", 
  "created_at": "2025-10-10T12:00:00"
}
```
