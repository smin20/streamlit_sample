import streamlit as st
import datetime 
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pykrx import stock

# 페이지 설정을 넓은 레이아웃으로 설정
st.set_page_config(layout="wide")

# Streamlit 앱 제목
st.title('매직스플릿 전략 최적화')

# 사용자 입력을 위한 사이드바 설정
st.sidebar.header('기초 설정')

# 변수 초기화 부분을 Streamlit 위젯으로 변경
initial_investment = st.sidebar.number_input('총 투자금액', value=5000000, step=100000)
unit_investment = st.sidebar.number_input('1차수당 금액', value=500000, step=50000)
max_buy_times = st.sidebar.number_input('최대 매수 횟수', value=10, min_value=1, step=1)
target_ticker = st.sidebar.text_input('종목 코드', value='161390')

# 매수 갭 %와 매도 %의 범위 설정 (고정 값으로 설정)
buy_next_percent_start = 5.00
buy_next_percent_end = 10.00
buy_next_percent_step = 1.0

sell_percent_start = 3.00
sell_percent_end = 5.00
sell_percent_step = 0.5

# 날짜 범위 선택
st.sidebar.header('날짜 범위 설정')
start_date_input = st.sidebar.date_input('시작 날짜', datetime.datetime.today() - datetime.timedelta(days=180))
end_date_input = st.sidebar.date_input('종료 날짜', datetime.datetime.today())

start_date = start_date_input.strftime('%Y%m%d')
end_date = end_date_input.strftime('%Y%m%d')

# 백테스트 실행 버튼
if st.sidebar.button('백테스트 실행'):
    # 데이터 가져오기
    try:
        st.write(f'종목 코드 {target_ticker}의 데이터를 {start_date_input}부터 {end_date_input}까지 가져옵니다.')
        df = stock.get_market_ohlcv_by_date(start_date, end_date, target_ticker)
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
    except Exception as e:
        st.error(f'데이터를 가져오는 중 오류 발생: {e}')
        st.stop()
    
    # 결과를 저장할 리스트 초기화
    results = []
    
    # 매수 갭 %와 매도 %의 범위 설정
    buy_next_percent_range = np.arange(buy_next_percent_start, buy_next_percent_end + buy_next_percent_step, buy_next_percent_step)
    sell_percent_range = np.arange(sell_percent_start, sell_percent_end + sell_percent_step, sell_percent_step)
    
    progress_text = "백테스팅 진행 중입니다. 잠시만 기다려주세요."
    my_bar = st.progress(0)
    total_iterations = len(buy_next_percent_range) * len(sell_percent_range)
    iteration = 0
    
    # 매수 갭 %와 매도 %의 모든 조합에 대해 백테스팅 실행
    for buy_next_percent in buy_next_percent_range:
        for sell_percent in sell_percent_range:
            iteration += 1
            # 퍼센트 값을 소수로 변환
            buy_next_percent_decimal = buy_next_percent / 100
            sell_percent_decimal = sell_percent / 100
            
            holdings = 0  # 보유 주식 수 (정수)
            cash = initial_investment
            
            # 수수료 및 세금 설정 (키움증권 기준)
            commission_rate = 0.00015       # 매수/매도 수수료 0.015%
            transaction_tax_rate = 0.0018   # 매도 시 거래세 0.18%
            
            # 새로운 변수들
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
    
    # 결과를 데이터프레임으로 변환
    results_df = pd.DataFrame(results)

    # 피벗 테이블 생성    
    pivot_table = results_df.pivot(index='매수 갭 %', columns='매도 %', values='총 수익률 (%)').astype(float)
    pivot_table = pivot_table.round(2)
    # 컬럼 제목 변경
    pivot_table.columns = ['매도 {}%'.format(col) for col in pivot_table.columns]

    st.subheader('백테스팅 결과')
    st.dataframe(pivot_table.style.format("{:.2f}").background_gradient(cmap='RdYlGn', axis=None))
        
    # 최적의 수익률 및 해당 변수 조합 찾기
    max_return = results_df['총 수익률 (%)'].max()
    optimal_row = results_df.loc[results_df['총 수익률 (%)'] == max_return].iloc[0]
    optimal_buy_next_percent = optimal_row['매수 갭 %']
    optimal_sell_percent = optimal_row['매도 %']
    
    st.write(f"최적의 총 수익률은 {max_return:.2f}%이며, 매수 갭 %는 {optimal_buy_next_percent}%, 매도 %는 {optimal_sell_percent}%입니다.")
    
    # 최적의 변수로 백테스팅 결과 시각화
    st.subheader('최적의 변수로 백테스팅 결과 시각화')
    
    # 최적의 변수로 다시 백테스팅 실행
    buy_next_percent = optimal_buy_next_percent
    sell_percent = optimal_sell_percent
    buy_next_percent_decimal = buy_next_percent / 100
    sell_percent_decimal = sell_percent / 100
    
    holdings = 0  # 보유 주식 수 (정수)
    cash = initial_investment
    portfolio_value = []
    dates = []
    trade_history = []
    
    # 수수료 및 세금 설정 (키움증권 기준)
    commission_rate = 0.00015       # 매수/매도 수수료 0.015%
    transaction_tax_rate = 0.0018   # 매도 시 거래세 0.18%
    
    # 새로운 변수들
    initial_buy_price = None          # 1차 매수 가격 저장
    waiting_for_initial_price = False # 1차 매수 가격까지 하락 대기 상태
    buy_count = 0                     # 현재 보유 중인 매수 차수
    buy_levels = []                   # 보유 중인 매수 레벨별 가격 및 수량
    
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
                        trade_history.append({'Date': date, 'Type': 'Buy', 'Price': initial_buy_price, 
                                              'Holdings': holdings, 'Cash': cash, 'Buy_Count': buy_count, 'Shares': number_of_shares})
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
                        trade_history.append({'Date': date, 'Type': 'Buy', 'Price': buy_price, 
                                              'Holdings': holdings, 'Cash': cash, 'Buy_Count': buy_count, 'Shares': number_of_shares})
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
                            trade_history.append({'Date': date, 'Type': 'Buy', 'Price': buy_price, 
                                                  'Holdings': holdings, 'Cash': cash, 'Buy_Count': buy_count, 'Shares': number_of_shares})
                    
                    target_sell_price = buy_levels[-1]['price'] * (1 + sell_percent_decimal)
                    if (price >= target_sell_price):
                        sell_price = target_sell_price
                        last_buy_level = buy_levels[-1]
                        number_of_shares_to_sell = last_buy_level['shares']
                        net_proceeds, commission, transaction_tax = calculate_proceeds_from_selling(
                            number_of_shares_to_sell, sell_price, commission_rate, transaction_tax_rate)
                        holdings -= number_of_shares_to_sell
                        cash += net_proceeds
                        trade_history.append({'Date': date, 'Type': 'Sell', 'Price': sell_price, 
                                              'Holdings': holdings, 'Cash': cash, 'Buy_Count': buy_count, 'Shares': number_of_shares_to_sell})
                        buy_count -= 1
                        buy_levels.pop()
                        
                        if buy_count == 0:
                            waiting_for_initial_price = True
        
        total_value = cash + holdings * close
        portfolio_value.append(total_value)
        dates.append(date)
    
    # 매수 및 매도 내역에서 매수/매도 차수 추출
    buy_dates = [trade['Date'] for trade in trade_history if trade['Type'] == 'Buy']
    buy_prices_plot = [trade['Price'] for trade in trade_history if trade['Type'] == 'Buy']
    buy_counts = [trade['Buy_Count'] for trade in trade_history if trade['Type'] == 'Buy']
    
    sell_dates = [trade['Date'] for trade in trade_history if trade['Type'] == 'Sell']
    sell_prices_plot = [trade['Price'] for trade in trade_history if trade['Type'] == 'Sell']
    sell_counts = [trade['Buy_Count'] for trade in trade_history if trade['Type'] == 'Sell']
    
    # 결과 시각화
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 고가와 저가를 함께 그리기
    ax.plot(df.index, df['고가'], label='고가', color='orange', alpha=0.6)
    ax.plot(df.index, df['저가'], label='저가', color='purple', alpha=0.6)
    
    # 종가를 함께 그리기
    ax.plot(df.index, df['종가'], label='종가', color='blue')
    
    # 매수 시점 표시
    ax.scatter(buy_dates, buy_prices_plot, marker='^', color='green', label='매수', s=100)
    
    # 매수 차수 라벨 표시
    for i, txt in enumerate(buy_counts):
        ax.annotate(f'{int(txt)}', (buy_dates[i], buy_prices_plot[i]), textcoords="offset points", xytext=(0,10), ha='center')
    
    # 매도 시점 표시
    ax.scatter(sell_dates, sell_prices_plot, marker='v', color='red', label='매도', s=100)
    
    # 매도 차수 라벨 표시
    for i, txt in enumerate(sell_counts):
        ax.annotate(f'{int(txt)}', (sell_dates[i], sell_prices_plot[i]), textcoords="offset points", xytext=(0,-15), ha='center')
    
    ax.set_title(f'{target_ticker} 매수 및 매도 시점 (최적화된 변수)')
    ax.set_xlabel('날짜')
    ax.set_ylabel('가격 (원)')
    ax.legend()
    ax.grid(True)
    
    st.pyplot(fig)
    
    # 포트폴리오 가치 변화 시각화
    portfolio_series = pd.Series(portfolio_value, index=dates)
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.plot(portfolio_series.index, portfolio_series.values)
    ax2.set_title('포트폴리오 가치 변화 (최적화된 변수)')
    ax2.set_xlabel('날짜')
    ax2.set_ylabel('포트폴리오 가치 (원)')
    ax2.grid(True)
    
    st.pyplot(fig2)
    
    # 매매 내역 표시
    st.subheader('매매 내역')
    trade_history_df = pd.DataFrame(trade_history)
    trade_history_df.set_index('Date', inplace=True)
    st.dataframe(trade_history_df)
    st.write("메일문의 : jsm02115@naver.com")
