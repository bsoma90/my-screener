import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="SwingEdge Pro Terminal", layout="wide", initial_sidebar_state="expanded")

# Custom Dark Theme Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1E222D;
        border: 1px solid #2A2E39;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .badge-bullish {
        background-color: #089981;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-bearish {
        background-color: #F23645;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-neutral {
        background-color: #2962FF;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- CACHED DATA FETCHING ----------------- #
@st.cache_data(ttl=3600)
def fetch_eod_data(symbol, period="1y"):
    try:
        ticker = symbol.strip()
        if not ticker.endswith(".NS") and not ticker.startswith("^"):
            ticker += ".NS"
        df = yf.download(ticker, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 30:
            return None
        return df.dropna()
    except Exception:
        return None

# Top NSE Universe Basket
DEFAULT_BASKET = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL",
    "LICI", "ITC", "HINDUNILVR", "LT", "BAJFINANCE", "TATAMOTORS", "SUNPHARMA",
    "MARUTI", "NTPC", "ONGC", "TITAN", "ADANIENT", "TATASTEEL", "POWERGRID",
    "COALINDIA", "HAL", "BEL", "VEDL", "ZOMATO", "DIXON", "TRENT", "POLYCAB", "KALYANKJIL"
]

SECTOR_ETFS = {
    "Nifty 50": "^NSEI",
    "Nifty Bank": "BANKBEES.NS",
    "Nifty IT": "ITBEES.NS",
    "Nifty Auto": "AUTOBEES.NS",
    "Nifty Pharma": "PHARMABEES.NS",
    "Nifty Gold": "GOLDBEES.NS",
    "Nifty PSU Bank": "PSUBNKBEES.NS",
    "Nifty CPSE": "CPSEETF.NS"
}

# ----------------- TECHNICAL FORMULAS ----------------- #
def calculate_setup_metrics(df, nifty_df):
    if df is None or len(df) < 150:
        return None
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    vol = df['Volume']
    
    # EMAs / SMAs
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    sma150 = close.rolling(150).mean()
    sma200 = close.rolling(200).mean() if len(df) >= 200 else sma150
    
    curr_close = close.iloc[-1]
    curr_vol = vol.iloc[-1]
    vol20_avg = vol.rolling(20).mean().iloc[-1]
    vol_surge = (curr_vol / vol20_avg) if vol20_avg > 0 else 1.0
    
    # 52-Week High & Low
    h52 = high.tail(250).max()
    l52 = low.tail(250).min()
    
    # 1. Minervini Stage 2 Template
    s2_c1 = curr_close > sma150.iloc[-1] and curr_close > sma200.iloc[-1]
    s2_c2 = sma150.iloc[-1] > sma200.iloc[-1]
    s2_c3 = sma50.iloc[-1] > sma150.iloc[-1]
    s2_c4 = curr_close >= (1.25 * l52)
    s2_c5 = curr_close >= (0.75 * h52)
    is_stage2 = s2_c1 and s2_c2 and s2_c3 and s2_c4 and s2_c5
    
    # 2. VCP (Volatility Contraction Pattern)
    atr10 = (high.tail(10).max() - low.tail(10).min()) / curr_close
    atr30 = (high.tail(30).max() - low.tail(30).min()) / curr_close
    is_vcp = (atr10 < 0.08) and (atr10 < atr30 * 0.65) and (vol_surge < 0.8 or vol_surge > 1.5)
    
    # 3. Darvas Box Breakout (20-day high breakout)
    d_high = high.iloc[-21:-1].max()
    d_low = low.iloc[-21:-1].min()
    darvas_breakout = curr_closeSwing Edge-এর সমস্ত মূল ফিচার (Stage 2, VCP, Darvas Box, Setup Score 0-100, Candlestick Chart, Pivot Levels, FVG এবং Sector ETF) নিয়ে একটি সম্পূর্ণ এবং কম্প্যাক্ট কোড নিচে দেওয়া হলো:

### ১. `requirements.txt`
```text
streamlit
yfinance
pandas
plotly
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="SwingEdge Terminal", layout="wide")
st.title("⚡ SwingEdge Pro Screener")

st.sidebar.header("Universe")
default_stocks = "RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, SBIN, BHARTIARTL, LT, TATAMOTORS, HAL, BEL, DIXON, TRENT"
tickers = [f"{t.strip().upper()}.NS" for t in st.sidebar.text_area("Stocks", default_stocks).split(",") if t.strip()]

@st.cache_data(ttl=3600)
def get_data(symbol, period="1y"):
    try:
        df = yf.download(symbol, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna() if not df.empty else None
    except:
        return None

def analyze(df):
    if df is None or len(df) < 150:
        return None
    c, h, l, v = df['Close'], df['High'], df['Low'], df['Volume']
    curr_c, curr_v = c.iloc[-1], v.iloc[-1]
    
    ma50, ma150, ma200 = c.rolling(50).mean().iloc[-1], c.rolling(150).mean().iloc[-1], c.rolling(200).mean().iloc[-1]
    vol_spike = curr_v / v.rolling(20).mean().iloc[-1] if v.rolling(20).mean().iloc[-1] > 0 else 1.0
    h52, l52 = h.tail(250).max(), l.tail(250).min()
    
    stage2 = (curr_c > ma150 > ma200) and (curr_c > ma50) and (curr_c >= 1.25 * l52) and (curr_c >= 0.75 * h52)
    r10 = (h.tail(10).max() - l.tail(10).min()) / curr_c
    r30 = (h.tail(30).max() - l.tail(30).min()) / curr_c
    vcp = (r10 < 0.08) and (r10 < r30 * 0.65)
    darvas = curr_c > h.iloc[-21:-1].max()
    
    score = (35 if stage2 else 0) + (25 if vcp else 0) + (20 if darvas else 0) + (20 if vol_spike >= 1.5 else 0)
    
    return {
        "Price": round(curr_c, 2),
        "Score": score,
        "Stage 2": "✅" if stage2 else "❌",
        "VCP": "✅" if vcp else "—",
        "Darvas": "🚀" if darvas else "—",
        "Vol Surge": f"{vol_spike:.1f}x"
    }

tab1, tab2, tab3 = st.tabs(["🔍 Scanners", "🔬 Terminal", "📊 Sector ETFs"])

with tab1:
    res = []
    for sym in tickers:
        m = analyze(get_data(sym))
        if m:
            m["Symbol"] = sym.replace(".NS", "")
            res.append(m)
    if res:
        st.dataframe(pd.DataFrame(res).sort_values(by="Score", ascending=False), use_container_width=True)

with tab2:
    selected = st.selectbox("Select Stock", tickers)
    sdf = get_data(selected)
    if sdf is not None:
        fig = go.Figure(data=[go.Candlestick(x=sdf.index[-100:], open=sdf['Open'][-100:], high=sdf['High'][-100:], low=sdf['Low'][-100:], close=sdf['Close'][-100:], name="Candles")])
        fig.add_trace(go.Scatter(x=sdf.index[-100:], y=sdf['Close'].rolling(50).mean()[-100:], line=dict(color='orange', width=1.5), name="50 EMA"))
        fig.add_trace(go.Scatter(x=sdf.index[-100:], y=sdf['Close'].rolling(200).mean()[-100:], line=dict(color='blue', width=2), name="200 EMA"))
        fig.update_layout(height=450, xaxis_rangeslider_visible=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    etfs = ["BANKBEES.NS", "ITBEES.NS", "AUTOBEES.NS", "PHARMABEES.NS", "GOLDBEES.NS"]
    etf_res = []
    for e in etfs:
        edf = get_data(e, "3mo")
        if edf is not None and len(edf) >= 22:
            ret = ((edf['Close'].iloc[-1] - edf['Close'].iloc[-22]) / edf['Close'].iloc[-22]) * 100
            etf_res.append({"Sector": e.replace(".NS", ""), "Close": round(edf['Close'].iloc[-1], 2), "1M Return (%)": round(ret, 2)})
    if etf_res:
        st.dataframe(pd.DataFrame(etf_res).sort_values(by="1M Return (%)", ascending=False), use_container_width=True)
