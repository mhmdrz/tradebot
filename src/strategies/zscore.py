def calculate(data, mean_window, std_window):
    mean = data['close'].rolling(window=mean_window).mean()
    std = data['close'].rolling(window=std_window).std()
    data['z_score'] = (data['close'] - mean) / std
    return data