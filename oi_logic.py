# oi_logic.py - Your original (perfect)
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
    results = []
    for i in range(len(df)-2):
        call_sum = df.iloc[i:i+3]["Call OI Change"].sum()
        put_sum = df.iloc[i:i+3]["Put OI Change"].sum()
        diff = call_sum - put_sum
        change_pct = 0
        if abs(call_sum + put_sum) > 0:
            change_pct = round((diff / abs(call_sum + put_sum))*100, 2)
        if abs(diff) > REV_THRESHOLD:
            signal = "Reversal Zone"
        else:
            signal = "-"
        results.append({
            "Strike Range": f"{df.iloc[i]['Strike']} - {df.iloc[i+2]['Strike']}",
            "3 Strike Call Change": call_sum,
            "3 Strike Put Change": put_sum,
            "Difference": diff,
            "Change % Difference": change_pct,
            "Rev Signal": signal
        })
    return pd.DataFrame(results)
