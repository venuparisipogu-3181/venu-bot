option_chain = {}

def update_chain(symbol, data):
    option_chain[symbol] = {
        "ltp": data["ltp"],
        "oi": data["oi"],
        "oi_change": data["oi_change"],
        "volume": data["volume"]
    }
