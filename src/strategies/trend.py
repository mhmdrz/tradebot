def calculate_swing_trend(data):
    first = data.iloc[-1]
    second = data.iloc[-2]
    third = data.iloc[-3]

    if first['high'] > second['high'] > third['high'] and first['low'] > second['low'] > third['low']:
        data['trend'] = 'uptrend'
    elif first['high'] < second['high'] < third['high'] and first['low'] < second['low'] < third['low']:
        data['trend'] = 'downtrend'
    else:
        data['trend'] = 'range'
    
    return data

def calculate_ema(data, period):
    data['ema'] = data['close'].ewm(period, adjust=False).mean()
    return data

def calculate_g(data, length):
    a = [0] * len(data)
    b = [0] * len(data)
    for i in range(1, len(data)):
        a[i] = max(data['close'][i], a[i-1]) - (a[i-1] - b[i-1]) / length
        b[i] = min(data['close'][i], b[i-1]) + (a[i-1] - b[i-1]) / length
    
    data['a'] = a
    data['b'] = b
    data['g_avg'] = (data['a'] + data['b']) / 2

    data['crossup'] = (data['b'].shift(1) < data['close'].shift(1)) & (data['b'] > data['close'])
    data['crossdn'] = (data['a'].shift(1) < data['close'].shift(1)) & (data['a'] > data['close'])
    data['barssince_crossup'] = (data['crossup'][::-1].cumsum() == 0).astype(int).cumsum()
    data['barssince_crossdn'] = (data['crossdn'][::-1].cumsum() == 0).astype(int).cumsum()
    data['bullish'] = data['barssince_crossdn'] > data['barssince_crossup']

    return data