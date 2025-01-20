# Airflow와 PostgreSQL 연동 

## 프로젝트 개요
이 프로젝트는 Apache Airflow와 PostgreSQL을 Docker Compose로 구성하여, Airflow DAG에서 외부 API 데이터를 가져와 PostgreSQL에 저장하는 방법을 보여줍니다. 이를 통해 워크플로우 자동화와 데이터 저장 및 관리를 배울 수 있습니다.

## 시스템 아키텍처
![image](https://github.com/user-attachments/assets/db931d74-5241-4af6-b8f7-702de4126c36)


## 프로젝트 주요 특징
1. **Airflow**: 워크플로우 스케줄링 및 관리.
2. **PostgreSQL**: 데이터 저장 및 관리.
3. **Rocket Launches API**: 우주 발사 정보 데이터를 가져오기 위한 RESTful API.
4. **Docker Compose**: 컨테이너화된 환경에서 모든 서비스 실행.

## 프로젝트 구조
```
airflow-postgres-setup/
├── dags/                  # Airflow DAG 파일
│   ├── locket-lunch.py    # Rocket Launches DAG
├── logs/                  # Airflow 로그
├── plugins/               # 사용자 정의 플러그인
├── docker-compose.yml     # Docker Compose 설정
├── .env                   # 환경 변수 파일
├── README.md              # 프로젝트 설명
```

## 시작하기

### 1. `.env` 파일 생성
`.env` 파일을 프로젝트 루트 디렉토리에 생성하여 환경 변수를 설정합니다.

#### 예시 `.env` 파일
```plaintext
# PostgreSQL 설정
POSTGRES_USER=airflow
POSTGRES_PASSWORD=securepassword
POSTGRES_DB=airflow

# Discord Webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url

# 추가 패키지 설치
_PIP_ADDITIONAL_REQUIREMENTS=python-dotenv
```

### 2. Docker Compose 실행
```bash
docker-compose up -d
```

## Rocket Launches API 설명
- **API URL**: `https://ll.thespacedevs.com/2.0.0/launch/upcoming/`
- **기능**: 다가오는 우주 발사 이벤트 정보를 제공합니다.
- **주요 데이터 필드**:
  - `id`: 발사 ID (고유값)
  - `name`: 발사 이름
  - `image`: 관련 이미지 URL
  - `net`: 발사 예정 시간 (UTC)
  - 기타 세부 정보는 JSON 형식으로 제공됩니다.

#### API 응답 예시 :
```json
{
  "results": [
    {
      "id": "12345",
      "name": "Falcon 9 - Starlink Mission",
      "image": "https://example.com/image.jpg",
      "net": "2025-01-17T06:00:00Z",
      "details": {
        "rocket": "Falcon 9",
        "provider": "SpaceX"
      }
    }
  ]
}
```
## Docker Compose 초기화 로직
`docker-compose.yml`에는 Airflow 초기화를 위한 `airflow-init` 서비스가 포함되어 있습니다. 이 서비스는 다음 작업을 수행합니다:

1. **데이터베이스 마이그레이션**:
   ```bash
   airflow db upgrade
   ```

2. **관리자 계정 생성**:
   ```bash
   airflow users create \
       --username admin \
       --password admin \
       --firstname Admin \
       --lastname User \
       --role Admin \
       --email admin@example.com
   ```

3. **DAG 디렉토리 초기화**:
   Airflow는 기본적으로 `/opt/airflow/dags` 디렉토리에서 DAG 파일을 검색합니다. DAG 파일이 올바른 위치에 있는지 확인합니다.

초기화 작업이 완료되면 `airflow-init` 컨테이너는 자동으로 종료됩니다.

## DAG 및 PostgreSQL 연동

DAG는 `dags/locket-lunch.py`에 정의되어 있습니다. 주요 코드:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import psycopg2
import requests
import os
import json

def initialize_schema():
    # PostgreSQL 테이블 초기화
    pass

def fetch_and_store_data():
    # API 데이터 가져오기 및 저장
    pass

def notify_discord():
    # Discord로 알림 전송
    pass

with DAG(
    'download_rocket_launches',
    start_date=airflow.utils.dates.days_ago(14),
    schedule_interval=None
) as dag:
    initialize_task = PythonOperator(
        task_id='initialize_schema',
        python_callable=initialize_schema
    )

    fetch_task = PythonOperator(
        task_id='fetch_and_store_data',
        python_callable=fetch_and_store_data
    )

    notify_task = PythonOperator(
        task_id='notify_discord',
        python_callable=notify_discord
    )

    initialize_task >> fetch_task >> notify_task
```
### DAG 흐름
1. **테이블 초기화**: PostgreSQL에 `rocket_launches` 테이블 생성.
2. **API 데이터 가져오기**: Rocket Launches API에서 데이터를 가져와 PostgreSQL에 저장.
3. **Discord 알림**: 가장 가까운 발사 일정을 Discord로 알림.


### DAG 작동 순서와 역할
1. **initialize_schema**:
   - PostgreSQL 데이터베이스에 `rocket_launches` 테이블이 존재하는지 확인.
   - 테이블이 없을 경우 새로 생성.
   - 테이블에는 발사 ID, 이름, 이미지 URL, 발사 시간, 세부 정보를 저장.

2. **fetch_and_store_data**:
   - Rocket Launches API에서 데이터를 가져옵니다.
   - 데이터를 파싱하여 `rocket_launches` 테이블에 저장.
   -  `ON CONFLICT` 구문을 사용하여 중복 데이터를 방지합니다다.

3. **notify_discord**:
   - 가장 최근 발사 일정과 이미지 데이터를 PostgreSQL에서 가져옵니다.
   - Discord Webhook을 사용하여 발사 일정과 이미지를 전송합니다.


## PostgreSQL에서 데이터 확인
1. PostgreSQL 컨테이너 내부 접속:
   ```bash
   docker exec -it <postgres_container_name> psql -U airflow -d airflow
   ```

2. 테이블 데이터 확인:
   ```sql
   SELECT id, launch_id, name, net, image_url FROM rocket_launches;
   ```

3. 정상적으로 저장된 데이터 예시:
   ```plaintext
    id |              launch_id               |            name            |         net          |                 image_url                 
   ----+--------------------------------------+----------------------------+----------------------+------------------------------------------
     1 | 91bfaa47-76d6-4111-9830-d6c6c46c4dab | Falcon 9 - Starlink Mission | 2025-01-17 06:00:00 | https://example.com/image.jpg            
   ```

## 워크플로우 설명
1. **Docker Compose 실행**:
   - `airflow-init` 서비스는 데이터베이스 마이그레이션과 사용자 계정을 생성한 뒤 종료됩니다.

2. **Airflow 서비스 시작**:
   - `airflow-scheduler`, `airflow-webserver`, `airflow-worker` 컨테이너가 실행됩니다.

3. **DAG 실행**:
   - Airflow 웹 UI에서 DAG를 활성화하고 실행합니다.
   - `initialize_schema` 작업이 실행되어 데이터베이스 테이블을 초기화합니다.
   - `fetch_and_store_data` 작업이 API 데이터를 가져와 데이터베이스에 저장합니다.
   - `notify_discord` 작업이 가장 가까운 발사 일정을 Discord로 전송합니다.

4. **PostgreSQL에서 결과 확인**:
   - 데이터를 확인하여 DAG 작업이 성공적으로 수행되었는지 검증합니다.

5. **Discord 동작 확인**:
   - Discord 채널에서 가장 가까운 발사 일정을 확인합니다.

## 스크린샷 및 이미지
1. **Airflow 웹 UI**
   ![image](https://github.com/user-attachments/assets/eaef41af-9b3b-4024-a85e-87b55b6e3cc0)


2. **PostgreSQL 데이터 확인**
```
SELECT id, name, launch_id, image_url, net FROM rocket_launches LIMIT 3;
```
```
id |                  name                   |              launch_id               |                                                    image_url                                                     |         net         
----+-----------------------------------------+--------------------------------------+------------------------------------------------------------------------------------------------------------------+---------------------
  1 | New Glenn | Maiden Flight               | 91bfaa47-76d6-4111-9830-d6c6c46c4dab | https://thespacedevs-prod.nyc3.digitaloceanspaces.com/media/images/new_glenn_on_lc_image_20250111175645.jpg      | 2025-01-16 07:03:00
  2 | Starship | Flight 7                     | c5566f6e-606e-4250-b8f4-477c5d82c798 | https://thespacedevs-prod.nyc3.digitaloceanspaces.com/media/images/starship_on_the_image_20250111100520.jpg      | 2025-01-16 22:37:00
  3 | Long March 2D | PRSC-EO1                | 4c5e9d81-a4e8-41b0-b906-f335ef5c2d95 | https://thespacedevs-prod.nyc3.digitaloceanspaces.com/media/images/
```
![image](https://github.com/user-attachments/assets/2da4f598-432f-4a25-a5ed-f4e979c0e273)


3. **Discord 동작 확인**
![image](https://github.com/user-attachments/assets/55b47c9a-a8bb-4dd5-909d-e382a7b0140f)


## 프로젝트 회고 및 인사이트

### 개발 과정에서의 도전과 해결
1. **Docker 환경 설정의 어려움**
   - 컨테이너 권한 설정이 특히 로컬 환경에서 까다로움
   - CS 지식의 부족으로 인한 어려움 경험
   - 권한 관련 문제 해결을 위한 학습 필요성 인식

### 주요 학습 포인트
1. **PostgreSQL 활용**
   - 현재: 전체 데이터 저장 및 관리
   - 향후 계획: 메타데이터만 저장하고 실제 데이터는 S3에 저장하는 방식 고려

2. **DAG 개발 경험**
   - 초기: 설정의 복잡성으로 어려움 느낌
   - 실제 개발: 함수 작성은 예상보다 수월
   - 장점: 기능별 분리로 디버깅과 문제해결이 용이

3. **기술적 인사이트**
   - 기존 curl 기반 데이터 수집에서 확장 가능성 발견
   - Kafka 스트리밍, Elasticsearch API 연동 가능성 확인
   - `&airflow-common-env`를 통한 효율적인 설정 관리 경험

### 개선 필요 사항
1. **기술적 역량**
   - 함수 분리 및 설계 능력 향상 필요
   - CS 기초 지식 보강 필요
   - Docker 및 권한 관리에 대한 이해도 향상 필요

### 향후 계획
1. **기능 확장**
   - 웹 크롤링 기능 추가
   - S3 연동 구현
   - Kafka, Elasticsearch 연동 검토

2. **아키텍처 개선**
   - PostgreSQL을 메타데이터 저장용으로 전환
   - S3를 메인 데이터 스토리지로 활용
   - 컨테이너 관리 최적화
