import numpy as np

def calculate(data, mean_window, std_window):
    mean = data['close'].rolling(window=mean_window).mean()
    std = data['close'].rolling(window=std_window).std()
    data['z_score'] = (data['close'] - mean) / std
    return data

def calculate_with_atr(data, mean_window, std_window, atr_window):
    mean = data['close'].rolling(window=mean_window).mean()
    std = data['close'].rolling(window=std_window).std()
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_range = np.maximum(high_low, high_close, low_close)
    atr = true_range.rolling(window=atr_window).mean()
    data['z_score'] = (data['close'] - mean) / (std * atr)
    
    return data