import warnings
warnings.filterwarnings("ignore", message="findfont: Font family 'Malgun Gothic' not found.")

import streamlit as st
import datetime 
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
from pykrx import stock
import sqlite3
import json
import logging

# 로그 설정: 기본 형식을 지정하고, INFO 레벨 이상의 로그를 출력하도록 합니다.
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# 페이지 설정 (넓은 레이아웃)
st.set_page_config(layout="wide")

# 앱 제목 (아이콘 추가)
st.info('🪄 매직스플릿 결과 백테스팅 페이지 입니다. 종목 선택 후 🚀 백테스트 실행 버튼 클릭하세요.')

# ---------------------------------------
# 사이드바: 종목 검색 및 선택 (아이콘 추가)
# ---------------------------------------
st.sidebar.header("🔍 종목 검색")
search_query = st.sidebar.text_input("🔎 종목 이름 입력 (예: 삼성)", key="search_query")

@st.cache_data
def load_ticker_info():
    # KOSPI, KOSDAQ 전체 티커와 이름 정보를 가져옵니다.
    tickers_kospi = stock.get_market_ticker_list(market="KOSPI")
    tickers_kosdaq = stock.get_market_ticker_list(market="KOSDAQ")
    ticker_dict = {}
    for t in tickers_kospi:
        try:
            ticker_dict[t] = stock.get_market_ticker_name(t)
        except Exception:
            ticker_dict[t] = "Unknown"
    for t in tickers_kosdaq:
        try:
            ticker_dict[t] = stock.get_market_ticker_name(t)
        except Exception:
            ticker_dict[t] = "Unknown"
    return ticker_dict

@st.cache_data(show_spinner=False)
def get_market_cap(ticker, date_str):
    """
    지정한 날짜(date_str: 'YYYYMMDD') 기준으로 해당 종목의 시가총액을 반환합니다.
    조회에 실패하면 0을 반환합니다.
    """
    try:
        df_cap = stock.get_market_cap_by_date(date_str, date_str, ticker)
        if df_cap.empty:
            return 0
        # df_cap의 '시가총액' 컬럼 값 반환 (필요에 따라 데이터 전처리 필요)
        return df_cap['시가총액'].iloc[0]
    except Exception:
        return 0

if search_query:
    ticker_info = load_ticker_info()
    # 검색어가 종목명에 포함된 티커들 필터링 (대소문자 구분 없이)
    filtered_tickers = {code: name for code, name in ticker_info.items() if search_query in name}
    if filtered_tickers:
        # 오늘 날짜 기준으로 시가총액 조회 (문자열 'YYYYMMDD' 형식)
        today_str = datetime.datetime.today().strftime("%Y%m%d")
        # (티커, 종목명) 튜플 리스트를 시가총액 기준 내림차순으로 정렬
        sorted_filtered_tickers = sorted(
            filtered_tickers.items(),
            key=lambda x: get_market_cap(x[0], today_str),
            reverse=True
        )
        # selectbox에 정렬된 결과 표시 ("티커 - 종목명" 형식)
        selected = st.sidebar.selectbox(
            "📋 검색 결과",
            sorted_filtered_tickers,
            format_func=lambda x: f"{x[0]} - {x[1]}"
        )
        target_ticker = selected[0]
        st.sidebar.write(f"✅ 선택된 종목: **{selected[0]} ({selected[1]})**")
    else:
        st.sidebar.write("❌ 검색 결과가 없습니다.")
        target_ticker = None
else:
    st.sidebar.write("ℹ️ 종목 검색어를 입력하세요.")
    target_ticker = None

# ---------------------------------------
# 사이드바: 기초 설정 (아이콘 추가)
# ---------------------------------------
st.sidebar.header('⚙️ 기초 설정')
initial_investment = st.sidebar.number_input('💰 총 투자금액', value=5000000, step=100000)
unit_investment = st.sidebar.number_input('📌 1차수당 금액', value=500000, step=50000)
max_buy_times = st.sidebar.number_input('🔁 최대 매수 횟수', value=10, min_value=1, step=1)

# -------------------------------
# 사이드바: 날짜 범위 설정 (아이콘 추가)
# -------------------------------
st.sidebar.header('📅 날짜 범위 설정 (기본 6개월)')
start_date_input = st.sidebar.date_input('시작 날짜', datetime.datetime.today() - datetime.timedelta(days=180))
end_date_input = st.sidebar.date_input('종료 날짜', datetime.datetime.today())
start_date = start_date_input.strftime('%Y%m%d')
end_date = end_date_input.strftime('%Y%m%d')

if st.sidebar.button('🚀 백테스트 실행'):
    log_line = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 백테스트 실행됨"
    if target_ticker:
        log_line += f" (종목: {target_ticker} - {stock.get_market_ticker_name(target_ticker)})"
    else:
        log_line += " (종목 미선택)"
    
    # 로그 출력
    logging.info(log_line)
    
    if not target_ticker:
        st.error("❗ 종목을 선택하세요.")
        st.stop()
    
    # 데이터 가져오기
    try:
        st.write(f'📈 종목 코드 {target_ticker} ({stock.get_market_ticker_name(target_ticker)}) 의 데이터를 {start_date_input}부터 {end_date_input}까지 가져옵니다.')
        df = stock.get_market_ohlcv_by_date(start_date, end_date, target_ticker)
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
    except Exception as e:
        st.error(f'❗ 데이터를 가져오는 중 오류 발생: {e}')
        st.stop()
    
    # 결과를 저장할 리스트 초기화
    results = []
    
    # 매수 갭 %와 매도 %의 범위 설정 (고정 값)
    buy_next_percent_start = 5.00
    buy_next_percent_end = 10.00
    buy_next_percent_step = 1.0
    sell_percent_start = 1.00
    sell_percent_end = 5.00
    sell_percent_step = 0.5
    
    # 진행바
    my_bar = st.progress(0)
    total_iterations = int(len(np.arange(buy_next_percent_start, buy_next_percent_end + buy_next_percent_step, buy_next_percent_step)) * 
                           len(np.arange(sell_percent_start, sell_percent_end + sell_percent_step, sell_percent_step)))
    iteration = 0
    
    # -------------------------------
    # 백테스팅 실행 (매수 갭 %와 매도 %의 모든 조합에 대해)
    # -------------------------------
    for buy_next_percent in np.arange(buy_next_percent_start, buy_next_percent_end + buy_next_percent_step, buy_next_percent_step):
        for sell_percent in np.arange(sell_percent_start, sell_percent_end + sell_percent_step, sell_percent_step):
            iteration += 1
            # 퍼센트 값을 소수로 변환
            buy_next_percent_decimal = buy_next_percent / 100
            sell_percent_decimal = sell_percent / 100
            
            holdings = 0  # 보유 주식 수 (정수)
            cash = initial_investment
            
            # 수수료 및 세금 설정 (키움증권 기준)
            commission_rate = 0.00015       # 매수/매도 수수료 0.015%
            transaction_tax_rate = 0.0018   # 매도 시 거래세 0.18%
            
            # 변수 초기화
            initial_buy_price = None          # 1차 매수 가격 저장
            waiting_for_initial_price = False # 1차 매수 가격까지 하락 대기 상태
            buy_count = 0                     # 현재 보유 중인 매수 차수
            buy_levels = []                   # 보유 중인 매수 레벨별 가격 및 수량
            
            # 매수 가능 주식 수 계산 함수
            def calculate_number_of_shares_to_buy(cash_available, unit_investment, price, commission_rate):
                max_investment = min(cash_available, unit_investment)
                number_of_shares = int(max_investment // (price * (1 + commission_rate)))
                if number_of_shares == 0:
                    return 0, 0, 0
                total_cost = number_of_shares * price
                commission = total_cost * commission_rate
                total_cost_including_commission = total_cost + commission
                while total_cost_including_commission > cash_available and number_of_shares > 0:
                    number_of_shares -= 1
                    total_cost = number_of_shares * price
                    commission = total_cost * commission_rate
                    total_cost_including_commission = total_cost + commission
                return number_of_shares, total_cost, commission
            
            # 매도 시 순수익 계산 함수
            def calculate_proceeds_from_selling(number_of_shares, sell_price, commission_rate, transaction_tax_rate):
                total_proceeds = number_of_shares * sell_price
                commission = total_proceeds * commission_rate
                transaction_tax = total_proceeds * transaction_tax_rate
                net_proceeds = total_proceeds - commission - transaction_tax
                return net_proceeds, commission, transaction_tax
            
            # 전략 구현
            for date, row in df.iterrows():
                high = row['고가']
                low = row['저가']
                close = row['종가']
                
                price_sequence = [
                    ('low', low),
                    ('high', high),
                    ('close', close)
                ]
                
                for price_type, price in price_sequence:
                    # 매수 로직
                    if waiting_for_initial_price:
                        if price <= initial_buy_price and cash >= unit_investment:
                            number_of_shares, total_cost, commission = calculate_number_of_shares_to_buy(
                                cash, unit_investment, initial_buy_price, commission_rate)
                            if number_of_shares > 0:
                                total_cost_including_commission = total_cost + commission
                                holdings += number_of_shares
                                cash -= total_cost_including_commission
                                buy_count = 1
                                buy_levels.append({'price': initial_buy_price, 'shares': number_of_shares})
                                waiting_for_initial_price = False
                    else:
                        if buy_count == 0 and cash >= unit_investment and price_type == 'close':
                            buy_price = price
                            number_of_shares, total_cost, commission = calculate_number_of_shares_to_buy(
                                cash, unit_investment, buy_price, commission_rate)
                            if number_of_shares > 0:
                                total_cost_including_commission = total_cost + commission
                                holdings += number_of_shares
                                cash -= total_cost_including_commission
                                initial_buy_price = buy_price
                                buy_count = 1
                                buy_levels.append({'price': buy_price, 'shares': number_of_shares})
                        elif buy_count > 0:
                            target_buy_price = buy_levels[-1]['price'] * (1 - buy_next_percent_decimal)
                            if (price <= target_buy_price) and (buy_count < max_buy_times) and (cash >= unit_investment):
                                buy_price = target_buy_price
                                number_of_shares, total_cost, commission = calculate_number_of_shares_to_buy(
                                    cash, unit_investment, buy_price, commission_rate)
                                if number_of_shares > 0:
                                    total_cost_including_commission = total_cost + commission
                                    holdings += number_of_shares
                                    cash -= total_cost_including_commission
                                    buy_count += 1
                                    buy_levels.append({'price': buy_price, 'shares': number_of_shares})
                            
                            target_sell_price = buy_levels[-1]['price'] * (1 + sell_percent_decimal)
                            if (price >= target_sell_price):
                                sell_price = target_sell_price
                                last_buy_level = buy_levels[-1]
                                number_of_shares_to_sell = last_buy_level['shares']
                                net_proceeds, commission, transaction_tax = calculate_proceeds_from_selling(
                                    number_of_shares_to_sell, sell_price, commission_rate, transaction_tax_rate)
                                holdings -= number_of_shares_to_sell
                                cash += net_proceeds
                                buy_count -= 1
                                buy_levels.pop()
                                
                                if buy_count == 0:
                                    waiting_for_initial_price = True
            
            total_value = cash + holdings * close
            total_return = (total_value - initial_investment) / initial_investment * 100
            
            results.append({
                '매수 갭 %': buy_next_percent,
                '매도 %': sell_percent,
                '총 수익률 (%)': total_return
            })
            
            # 진행 상황 업데이트
            my_bar.progress(iteration / total_iterations)
    
    # 결과 데이터프레임 및 피벗 테이블 생성    
    results_df = pd.DataFrame(results)
    pivot_table = results_df.pivot(index='매수 갭 %', columns='매도 %', values='총 수익률 (%)').astype(float)
    pivot_table = pivot_table.round(2)
    pivot_table.columns = ['매도 {}%'.format(col) for col in pivot_table.columns]
    
    st.subheader('📊 백테스팅 결과')
    st.dataframe(pivot_table.style.format("{:.2f}").background_gradient(cmap='RdYlGn', axis=None))
        
    # 최적의 수익률 및 해당 변수 조합 찾기
    max_return = results_df['총 수익률 (%)'].max()
    optimal_row = results_df.loc[results_df['총 수익률 (%)'] == max_return].iloc[0]
    optimal_buy_next_percent = optimal_row['매수 갭 %']
    optimal_sell_percent = optimal_row['매도 %']
    
    st.write(f"🏆 최적의 총 수익률은 {max_return:.2f}%이며, 매수 갭 %는 {optimal_buy_next_percent}%, 매도 %는 {optimal_sell_percent}%입니다.")
    
    # 최적의 변수로 백테스팅 결과 시각화
    st.subheader('📈 최적의 변수로 백테스팅 결과 시각화')
    
    # 최적의 변수로 다시 백테스팅 실행 (매매 내역 및 포트폴리오 가치 기록)
    buy_next_percent = optimal_buy_next_percent
    sell_percent = optimal_sell_percent
    buy_next_percent_decimal = buy_next_percent / 100
    sell_percent_decimal = sell_percent / 100
    
    holdings = 0
    cash = initial_investment
    portfolio_value = []
    dates = []
    trade_history = []
    
    commission_rate = 0.00015
    transaction_tax_rate = 0.0018
    
    initial_buy_price = None
    waiting_for_initial_price = False
    buy_count = 0
    buy_levels = []
    
    for date, row in df.iterrows():
        high = row['고가']
        low = row['저가']
        close = row['종가']
        
        price_sequence = [
            ('low', low),
            ('high', high),
            ('close', close)
        ]
        
        for price_type, price in price_sequence:
            if waiting_for_initial_price:
                if price <= initial_buy_price and cash >= unit_investment:
                    number_of_shares, total_cost, commission = calculate_number_of_shares_to_buy(
                        cash, unit_investment, initial_buy_price, commission_rate)
                    if number_of_shares > 0:
                        total_cost_including_commission = total_cost + commission
                        holdings += number_of_shares
                        cash -= total_cost_including_commission
                        buy_count = 1
                        buy_levels.append({'price': initial_buy_price, 'shares': number_of_shares})
                        trade_history.append({
                            'Date': date, 'Type': 'Buy', 'Price': initial_buy_price, 
                            'Holdings': holdings, 'Cash': cash, 'Buy_Count': buy_count, 'Shares': number_of_shares
                        })
                        waiting_for_initial_price = False
            else:
                if buy_count == 0 and cash >= unit_investment and price_type == 'close':
                    buy_price = price
                    number_of_shares, total_cost, commission = calculate_number_of_shares_to_buy(
                        cash, unit_investment, buy_price, commission_rate)
                    if number_of_shares > 0:
                        total_cost_including_commission = total_cost + commission
                        holdings += number_of_shares
                        cash -= total_cost_including_commission
                        initial_buy_price = buy_price
                        buy_count = 1
                        buy_levels.append({'price': buy_price, 'shares': number_of_shares})
                        trade_history.append({
                            'Date': date, 'Type': 'Buy', 'Price': buy_price, 
                            'Holdings': holdings, 'Cash': cash, 'Buy_Count': buy_count, 'Shares': number_of_shares
                        })
                elif buy_count > 0:
                    target_buy_price = buy_levels[-1]['price'] * (1 - buy_next_percent_decimal)
                    if (price <= target_buy_price) and (buy_count < max_buy_times) and (cash >= unit_investment):
                        buy_price = target_buy_price
                        number_of_shares, total_cost, commission = calculate_number_of_shares_to_buy(
                            cash, unit_investment, buy_price, commission_rate)
                        if number_of_shares > 0:
                            total_cost_including_commission = total_cost + commission
                            holdings += number_of_shares
                            cash -= total_cost_including_commission
                            buy_count += 1
                            buy_levels.append({'price': buy_price, 'shares': number_of_shares})
                            trade_history.append({
                                'Date': date, 'Type': 'Buy', 'Price': buy_price, 
                                'Holdings': holdings, 'Cash': cash, 'Buy_Count': buy_count, 'Shares': number_of_shares
                            })
                    
                    target_sell_price = buy_levels[-1]['price'] * (1 + sell_percent_decimal)
                    if (price >= target_sell_price):
                        sell_price = target_sell_price
                        last_buy_level = buy_levels[-1]
                        number_of_shares_to_sell = last_buy_level['shares']
                        net_proceeds, commission, transaction_tax = calculate_proceeds_from_selling(
                            number_of_shares_to_sell, sell_price, commission_rate, transaction_tax_rate)
                        holdings -= number_of_shares_to_sell
                        cash += net_proceeds
                        trade_history.append({
                            'Date': date, 'Type': 'Sell', 'Price': sell_price, 
                            'Holdings': holdings, 'Cash': cash, 'Buy_Count': buy_count, 'Shares': number_of_shares_to_sell
                        })
                        buy_count -= 1
                        buy_levels.pop()
                        
                        if buy_count == 0:
                            waiting_for_initial_price = True
        
        total_value = cash + holdings * close
        portfolio_value.append(total_value)
        dates.append(date)
    
    # -------------------------------
    # 캔들차트에 매매 시점 표시 (mplfinance)
    # -------------------------------
    df_candle = df.rename(columns={'시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close'})
    
    buy_signals = pd.Series(np.nan, index=df_candle.index)
    sell_signals = pd.Series(np.nan, index=df_candle.index)
    
    for trade in trade_history:
        if trade['Type'] == 'Buy':
            buy_signals.loc[trade['Date']] = trade['Price']
        elif trade['Type'] == 'Sell':
            sell_signals.loc[trade['Date']] = trade['Price']
    
    apds = [
        mpf.make_addplot(buy_signals, type='scatter', markersize=100, marker='^', color='green'),
        mpf.make_addplot(sell_signals, type='scatter', markersize=100, marker='v', color='red')
    ]
    

    
    fig, ax = mpf.plot(
        df_candle,
        type='candle',
        style='yahoo',
        addplot=apds,
        returnfig=True,
        title=f'{target_ticker} () Buy and Sell Signals (Optimized Parameters)',
        ylabel='Price (KRW)'
    )
    
    for trade in trade_history:
        if trade['Type'] == 'Buy':
            ax[0].annotate(f"{int(trade['Buy_Count'])}", xy=(trade['Date'], trade['Price']),
                           xytext=(0,10), textcoords='offset points', color='green', ha='center')
        elif trade['Type'] == 'Sell':
            ax[0].annotate(f"{int(trade['Buy_Count'])}", xy=(trade['Date'], trade['Price']),
                           xytext=(0,-15), textcoords='offset points', color='red', ha='center')
    
    st.pyplot(fig)
    
    # 포트폴리오 가치 변화 시각화
    portfolio_series = pd.Series(portfolio_value, index=dates)
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.plot(portfolio_series.index, portfolio_series.values)
    ax2.set_title('Portfolio Value Change (Optimized Parameters)')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Portfolio Value (KRW)')
    ax2.grid(True)
    
    st.pyplot(fig2)
    
    # 매매 내역 표시 (아이콘 추가)
    st.subheader('📜 매매 내역')
    trade_history_df = pd.DataFrame(trade_history)
    trade_history_df.set_index('Date', inplace=True)
    st.dataframe(trade_history_df)
    st.write("For inquiries: jsm02115@naver.com")
    
    # ========================================================
    # DB 저장: 백테스트 실행 시 사용한 값 및 결과를 하나의 .db 파일에 저장
    # ========================================================
    conn = sqlite3.connect("backtest_results.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backtest_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT,
            target_ticker TEXT,
            ticker_name TEXT,
            initial_investment REAL,
            unit_investment REAL,
            max_buy_times INTEGER,
            start_date TEXT,
            end_date TEXT,
            buy_next_percent_start REAL,
            buy_next_percent_end REAL,
            buy_next_percent_step REAL,
            sell_percent_start REAL,
            sell_percent_end REAL,
            sell_percent_step REAL,
            optimal_buy_next_percent REAL,
            optimal_sell_percent REAL,
            max_return REAL
        )
    """)
    conn.commit()
    
    run_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ticker_name = stock.get_market_ticker_name(target_ticker)
    
    cursor.execute("""
        INSERT INTO backtest_runs (
            run_timestamp, target_ticker, ticker_name, initial_investment, unit_investment, max_buy_times,
            start_date, end_date, buy_next_percent_start, buy_next_percent_end, buy_next_percent_step,
            sell_percent_start, sell_percent_end, sell_percent_step, optimal_buy_next_percent,
            optimal_sell_percent, max_return
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_timestamp, target_ticker, ticker_name, initial_investment, unit_investment, max_buy_times,
        start_date_input.strftime('%Y-%m-%d'), end_date_input.strftime('%Y-%m-%d'),
        buy_next_percent_start, buy_next_percent_end, buy_next_percent_step,
        sell_percent_start, sell_percent_end, sell_percent_step,
        optimal_buy_next_percent, optimal_sell_percent, max_return 
    ))
    conn.commit()
    conn.close()
    # st.success("✅ 백테스트 결과가 데이터베이스에 저장되었습니다!")
