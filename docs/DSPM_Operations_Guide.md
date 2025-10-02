# DSPM Platform 운영 가이드

## 🚀 배포 가이드

### 인프라 배포 (CDK)

```bash
# 1. CDK 의존성 설치
cd cdk
pip install -r requirements.txt

# 2. AWS 자격증명 설정
aws configure

# 3. CDK 부트스트랩 (최초 1회)
cdk bootstrap

# 4. 인프라 배포
cdk deploy

# 5. 배포 확인
kubectl get nodes
```

### 애플리케이션 배포 (Kubernetes)

```bash
# 1. 네임스페이스 생성
kubectl apply -f k8s/namespace.yaml

# 2. 시크릿 설정
kubectl apply -f k8s/rds-secret.yaml

# 3. 서비스별 배포
kubectl apply -f k8s/dashboard/
kubectl apply -f k8s/dspm-backend/
kubectl apply -f k8s/analyzer/
kubectl apply -f k8s/lineage/

# 4. 배포 상태 확인
kubectl get pods -n dspm
kubectl get services -n dspm
```

---

## 🔧 일상 운영 명령어

### 파드 관리

```bash
# 파드 상태 확인
kubectl get pods -n dspm

# 특정 파드 상세 정보
kubectl describe pod <pod-name> -n dspm

# 파드 로그 확인
kubectl logs <pod-name> -n dspm

# 파드 재시작
kubectl delete pod <pod-name> -n dspm

# 실시간 로그 모니터링
kubectl logs -f <pod-name> -n dspm
```

### 서비스 관리

```bash
# 서비스 상태 확인
kubectl get services -n dspm

# 외부 접근 URL 확인
kubectl get service dashboard -n dspm

# 포트 포워딩 (로컬 테스트용)
kubectl port-forward service/dspm-backend 8080:8080 -n dspm
```

### 스케일링

```bash
# replica 수 조정
kubectl scale deployment analyzer --replicas=2 -n dspm

# 스케일링 상태 확인
kubectl get deployment -n dspm
```

---

## 🔍 트러블슈팅 가이드

### 일반적인 문제들

#### 1. 파드가 시작되지 않음

```bash
# 파드 상태 확인
kubectl describe pod <pod-name> -n dspm

# 이벤트 확인
kubectl get events -n dspm --sort-by='.lastTimestamp'

# 일반적인 원인:
# - 이미지 pull 실패
# - 리소스 부족
# - Secret/ConfigMap 누락
```

#### 2. 서비스 접근 불가

```bash
# 서비스 엔드포인트 확인
kubectl get endpoints -n dspm

# 서비스와 파드 라벨 매칭 확인
kubectl get pods --show-labels -n dspm
kubectl describe service <service-name> -n dspm
```

#### 3. 데이터베이스 연결 실패

```bash
# Secret 확인
kubectl get secret rds-secret -n dspm -o yaml

# 네트워크 연결성 테스트
kubectl run test-pod --image=postgres:14 --rm -it --restart=Never -n dspm -- psql -h <rds-endpoint> -U dspm_user -d dspm
```

### 로그 분석

```bash
# 모든 파드 로그 수집
for pod in $(kubectl get pods -n dspm -o name); do
  echo "=== $pod ==="
  kubectl logs $pod -n dspm --tail=50
done

# 에러 로그만 필터링
kubectl logs <pod-name> -n dspm | grep -i error

# 특정 시간대 로그
kubectl logs <pod-name> -n dspm --since=1h
```

---

## 📊 모니터링

### 리소스 사용량 확인

```bash
# 노드 리소스 사용량
kubectl top nodes

# 파드 리소스 사용량
kubectl top pods -n dspm

# 클러스터 전체 상태
kubectl cluster-info
```

### 헬스체크

```bash
# 파드 헬스 상태
kubectl get pods -n dspm -o wide

# 서비스 상태 확인
curl -I http://<load-balancer-url>/health

# 데이터베이스 연결 확인
kubectl exec -it <backend-pod> -n dspm -- curl localhost:8080/actuator/health
```

---

## 🔐 보안 관리

### Secret 관리

```bash
# Secret 목록 확인
kubectl get secrets -n dspm

# Secret 내용 확인 (base64 디코딩)
kubectl get secret rds-secret -n dspm -o jsonpath='{.data.username}' | base64 -d

# Secret 업데이트
kubectl create secret generic rds-secret \
  --from-literal=username=<new-username> \
  --from-literal=password=<new-password> \
  --from-literal=url=<new-url> \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 네트워크 정책

```bash
# 현재 네트워크 정책 확인
kubectl get networkpolicies -n dspm

# 보안 그룹 상태 (AWS CLI)
aws ec2 describe-security-groups --group-ids <sg-id>
```

---

## 🔄 백업 및 복구

### 데이터베이스 백업

```bash
# RDS 스냅샷 생성 (AWS CLI)
aws rds create-db-snapshot \
  --db-instance-identifier <rds-instance-id> \
  --db-snapshot-identifier dspm-backup-$(date +%Y%m%d-%H%M%S)

# 스냅샷 목록 확인
aws rds describe-db-snapshots --db-instance-identifier <rds-instance-id>
```

### 설정 백업

```bash
# Kubernetes 리소스 백업
kubectl get all -n dspm -o yaml > dspm-backup-$(date +%Y%m%d).yaml

# Secret 백업 (암호화된 상태로)
kubectl get secrets -n dspm -o yaml > secrets-backup-$(date +%Y%m%d).yaml
```

---

## ⚡ 성능 최적화

### 리소스 제한 설정

```yaml
# deployment.yaml에 추가
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 수평 확장 설정

```yaml
# hpa.yaml 생성
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: dspm-backend-hpa
  namespace: dspm
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: dspm-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 🆘 긴급 상황 대응

### 서비스 전체 중단

```bash
# 1. 빠른 상태 확인
kubectl get pods -n dspm
kubectl get nodes

# 2. 로드밸런서 상태 확인
kubectl get service dashboard -n dspm

# 3. 긴급 재시작
kubectl rollout restart deployment -n dspm

# 4. 로그 수집
kubectl logs -l app=dashboard -n dspm --tail=100
```

### 데이터베이스 연결 실패

```bash
# 1. RDS 상태 확인
aws rds describe-db-instances --db-instance-identifier <instance-id>

# 2. 네트워크 연결성 확인
kubectl run test-connection --image=busybox --rm -it --restart=Never -n dspm -- nslookup <rds-endpoint>

# 3. Secret 재적용
kubectl delete secret rds-secret -n dspm
kubectl apply -f k8s/rds-secret.yaml
```

---

## 📞 연락처 및 에스컬레이션

### 개발팀 연락처
- **인프라 담당**: [연락처]
- **백엔드 담당**: [연락처]  
- **프론트엔드 담당**: [연락처]

### 외부 지원
- **AWS Support**: [AWS 콘솔]
- **Kubernetes 문서**: https://kubernetes.io/docs/

---

**문서 최종 업데이트**: 2025년 10월 2일