def calculate_pcr(chain):
    put_oi = sum(v["oi"] for k,v in chain.items() if k.endswith("PE"))
    call_oi = sum(v["oi"] for k,v in chain.items() if k.endswith("CE"))

    return round(put_oi / call_oi, 2) if call_oi else 0
