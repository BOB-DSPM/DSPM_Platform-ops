### DSPM Kubernetes 이중화 배치 설계

## 1. Pod Anti-Affinity 규칙 적용

### Backend 서비스 (고가용성 필수)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dspm-backend
spec:
  replicas: 3  # 최소 3개로 증가
  template:
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: dspm-backend
            topologyKey: kubernetes.io/hostname  # 다른 노드에 배치
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: dspm-backend
              topologyKey: topology.kubernetes.io/zone  # 다른 AZ 선호
```

### Dashboard (Frontend) 서비스
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dashboard
spec:
  replicas: 2  # 최소 2개
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: dashboard
              topologyKey: kubernetes.io/hostname
```

## 2. Node Pool 배치 전략

### Multi-AZ Node 분산
```
ap-northeast-2a:
├── Node 1 (t3.medium)
│   ├── dspm-backend-pod-1
│   ├── dashboard-pod-1
│   └── analyzer-pod-1
└── Node 2 (t3.medium)
    ├── collector-pod-1
    └── lineage-pod-1

ap-northeast-2c:
├── Node 3 (t3.medium)
│   ├── dspm-backend-pod-2
│   ├── dashboard-pod-2
│   └── analyzer-pod-2
└── Node 4 (t3.medium)
    ├── collector-pod-2
    └── lineage-pod-2
```

## 3. 네트워크 계층 구성

### Service Mesh 고려사항
```yaml
# 서비스 간 통신 최적화
apiVersion: v1
kind: Service
metadata:
  name: dspm-backend
spec:
  type: ClusterIP
  sessionAffinity: ClientIP  # 세션 유지
  ports:
  - port: 8080
    targetPort: 8080
  selector:
    app: dspm-backend
```

### Ingress 이중화
```yaml
# Multiple Ingress Controllers
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dspm-ingress-primary
  annotations:
    nginx.ingress.kubernetes.io/upstream-hash-by: "$request_uri"
    nginx.ingress.kubernetes.io/load-balance: "round_robin"
```

## 4. 모니터링 및 Health Check 강화

### Liveness & Readiness Probes
```yaml
containers:
- name: dspm-backend
  livenessProbe:
    httpGet:
      path: /actuator/health
      port: 8080
    initialDelaySeconds: 60
    periodSeconds: 10
  readinessProbe:
    httpGet:
      path: /actuator/health/readiness
      port: 8080
    initialDelaySeconds: 30
    periodSeconds: 5
```

## 5. 리소스 할당 및 QoS

### Resource Requests/Limits
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

### Priority Class 설정
```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: dspm-high-priority
value: 1000
description: "High priority for critical DSPM services"
```