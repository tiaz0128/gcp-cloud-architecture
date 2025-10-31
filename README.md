
# 🏗️ Cloud Architecture Diagram Generator

## 프로젝트 개요

- **클라우드 도식화**에 관심이 많음
  - 이것저것 써봄 / 수동 / 자유도🔻/ 유료...
- AI 기반 클라우드 **아키텍처 다이어그램 자동 생성** 웹 애플리케이션
- 자연어 설명을 다이어그램으로 변환

## 프로젝트 링크

<div align="center">
  <h3><a href="https://storage.googleapis.com/gleaming-modem-474701-f3-cloud-architecture-frontend/index.html">URL 링크 클릭</h3>
  <img src="img/qr.png" width="320px"/>
</div>

## 🚀 주요 기능

- **AI 기반 다이어그램 생성**: Gemini AI를 활용한 자연어 설명 → 다이어그램 자동 변환
- **멀티 클라우드 지원**: GCP, AWS, Azure 아키텍처 다이어그램 생성
- **실시간 렌더링**: Mermaid를 이용한 인터랙티브 다이어그램
- **수동 코드 입력**: Architecture-beta 코드를 직접 작성하여 렌더링
- **다이어그램 내보내기**: SVG, PNG 형식으로 다운로드

## 🛠️ 기술 스택

### Backend
- **FastAPI**: Python 웹 프레임워크
- **Vertex AI (Gemini)**: AI 기반 다이어그램 생성
- **Firestore**: 다이어그램 데이터 저장
- **Cloud Run**: 서버리스 배포

### Frontend
- **HTML/CSS/JavaScript**: 순수 웹 기술
- **Mermaid.js**: 다이어그램 렌더링
- **Cloud Storage**: 정적 웹 호스팅

## 📋 환경 변수 설정

### 필수 환경 변수

```bash
# GCP 프로젝트 ID (필수)
export GOOGLE_CLOUD_PROJECT=your-project-id

# 또는 다음 중 하나
export GCP_PROJECT=your-project-id
export GCLOUD_PROJECT=your-project-id
```

### 선택적 환경 변수

```bash
# CORS 허용 오리진 (쉼표로 구분, 기본값: *)
# 프로덕션에서는 반드시 설정 권장
export ALLOWED_ORIGINS="https://example.com,https://storage.googleapis.com"

# 개발 환경 기본 프로젝트 ID (개발용)
export DEFAULT_PROJECT_ID=your-dev-project-id

# Cloud Storage 버킷 접미사 (프론트엔드 배포용)
export BUCKET_SUFFIX=cloud-architecture-frontend
```

## 🔧 로컬 개발 환경 설정

### 1. 백엔드 실행

```bash
cd backend

# UV를 사용한 의존성 설치
uv venv
uv sync

# 환경변수 설정
export GOOGLE_CLOUD_PROJECT=your-project-id

# 서버 실행
uvicorn main:app --reload --port 8080
```

### 2. 프론트엔드 실행

```bash
cd frontend

# 간단한 HTTP 서버 실행
python3 -m http.server 8000

# 또는
npx serve .
```

브라우저에서 `http://localhost:8000` 접속

## 🚀 배포

### 백엔드 배포

```bash
# .env 파일 생성
cat > .env << EOF
GOOGLE_CLOUD_PROJECT=your-project-id
ALLOWED_ORIGINS=https://your-domain.com
EOF

# 배포 실행
./deploy-backend.sh
```

### 프론트엔드 배포

```bash
./deploy-frontend.sh
```

## 📚 API 문서

배포 후 다음 URL에서 API 문서 확인:
- Swagger UI: `https://your-backend-url/docs`
- ReDoc: `https://your-backend-url/redoc`

### 주요 엔드포인트

- `POST /generate-diagram`: AI로 다이어그램 생성
- `GET /diagrams`: 다이어그램 목록 조회
- `GET /diagrams/{id}`: 특정 다이어그램 조회
- `PUT /diagrams/{id}`: 다이어그램 수정
- `DELETE /diagrams/{id}`: 다이어그램 삭제
- `GET /health`: 서비스 상태 확인

## 🔒 보안

자세한 보안 정보는 [SECURITY_SUMMARY.md](SECURITY_SUMMARY.md) 참조

### 주요 보안 기능
- ✅ 입력 검증 (길이 제한, 패턴 매칭)
- ✅ 설정 가능한 CORS
- ✅ 에러 처리 및 로깅
- ⚠️ 인증/권한 관리 (추가 권장)
- ⚠️ Rate Limiting (추가 권장)

## 📊 코드 리뷰

전체 코드 리뷰 결과는 [CODE_REVIEW.md](CODE_REVIEW.md) 참조

**전체 품질 점수:** ⭐⭐⭐⭐ (4/5)

## 📝 라이선스

MIT License

## 👨‍💻 개발자

- GitHub: [@tiaz0128](https://github.com/tiaz0128)

---

<br/>
<br/>
<br/>

![](img/marp-01.png)
![](img/marp-02.png)
![](img/marp-03.png)
![](img/marp-04.png)
![](img/marp-05.png)
![](img/marp-06.png)
![](img/marp-07.png)
![](img/marp-08.png)
![](img/marp-09.png)
![](img/marp-10.png)
![](img/marp-11.png)
![](img/marp-12.png)
![](img/marp-13.png)
![](img/marp-14.png)
![](img/marp-15.png)
