#!/bin/bash

# DSPM Kubernetes 배포 스크립트
# 환경변수를 사용해서 템플릿에서 실제 YAML 파일 생성

set -e  # 오류 발생시 스크립트 중단

echo "🔧 DSPM Kubernetes 배포 준비 중..."

# .env 파일 로드
if [ -f .env ]; then
    echo "📁 .env 파일 로드 중..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env 파일이 없습니다!"
    exit 1
fi

# RDS 자격증명 환경변수 설정
echo "🔐 RDS 자격증명 인코딩 중..."
export RDS_USERNAME_B64=$(echo -n "$RDS_USERNAME" | base64 -w 0)
export RDS_PASSWORD_B64=$(echo -n "$RDS_PASSWORD" | base64 -w 0)
export RDS_URL_B64=$(echo -n "jdbc:postgresql://$RDS_HOST:$RDS_PORT/$RDS_DATABASE" | base64 -w 0)

# 템플릿에서 실제 파일 생성
echo "📋 템플릿에서 YAML 파일 생성 중..."

# RDS Secret 생성
envsubst < k8s/rds-secret.yaml.template > k8s/rds-secret.yaml
echo "✅ k8s/rds-secret.yaml 생성됨"

# Access Entry 생성  
envsubst < k8s/access-entries/dspm-lee-access.yaml.template > k8s/access-entries/dspm-lee-access.yaml
echo "✅ k8s/access-entries/dspm-lee-access.yaml 생성됨"

echo ""
echo "🎯 생성된 파일들:"
echo "   - k8s/rds-secret.yaml"
echo "   - k8s/access-entries/dspm-lee-access.yaml"
echo ""
echo "⚠️  주의: 이 파일들은 Git에 커밋하지 마세요!"
echo ""
echo "🚀 이제 다음 명령으로 배포할 수 있습니다:"
echo "   kubectl apply -f k8s/rds-secret.yaml"
echo "   kubectl apply -f k8s/access-entries/dspm-lee-access.yaml"