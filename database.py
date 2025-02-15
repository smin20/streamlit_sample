# database.py
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime

def get_supabase_client() -> Client:
    """
    Supabase 클라이언트를 생성합니다.
    """
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_backtest_result(data: dict):
    """
    백테스트 결과를 Supabase DB에 저장합니다.
    """
    client = get_supabase_client()
    result = client.table("backtest_results").insert(data).execute()
    return result

def fetch_recent_searches(limit=20):
    client = get_supabase_client()
    response = client.table("backtest_results") \
        .select("run_timestamp, target_ticker, ticker_name, start_date, end_date, max_return") \
        .order("run_timestamp", desc=True) \
        .limit(limit) \
        .execute()
    
    # 데이터 포매팅: run_timestamp를 '년-월-일 시:분' 형태로 변환
    formatted_data = []
    for item in response.data:
        # run_timestamp를 datetime 객체로 변환하고 '년-월-일 시:분' 형태로 포맷팅합니다.
        original_timestamp = item['run_timestamp']
        formatted_timestamp = datetime.fromisoformat(original_timestamp).strftime('%Y-%m-%d %H:%M')
        # 포맷팅된 timestamp를 아이템에 반영하고 새로운 아이템을 리스트에 추가합니다.
        item['run_timestamp'] = formatted_timestamp
        formatted_data.append(item)

    return formatted_data