from bot import Bot
import MetaTrader5 as mt5

if __name__ == "__main__":
    bot = Bot(
        symbol="GBPUSD_o",
        timeframe=mt5.TIMEFRAME_M1,
        balance_percentage=5,
        sl_pips=None,
        tp_pips=None,
        trailing_pips=None,
        lot_size=0.1,
        rr_ratio=2
    )
    try:
        bot.bot_loop()
    except KeyboardInterrupt:
        bot.shutdown()