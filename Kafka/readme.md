# Kafka Producer-Consumer with Docker for Bitcoin Trading Data

## Overview
이 프로젝트는 Docker를 사용하여 Kafka 메시징 시스템을 구현한 예제입니다. Binance WebSocket API를 통해 실시간 Bitcoin 거래 데이터를 수집하고, Kafka로 데이터를 처리한 후 최종적으로 분석 가능한 형태로 저장합니다. 실시간 거래 데이터를 효율적으로 처리하기 위해 1초 단위로 데이터를 집계하여 처리합니다.

### 주요 기능
- Binance WebSocket API를 통한 실시간 BTC-USD 거래 데이터 수집
- 리소스 최적화를 위한 1초 단위 데이터 집계
- Kafka를 통한 안정적인 메시지 큐잉 및 처리
- CSV 형태의 데이터 저장으로 추후 분석 용이성 확보
- 배치 처리를 통한 효율적인 데이터 저장

### 향후 확장 가능성
- Elasticsearch와 Kibana를 통한 실시간 데이터 시각화
- Grafana 대시보드를 통한 거래 데이터 모니터링
- 실시간 거래 패턴 분석 및 알림 시스템 구축

## Table of Contents
- [Architecture & Workflow](#architecture--workflow)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup & Running](#setup--running)
- [Data Flow & Output](#data-flow--output)
- [Troubleshooting](#troubleshooting)
- [Lessons Learned](#lessons-learned)
- [Future Extensions](#future-extensions)
- [License](#license)

## Architecture & Workflow
### 시스템 구성
- **Data Source**: Binance WebSocket API (BTC-USD 실시간 거래 데이터)
- **Queue System**: 1초 단위 데이터 집계를 위한 메모리 큐
- **Kafka & Zookeeper**: Docker Compose로 구성된 메시징 시스템
- **Kafka Client**: Producer와 Consumer가 포함된 별도의 Docker 컨테이너
- **Data Storage**: 처리된 데이터는 CSV 파일 형태로 저장

### 상세 워크플로우
1. **초기 설정**
   - Docker Compose를 통해 Zookeeper와 Kafka 브로커 이미지 빌드
   - Kafka-Client 컨테이너는 별도의 Dockerfile로 Python 환경 구성
   - 각 컨테이너 간 네트워크 연결 설정

2. **토픽 및 네트워크 설정**
   - Kafka 컨테이너에서 토픽 생성 
   - Kafka-Client 컨테이너를 Kafka 네트워크에 연결
   - 브로커와 클라이언트 간 통신 설정

3. **데이터 수집 및 처리**
   - **Producer 처리**:
     - Binance WebSocket으로부터 실시간 데이터 수신
     - 1초 동안 메모리 큐에 데이터 축적
     - 축적된 데이터의 평균 가격, 총 거래량 집계
     - 집계된 데이터를 JSON 형태로 브로커에 전송
   
   - **Consumer 처리**:
     - 배치 사이즈: 10개 메시지
     - 처리 간격: 1초
     - 10초마다 한 배치의 데이터를 CSV 파일로 저장

## Project Structure
```
Kafka/
├── config/                         # Kafka 및 Zookeeper 설정 파일
├── KafkaClient/                    # Kafka 클라이언트 애플리케이션
│   ├── consumer.py                 # 메시지를 소비하는 컨슈머 스크립트
│   ├── Dockerfile                  # 클라이언트 도커 이미지 빌드 파일
│   ├── producer.py                 # 메시지를 생성하는 프로듀서 스크립트
│   └── requirements.txt            # Python 의존성 패키지 목록
├── outputs/                        # Consumer 출력 CSV 저장 경로
└── zookeeper-data/                 # Zookeeper 데이터 저장소
    ├── data/                       # Zookeeper 로그 및 스냅샷 저장 경로
    │   └── version-2/
    │       └── myid
    └── docker-compose.yml          # Kafka & Zookeeper 컨테이너 구성 파일
```

## Prerequisites
- Docker 및 Docker Compose 설치
- Python 3.8 이상
- Kafka 관련 기본 지식
- Binance API 이해

## Setup & Running

### 1. Docker 환경 구성
```bash
# Docker Compose로 Kafka & Zookeeper 실행
docker-compose up -d

# Kafka Client 컨테이너 실행 및 네트워크 연결
docker run --network kafka_kafka_network -it --name kafka-client-container kafka-client bash
```

> **중요**: 
> - Kafka Client 컨테이너는 반드시 Kafka 네트워크에 수동으로 연결해야 합니다.
> - `--name` 옵션으로 컨테이너 이름을 지정하지 않으면 임의의 이름이 생성됩니다.
> - 브로커와 클라이언트 간 네트워크 연결이 없으면 통신이 불가능합니다.

### 2. Kafka 토픽 생성 및 확인
```bash
# 기존 토픽 삭제 (필요한 경우)
kafka-topics.sh --delete --topic bit_topic --bootstrap-server localhost:9092

# 새 토픽 생성
kafka-topics.sh --create --topic bit_topic --bootstrap-server localhost:9092

# 토픽 데이터 확인 (콘솔 컨슈머)
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic bit_topic --from-beginning
```

### 3. Producer & Consumer 실행
```bash
# Producer 실행 (Kafka Client 컨테이너에서)
python3 producer.py

# Consumer 실행 (별도 터미널에서)
python3 consumer.py
```

## Data Flow & Output

### 1. Producer Output (1초 단위 집계 데이터)
```json
{
    "ticker": "BTC-USD",
    "avg_price": 95568.29,        # 1초간의 평균 거래가
    "total_volume": 0.07399,      # 1초간의 총 거래량
    "batch_size": 18,             # 1초간 집계된 거래 건수
    "timestamp": "2025-01-14T08:14:36.553542"
}
```

### 2. Kafka Console Consumer Output
실시간 스트림 데이터 예시:
```json
{"ticker": "BTC-USD", "avg_price": 95568.29, "total_volume": 0.07399, "batch_size": 18, "timestamp": "2025-01-14T08:14:36.553542"}
{"ticker": "BTC-USD", "avg_price": 95568.29, "total_volume": 0.10698, "batch_size": 18, "timestamp": "2025-01-14T08:14:37.556749"}
{"ticker": "BTC-USD", "avg_price": 95572.55, "total_volume": 0.9494, "batch_size": 141, "timestamp": "2025-01-14T08:14:38.560130"}
{"ticker": "BTC-USD", "avg_price": 95578.42, "total_volume": 0.35957, "batch_size": 21, "timestamp": "2025-01-14T08:14:39.562769"}
{"ticker": "BTC-USD", "avg_price": 95578.43, "total_volume": 0.07498, "batch_size": 8, "timestamp": "2025-01-14T08:14:40.566278"}
{"ticker": "BTC-USD", "avg_price": 95575.48, "total_volume": 0.45019, "batch_size": 155, "timestamp": "2025-01-14T08:14:41.571902"}
```

### 3. Python Consumer Output
배치 처리 결과:
```bash
Written 10 records to CSV.
Written 10 records to CSV.
Written 10 records to CSV.
Written 10 records to CSV.
Written 10 records to CSV.
```

## Future Extensions
### 1. Elasticsearch & Kibana 연동
- 실시간 거래 데이터 인덱싱
- 커스텀 대시보드를 통한 거래 패턴 분석
- 이상 거래 탐지 및 알림 구성
- 다양한 시간대별 데이터 집계 및 분석

### 2. Grafana 대시보드
- 실시간 가격 변동 모니터링
- 거래량 분석 및 시각화
- 커스텀 메트릭 설정 및 알림 구성
- 기술적 분석 지표 시각화

### 3. 데이터 분석 확장
- 실시간 거래 패턴 분석
- 머신러닝 모델 적용
- 가격 예측 시스템 구축
- 자동 거래 시스템 연동

## Troubleshooting
1. **네트워크 연결 문제**
   - 증상: 컨테이너 간 통신 불가
   - 해결: 명시적 네트워크 설정 및 컨테이너 이름 지정

2. **도커 이미지 및 네트워크 문제**
   - 증상: 이전 설정과의 충돌
   - 해결: Docker 시스템 초기화 및 재설정

3. **권한 및 의존성 문제**
   - 증상: Python 스크립트 실행 오류
   - 해결: bitnami 이미지 사용 및 권한 설정

## Lessons Learned
1. **Docker 관련**
   - 컨테이너 간 네트워크 설정의 중요성
   - 컨테이너 의존성 관리의 필요성
   - 버전 호환성 확인의 중요성

2. **개발 프로세스**
   - 단계적 기능 구현의 이점
   - 기존 이미지 활용의 중요성
   - 테스트 및 검증의 필요성

3. **시스템 설계**
   - 확장성을 고려한 설계의 중요성
   - 데이터 처리 최적화의 필요성
   - 모니터링 및 로깅의 중요성

## Acknowledgments
- Binance API Documentation
- Kafka Documentation
- Docker Documentation
- Python Community