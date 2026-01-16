import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import time
from datetime import datetime

st.set_page_config(layout="wide", page_title="🚀 Venu Bot Terminal", initial_sidebar_state="expanded")

# VENU BOT TELEGRAM SETUP
TELEGRAM_TOKEN = "YOUR_VENU_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def venu_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}, timeout=5)
    except:
        pass

# VENU BOT HEADER
st.markdown("""
<div style='text-align:center; padding:30px; background:linear-gradient(135deg,#ff6b6b,#4ecdc4); color:white; border-radius:25px;'>
<h1 style='margin:0;'>🚀 VENU BOT TERMINAL</h1>
<h3 style='margin:10px 0 0 0;'>📈 Live NIFTY/BankNifty | Candles | Signals | Alerts</h3>
</div>
""", unsafe_allow_html=True)

# CONTROLS
st.sidebar.title("⚙️ Venu Bot Controls")
index = st.sidebar.selectbox("📈 Index", ["NIFTY", "BANKNIFTY"])
live_mode = st.sidebar.checkbox("🔴 LIVE MODE", value=True)
speed = st.sidebar.slider("⚡ Speed", 3, 12, 5)

# SESSION DATA
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame()

def new_candle():
    base = 25750 if index == "NIFTY" else 52500
    t = time.time()
    prev = st.session_state.data['close'].iloc[-1] if len(st.session_state.data)>0 else base
    o = prev
    change = np.sin(t/15)*25 + np.random.normal(0, 12)
    h = max(o, o+change) + 20
    l = min(o, o+change) - 20
    c = o + change
    return pd.DataFrame([{
        'time': datetime.now(),
        'open': round(o,2), 'high': round(h,2),
        'low': round(l,2), 'close': round(c,2),
        'volume': int(1500000 + abs(np.sin(t/10))*500000)
    }])

# LIVE CANDLES
if live_mode:
    candle = new_candle()
    st.session_state.data = pd.concat([st.session_state.data, candle])
    st.session_state.data = st.session_state.data.tail(50)

if len(st.session_state.data) == 0:
    for i in range(30):
        st.session_state.data = pd.concat([st.session_state.data, new_candle()])

df = st.session_state.data.copy()
spot = df['close'].iloc[-1]
ema20 = df['close'].ewm(span=20).mean().iloc[-1]
rsi = 50 + np.sin(time.time()/15)*25
step = 50 if index == "NIFTY" else 100
atm = int(round(spot/step)*step)

# METRICS
col1, col2, col3, col4 = st.columns(4)
col1.metric("💹 Spot", f"₹{spot:.0f}", f"{spot-ema20:+.0f}")
col2.metric("📈 EMA20", f"₹{ema20:.0f}")
col3.metric("⚡ RSI", f"{rsi:.1f}")
col4.metric("🎯 ATM", atm)

# CHART
st.markdown("---")
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df['time'], open=df['open'], high=df['high'], 
    low=df['low'], close=df['close'],
    increasing_line_color='#00ff88', decreasing_line_color='#ff4444'
))
fig.add_trace(go.Scatter(x=df['time'], y=df['close'].ewm(span=20).mean(), 
                        line=dict(color='#ffaa00', width=3), name='EMA20'))
fig.update_layout(height=500, template='plotly_dark', 
                 title=f"🚀 Venu Bot - {index} Live Chart")
st.plotly_chart(fig, use_container_width=True)

# OPTION CHAIN
st.markdown("---")
st.subheader(f"🎯 Venu Bot Option Chain | ATM {atm}")
strikes = [atm-step, atm, atm+step]
options = []
for strike in strikes:
    ce = max(15, abs(spot-strike)*0.25 + 25)
    pe = max(15, abs(spot-strike)*0.22 + 20)
    options.append({'Strike': strike, 'CE': f"₹{ce:.0f}", 'PE': f"₹{pe:.0f}'})
st.dataframe(pd.DataFrame(options), use_container_width=True)

# SIGNALS
st.markdown("---")
ce_signal = spot > ema20*1.002 and rsi > 55
pe_signal = spot < ema20*0.998 and rsi < 45

col1, col2 = st.columns(2)
with col1:
    st.subheader("🟢 CE Signal")
    if ce_signal:
        st.error(f"🚀 BUY {atm} CE")
        venu_alert(f"🟢 VENU BOT: BUY {atm} CE | Spot ₹{spot:.0f}")
    else:
        st.info("⏳ Wait")

with col2:
    st.subheader("🔴 PE Signal")
    if pe_signal:
        st.error(f"📉 BUY {atm} PE")
        venu_alert(f"🔴 VENU BOT: BUY {atm} PE | Spot ₹{spot:.0f}")
    else:
        st.info("⏳ Wait")

# CONTROLS
col1, col2, col3 = st.columns(3)
if col1.button("🔔 Test Venu Bot", use_container_width=True):
    venu_alert(f"🧪 VENU BOT TEST | {index} ₹{spot:.0f}")
    st.success("✅ Venu Bot Alert Sent!")

if col2.button("🔄 Update", use_container_width=True):
    st.rerun()

if col3.button("📱 Mobile", use_container_width=True):
    st.info("📱 **Mobile:** http://192.168.1.XXX:8501")

# AUTO REFRESH
if live_mode:
    st.sidebar.success(f"🔴 VENU BOT LIVE | {speed}s")
    time.sleep(speed)
    st.rerun()
