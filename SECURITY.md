# 🔒 Security Configuration Guide

## Quick Start
```bash
# 1. .env 파일이 있는지 확인
ls .env

# 2. 시크릿 파일 자동 생성
./scripts/generate-secrets.sh

# 3. Kubernetes에 적용
kubectl apply -f k8s/rds-secret.yaml
kubectl apply -f k8s/access-entries/dspm-lee-access.yaml
```

## Manual Setup (선택사항)

### 1. Environment Variables
`.env` 파일 확인:
```bash
AWS_ACCOUNT_ID=651706765732
AWS_REGION=ap-northeast-2
EKS_ADMIN_ROLE_ARN=arn:aws:iam::651706765732:role/EksAdminRole
EKS_CLUSTER_NAME=DspmEksCluster6F1D4525-94a78eb3271540cd8f8ef72a668cf7bf
```

### 2. Manual Environment Variable Substitution
```bash
# RDS 자격증명 설정
export RDS_USERNAME_B64=$(echo -n "dspm_user" | base64)
export RDS_PASSWORD_B64=$(echo -n "__.miZ_EIMXFW01hms1pC=wC,Ht,zK9I" | base64)

# 템플릿에서 실제 파일 생성
envsubst < k8s/rds-secret.yaml.template > k8s/rds-secret.yaml
envsubst < k8s/access-entries/dspm-lee-access.yaml.template > k8s/access-entries/dspm-lee-access.yaml
```

## Security Notes
- ✅ 템플릿 파일(`.template`)만 Git에 커밋됨
- ❌ 실제 시크릿 파일은 `.gitignore`로 제외됨  
- 🔒 모든 민감한 정보는 환경변수로 관리
- 🚀 `./scripts/generate-secrets.sh` 스크립트로 자동화