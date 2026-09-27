import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="My Swing & Technical Screener", layout="wide")

st.title("📈 Indian Stock Market - Swing & Technical Screener")
st.caption("Custom-built End-of-Day Technical Screener for NSE Equities")

# Sidebar - Settings
st.sidebar.header("User Settings")
benchmark_ticker = "^NSEI" # Nifty 50

# Default Watchlist
default_symbols = "TCS.NS, INFY.NS, RELIANCE.NS, HDFCBANK.NS, ICICIBANK.NS, LT.NS, TATAMOTORS.NS, SBIN.NS, BHARTIARTL.NS, HAL.NS"
user_symbols = st.sidebar.text_area("NSE Tickers (Comma separated, with .NS)", default_symbols)
tickers = [t.strip() for t in user_symbols.split(",") if t.strip()]

@st.cache_data(ttl=3600)
def fetch_stock_data(symbol, period="1y"):
    try:
        df = yf.download(symbol, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return None

# Nifty 50 Benchmark data for Relative Strength
nifty_df = fetch_stock_data(benchmark_ticker, "1y")

def calculate_technical_metrics(df, bench_df):
    if df is None or len(df) < 200:
        return None
    
    close = df['Close']
    volume = df['Volume']
    
    # Moving Averages
    df['SMA_20'] = close.rolling(20).mean()
    df['SMA_50'] = close.rolling(50).mean()
    df['SMA_150'] = close.rolling(150).mean()
    df['SMA_200'] = close.rolling(200).mean()
    
    # 52 Week High/Low
    high_52 = close.tail(250).max()
    low_52 = close.tail(250).min()
    current_close = close.iloc[-1]
    
    # Stage 2 Minervini Criteria
    c1 = current_close > df['SMA_150'].iloc[-1] and current_close > df['SMA_200'].iloc[-1]
    c2 = df['SMA_150'].iloc[-1] > df['SMA_200'].iloc[-1]
    c3 = df['SMA_50'].iloc[-1] > df['SMA_150'].iloc[-1] and df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1]
    c4 = current_close > df['SMA_50'].iloc[-1]
    c5 = current_close >= (1.25 * low_52) # 25% above 52-week low
    c6 = current_close >= (0.75 * high_52) # within 25% of 52-week high
    is_stage_2 = c1 and c2 and c3 and c4 and c5 and c6
    
    # Volume Spurt
    avg_vol_20 = volume.rolling(20).mean().iloc[-1]
    curr_vol = volume.iloc[-1]
    vol_multiple = curr_vol / avg_vol_20 if avg_vol_20 > 0 else 0
    
    # Relative Strength vs Nifty 50 (1-Month Return vs Nifty 1-Month Return)
    stock_1m_ret = ((close.iloc[-1] - close.iloc[-22]) / close.iloc[-22]) * 100 if len(close) >= 22 else 0
    if bench_df is not None and len(bench_df) >= 22:
        nifty_1m_ret = ((bench_df['Close'].iloc[-1] - bench_df['Close'].iloc[-22]) / bench_df['Close'].iloc[-22]) * 100
        rs_score = stock_1m_ret - nifty_1m_ret
    else:
        rs_score = 0
        
    # Darvas Box Range (20-day high vs low)
    box_high = close.tail(20).max()
    box_low = close.tail(20).min()
    box_breakout = current_close >= box_high
    
    return {
        "Close": round(current_close, 2),
        "Stage 2 Trend": "✅ Pass" if is_stage_2 else "❌ Fail",
        "Volume Spike (x)": round(vol_multiple, 2),
        "1M Outperformance vs Nifty (%)": round(rs_score, 2),
        "Darvas 20D High": round(box_high, 2),
        "Darvas 20D Low": round(box_low, 2),
        "Darvas Breakout": "🚀 Breakout" if box_breakout else "In Range",
        "52W High": round(high_52, 2),
        "52W Low": round(low_52, 2)
    }

# Tab Layout
tab1, tab2 = st.tabs(["📊 Multi-Stock Screener", "🔍 Single Stock Deep Dive"])

with tab1:
    st.subheader("Automated Screener Results")
    results = []
    for sym in tickers:
        df = fetch_stock_data(sym, "1y")
        metrics = calculate_technical_metrics(df, nifty_df)
        if metrics:
            metrics["Symbol"] = sym.replace(".NS", "")
            results.append(metrics)
            
    if results:
        res_df = pd.DataFrame(results)
        cols = ["Symbol", "Close", "Stage 2 Trend", "Volume Spike (x)", "1M Outperformance vs Nifty (%)", "Darvas Breakout", "52W High", "52W Low"]
        st.dataframe(res_df[cols], use_container_width=True)
    else:
        st.warning("No data retrieved. Please check ticker symbols.")

with tab2:
    st.subheader("Stock Deep Dive & Interactive Chart")
    selected_sym = st.selectbox("Select Stock for Chart Analysis", tickers)
    s_df = fetch_stock_data(selected_sym, "1y")
    
    if s_df is not None:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=s_df.index,
            open=s_df['Open'],
            high=s_df['High'],
            low=s_df['Low'],
            close=s_df['Close'],
            name="Price"
        ))
        
        # Add EMAs
        fig.add_trace(go.Scatter(x=s_df.index, y=s_df['Close'].rolling(50).mean(), mode='lines', line=dict(color='orange', width=1.5), name='50 SMA'))
        fig.add_trace(go.Scatter(x=s_df.index, y=s_df['Close'].rolling(200).mean(), mode='lines', line=dict(color='blue', width=2), name='200 SMA'))
        
        fig.update_layout(title=f"{selected_sym} Technical Chart", yaxis_title="Price (INR)", xaxis_rangeslider_visible=False, height=550)
        st.plotly_chart(fig, use_container_width=True)
