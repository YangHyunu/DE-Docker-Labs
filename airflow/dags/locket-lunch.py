import airflow
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from datetime import datetime
import psycopg2
import requests
import json
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(dotenv_path="/opt/airflow/.env")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  
# URL 및 PostgreSQL 설정
ROCKET_LAUNCHES_URL = "https://ll.thespacedevs.com/2.0.0/launch/upcoming/"

def get_db_connection():
    """PostgreSQL 연결"""
    return psycopg2.connect(
        dbname= POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host='postgres',
        port=5432
    )

def initialize_schema():
    """테이블 초기화"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name = 'rocket_launches';
    """)
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE rocket_launches (
                id SERIAL PRIMARY KEY,
                launch_id VARCHAR(255) UNIQUE,
                name VARCHAR(255),
                image_url TEXT,
                net TIMESTAMP,
                details JSONB
            );
        """)
        conn.commit()
    cursor.close()
    conn.close()

def fetch_and_store_data():
    """API 데이터 가져오기 및 저장"""
    conn = get_db_connection()
    cursor = conn.cursor()
    response = requests.get(ROCKET_LAUNCHES_URL)
    response.raise_for_status()
    launches = response.json()
    for launch_data in launches['results']:
        cursor.execute("""
            INSERT INTO rocket_launches (launch_id, name, image_url, net, details)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (launch_id) DO NOTHING;
        """, (
            launch_data['id'],
            launch_data['name'],
            launch_data['image'],
            launch_data['net'],
            json.dumps(launch_data)
        ))
    conn.commit()
    cursor.close()
    conn.close()

def notify_discord():
    """Discord에 알림 전송"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
                    SELECT name , image_url , net FROM rocket_launches ORDER BY net LIMIT 1""")
    launch = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if launch:
        name , image_url, net = launch
        message = {
            "content": f":rocket: **최근 우주 발사 일정**\n\n**이름**: {name}\n**일정**: {net}\n",
            "embeds": [{"image": {"url": image_url}}],
        }
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json = message,
            headers = {"Content-Type": "application/json"},
        )
        response.raise_for_status()

# DAG 정의
with DAG(
    'download_rocket_launches',
    start_date = airflow.utils.dates.days_ago(7),
    schedule_interval = None
)as dag:
    # Task 1: 테이블 초기화
    initialize_task = PythonOperator(
        task_id='initialize_schema',
        python_callable=initialize_schema
    )
    
    # Task 2: API 데이터 가져오기 및 저장
    fetch_task = PythonOperator(
        task_id='fetch_and_store_data',
        python_callable=fetch_and_store_data
    )
    notify_task = PythonOperator(
        task_id="notify_discord",
        python_callable=notify_discord,
    )

    initialize_task >> fetch_task >> notify_task
