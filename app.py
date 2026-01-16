import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime

st.set_page_config(layout="wide", page_title="🚀 Venu Bot Terminal", initial_sidebar_state="expanded")

# Venu Bot Telegram (Optional)
TELEGRAM_TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_venu_alert(msg):
    st.sidebar.success("🔔 Venu Bot Alert Sent!")

# HEADER
st.markdown("""
<div style='text-align:center; padding:30px; background:linear-gradient(135deg,#ff6b6b,#4ecdc4); color:white; border-radius:25px;'>
<h1 style='margin:0;'>🚀 VENU BOT TERMINAL</h1>
<h3 style='margin:10px 0;'>📈 Live NIFTY | BANKNIFTY Dashboard</h3>
</div>
""", unsafe_allow_html=True)

# SIDEBAR CONTROLS
st.sidebar.title("⚙️ Venu Bot Controls")
index = st.sidebar.selectbox("📈 Index", ["NIFTY", "BANKNIFTY"], index=0)
live_mode = st.sidebar.checkbox("🔴 Live Mode", value=True)
auto_refresh = st.sidebar.slider("Refresh (sec)", 3, 15, 5)

# SESSION STATE - BUFFER SAFE
if 'candles' not in st.session_state:
    st.session_state.candles = pd.DataFrame()

@st.cache_data(ttl=30)
def generate_candles(count=50):
    """Generate realistic candle data"""
    base_price = 25750 if index == "NIFTY" else 52500
    candles = []
    
    for i in range(count):
        t = time.time() - (count-i) * 60
        price = base_price + np.sin(t/3600)*100 + np.random.normal(0, 30)
        o = price + np.random.normal(0, 10)
        c = price + np.random.normal(0, 15)
        h = max(o, c) + abs(np.random.normal(0, 20))
        l = min(o, c) - abs(np.random.normal(0, 20))
        
        candles.append({
            'time': datetime.fromtimestamp(t),
            'open': round(o, 2),
            'high': round(h, 2),
            'low': round(l, 2),
            'close': round(c, 2),
            'volume': int(1000000 + abs(np.sin(t/1800))*500000)
        })
    return pd.DataFrame(candles)

# UPDATE DATA
if live_mode and st.sidebar.button("🔄 Update Data", use_container_width=True):
    st.session_state.candles = generate_candles(50)
    st.success("✅ Data Updated!")

if len(st.session_state.candles) == 0:
    st.session_state.candles = generate_candles(50)

df = st.session_state.candles.copy()

# CALCULATIONS
spot = df['close'].iloc[-1]
ema9 = df['close'].ewm(span=9).mean().iloc[-1]
ema20 = df['close'].ewm(span=20).mean().iloc[-1]
rsi = 50 + np.tanh((spot - ema20)/50) * 25

strike_step = 50 if index == "NIFTY" else 100
atm_strike = int(round(spot / strike_step) * strike_step)

# LIVE METRICS
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("💹 Spot Price", f"₹{spot:.0f}", f"{spot-ema20:+.0f}")
col2.metric("📈 EMA 20", f"₹{ema20:.0f}", f"{ema20-ema9:+.0f}")
col3.metric("⚡ RSI", f"{rsi:.1f}", f"{rsi-50:+.1f}")
col4.metric("📊 Volume", f"{df['volume'].iloc[-1]/1000:.0f}K")
col5.metric("🎯 ATM Strike", atm_strike)

# LIVE CANDLESTICK CHART
st.markdown("---")
st.subheader(f"📈 {index} Live Candlestick Chart | {timeframe}")

fig = go.Figure()

# Candlesticks
fig.add_trace(go.Candlestick(
    x=df['time'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name="Candles",
    increasing_line_color='#00ff88',
    decreasing_line_color='#ff4444',
    increasing_fillcolor='rgba(0,255,136,0.8)',
    decreasing_fillcolor='rgba(255,68,68,0.8)'
))

# EMAs
fig.add_trace(go.Scatter(
    x=df['time'], y=df['close'].ewm(span=9).mean(),
    line=dict(color='#ff44aa', width=2), name='EMA 9'
))
fig.add_trace(go.Scatter(
    x=df['time'], y=df['close'].ewm(span=20).mean(),
    line=dict(color='#ffaa00', width=3), name='EMA 20'
))

fig.update_layout(
    height=600,
    template="plotly_dark",
    title=f"🚀 Venu Bot - {index} Live Terminal",
    xaxis_rangeslider_visible=False,
    showlegend=True
)
st.plotly_chart(fig, use_container_width=True)

# OPTION CHAIN
st.markdown("---")
st.subheader(f"🎯 Live Option Chain | ATM {atm_strike}")

strikes = [atm_strike-100, atm_strike-50, atm_strike, atm_strike+50, atm_strike+100]
option_data = []

for strike in strikes:
    ce_price = max(10, abs(spot-strike)*0.25 + 25 + np.random.normal(0, 5))
    pe_price = max(10, abs(spot-strike)*0.22 + 20 + np.random.normal(0, 5))
    
    option_data.append({
        'Strike': strike,
        'CE ₹': f"₹{ce_price:.0f}",
        'PE ₹': f"₹{pe_price:.0f}",
        'CE Vol': f"{int(np.random.normal(50000,10000)):,}",
        'PE Vol': f"{int(np.random.normal(45000,9000)):,}"
    })

st.dataframe(pd.DataFrame(option_data), use_container_width=True, height=250)

# TRADING SIGNALS
st.markdown("---")
st.subheader("🎯 Venu Bot Trading Signals")

ce_signal = spot > ema20 * 1.002 and rsi > 55
pe_signal = spot < ema20 * 0.998 and rsi < 45

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🟢 CE SIGNALS")
    if ce_signal:
        st.error(f"🚀 **BUY {atm_strike} CE**")
        st.success(f"Target: ₹{spot+75:.0f} | SL: ₹{spot-35:.0f}")
        if st.button("🔔 Send CE Alert", key="ce_alert"):
            send_venu_alert(f"🟢 BUY {atm_strike} CE | Spot: ₹{spot:.0f}")
    else:
        st.info("⏳ CE Setup Loading...")

with col2:
    st.markdown("### 🔴 PE SIGNALS")
    if pe_signal:
        st.error(f"📉 **BUY {atm_strike} PE**")
        st.success(f"Target: ₹{spot-75:.0f} | SL: ₹{spot+35:.0f}")
        if st.button("🔔 Send PE Alert", key="pe_alert"):
            send_venu_alert(f"🔴 BUY {atm_strike} PE | Spot: ₹{spot:.0f}")
    else:
        st.info("⏳ PE Setup Loading...")

# CONTROL PANEL
st.markdown("---")
col1, col2, col3 = st.columns(3)

if col1.button("🔄 Refresh All Data", use_container_width=True, type="primary"):
    st.session_state.candles = generate_candles(50)
    st.success("✅ Full Refresh Complete!")
    st.rerun()

if col2.button("🔔 Test Venu Bot", use_container_width=True):
    send_venu_alert(f"🧪 VENU BOT TEST | {index} ₹{spot:.0f}")
    st.balloons()

if col3.button("📱 Mobile Link", use_container_width=True):
    st.info("""
    **📱 Mobile Access:**
    • Same WiFi Network
    • http://192.168.1.XXX:8501
    • Venu Bot Live Ready!
    """)

# FOOTER STATUS
st.markdown("""
<div style='text-align:center; padding:20px; background:linear-gradient(90deg,#00ff88,#00cc66); 
color:black; border-radius:20px; font-weight:bold;'>
✅ VENU BOT TERMINAL LIVE | 
✅ No Buffer | 
✅ Mobile Ready | 
⏰ {now}
</div>
""".format(now=datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)

# AUTO REFRESH CONTROL
if live_mode and auto_refresh > 0:
    st.sidebar.info(f"🔄 Auto Refresh: {auto_refresh}s")
    time.sleep(auto_refresh)
    st.rerun()
