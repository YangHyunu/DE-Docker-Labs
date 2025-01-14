FROM python:3.9-slim

# 필요한 디렉토리 생성
RUN mkdir -p /app/outputs

# Python 의존성 설치
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 작업 디렉토리 설정
WORKDIR /app

# Kafka 클라이언트 코드 복사
COPY producer.py /app/producer.py
COPY consumer.py /app/consumer.py

# 기본 명령어 설정
CMD ["bash"]