import MetaTrader5 as mt5
import pandas as pd
from strategies import zscore, trend
from utils import sessions, botlog, utils
import time

class Bot:
    def __init__(self, symbol, timeframe, lot_size, balance_percentage, sl_pips, tp_pips, trailing_pips, rr_ratio):
        self.symbol = symbol
        self.timeframe = timeframe
        self.lot_size = lot_size
        self.balance_percentage = balance_percentage
        self.sl_pips = sl_pips
        self.tp_pips = tp_pips
        self.trailing_pips = trailing_pips
        self.rr_ratio = rr_ratio

        self.is_market_open = sessions.market_time_check()

        if not mt5.initialize():
            print("Initialization failed")
            mt5.shutdown()
        
        print("Initialized...")
    
    def shutdown(self):
        mt5.shutdown()
    
    def get_data(self):
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 100)
        data = pd.DataFrame(rates)
        data['time'] = pd.to_datetime(data['time'], unit='s')
        return data
    
    def calculate_signals(self):
        data = self.get_data()
        data = trend.calculate_swing_trend(data)
        data = zscore.calculate(data, 20, 4)
        latest = data.iloc[-1]
        print(latest)
        botlog.logger.info(latest)
        return latest
    
    def calculate_lot_size(self, balance):
        lot_size = (balance * self.balance_percentage * 0.01) * (self.sl_pips * 0.0001 * 10)
        return round(lot_size, 2)
    
    def manage_trailing(self, order_ticket, order_type):
        while True:
            positions = mt5.positions_get(ticket=order_ticket)
            if not positions:
                print("No open positions found for trailing stop.")
                break

            position = positions[0]
            current_price = mt5.symbol_info_tick(self.symbol).ask if order_type == 'buy' else mt5.symbol_info_tick(self.symbol).bid
            new_sl_price = current_price - self.trailing_pips if order_type == 'buy' else current_price + self.trailing_pips

            if (order_type == 'buy' and new_sl_price > position.sl) or (order_type == 'sell' and new_sl_price < position.sl):
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": position.ticket,
                    "sl": new_sl_price,
                    "tp": position.tp,
                }
                result = mt5.order_send(request)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"Failed to update trailing stop: {result.retcode}")
                else:
                    print(f"Trailing stop updated to: {new_sl_price}")
            
            time.sleep(25)
    
    def place_order(self, order_type, lot_size, price, sl_price, tp_price):
        if order_type == 'buy':
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": lot_size,
                "type": mt5.ORDER_TYPE_BUY,
                "price": price,
                "sl": sl_price,
                "tp": tp_price,
            }
        elif order_type == 'sell':
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": lot_size,
                "type": mt5.ORDER_TYPE_SELL,
                "price": price,
                "sl": sl_price,
                "tp": tp_price,
            }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed: {result.retcode}")
        else:
            print(f"Order placed successfully: {result}")
            order_ticket = result.order
            if self.trailing_pips:
                self.manage_trailing(order_ticket, order_type)
    
    def loop(self):
        while True:
            self.is_market_open = sessions.market_time_check()

            if not self.is_market_open:
                return

            balance = mt5.account_info().balance

            if self.lot_size:
                lot_size = self.lot_size
            else:
                lot_size = self.calculate_lot_size(balance)

            data = self.calculate_signals()
            ask_price = mt5.symbol_info_tick(self.symbol).ask
            bid_price = mt5.symbol_info_tick(self.symbol).bid
            decimal = utils.count_price_decimals(ask_price)
            
            if self.sl_pips and decimal > 2:
                sl_pips = self.sl_pips * 0.0001
            elif self.sl_pips and decimal <= 2:
                sl_pips = self.sl_pips * 0.01

            if self.tp_pips and decimal > 2:
                tp_pips = self.tp_pips * 0.0001
            elif self.tp_pips and decimal <= 2:
                tp_pips = self.tp_pips * 0.01
            
            if data['z_score'] < -2:
                sl_price = ask_price - sl_pips if self.sl_pips else zscore.calculate_dynamic_sl()
                tp_price = ask_price + tp_pips if self.tp_pips else ask_price + (sl_pips * self.rr_ratio)
                self.place_order('buy', lot_size, ask_price, sl_price, tp_price)
            elif data['z_score'] > 2:
                sl_price = bid_price + sl_pips if self.sl_pips else zscore.calculate_dynamic_sl()
                tp_price = bid_price - tp_pips if self.tp_pips else bid_price - (sl_pips * self.rr_ratio)
                self.place_order('sell', lot_size, bid_price, sl_price, tp_price)
            
            time.sleep(60)