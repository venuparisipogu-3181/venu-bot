import streamlit as st
import pandas as pd
from dhanhq import dhanhq
import time
import requests
from datetime import datetime
import streamlit.components.v1 as components

# --- 1. SETUP & AUTHENTICATION ---
st.set_page_config(layout="wide", page_title="PRO Algo-Assistant", page_icon="🏹")

# Secrets Check
if "DHAN_CLIENT_ID" not in st.secrets:
    st.error("❌ Secrets లో ధన్ వివరాలు (1106476940, eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY5NjE1NzAyLCJpYXQiOjE3Njk1MjkzMDIsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA2NDc2OTQwIn0.MygCo_b-l1khRfC-V8_iYvqbeykHy4upKbdghs8ElQxBegN-wMDKfUwNNDyUH0ZQK8_YYZeQULFICMhoYsxTWA) యాడ్ చేయండి!")
    st.stop()

dhan = dhanhq(st.secrets["DHAN_CLIENT_ID"], st.secrets["DHAN_ACCESS_TOKEN"])

# --- 2. CORE UTILITY FUNCTIONS ---
def send_telegram_alert(msg):
    token = st.secrets.get("TELEGRAM_BOT_TOKEN")
    chat_id = st.secrets.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

def display_tradingview_chart(symbol_name):
    tradingview_html = f"""
    <div style="height:600px; width:100%;">
      <div id="tv_chart_main" style="height:600px;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true, "symbol": "{symbol_name}", "interval": "5",
        "timezone": "Asia/Kolkata", "theme": "dark", "style": "1",
        "locale": "in", "toolbar_bg": "#f1f3f6", "enable_publishing": false,
        "withdateranges": true, "hide_side_toolbar": false,
        "allow_symbol_change": true, "details": true, "container_id": "tv_chart_main"
      }});
      </script>
    </div>
    """
    components.html(tradingview_html, height=620)

@st.cache_data(ttl=60)
def get_option_chain_data(index_name):
    idx_map = {"NIFTY": 13, "BANKNIFTY": 25, "FINNIFTY": 27, "SENSEX": 51}
    u_id = idx_map.get(index_name, 13)
    inst_type = "IDX_I" if index_name != "SENSEX" else "BSE_INDICES"
    
    try:
        exp_resp = dhan.expiry_list(u_id, inst_type)
        if exp_resp['status'] != 'success': return None, None
        latest_expiry = exp_resp['data'][0]
        oc_resp = dhan.option_chain(u_id, inst_type, latest_expiry)
        
        if oc_resp['status'] == 'success':
            data_list = []
            for strike, val in oc_resp['data']['oc'].items():
                data_list.append({
                    "Strike": float(strike),
                    "CE_ID": val['ce']['security_id'],
                    "CE_LTP": val['ce']['last_price'],
                    "CE_OI_CHG": val['ce'].get('oi_abs_change', 0),
                    "PE_ID": val['pe']['security_id'],
                    "PE_LTP": val['pe']['last_price'],
                    "PE_OI_CHG": val['pe'].get('oi_abs_change', 0)
                })
            return pd.DataFrame(data_list).sort_values("Strike"), latest_expiry
    except: return None, None
    return None, None

# --- 3. SESSION STATE MANAGEMENT ---
if 'monitor_on' not in st.session_state: st.session_state.monitor_on = False
if 'chart_history' not in st.session_state: st.session_state.chart_history = pd.DataFrame(columns=['Time', 'Price'])
if 'entry_price' not in st.session_state: st.session_state.entry_price = 0

# --- 4. DASHBOARD UI ---
st.title("🏹 Venu's Smart Algo-Terminal")

# Sidebar
idx = st.sidebar.selectbox("ఇండెక్స్ సెలెక్ట్ చేయండి", ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX"])
side = st.sidebar.radio("ట్రేడ్ వైపు", ["CE", "PE"])
chart_sym_map = {"NIFTY": "NSE:NIFTY", "BANKNIFTY": "NSE:BANKNIFTY", "FINNIFTY": "NSE:FINNIFTY", "SENSEX": "BSE:SENSEX"}

# --- 5. SMART MONITORING MODE ---
if st.session_state.monitor_on:
    resp = dhan.get_ltp_data(securities={"NSE_FNO": [st.session_state.active_id]})
    
    if resp['status'] == 'success':
        tick = resp['data'][str(st.session_state.active_id)]
        ltp, oi_chg = tick['last_price'], tick.get('oi_abs_change', 0)
        
        if st.session_state.entry_price == 0: 
            st.session_state.entry_price = ltp
            st.session_state.current_sl = ltp - 15
            send_telegram_alert(f"🚀 Trade Started!\nStrike: {st.session_state.active_strike}\nEntry: {ltp}")

        pnl = ltp - st.session_state.entry_price
        
        # --- YOUR SMART LOGIC ---
        signal = "HOLD"
        sig_color = "#333"
        if pnl > 0 and oi_chg < -5000:
            signal = "STRONG BUY / HOLD (Short Covering) 🔥"
            sig_color = "#2ecc71"
        elif pnl < -10:
            signal = "EXIT / CAUTION 🛑"
            sig_color = "#e74c3c"

        # Display Metrics
        st.markdown(f"<div style='background-color:{sig_color}; padding:10px; border-radius:10px; text-align:center;'><h2>{signal}</h2></div>", unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Live Price", f"₹{ltp}", f"{pnl:+.2f}")
        m2.metric("OI Change", f"{oi_chg:+}")
        m3.metric("Trailing SL", f"₹{st.session_state.current_sl:.2f}")

        # Trailing SL Update
        if ltp - 15 > st.session_state.current_sl:
            st.session_state.current_sl = ltp - 15
            st.toast("SL Trailed Up! 🛡️")

        if st.button("⏹️ STOP MONITORING"):
            st.session_state.monitor_on = False
            st.rerun()

# --- 6. SELECTION MODE (OPTION CHAIN) ---
else:
    oc_df, expiry_date = get_option_chain_data(idx)
    if oc_df is not None:
        st.subheader(f"📊 {idx} Option Chain (Expiry: {expiry_date})")
        # Highlighted Dataframe
        st.dataframe(oc_df[['CE_OI_CHG', 'CE_LTP', 'Strike', 'PE_LTP', 'PE_OI_CHG']].style.background_gradient(subset=['CE_OI_CHG', 'PE_OI_CHG'], cmap='RdYlGn'), use_container_width=True, hide_index=True)
        
        selected_strike = st.selectbox("మానిటర్ చేయాల్సిన స్ట్రైక్ ఎంచుకోండి", oc_df['Strike'].unique())
        if st.button("🚀 START SMART ASSISTANT"):
            row = oc_df[oc_df['Strike'] == selected_strike].iloc[0]
            st.session_state.monitor_on = True
            st.session_state.active_id = row[f'{side}_ID']
            st.session_state.active_strike = f"{selected_strike} {side}"
            st.session_state.entry_price = 0
            st.rerun()

st.divider()

# --- 7. ADVANCED LIVE CHART ---
st.subheader(f"📈 {idx} Live Advanced Analysis")
display_tradingview_chart(chart_sym_map.get(idx, "NSE:NIFTY"))

# Auto-refresh loop
if st.session_state.monitor_on:
    time.sleep(2)
    st.rerun()
