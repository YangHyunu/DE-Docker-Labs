from confluent_kafka import Consumer, KafkaException, KafkaError
import csv
import json
import os

# Kafka Consumer 설정
conf = {
    'bootstrap.servers': 'kafka:9092',  # Kafka 브로커 주소
    'auto.offset.reset': 'earliest',   # 가장 오래된 메시지부터 읽기
    'group.id': 'batch_consumer_group', # 컨슈머 그룹 ID
    'enable.auto.commit': False        # 자동 오프셋 커밋 비활성화
}
consumer = Consumer(conf)

# Kafka 토픽 구독
consumer.subscribe(['bit_topic'])

# CSV 파일 생성 및 데이터 저장
output_path = '/app/outputs/output.csv'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
buffer = []  # 버퍼 생성
buffer_size = 10 # 버퍼에 저장할 메시지 수

with open(output_path, 'w', newline='') as csv_file:
    # 필드 이름은 프로듀서의 데이터 구조에 맞춰 설정
    fieldnames = ['ticker', 'avg_price', 'total_volume', 'batch_size', 'timestamp']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()  # CSV 파일에 헤더 작성

    while True:
        # 메시지 읽기
        messages = consumer.consume(num_messages=buffer_size, timeout=1)  # 최대 buffer_size 메시지를 1초 동안 읽음
        if not messages:
            print("No messages received in this batch.")
            continue

        for message in messages:
            if message.error():
                print(f"Consumer error: {message.error()}")
                continue

            # 메시지 디코딩 및 버퍼에 추가
            try:
                raw_message = message.value()
                data = json.loads(raw_message.decode('utf-8'))  # JSON 디코딩
                buffer.append(data)  # 버퍼에 데이터 추가
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                continue

        # 버퍼 크기가 설정된 크기 이상일 경우 CSV로 저장
        if len(buffer) >= buffer_size:
            writer.writerows(buffer)  # 버퍼 데이터를 한 번에 기록
            print(f"Written {len(buffer)} records to CSV.")
            buffer.clear()  # 버퍼 초기화

            # 배치가 성공적으로 처리된 경우 오프셋 커밋
            consumer.commit(asynchronous=False)  # 동기식 커밋으로 오프셋 저장