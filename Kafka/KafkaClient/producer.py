from confluent_kafka import Producer
import websocket
import json
from queue import Queue, Full
from threading import Thread
import time
from datetime import datetime

# Kafka 프로듀서 구성
conf = {
    'bootstrap.servers': 'kafka:9092',
    'client.id': 'crypto-price-producer',
    'linger.ms': 5000,
    'batch.size': 65536
}
producer = Producer(conf)
topic = 'bit_topic'

# Binance WebSocket URL
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@trade"

# 메시지를 저장할 큐
message_queue = Queue(maxsize=500)

# Kafka 전송 작업자 함수
def kafka_worker():
    while True:
        batch = []
        start_time = time.time()

        # 5초 동안 데이터를 모으면서 배치 처리
        while time.time() - start_time < 1:
            if not message_queue.empty():
                batch.append(message_queue.get())

        # 배치 데이터 집계 및 Kafka 전송
        if batch:
            avg_price = sum(item['price'] for item in batch) / len(batch)
            total_volume = sum(item['volume'] for item in batch)

            aggregated_message = {
                "ticker": "BTC-USD",
                "avg_price": round(avg_price, 2),
                "total_volume": round(total_volume, 6),
                "batch_size": len(batch),
                "timestamp": datetime.utcnow().isoformat()
            }

            producer.produce(topic, key="BTC-USD", value=json.dumps(aggregated_message))
            producer.flush()
            print(f"Sent aggregated data to Kafka: {aggregated_message}")

        # 정확히 5초 간격으로 실행
        time.sleep(max(0, 1 - (time.time() - start_time)))

# Kafka 작업자 스레드 시작
worker_thread = Thread(target=kafka_worker, daemon=True)
worker_thread.start()

# WebSocket 메시지 처리
def on_message(ws, message):
    try:
        # 메시지를 JSON 형식으로 로드
        data = json.loads(message)
        price = float(data['p'])  # 현재 거래 가격
        quantity = float(data['q'])  # 거래량
        timestamp = data['T']  # 거래 시간
        trade_id = data['t']
        buyer_is_maker = data['m']

        # Timestamp 변환
        human_readable_timestamp = datetime.utcfromtimestamp(timestamp / 1000).isoformat()

        # Kafka로 보낼 메시지 구성
        kafka_message = {
            "ticker": "BTC-USD",
            "price": price,
            "volume": quantity,
            "trade_id": trade_id,
            "trade_type": "BUY" if buyer_is_maker else "SELL",
            "timestamp": human_readable_timestamp
        }

        # 메시지를 큐에 추가
        try:
            message_queue.put(kafka_message, block=False)
        except Full:
            print("Queue is full. Dropping oldest message.")
            message_queue.get()  # 오래된 메시지 제거
            message_queue.put(kafka_message, block=False)

        print(f"Queued message: {kafka_message}")
    except Exception as e:
        print(f"Error processing message: {e}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

def on_open(ws):
    print("WebSocket connection opened")

# WebSocket 연결 생성
ws = websocket.WebSocketApp(
    BINANCE_WS_URL,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.on_open = on_open
ws.run_forever()