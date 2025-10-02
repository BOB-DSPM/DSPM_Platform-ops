# DSPM 플랫폼 이중화 아키텍처 다이어그램

## 🏗️ High-Level 이중화 아키텍처

```mermaid
graph TB
    subgraph "Internet"
        USERS[👥 Users]
    end
    
    subgraph "AWS ap-northeast-2 Region"
        subgraph "Availability Zone 2a"
            subgraph "Public Subnet 2a"
                NAT1[🌐 NAT Gateway 1]
                ALB1[⚖️ Application Load Balancer]
            end
            
            subgraph "Private Subnet 2a"
                subgraph "EKS Node Group 2a"
                    NODE1[🖥️ t3.medium Node 1]
                    NODE2[🖥️ t3.medium Node 2]
                end
                RDS1[🗄️ RDS Primary<br/>ap-northeast-2a]
            end
        end
        
        subgraph "Availability Zone 2c"
            subgraph "Public Subnet 2c"
                NAT2[🌐 NAT Gateway 2]
            end
            
            subgraph "Private Subnet 2c"
                subgraph "EKS Node Group 2c"
                    NODE3[🖥️ t3.medium Node 3]
                    NODE4[🖥️ t3.medium Node 4]
                end
                RDS2[🗄️ RDS Standby<br/>ap-northeast-2c]
            end
        end
        
        IGW[🌍 Internet Gateway]
    end
    
    USERS --> IGW
    IGW --> ALB1
    ALB1 --> NODE1
    ALB1 --> NODE2
    ALB1 --> NODE3
    ALB1 --> NODE4
    
    RDS1 -.-> RDS2
    
    style RDS1 fill:#ff9999
    style RDS2 fill:#99ccff
    style ALB1 fill:#99ff99
```

## 🔄 Kubernetes 클러스터 내부 Pod 배치

```mermaid
graph TB
    subgraph "EKS Cluster - dspm namespace"
        subgraph "AZ 2a - Node 1"
            POD1A[🏠 Dashboard Pod 1<br/>nginx+react:80]
            POD1B[⚙️ Backend Pod 1<br/>Spring Boot:8080]
            POD1C[🔍 Analyzer Pod 1<br/>Java:8080]
        end
        
        subgraph "AZ 2a - Node 2"
            POD2A[📊 Collector Pod 1<br/>Rust:8000]
            POD2B[🔗 Lineage Pod 1<br/>Python:8000]
        end
        
        subgraph "AZ 2c - Node 3"
            POD3A[🏠 Dashboard Pod 2<br/>nginx+react:80]
            POD3B[⚙️ Backend Pod 2<br/>Spring Boot:8080]
            POD3C[🔍 Analyzer Pod 2<br/>Java:8080]
        end
        
        subgraph "AZ 2c - Node 4"
            POD4A[📊 Collector Pod 2<br/>Rust:8000]
            POD4B[🔗 Lineage Pod 2<br/>Python:8000]
            POD4C[⚙️ Backend Pod 3<br/>Spring Boot:8080]
        end
        
        subgraph "Service Layer"
            SVC1[🔌 LoadBalancer Service<br/>Dashboard :80]
            SVC2[🔌 ClusterIP Service<br/>Backend :8080]
            SVC3[🔌 ClusterIP Service<br/>Analyzer :8080]
            SVC4[🔌 ClusterIP Service<br/>Collector :8000]
            SVC5[🔌 ClusterIP Service<br/>Lineage :8000]
        end
    end
    
    SVC1 --> POD1A
    SVC1 --> POD3A
    
    SVC2 --> POD1B
    SVC2 --> POD3B
    SVC2 --> POD4C
    
    SVC3 --> POD1C
    SVC3 --> POD3C
    
    SVC4 --> POD2A
    SVC4 --> POD4A
    
    SVC5 --> POD2B
    SVC5 --> POD4B
```

## 📊 이중화 상태 현황표

| 구성요소 | 현재 상태 | 이중화 목표 | 이중화 레벨 |
|---------|----------|------------|------------|
| 🌐 **네트워크** | Single NAT | Dual NAT (Multi-AZ) | ⭐⭐⭐ |
| 🗄️ **데이터베이스** | Single AZ | Multi-AZ RDS | ⭐⭐⭐ |
| 🖥️ **컴퓨팅** | 2 Nodes | 4 Nodes (2 per AZ) | ⭐⭐⭐ |
| 🏠 **Frontend** | 1 replica | 2 replicas | ⭐⭐ |
| ⚙️ **Backend** | 1 replica | 3 replicas | ⭐⭐⭐ |
| 🔍 **Analyzer** | 1 replica | 2 replicas | ⭐⭐ |
| 📊 **Collector** | 1 replica | 2 replicas | ⭐⭐ |
| 🔗 **Lineage** | 1 replica | 2 replicas | ⭐⭐ |

**이중화 레벨:**
- ⭐ = 기본 (Single Point)
- ⭐⭐ = 부분 이중화 (2개 복제본)
- ⭐⭐⭐ = 완전 이중화 (3개+ 복제본, Multi-AZ)

## 🚀 이중화 구현 로드맵

### Phase 1: 인프라 이중화 (우선순위: 높음)
```yaml
# CDK 변경사항
vpc = ec2.Vpc(
    self, "DspmVpc",
    max_azs=2,
    nat_gateways=2  # ✅ 이중화
)

database = rds.DatabaseInstance(
    # ... 기존 설정
    multi_az=True  # ✅ 이중화
)
```

### Phase 2: 애플리케이션 이중화 (우선순위: 중간)
```yaml
# Backend 3개 replicas + Anti-Affinity
replicas: 3
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - topologyKey: kubernetes.io/hostname
```

### Phase 3: 모니터링 및 자동복구 (우선순위: 중간)
- Health Check 강화
- Auto Scaling 설정
- 장애 감지 및 알림

## 📈 이중화 효과 지표

| 지표 | 현재 | 목표 | 개선률 |
|-----|------|------|--------|
| **가용성** | 99.5% | 99.9% | ⬆️ 0.4% |
| **복구시간** | 5-10분 | 1-2분 | ⬇️ 80% |
| **동시장애 허용** | 0개 | 1-2개 | ⬆️ 200% |
| **데이터 손실** | 위험 | 최소화 | ⬇️ 95% |

이 구성을 통해 **단일 장애점 없는 고가용성 DSPM 플랫폼**을 구축할 수 있습니다! 🎯