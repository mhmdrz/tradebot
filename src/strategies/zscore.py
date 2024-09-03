import numpy as np

def calculate(data, mean_window, std_window):
    mean = data['close'].rolling(window=mean_window).mean()
    std = data['close'].rolling(window=std_window).std()
    data['z_score'] = (data['close'] - mean) / std
    return data

def calculate_dynamic_sl(data, current_price, z_score_threshold, window):
    z_score = data['z_score'].iloc[-1]
    prices = data['close']

    if z_score > z_score_threshold:
        sl_price = current_price - (0.5 * np.std(prices[-window:]))
    elif z_score < -z_score_threshold:
        sl_price = current_price + (0.5 * np.std(prices[-window:]))
    else:
        sl_price = current_price - (1.0 * np.std(prices[-window:]))

    return sl_price