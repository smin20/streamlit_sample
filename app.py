import streamlit as st
import datetime
import numpy as np
import pandas as pd
import warnings

from config import (
    INITIAL_INVESTMENT, UNIT_INVESTMENT, MAX_BUY_TIMES,
    BUY_NEXT_PERCENT_START, BUY_NEXT_PERCENT_END, BUY_NEXT_PERCENT_STEP,
    SELL_PERCENT_START, SELL_PERCENT_END, SELL_PERCENT_STEP
)
from logger import logger
from data_loader import load_ticker_info, load_etf_ticker_info, get_market_cap, load_market_data
from strategy import run_backtest
from visualization import plot_candlestick_with_signals, plot_portfolio_value
from database import insert_backtest_result, fetch_recent_searches

warnings.filterwarnings("ignore", message="findfont: Font family 'Malgun Gothic' not found.")

st.set_page_config(layout="wide")
st.info('🪄 매직스플릿 결과 백테스팅 페이지 입니다. 종목 선택 후 🚀 백테스트 실행 버튼을 클릭하세요.')

# ----------------------------
# 사이드바: 투자 유형 및 종목 검색
# ----------------------------
st.sidebar.header("🔍 투자 유형 및 종목 검색")
instrument_type = st.sidebar.radio("📊 투자 유형 선택", ["주식", "ETF"])
search_query = st.sidebar.text_input("🔎 종목/ETF 이름 혹은 Code\n\n(ex. 삼성/KODEX/005930)", key="search_query")

target_ticker = None
ticker_name = None
if search_query:
    if instrument_type == "주식":
        ticker_info = load_ticker_info()
        filtered_tickers = {
            code: name
            for code, name in ticker_info.items()
            if search_query.lower() in name.lower() or search_query in code
        }
        if filtered_tickers:
            today_str = datetime.datetime.today().strftime("%Y%m%d")
            sorted_filtered_tickers = sorted(
                filtered_tickers.items(),
                key=lambda x: get_market_cap(x[0], today_str),
                reverse=True
            )
            selected = st.sidebar.selectbox(
                "📋 검색 결과",
                sorted_filtered_tickers,
                format_func=lambda x: f"{x[0]} - {x[1]}"
            )
            target_ticker = selected[0]
            st.sidebar.write(f"✅ 선택된 종목: **{selected[0]} ({selected[1]})**")
        else:
            st.sidebar.write("❌ 검색 결과가 없습니다.")
    else:
        ticker_info = load_etf_ticker_info()
        filtered_tickers = {
            code: name
            for code, name in ticker_info.items()
            if search_query.lower() in name.lower() or search_query in code
        }
        if filtered_tickers:
            sorted_filtered_tickers = sorted(filtered_tickers.items(), key=lambda x: x[0])
            selected = st.sidebar.selectbox(
                "📋 검색 결과",
                sorted_filtered_tickers,
                format_func=lambda x: f"{x[0]} - {x[1]}"
            )
            target_ticker = selected[0]
            st.sidebar.write(f"✅ 선택된 ETF: **{selected[0]} ({selected[1]})**")
        else:
            st.sidebar.write("❌ 검색 결과가 없습니다.")
else:
    st.sidebar.write("ℹ️ 종목/ETF 검색어를 입력하세요.")

# ----------------------------
# 사이드바: 기초 설정
# ----------------------------
st.sidebar.header('⚙️ 기초 설정')
initial_investment = st.sidebar.number_input('💰 총 투자금액', value=INITIAL_INVESTMENT, step=100000)
unit_investment = st.sidebar.number_input('📌 1차수당 금액', value=UNIT_INVESTMENT, step=50000)
max_buy_times = st.sidebar.number_input('🔁 최대 매수 횟수', value=MAX_BUY_TIMES, min_value=1, step=1)

# ----------------------------
# 사이드바: 날짜 범위 설정
# ----------------------------
st.sidebar.header('📅 날짜 범위 설정 (기본 6개월)')
start_date_input = st.sidebar.date_input('시작 날짜', datetime.datetime.today() - datetime.timedelta(days=180))
end_date_input = st.sidebar.date_input('종료 날짜', datetime.datetime.today())
start_date = start_date_input.strftime('%Y%m%d')
end_date = end_date_input.strftime('%Y%m%d')

# ----------------------------
# 백테스트 실행 및 결과 저장 (세션 상태 활용)
# ----------------------------
if st.sidebar.button('🚀 백테스트 실행'):
    log_line = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 백테스트 실행됨"
    if target_ticker:
        # 종목 이름 확인 (ETF와 주식 구분)
        from pykrx import stock
        if instrument_type == "ETF":
            ticker_name = stock.get_etf_ticker_name(target_ticker)
        else:
            ticker_name = stock.get_market_ticker_name(target_ticker)
        log_line += f" (종목: {target_ticker} - {ticker_name})"
    else:
        log_line += " (종목 미선택)"
    logger.info(log_line)

    if not target_ticker:
        st.error("❗ 종목/ETF를 선택하세요.")
        st.stop()

    # 데이터 로드
    try:
        st.write(f'📈 {instrument_type} 코드 {target_ticker} ({ticker_name}) 의 데이터를 {start_date_input}부터 {end_date_input}까지 가져옵니다.')
        df = load_market_data(instrument_type, target_ticker, start_date, end_date)
    except Exception as e:
        st.error(f'❗ 데이터를 가져오는 중 오류 발생: {e}')
        st.stop()

    # 매개변수 그리드에 따른 백테스트 실행
    results = []
    total_iterations = int(
        len(np.arange(BUY_NEXT_PERCENT_START, BUY_NEXT_PERCENT_END + BUY_NEXT_PERCENT_STEP, BUY_NEXT_PERCENT_STEP)) *
        len(np.arange(SELL_PERCENT_START, SELL_PERCENT_END + SELL_PERCENT_STEP, SELL_PERCENT_STEP))
    )
    iteration = 0
    progress_bar = st.progress(0)
    
    for buy_next_percent in np.arange(BUY_NEXT_PERCENT_START, BUY_NEXT_PERCENT_END + BUY_NEXT_PERCENT_STEP, BUY_NEXT_PERCENT_STEP):
        for sell_percent in np.arange(SELL_PERCENT_START, SELL_PERCENT_END + SELL_PERCENT_STEP, SELL_PERCENT_STEP):
            iteration += 1
            trade_history, final_value, total_return = run_backtest(
                df, initial_investment, unit_investment, max_buy_times, buy_next_percent, sell_percent
            )
            results.append({
                '매수 갭 %': buy_next_percent,
                '매도 %': sell_percent,
                '총 수익률 (%)': total_return
            })
            progress_bar.progress(iteration / total_iterations)
    
    results_df = pd.DataFrame(results)
    pivot_table = results_df.pivot(index='매수 갭 %', columns='매도 %', values='총 수익률 (%)').astype(float).round(2)
    pivot_table.columns = [f'매도 {col}%' for col in pivot_table.columns]
    
    # 최적 파라미터 도출
    max_return = results_df['총 수익률 (%)'].max()
    optimal_row = results_df.loc[results_df['총 수익률 (%)'] == max_return].iloc[0]
    optimal_buy_next_percent = optimal_row['매수 갭 %']
    optimal_sell_percent = optimal_row['매도 %']
    
    # 최적 파라미터로 다시 백테스트 실행 (매매 내역 기록)
    trade_history, final_value, total_return = run_backtest(
        df, initial_investment, unit_investment, max_buy_times, optimal_buy_next_percent, optimal_sell_percent
    )
    
    # 포트폴리오 가치 변화 계산: trade_history를 반영하여 각 날짜별 cash와 holdings 업데이트
    from strategy import compute_portfolio_history  # 새로 추가한 함수
    dates, portfolio_values = compute_portfolio_history(df, trade_history, initial_investment)
    
    # 시각화
    fig_candle = plot_candlestick_with_signals(df, trade_history, target_ticker)
    fig_portfolio = plot_portfolio_value(dates, portfolio_values)
    
    # 매매 내역 DataFrame
    trade_history_df = pd.DataFrame(trade_history)
    if not trade_history_df.empty:
        trade_history_df.set_index('Date', inplace=True)
    
    
    
    # Supabase DB에 결과 저장
    insert_data = {
        'instrument_type': instrument_type,
        'target_ticker': target_ticker,
        'ticker_name': ticker_name,
        'initial_investment': initial_investment,
        'unit_investment': unit_investment,
        'max_buy_times': max_buy_times,
        'start_date': start_date_input.strftime('%Y-%m-%d'),
        'end_date': end_date_input.strftime('%Y-%m-%d'),
        'optimal_buy_next_percent': optimal_buy_next_percent,
        'optimal_sell_percent': optimal_sell_percent,
        'max_return': max_return,
        'final_portfolio_value': final_value
    }
    insert_backtest_result(insert_data)
    
    # 백테스트 결과를 세션 상태에 저장 (추후 탭에서 활용)
    st.session_state['backtest_output'] = {
        'pivot_table': pivot_table,
        'max_return': max_return,
        'optimal_buy_next_percent': optimal_buy_next_percent,
        'optimal_sell_percent': optimal_sell_percent,
        'fig_candle': fig_candle,
        'fig_portfolio': fig_portfolio,
        'trade_history_df': trade_history_df,
        'target_ticker': target_ticker,
        'ticker_name': ticker_name,
        'final_value': final_value,
    }

# ----------------------------
# 메인 화면: 탭 구성 ("백테스팅 결과"와 "최근 검색 내역")
# ----------------------------
tabs = st.tabs(["📊 백테스팅 결과", "📝 최근 검색 내역"])

with tabs[0]:
    st.subheader("📊 백테스팅 결과")
    if 'backtest_output' in st.session_state:
        output = st.session_state['backtest_output']
        st.dataframe(output['pivot_table'].style.format("{:.2f}").background_gradient(cmap='RdYlGn', axis=None))
        st.write(f"🏆 최적의 총 수익률은 {output['max_return']:.2f}%이며, 매수 갭 %는 {output['optimal_buy_next_percent']}%, 매도 %는 {output['optimal_sell_percent']}%입니다.")
        st.pyplot(output['fig_candle'])
        st.pyplot(output['fig_portfolio'])
        st.subheader("📜 매매 내역")
        if not output['trade_history_df'].empty:
            st.dataframe(output['trade_history_df'])
            st.write("에러 혹은 피드백은 메일 주시면 답변드리겠습니다. : jsm02115@naver.com")
        else:
            st.write("매매 내역이 없습니다.")
    else:
        st.info("좌측 사이드바에서 🚀 백테스트 실행 버튼을 클릭하여 결과를 확인하세요.")
        
with tabs[1]:
    st.subheader("📝 다른 사용자의 최근 검색 내역")
    recent_searches = fetch_recent_searches(limit=20)  # 중복을 고려하여 더 많은 데이터를 요청할 수 있음
    if recent_searches:
        df_recent = pd.DataFrame(recent_searches)
        df_recent = df_recent.drop_duplicates().head(20)  # 중복 항목 제거 후 상위 5개만 보여줌
        st.dataframe(df_recent)
    else:
        st.write("최근 검색 내역이 없습니다.")
