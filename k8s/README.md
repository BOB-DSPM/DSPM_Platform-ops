# DSPM Platform Kubernetes Deployment

## 📋 GitHub Secrets 설정 필요

### 데이터베이스 정보
```
DB_URL=jdbc:postgresql://dspmeksstack-dspmdatabasea69d27a7-nd2xz2vwca6v.cdsikyuewe0q.ap-northeast-2.rds.amazonaws.com:5432/dspm
DB_USERNAME=dspm_user
DB_PASSWORD=ayCCd1ApGcGy=gnU3esC9Zet-gtGdt^D
```

### AWS 자격 증명 (Collector용)
```
AWS_ACCESS_KEY_ID=[여기에 AWS Access Key ID 입력]
AWS_SECRET_ACCESS_KEY=[여기에 AWS Secret Access Key 입력]
AWS_REGION=ap-northeast-2
```

## 🏗️ 아키텍처

```
Internet
    ↓
[ Ingress ]
    ↓
┌─────────────────────────────────────────┐
│  Dashboard (React)                      │ ← Frontend
│  Port: 80                               │
└─────────────────────────────────────────┘
    ↓ API calls
┌─────────────────────────────────────────┐
│  Analyzer (Spring Boot)                 │ ← Backend API
│  Port: 8080                             │
│  └── PostgreSQL RDS                     │
└─────────────────────────────────────────┘
    ↑ Data push
┌─────────────────────────────────────────┐
│  Collector (Rust)                       │ ← Data Collection
│  Port: 8000                             │
│  └── AWS SDK                            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Lineage (Data Lineage)                 │ ← Data Lineage
│  Port: 8000                             │
└─────────────────────────────────────────┘
```

## 🚀 배포 방법

### 1. 수동 배포
```bash
# 네임스페이스 생성
kubectl apply -f namespace.yaml

# Secrets 생성 (AWS 자격 증명은 별도 설정 필요)
kubectl apply -f rds-secret.yaml
kubectl apply -f aws-credentials-secret.yaml

# 서비스들 배포
kubectl apply -f analyzer/
kubectl apply -f collector/
kubectl apply -f dashboard/
kubectl apply -f lineage/

# Ingress 설정
kubectl apply -f ingress.yaml
```

### 2. 자동 배포 스크립트
```bash
./deploy.sh
```

## 🔗 서비스 간 연결

### Analyzer ← Collector
- Collector가 AWS 리소스를 스캔하여 Analyzer API로 전송
- `http://analyzer:8080/api/assets:bulk`

### Dashboard ← Analyzer  
- Dashboard가 Analyzer API에서 데이터 조회
- `http://analyzer:8080/api`

### Lineage ← Analyzer
- Lineage가 Analyzer에서 데이터 계보 정보 조회
- `http://analyzer:8080/api`

## 🌐 외부 접근 경로

- **Dashboard**: `http://[LOAD-BALANCER-IP]/dashboard`
- **API**: `http://[LOAD-BALANCER-IP]/api`
- **Lineage**: `http://[LOAD-BALANCER-IP]/lineage`

## 🔍 모니터링 & 디버깅

```bash
# 전체 상태 확인
kubectl get all -n dspm

# 실시간 파드 상태
kubectl get pods -n dspm -w

# 서비스 로그 확인
kubectl logs -f deployment/analyzer -n dspm
kubectl logs -f deployment/collector -n dspm
kubectl logs -f deployment/dashboard -n dspm
kubectl logs -f deployment/lineage -n dspm

# 서비스 간 연결 테스트
kubectl exec -it deployment/collector -n dspm -- curl http://analyzer:8080/health
```

## 🔒 보안 설정

- **NetworkPolicy**: 서비스 간 통신 제한
- **RBAC**: 최소 권한 원칙 적용
- **Secrets**: 민감한 정보는 Secret으로 관리
- **IRSA**: AWS 접근 시 IAM Role 사용 권장

## 📊 환경변수 설정

### Analyzer (Spring Boot)
- `SPRING_DATASOURCE_URL`: PostgreSQL 연결 URL
- `SPRING_DATASOURCE_USERNAME`: DB 사용자명
- `SPRING_DATASOURCE_PASSWORD`: DB 비밀번호
- `SPRING_PROFILES_ACTIVE`: 프로필 (production)

### Collector (Rust)
- `ANALYZER_URL`: Analyzer 서비스 URL
- `AWS_ACCESS_KEY_ID`: AWS 액세스 키 
- `AWS_SECRET_ACCESS_KEY`: AWS 시크릿 키
- `AWS_REGION`: AWS 리전

### Dashboard (React)
- `REACT_APP_API_BASE_URL`: Backend API URL
- `NODE_ENV`: 환경 (production)

### Lineage
- `ANALYZER_API_URL`: Analyzer API URL
- `REFRESH_INTERVAL`: 새로고침 간격 (초)