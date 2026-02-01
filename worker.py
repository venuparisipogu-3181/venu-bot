from py_vollib.black_scholes import black_scholes as bs
from py_vollib.black_scholes.greeks.analytical import delta

def get_delta(flag, spot, strike, t, r, iv):
    return delta(flag, spot, strike, t, r, iv)
