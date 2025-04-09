from datetime import datetime, timezone

# Checks only London and New-York time in UTC
def market_time_check():
    time = datetime.now(timezone.utc)
    
    return True if time.hour >= 7 and time.hour < 21 else False