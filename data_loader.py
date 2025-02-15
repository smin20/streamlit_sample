# data_loader.py
import datetime
import pandas as pd
import streamlit as st
from pykrx import stock

@st.cache_data
def load_ticker_info():
    """ KOSPI, KOSDAQ 전체 티커와 이름 정보를 가져옵니다. """
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

@st.cache_data
def load_etf_ticker_info():
    """ ETF 전체 티커와 이름 정보를 가져옵니다. """
    tickers = stock.get_etf_ticker_list()
    ticker_dict = {}
    for t in tickers:
        try:
            ticker_dict[t] = stock.get_etf_ticker_name(t)
        except Exception:
            ticker_dict[t] = "Unknown"
    return ticker_dict

@st.cache_data(show_spinner=False)
def get_market_cap(ticker, date_str):
    """
    지정한 날짜(date_str: 'YYYYMMDD') 기준으로 해당 종목의 시가총액을 반환합니다.
    (ETF에는 적용되지 않습니다.)
    """
    try:
        df_cap = stock.get_market_cap_by_date(date_str, date_str, ticker)
        if df_cap.empty:
            return 0
        return df_cap['시가총액'].iloc[0]
    except Exception:
        return 0

def load_market_data(instrument_type, target_ticker, start_date, end_date):
    """
    종목 또는 ETF의 OHLCV 데이터를 지정한 기간 동안 불러옵니다.
    """
    if instrument_type == "주식":
        df = stock.get_market_ohlcv_by_date(start_date, end_date, target_ticker)
    else:
        df = stock.get_etf_ohlcv_by_date(start_date, end_date, target_ticker)
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    return df
