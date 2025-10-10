#!/bin/bash

# 프론트엔드만 배포하는 스크립트
# HTML 파일 수정 후 빠르게 배포하고 싶을 때 사용

set -e  # 에러 발생 시 스크립트 중단

echo "🚀 프론트엔드만 배포 시작..."
echo "📂 현재 작업 디렉토리: $(pwd)"

# 프론트엔드 파일 확인
if [ ! -f "frontend/index.html" ]; then
    echo "❌ frontend/index.html 파일을 찾을 수 없습니다."
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

# 버킷명 설정
if [ -n "$BUCKET_SUFFIX" ]; then
    BUCKET_NAME="${GOOGLE_CLOUD_PROJECT}-${BUCKET_SUFFIX}"
else
    BUCKET_NAME="${GOOGLE_CLOUD_PROJECT}-cloud-architecture-frontend"
fi

echo "✅ Google Cloud 프로젝트: $GOOGLE_CLOUD_PROJECT"
echo "✅ Cloud Storage 버킷명: $BUCKET_NAME"

# Google Cloud 인증 확인
echo "🔐 Google Cloud 인증 상태 확인..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null; then
    echo "❌ Google Cloud에 로그인되지 않았습니다."
    echo "💡 다음 명령어로 로그인하세요:"
    echo "   gcloud auth login"
    exit 1
fi

# 백엔드 서비스 URL 가져오기 (메타 태그 설정용)
echo "🔍 백엔드 서비스 URL 확인 중..."
BACKEND_URL=$(gcloud run services describe cloud-diagram-generator --region=asia-northeast3 --format="value(status.url)" 2>/dev/null || echo "")

if [ -z "$BACKEND_URL" ]; then
    echo "⚠️  백엔드 서비스를 찾을 수 없습니다. API URL 설정을 건너뜁니다."
    BACKEND_URL="https://cloud-diagram-generator-hfqglxuxxa-du.a.run.app"  # 기본값
fi

echo "🌐 백엔드 서비스 URL: $BACKEND_URL"

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

# 커스텀 아이콘 파일들 복사
if [ -d "frontend/icons" ]; then
    cp -r frontend/icons $TEMP_DIR/
    echo "✅ icons 디렉토리 포함"
fi

# 추가 정적 파일들이 있으면 복사
if [ -d "frontend/assets" ]; then
    cp -r frontend/assets $TEMP_DIR/
    echo "✅ assets 디렉토리 포함"
fi

# 메타 태그에 백엔드 URL 설정
echo "🔧 API URL 자동 설정 중..."
# 기존 메타 태그가 있으면 교체, 없으면 head 섹션에 추가
if grep -q "api-base-url" $TEMP_DIR/index.html; then
    sed -i "s|<meta name=\"api-base-url\" content=\"[^\"]*\">|<meta name=\"api-base-url\" content=\"$BACKEND_URL\">|g" $TEMP_DIR/index.html
else
    # head 섹션 끝에 메타 태그 추가
    sed -i "s|</head>|    <meta name=\"api-base-url\" content=\"$BACKEND_URL\">\n</head>|g" $TEMP_DIR/index.html
fi

# 기존 HTML 파일들 완전 삭제 (캐시 문제 해결)
echo "🗑️  기존 HTML 파일들 완전 삭제 중 (캐시 초기화)..."
gsutil rm gs://$BUCKET_NAME/index.html 2>/dev/null || echo "ℹ️  기존 index.html이 없습니다."
gsutil rm gs://$BUCKET_NAME/404.html 2>/dev/null || echo "ℹ️  기존 404.html이 없습니다."

echo "📤 프론트엔드 파일을 Cloud Storage에 새로 업로드 중..."

# HTML과 404 파일을 새로 업로드
gsutil cp $TEMP_DIR/index.html gs://$BUCKET_NAME/

if [ -f "$TEMP_DIR/404.html" ]; then
    gsutil cp $TEMP_DIR/404.html gs://$BUCKET_NAME/
fi

# 아이콘 파일이 있으면 업데이트
if [ -d "$TEMP_DIR/icons" ]; then
    echo "🎨 아이콘 파일 업데이트 중..."
    gsutil -m cp -r $TEMP_DIR/icons/* gs://$BUCKET_NAME/icons/
fi

# HTML 파일에 no-cache 설정 (즉시 업데이트)
echo "📄 HTML 파일 no-cache 설정..."
gsutil setmeta -h "Cache-Control:no-cache, no-store, must-revalidate" \
    -h "Pragma:no-cache" \
    -h "Expires:0" \
    -h "Content-Type:text/html; charset=utf-8" \
    gs://$BUCKET_NAME/index.html

if [ -f "$TEMP_DIR/404.html" ]; then
    gsutil setmeta -h "Cache-Control:no-cache, no-store, must-revalidate" \
        -h "Pragma:no-cache" \
        -h "Expires:0" \
        -h "Content-Type:text/html; charset=utf-8" \
        gs://$BUCKET_NAME/404.html
fi

# 임시 디렉토리 정리
rm -rf $TEMP_DIR

# Cloud CDN 캐시 무효화 (만약 CDN을 사용하고 있다면)
echo "🔄 전역 캐시 무효화 시도 중..."
# Cloud Storage의 전역 캐시를 강제로 새로고침
curl -X POST "https://storage.googleapis.com/$BUCKET_NAME/index.html" \
     -H "Cache-Control: no-cache" 2>/dev/null || echo "ℹ️  캐시 무효화 요청 완료"

echo ""
echo "🎉 프론트엔드 배포 완료! (캐시 완전 삭제됨)"
echo ""
echo "=== 📋 배포 정보 ==="
echo "🌍 프론트엔드 웹사이트:"
echo "   • 메인 URL: https://$BUCKET_NAME.storage.googleapis.com"
echo "   • 직접 링크: https://storage.googleapis.com/$BUCKET_NAME/index.html"
echo "   • 캐시 우회 URL: https://storage.googleapis.com/$BUCKET_NAME/index.html?v=$(date +%s)"
echo ""
echo "🔗 연결된 백엔드 API: $BACKEND_URL"
echo "💾 Cloud Storage 버킷: gs://$BUCKET_NAME"
echo ""
echo "✨ 캐시가 완전히 삭제되었으므로 즉시 변경사항이 적용됩니다!"
echo "💡 여전히 브라우저 캐시가 있다면 Ctrl+Shift+R (하드 리프레시)를 사용하세요."
echo "🔄 또는 캐시 우회 URL을 사용하세요."