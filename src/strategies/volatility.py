def calculate_atr(data, atr_window):
    previous_close = data['close'].shift(1)
    data['tr1'] = data['high'] - data['low']
    data['tr2'] = abs(data['high'] - previous_close)
    data['tr3'] = abs(data['low'] - previous_close)
    data['true_range'] = data[['tr1', 'tr2', 'tr3']].max(axis=1)
    data['atr'] = data['true_range'].rolling(window=atr_window).mean()
    return data