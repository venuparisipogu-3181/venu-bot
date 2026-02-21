import streamlit as st
import pandas as pd
import numpy as np
import time
from dhan_client import DhanLiveFeed
from oi_logic import *

st.set_page_config(layout="wide")
st.title("🚀 NIFTY LIVE OI DASHBOARD")
st.caption("venu-bot | Feb 21, 2026 | ATM ±5 | PCR Analysis")

TOKENS = [257501, 257502, 258001, 258002, 258501, 258502]

if 'feed' not in st.session_state:
    st.session_state.feed = DhanLiveFeed("demo", "demo", TOKENS)
    st.session_state.feed.start()
    st.session_state.previous_oi = {}

feed = st.session_state.feed

if len(feed.data_store) > 0:
    rows, total_call, total_put = [], 0, 0
    
    for token, data in feed.data_store.items():
        strike = token // 100
        current_oi = data["oi"]
        
        if token not in st.session_state.previous_oi:
            st.session_state.previous_oi[token] = current_oi
        
        oi_change = current_oi - st.session_state.previous_oi[token]
        st.session_state.previous_oi[token] = current_oi
        
        is_call = token % 2 == 1
        change = oi_change if is_call else -oi_change
        
        total_call += change if is_call else 0
        total_put += abs(change) if not is_call else 0
        
        diff = total_call - total_put
        strength = tag_strength(diff)
        
        rows.append({
            "Strike": strike,
            "Call OI Δ": change if is_call else 0,
            "Put OI Δ": abs(change) if not is_call else 0,
            "Difference": diff,
            "Strength": strength
        })
    
    df = pd.DataFrame(rows)
    pcr = calculate_pcr(total_call, total_put)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📈 Call Total", f"{total_call:,.0f}")
    col2.metric("📉 Put Total", f"{total_put:,.0f}")
    col3.metric("🎯 PCR", pcr)
    
    st.subheader("🔥 Strike Wise Analysis")
    st.dataframe(df, use_container_width=True)
    
    st.subheader("🎯 3-Strike Reversal")
    if len(df) >= 3:
        three_df = three_strike_analysis(df)
        st.dataframe(three_df)
    
    st.success("🟢 LIVE! 3s refresh | Monday market ready")
else:
    st.info("🔄 5 seconds... initializing")

time.sleep(3)
st.rerun()
