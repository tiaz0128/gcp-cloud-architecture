#!/bin/bash

# 백엔드만 배포하는 스크립트
# API 수정 후 빠르게 백엔드만 다시 배포하고 싶을 때 사용

set -e  # 에러 발생 시 스크립트 중단

echo "🚀 백엔드만 배포 시작..."
echo "📂 현재 작업 디렉토리: $(pwd)"

# 백엔드 디렉토리 확인
if [ ! -d "backend" ]; then
    echo "❌ backend 디렉토리를 찾을 수 없습니다."
    echo "📍 올바른 실행 위치: 프로젝트 최상단 (gcp-cloud-architecture)"
    exit 1
fi

# 백엔드 필수 파일 확인
if [ ! -f "backend/cloudbuild.yaml" ]; then
    echo "❌ backend/cloudbuild.yaml 파일을 찾을 수 없습니다."
    exit 1
fi

if [ ! -f "backend/main.py" ]; then
    echo "❌ backend/main.py 파일을 찾을 수 없습니다."
    exit 1
fi

# .env 파일에서 환경변수 로드
if [ -f ".env" ]; then
    echo "📋 .env 파일에서 환경변수를 로드합니다..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "✅ .env 파일 로드 완료"
else
    echo "⚠️  .env 파일을 찾을 수 없습니다."
fi

# 환경변수 확인
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "❌ GOOGLE_CLOUD_PROJECT 환경변수가 설정되지 않았습니다."
    echo "📝 .env 파일을 생성하거나 환경변수를 설정해주세요:"
    echo "   export GOOGLE_CLOUD_PROJECT=your-project-id"
    exit 1
fi

echo "✅ Google Cloud 프로젝트: $GOOGLE_CLOUD_PROJECT"

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

# 필수 API 활성화 확인
echo "🔧 필수 API 활성화 확인..."
REQUIRED_APIS=("cloudbuild.googleapis.com" "run.googleapis.com" "artifactregistry.googleapis.com")

for api in "${REQUIRED_APIS[@]}"; do
    if ! gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo "⚡ $api 활성화 중..."
        gcloud services enable $api
    else
        echo "✅ $api 이미 활성화됨"
    fi
done

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

echo "📋 배포할 파일 확인:"
echo "   • main.py: $(ls -la main.py 2>/dev/null || echo '없음')"
echo "   • Dockerfile: $(ls -la Dockerfile 2>/dev/null || echo '없음')"
echo "   • pyproject.toml: $(ls -la pyproject.toml 2>/dev/null || echo '없음')"
echo "   • cloudbuild.yaml: $(ls -la cloudbuild.yaml 2>/dev/null || echo '없음')"

echo ""
echo "🚀 Cloud Build 시작 (asia-northeast3 리전)..."
gcloud builds submit --config cloudbuild.yaml \
    --region=asia-northeast3

if [ $? -ne 0 ]; then
    echo "❌ 백엔드 배포 실패"
    cd ..
    exit 1
fi

echo "✅ Cloud Build 완료!"

# 배포된 서비스 URL 가져오기
echo "🔍 배포된 서비스 정보 확인 중..."
BACKEND_URL=$(gcloud run services describe cloud-diagram-generator --region=asia-northeast3 --format="value(status.url)")

if [ -z "$BACKEND_URL" ]; then
    echo "⚠️  서비스 URL을 가져올 수 없습니다. 잠시 후 다시 확인해주세요."
else
    echo "🌐 백엔드 서비스 URL: $BACKEND_URL"
fi

# 서비스 상태 확인
echo "📊 서비스 상태 확인..."
gcloud run services describe cloud-diagram-generator --region=asia-northeast3 --format="table(status.conditions[0].type,status.conditions[0].status,status.conditions[0].reason)"

# 프로젝트 루트로 돌아가기
cd ..

echo ""
echo "🎉 백엔드 배포 완료!"
echo ""
echo "=== 📋 배포 정보 ==="
echo "🏗️  서비스명: cloud-diagram-generator"
echo "🌍 리전: asia-northeast3"
echo "🌐 API 엔드포인트: $BACKEND_URL"
echo "🌏 GCP 프로젝트: $GOOGLE_CLOUD_PROJECT"
echo ""
echo "✨ API 테스트 방법:"
echo "   curl $BACKEND_URL/health"
echo "   curl $BACKEND_URL/api/docs (API 문서)"
echo ""
echo "💡 프론트엔드도 함께 배포하려면 './deploy-frontend.sh'를 실행하세요."