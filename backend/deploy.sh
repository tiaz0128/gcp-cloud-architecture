#!/bin/bash

echo "🚀 Cloud Diagram Generator 배포 시작..."

# .env 파일에서 환경변수 로드
if [ -f ".env" ]; then
    echo "📋 .env 파일에서 환경변수를 로드합니다..."
    # .env 파일을 읽어서 환경변수로 설정
    export $(grep -v '^#' .env | xargs)
    echo "✅ .env 파일 로드 완료"
else
    echo "⚠️  .env 파일을 찾을 수 없습니다. 기본 환경변수를 확인합니다..."
fi

# 환경변수 확인
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "❌ GOOGLE_CLOUD_PROJECT 환경변수가 설정되지 않았습니다."
    echo "📝 .env 파일을 편집하여 프로젝트 ID를 설정해주세요:"
    echo "   GOOGLE_CLOUD_PROJECT=your_project_id"
    exit 1
fi

echo "✅ 프로젝트: $GOOGLE_CLOUD_PROJECT"
echo "✅ 환경변수 설정 완료"

# Artifact Registry 리포지토리 생성 (필요한 경우)
echo "📦 Artifact Registry 리포지토리 확인..."
gcloud artifacts repositories create cloud-run-source-deploy \
    --repository-format=docker \
    --location=asia-northeast3 \
    --description="Docker repository for Cloud Run" 2>/dev/null || echo "리포지토리가 이미 존재합니다."

# Docker에서 Artifact Registry 인증
echo "🔐 Docker 인증 설정..."
gcloud auth configure-docker asia-northeast3-docker.pkg.dev

# Cloud Build로 배포
echo "🏗️ Cloud Build 실행..."
gcloud builds submit --config cloudbuild.yaml \
    --region=asia-northeast3

if [ $? -eq 0 ]; then
    echo "✅ 배포 완료!"
    echo "🌐 서비스 URL:"
    gcloud run services describe cloud-diagram-generator --region=asia-northeast3 --format="value(status.url)"
else
    echo "❌ 배포 실패"
    exit 1
fi