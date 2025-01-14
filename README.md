### Kafka [카프카 스트리밍]
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
