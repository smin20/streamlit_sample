# strategy.py
from config import COMMISSION_RATE, TRANSACTION_TAX_RATE

def calculate_number_of_shares_to_buy(cash_available, unit_investment, price, commission_rate=COMMISSION_RATE):
    """
    매수 가능한 주식 수를 계산합니다.
    """
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

def calculate_proceeds_from_selling(number_of_shares, sell_price, commission_rate=COMMISSION_RATE, transaction_tax_rate=TRANSACTION_TAX_RATE):
    """
    매도 후 순수익을 계산합니다.
    """
    total_proceeds = number_of_shares * sell_price
    commission = total_proceeds * commission_rate
    transaction_tax = total_proceeds * transaction_tax_rate
    net_proceeds = total_proceeds - commission - transaction_tax
    return net_proceeds, commission, transaction_tax

def run_backtest(df, initial_investment, unit_investment, max_buy_times, buy_next_percent, sell_percent):
    """
    단일 파라미터 조합에 대해 백테스트를 실행합니다.
    반환값:
      - trade_history: 매매 내역 리스트
      - final_value: 최종 포트폴리오 가치
      - total_return: 총 수익률 (%)
    """
    buy_next_percent_decimal = buy_next_percent / 100
    sell_percent_decimal = sell_percent / 100

    holdings = 0
    cash = initial_investment
    buy_count = 0
    buy_levels = []
    trade_history = []
    waiting_for_initial_price = False
    initial_buy_price = None

    for date, row in df.iterrows():
        high = row['고가']
        low = row['저가']
        close = row['종가']

        price_sequence = [('low', low), ('high', high), ('close', close)]
        
        for price_type, price in price_sequence:
            # 만약 매도 후 초기 상태라면, 지정한 가격 이하에서 다시 매수 시작
            if waiting_for_initial_price:
                if initial_buy_price is not None and price <= initial_buy_price and cash >= unit_investment:
                    number_of_shares, total_cost, commission = calculate_number_of_shares_to_buy(cash, unit_investment, initial_buy_price)
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
                    # 첫 매수
                    buy_price = price
                    number_of_shares, total_cost, commission = calculate_number_of_shares_to_buy(cash, unit_investment, buy_price)
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
                    # 추가 매수 조건
                    target_buy_price = buy_levels[-1]['price'] * (1 - buy_next_percent_decimal)
                    if price <= target_buy_price and buy_count < max_buy_times and cash >= unit_investment:
                        buy_price = target_buy_price
                        number_of_shares, total_cost, commission = calculate_number_of_shares_to_buy(cash, unit_investment, buy_price)
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
                    # 매도 조건
                    target_sell_price = buy_levels[-1]['price'] * (1 + sell_percent_decimal)
                    if price >= target_sell_price:
                        sell_price = target_sell_price
                        last_buy_level = buy_levels[-1]
                        number_of_shares_to_sell = last_buy_level['shares']
                        net_proceeds, _, _ = calculate_proceeds_from_selling(number_of_shares_to_sell, sell_price)
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

    final_value = cash + holdings * df.iloc[-1]['종가']
    total_return = (final_value - initial_investment) / initial_investment * 100

    return trade_history, final_value, total_return

# strategy.py (추가 함수)
def compute_portfolio_history(df, trade_history, initial_investment):
    """
    trade_history의 거래 내역과 df (날짜별 종가)를 기반으로 포트폴리오 가치를 기록합니다.
    
    Parameters:
      df (DataFrame): 날짜별 OHLCV 데이터 (인덱스는 datetime)
      trade_history (list): 각 거래 이벤트를 담은 리스트 (각 항목은 dict)
      initial_investment (int): 초기 투자 금액
      
    Returns:
      dates (list): 날짜 리스트
      portfolio_values (list): 각 날짜의 포트폴리오 가치 (cash + holdings * 종가)
    """
    # 거래 내역을 날짜 순으로 정렬
    trade_history_sorted = sorted(trade_history, key=lambda x: x['Date'])
    
    portfolio_values = []
    cash = initial_investment
    holdings = 0
    trade_idx = 0
    trades_len = len(trade_history_sorted)
    
    # df의 각 날짜별로 거래 내역 업데이트 반영
    for date, row in df.iterrows():
        # 해당 날짜에 발생한 모든 거래 처리
        while trade_idx < trades_len and trade_history_sorted[trade_idx]['Date'] == date:
            trade = trade_history_sorted[trade_idx]
            cash = trade['Cash']       # 거래 후 cash 값 업데이트
            holdings = trade['Holdings']  # 거래 후 holdings 값 업데이트
            trade_idx += 1
        # 해당 날짜 종가 기준 포트폴리오 가치 계산
        portfolio_value = cash + holdings * row['종가']
        portfolio_values.append(portfolio_value)
        
    return list(df.index), portfolio_values