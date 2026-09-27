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
