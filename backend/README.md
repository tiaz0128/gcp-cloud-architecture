# Cloud Architecture Diagram Generator

GCP 클라우드 아키텍처 다이어그램을 AI로 자동 생성하는 FastAPI 백엔드 서비스입니다.

## 환경 설정

### 1. 환경 변수 설정

배포하기 전에 환경 변수를 설정해야 합니다:

```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일을 편집하여 실제 값들을 입력
nano .env
```

`.env` 파일에서 설정해야 할 값들:

- `GEMINI_API_KEY`: Google AI Studio에서 발급받은 Gemini API 키
- `GOOGLE_CLOUD_PROJECT`: Google Cloud 프로젝트 ID

### 2. 배포

환경 변수 설정 후 배포 스크립트를 실행:

```bash
./deploy.sh
```

## API 엔드포인트

- `GET /`: 서비스 정보
- `GET /health`: 헬스체크
- `POST /generate-diagram`: 다이어그램 생성
- `GET /diagrams`: 다이어그램 목록
- `GET /diagrams/{id}`: 특정 다이어그램 조회
- `PUT /diagrams/{id}`: 다이어그램 수정
- `DELETE /diagrams/{id}`: 다이어그램 삭제

## 기술 스택

- FastAPI
- Google Cloud Firestore
- Google Vertex AI (Gemini)
- Docker
- Google Cloud Run