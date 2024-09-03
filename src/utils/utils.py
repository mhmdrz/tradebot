def count_price_decimals(price):
    number = str(price)

    if '.' in number:
        decimal_part = number.split('.')[1]
        return len(decimal_part)
    else:
        return 0