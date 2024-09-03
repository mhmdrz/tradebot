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