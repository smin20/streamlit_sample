# config.py
# 기본 투자 설정 및 파라미터, Supabase 관련 설정

# 투자 관련 상수
INITIAL_INVESTMENT = 5000000       # 총 투자금액
UNIT_INVESTMENT = 500000           # 1차수당 금액
MAX_BUY_TIMES = 10               # 최대 매수 횟수

# 거래 수수료 및 세금 (예: 키움증권 기준)
COMMISSION_RATE = 0.00015        # 매수/매도 수수료 0.015%
TRANSACTION_TAX_RATE = 0.0018    # 매도 시 거래세 0.18%

# 백테스트 파라미터 범위
BUY_NEXT_PERCENT_START = 2.00    # 매수 갭 % 시작 값
BUY_NEXT_PERCENT_END = 10.00     # 매수 갭 % 끝 값
BUY_NEXT_PERCENT_STEP = 1.0      # 매수 갭 % 증분

SELL_PERCENT_START = 1.00        # 매도 % 시작 값
SELL_PERCENT_END = 10.00          # 매도 % 끝 값
SELL_PERCENT_STEP = 0.5          # 매도 % 증분

# Supabase 설정 (실제 값으로 교체하세요)
SUPABASE_URL = "https://aeslupwjojhjuvtufcom.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlc2x1cHdqb2poanV2dHVmY29tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk2Mjk0ODcsImV4cCI6MjA1NTIwNTQ4N30.vgBMJh1w2hgra8kHGhdAh7ju3Vq6ssVeDyV_NUkP1fg"
