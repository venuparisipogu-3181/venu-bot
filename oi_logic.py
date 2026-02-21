# oi_logic.py - FIXED column names!
import pandas as pd
import numpy as np

STRONG_THRESHOLD = 2000000
REV_THRESHOLD = 1500000

def calculate_oi_change(current, previous):
    return current - previous

def tag_strength(diff):
    if diff > STRONG_THRESHOLD:
        return "Strong Resistance"
    elif diff < -STRONG_THRESHOLD:
        return "Strong Support"
    else:
        return "Neutral"

def calculate_pcr(total_call, total_put):
    if total_call == 0:
        return 0
    return round(total_put / abs(total_call), 2)

def three_strike_analysis(df):
    # FIXED: Column names match app.py output
    if len(df) < 3:
        return pd.DataFrame()
    
    results = []
    for i in range(len(df)-2):
        # Use exact column names from app.py
        call_sum = df.iloc[i:i+3]["Call OI Δ"].sum()
        put_sum = df.iloc[i:i+3]["Put OI Δ"].sum()
        diff = call_sum - put_sum
        
        change_pct = 0
        if abs(call_sum + put_sum) > 0:
            change_pct = round((diff / abs(call_sum + put_sum))*100, 2)
        
        signal = "Reversal Zone" if abs(diff) > REV_THRESHOLD else "-"
        
        results.append({
            "Strike Range": f"{df.iloc[i]['Strike']} - {df.iloc[i+2]['Strike']}",
            "3 Strike Call": call_sum,
            "3 Strike Put": put_sum,
            "Difference": diff,
            "Change %": change_pct,
            "Rev Signal": signal
        })
    return pd.DataFrame(results)
