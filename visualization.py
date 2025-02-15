# visualization.py
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import numpy as np

def plot_candlestick_with_signals(df, trade_history, target_ticker):
    """
    캔들 차트에 매매 시점을 표시하는 함수입니다.
    """
    df_candle = df.rename(columns={'시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close'})
    buy_signals = pd.Series(np.nan, index=df_candle.index)
    sell_signals = pd.Series(np.nan, index=df_candle.index)

    for trade in trade_history:
        if trade['Type'] == 'Buy':
            buy_signals.loc[trade['Date']] = trade['Price']
        elif trade['Type'] == 'Sell':
            sell_signals.loc[trade['Date']] = trade['Price']

    apds = []
    if not buy_signals.dropna().empty:
        apds.append(mpf.make_addplot(buy_signals, type='scatter', markersize=100, marker='^', color='green'))
    if not sell_signals.dropna().empty:
        apds.append(mpf.make_addplot(sell_signals, type='scatter', markersize=100, marker='v', color='red'))

    fig, ax = mpf.plot(
        df_candle,
        type='candle',
        style='yahoo',
        addplot=apds,
        returnfig=True,
        title=f'{target_ticker} Buy and Sell Signals (Optimized Parameters)',
        ylabel='Price (KRW)'
    )
    # 거래 내역에 따른 텍스트 표시
    for trade in trade_history:
        if trade['Type'] == 'Buy':
            ax[0].annotate(
                f"{int(trade['Buy_Count'])}차 매수",
                xy=(trade['Date'], trade['Price']),
                xytext=(0, 10),
                textcoords='offset points',
                color='green',
                ha='center',
                fontsize=8,
                clip_on=False,
                zorder=10
            )
        elif trade['Type'] == 'Sell':
            ax[0].annotate(
                f"{int(trade['Buy_Count'])}차 매도",
                xy=(trade['Date'], trade['Price']),
                xytext=(0, -15),
                textcoords='offset points',
                color='red',
                ha='center',
                fontsize=8,
                clip_on=False,
                zorder=10
            )
    return fig

def plot_portfolio_value(dates, portfolio_values):
    """
    포트폴리오 가치 변화를 선 그래프로 나타냅니다.
    
    Parameters:
      dates (list): x축에 표시할 날짜 리스트 (문자열 또는 datetime)
      portfolio_values (list): 포트폴리오 가치 값 리스트
    Returns:
      fig: matplotlib Figure 객체
    """
    # 날짜가 문자열인 경우 datetime 형식으로 변환
    dates = pd.to_datetime(dates)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, portfolio_values, marker='o', linestyle='-')
    ax.set_title('Portfolio Value Change (Optimized Parameters)')
    ax.set_xlabel('Date')
    ax.set_ylabel('Portfolio Value (KRW)')
    ax.grid(True)
    
    # 날짜 레이블 자동 정렬
    fig.autofmt_xdate()
    return fig