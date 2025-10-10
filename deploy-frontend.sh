#!/bin/bash

# 프론트엔드만 배포하는 스크립트 (캐싱 문제 해결 버전)
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

# 백엔드 서비스 URL 가져오기
echo "🔍 백엔드 서비스 URL 확인 중..."
BACKEND_URL=$(gcloud run services describe cloud-diagram-generator --region=asia-northeast3 --format="value(status.url)" 2>/dev/null || echo "")

if [ -z "$BACKEND_URL" ]; then
    echo "⚠️  백엔드 서비스를 찾을 수 없습니다. API URL 설정을 건너뜁니다."
    BACKEND_URL="https://cloud-diagram-generator-hfqglxuxxa-du.a.run.app"
fi

echo "🌐 백엔드 서비스 URL: $BACKEND_URL"

# 임시 디렉토리 생성
TEMP_DIR=$(mktemp -d)
echo "📁 임시 빌드 디렉토리: $TEMP_DIR"

# 프론트엔드 파일 복사
echo "📋 프론트엔드 파일 복사 중..."
cp -r frontend/* $TEMP_DIR/ 2>/dev/null || true
cp -r frontend/.[^.]* $TEMP_DIR/ 2>/dev/null || true

# 복사된 파일 목록 표시
echo "✅ 복사된 파일 목록:"
find $TEMP_DIR -type f | sed "s|$TEMP_DIR/|   • |g" | sort

# 메타 태그에 백엔드 URL 설정
echo "🔧 API URL 자동 설정 중..."
if [ -f "$TEMP_DIR/index.html" ]; then
    if grep -q "api-base-url" $TEMP_DIR/index.html; then
        sed -i "s|<meta name=\"api-base-url\" content=\"[^\"]*\">|<meta name=\"api-base-url\" content=\"$BACKEND_URL\">|g" $TEMP_DIR/index.html
    else
        sed -i "s|</head>|    <meta name=\"api-base-url\" content=\"$BACKEND_URL\">\n</head>|g" $TEMP_DIR/index.html
    fi
    echo "✅ index.html에 API URL 설정 완료"
fi

# 타임스탬프 추가 (브라우저 캐시 무효화용)
TIMESTAMP=$(date +%s)
echo "🕐 배포 타임스탬프: $TIMESTAMP"

# index.html에 타임스탬프 메타 태그 추가
if [ -f "$TEMP_DIR/index.html" ]; then
    sed -i "s|</head>|    <meta name=\"deploy-timestamp\" content=\"$TIMESTAMP\">\n</head>|g" $TEMP_DIR/index.html
fi

# 기존 파일들 삭제
echo "🗑️  기존 파일들 삭제 중..."
gsutil -m rm -r gs://$BUCKET_NAME/** 2>/dev/null || echo "ℹ️  삭제할 기존 파일이 없습니다."

# 삭제 완료 대기
sleep 2

echo "📤 프론트엔드 파일을 Cloud Storage에 업로드 중 (캐시 헤더 포함)..."

# 공통 캐시 헤더 설정
NO_CACHE="Cache-Control:no-cache, no-store, must-revalidate, max-age=0"

# HTML 파일 업로드
if [ -f "$TEMP_DIR/index.html" ]; then
    gsutil -h "$NO_CACHE" \
           -h "Content-Type:text/html; charset=utf-8" \
           cp $TEMP_DIR/index.html gs://$BUCKET_NAME/
    echo "✅ index.html 업로드 완료"
fi

if [ -f "$TEMP_DIR/404.html" ]; then
    gsutil -h "$NO_CACHE" \
           -h "Content-Type:text/html; charset=utf-8" \
           cp $TEMP_DIR/404.html gs://$BUCKET_NAME/
    echo "✅ 404.html 업로드 완료"
fi

# CSS 파일 업로드
if [ -f "$TEMP_DIR/styles.css" ]; then
    gsutil -h "$NO_CACHE" \
           -h "Content-Type:text/css; charset=utf-8" \
           cp $TEMP_DIR/styles.css gs://$BUCKET_NAME/
    echo "✅ styles.css 업로드 완료"
fi

# JavaScript 파일 업로드
if [ -f "$TEMP_DIR/app.js" ]; then
    gsutil -h "$NO_CACHE" \
           -h "Content-Type:application/javascript; charset=utf-8" \
           cp $TEMP_DIR/app.js gs://$BUCKET_NAME/
    echo "✅ app.js 업로드 완료"
fi

# 아이콘 디렉토리가 있으면 업로드
if [ -d "$TEMP_DIR/icons" ]; then
    echo "🎨 아이콘 파일 업로드 중..."
    for icon_file in $TEMP_DIR/icons/*.json; do
        if [ -f "$icon_file" ]; then
            filename=$(basename "$icon_file")
            gsutil -h "$NO_CACHE" \
                   -h "Content-Type:application/json; charset=utf-8" \
                   cp "$icon_file" gs://$BUCKET_NAME/icons/
        fi
    done
    echo "✅ 아이콘 파일 업로드 완료"
fi

# 기타 파일들 업로드 (images, fonts 등)
for dir in $TEMP_DIR/*; do
    if [ -d "$dir" ]; then
        dirname=$(basename "$dir")
        # 이미 처리한 icons 디렉토리는 건너뛰기
        if [ "$dirname" != "icons" ]; then
            echo "📦 $dirname 디렉토리 업로드 중..."
            gsutil -m -h "$NO_CACHE" cp -r "$dir" gs://$BUCKET_NAME/
            echo "✅ $dirname 업로드 완료"
        fi
    fi
done

# 버킷의 기본 캐시 설정 확인
echo ""
echo "🔍 업로드된 파일의 메타데이터 확인..."
gsutil stat gs://$BUCKET_NAME/index.html | grep -E "Cache-Control|Content-Type" || echo "⚠️ 메타데이터를 확인할 수 없습니다."

# 임시 디렉토리 정리
rm -rf $TEMP_DIR

echo ""
echo "🎉 프론트엔드 배포 완료!"
echo ""
echo "=== 📋 배포 정보 ==="
echo "🌍 프론트엔드 웹사이트:"
echo "   • 메인 URL: https://storage.googleapis.com/$BUCKET_NAME/index.html"
echo "   • Cloud Storage URL: https://$BUCKET_NAME.storage.googleapis.com"
echo ""
echo "🔗 연결된 백엔드 API: $BACKEND_URL"
echo "💾 Cloud Storage 버킷: gs://$BUCKET_NAME"
echo "🕐 배포 타임스탬프: $TIMESTAMP"
echo ""
echo "✨ 모든 파일에 no-cache 헤더가 설정되었습니다."
echo ""
echo "💡 브라우저에서 테스트 방법:"
echo "   1. 시크릿/프라이빗 모드로 열기"
echo "   2. 일반 모드에서 Ctrl+Shift+R (하드 리프레시)"
echo "   3. 개발자 도구(F12) > Network > 'Disable cache' 체크"
echo ""
echo "🔍 캐시 설정 확인:"
echo "   gsutil stat gs://$BUCKET_NAME/index.html"