from datetime import datetime, timezone
import asyncio

# Checks only London and New-York time in UTC
def market_time_check():
    time = datetime.now(timezone.utc)

    if time.hour >= 7 and time.hour < 21:
        return True
    else:
        return False

async def check_async():
    while True:
        await asyncio.sleep(24)
        market_time_check()
