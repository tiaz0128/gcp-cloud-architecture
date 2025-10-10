#!/bin/bash

# Cloud Architecture Diagram Generator 통합 배포 스크립트
# 프로젝트 최상단에서 실행하여 백엔드와 프론트엔드를 모두 배포합니다.

set -e  # 에러 발생 시 스크립트 중단

echo "🚀 Cloud Diagram Generator 통합 배포 시작..."
echo "📂 현재 작업 디렉토리: $(pwd)"

# 프로젝트 구조 확인
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ 프로젝트 구조가 올바르지 않습니다."
    echo "📁 현재 디렉토리에 'backend'와 'frontend' 폴더가 있는지 확인해주세요."
    echo "📍 올바른 실행 위치: 프로젝트 최상단 (gcp-cloud-architecture)"
    exit 1
fi

# .env 파일에서 환경변수 로드
if [ -f ".env" ]; then
    echo "📋 .env 파일에서 환경변수를 로드합니다..."
    # .env 파일을 읽어서 환경변수로 설정 (주석과 빈 줄 제외)
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "✅ .env 파일 로드 완료"
else
    echo "⚠️  .env 파일을 찾을 수 없습니다. 기본 환경변수를 확인합니다..."
fi

# 환경변수 확인
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "❌ GOOGLE_CLOUD_PROJECT 환경변수가 설정되지 않았습니다."
    echo "📝 프로젝트 루트에 .env 파일을 생성하여 프로젝트 ID를 설정해주세요:"
    echo ""
    echo "   GOOGLE_CLOUD_PROJECT=your-project-id"
    echo "   # BUCKET_SUFFIX=custom-suffix  # 선택사항: 버킷명 사용자 정의"
    echo ""
    echo "💡 또는 환경변수로 직접 설정:"
    echo "   export GOOGLE_CLOUD_PROJECT=your-project-id"
    exit 1
fi

echo "✅ Google Cloud 프로젝트: $GOOGLE_CLOUD_PROJECT"

# 버킷명 설정 (사용자 정의 suffix 지원)
if [ -n "$BUCKET_SUFFIX" ]; then
    BUCKET_NAME="${GOOGLE_CLOUD_PROJECT}-${BUCKET_SUFFIX}"
else
    BUCKET_NAME="${GOOGLE_CLOUD_PROJECT}-cloud-architecture-frontend"
fi

echo "✅ Cloud Storage 버킷명: $BUCKET_NAME"
echo "✅ 환경변수 설정 완료"
echo ""

# Google Cloud 인증 확인
echo "🔐 Google Cloud 인증 상태 확인..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null; then
    echo "❌ Google Cloud에 로그인되지 않았습니다."
    echo "💡 다음 명령어로 로그인하세요:"
    echo "   gcloud auth login"
    echo "   gcloud config set project $GOOGLE_CLOUD_PROJECT"
    exit 1
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)
echo "✅ 활성 계정: $ACTIVE_ACCOUNT"

# 현재 프로젝트 확인 및 설정
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ "$CURRENT_PROJECT" != "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "🔧 프로젝트 설정 변경: $CURRENT_PROJECT → $GOOGLE_CLOUD_PROJECT"
    gcloud config set project $GOOGLE_CLOUD_PROJECT
fi

echo ""
echo "=== 🏗️  백엔드 배포 단계 ==="

# Cloud Storage 버킷 생성 (웹사이트 호스팅용)
echo "🪣 Cloud Storage 버킷 확인 및 생성..."
gsutil mb -p $GOOGLE_CLOUD_PROJECT -c STANDARD -l asia-northeast3 gs://$BUCKET_NAME 2>/dev/null || echo "ℹ️  버킷이 이미 존재합니다."

# 웹사이트 호스팅 설정
echo "🌐 웹사이트 호스팅 설정..."
gsutil web set -m index.html -e 404.html gs://$BUCKET_NAME

# 버킷을 공개 읽기로 설정
echo "🔓 버킷 공개 액세스 설정..."
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME

# Artifact Registry 리포지토리 생성 (필요한 경우)
echo "📦 Artifact Registry 리포지토리 확인..."
gcloud artifacts repositories create cloud-run-source-deploy \
    --repository-format=docker \
    --location=asia-northeast3 \
    --description="Docker repository for Cloud Run" 2>/dev/null || echo "ℹ️  리포지토리가 이미 존재합니다."

# Docker에서 Artifact Registry 인증
echo "🔐 Docker 인증 설정..."
gcloud auth configure-docker asia-northeast3-docker.pkg.dev

# 백엔드 디렉토리로 이동하여 Cloud Build 실행
echo "🏗️  백엔드 Cloud Build 실행..."
cd backend

if [ ! -f "cloudbuild.yaml" ]; then
    echo "❌ backend/cloudbuild.yaml 파일을 찾을 수 없습니다."
    exit 1
fi

gcloud builds submit --config cloudbuild.yaml \
    --region=asia-northeast3

if [ $? -ne 0 ]; then
    echo "❌ 백엔드 배포 실패"
    exit 1
fi

# 백엔드 서비스 URL 가져오기
BACKEND_URL=$(gcloud run services describe cloud-diagram-generator --region=asia-northeast3 --format="value(status.url)")
echo "✅ 백엔드 배포 완료!"
echo "🌐 백엔드 서비스 URL: $BACKEND_URL"

# 프로젝트 루트로 돌아가기
cd ..

echo ""
echo "=== 📤 프론트엔드 배포 단계 ==="

# 프론트엔드 파일 존재 확인
if [ ! -f "frontend/index.html" ]; then
    echo "❌ frontend/index.html 파일을 찾을 수 없습니다."
    echo "⚠️  백엔드만 배포되었습니다."
    echo "🌐 백엔드 서비스 URL: $BACKEND_URL"
    exit 0
fi

echo "📂 프론트엔드 파일 확인 완료"

# 임시 디렉토리 생성
TEMP_DIR=$(mktemp -d)
echo "📁 임시 빌드 디렉토리: $TEMP_DIR"

# 프론트엔드 파일들을 임시 디렉토리에 복사
echo "📋 프론트엔드 파일 복사 중..."
cp frontend/index.html $TEMP_DIR/

# 404 페이지가 있으면 복사
if [ -f "frontend/404.html" ]; then
    cp frontend/404.html $TEMP_DIR/
    echo "✅ 404 에러 페이지 포함"
fi

# 추가 정적 파일들이 있으면 복사 (css, js, images 등)
if [ -d "frontend/assets" ]; then
    cp -r frontend/assets $TEMP_DIR/
    echo "✅ assets 디렉토리 포함"
fi

# 메타 태그에 백엔드 URL 설정 (주석 해제하고 URL 설정)
echo "🔧 API URL 자동 설정 중..."
sed -i "s|<!-- <meta name=\"api-base-url\" content=\"https://backend-service-url.run.app\"> -->|<meta name=\"api-base-url\" content=\"$BACKEND_URL\">|g" $TEMP_DIR/index.html

# 프론트엔드 파일을 Cloud Storage에 업로드
echo "📤 프론트엔드 파일을 Cloud Storage에 업로드 중..."
gsutil -m cp -r $TEMP_DIR/* gs://$BUCKET_NAME/

# 캐시 설정 (HTML은 짧은 캐시, 정적 파일은 긴 캐시)
echo "⚡ 캐시 설정 적용 중..."
gsutil -m setmeta -h "Cache-Control:public, max-age=300" gs://$BUCKET_NAME/index.html

if [ -f "$TEMP_DIR/404.html" ]; then
    gsutil -m setmeta -h "Cache-Control:public, max-age=300" gs://$BUCKET_NAME/404.html
fi

# 정적 파일에 대한 긴 캐시 설정 (있는 경우)
if [ -d "$TEMP_DIR/assets" ]; then
    gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" gs://$BUCKET_NAME/assets/**
fi

# CORS 설정 (API 호출을 위해)
echo "🔗 CORS 설정 적용 중..."
echo '[{"origin":["*"],"method":["GET","POST","OPTIONS"],"responseHeader":["Content-Type","Authorization"],"maxAgeSeconds":3600}]' > cors.json
gsutil cors set cors.json gs://$BUCKET_NAME
rm cors.json

# 임시 디렉토리 정리
rm -rf $TEMP_DIR

echo ""
echo "🎉 배포 완료!"
echo ""
echo "=== 📋 배포 정보 ==="
echo "🏗️  백엔드 API: $BACKEND_URL"
echo "🌍 프론트엔드 웹사이트:"
echo "   • 메인 URL: https://$BUCKET_NAME.storage.googleapis.com"
echo "   • 직접 링크: https://storage.googleapis.com/$BUCKET_NAME/index.html"
echo ""
echo "💾 Cloud Storage 버킷: gs://$BUCKET_NAME"
echo "🌏 GCP 프로젝트: $GOOGLE_CLOUD_PROJECT"
echo ""
echo "✨ 웹사이트에 접속하여 클라우드 아키텍처 다이어그램을 생성해보세요!"