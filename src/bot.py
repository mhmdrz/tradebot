import MetaTrader5 as mt5
import pandas as pd
from strategies import zscore, trend, volatility
from utils import sessions, botlog, utils, crawler
import numpy as np
import time
from datetime import datetime, timedelta

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
            print('Initialization failed')
            mt5.shutdown()
        
        print('Initialized...')
    
    def shutdown(self):
        mt5.shutdown()
    
    def get_data(self):
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 100)
        data = pd.DataFrame(rates)
        data['time'] = pd.to_datetime(data['time'], unit='s')
        return data
    
    def calculate_signals(self):
        data = self.get_data()
        data = volatility.calculate_atr(data, 14)
        data = trend.calculate_ema(data, 200)
        data = trend.calculate_g(data, 20)

        return data
    
    def calculate_lot_size(self, balance):
        lot_size = (balance * self.balance_percentage * 0.01) * (self.sl_pips * 0.0001 * 10)
        return round(lot_size, 2)
    
    def calculate_dynamic_sl(self, latest, multiplier, type):
        if type == 'buy':
            stoploss = latest['close'] - (latest['atr'] * multiplier)
        elif type == 'sell':
            stoploss = latest['close'] + (latest['atr'] * multiplier)
        else:
            print("Error setting atr based stop loss!")
        
        return stoploss
    
    def manage_trailing(self, order_ticket, order_type):
        while True:
            positions = mt5.positions_get(ticket=order_ticket)
            if not positions:
                print('No open positions found for trailing stop.')
                break

            position = positions[0]
            current_price = mt5.symbol_info_tick(self.symbol).ask if order_type == 'buy' else mt5.symbol_info_tick(self.symbol).bid
            new_sl_price = current_price - self.trailing_pips if order_type == 'buy' else current_price + self.trailing_pips

            if (order_type == 'buy' and new_sl_price > position.sl) or (order_type == 'sell' and new_sl_price < position.sl):
                request = {
                    'action': mt5.TRADE_ACTION_SLTP,
                    'position': position.ticket,
                    'sl': new_sl_price,
                    'tp': position.tp,
                }
                result = mt5.order_send(request)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f'Failed to update trailing stop: {result.retcode}')
                    botlog.logger.info(f'Failed to update trailing stop: {result.retcode}')
                else:
                    print(f'Trailing stop updated to: {new_sl_price}')
                    botlog.logger.info(f'Trailing stop updated to: {new_sl_price}')
            
            time.sleep(25)
    
    def place_order(self, order_type, lot_size, price, sl_price, tp_price):
        if order_type == 'buy':
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': self.symbol,
                'volume': lot_size,
                'type': mt5.ORDER_TYPE_BUY,
                'price': price,
                'sl': sl_price,
                'tp': tp_price,
            }
        elif order_type == 'sell':
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': self.symbol,
                'volume': lot_size,
                'type': mt5.ORDER_TYPE_SELL,
                'price': price,
                'sl': sl_price,
                'tp': tp_price,
            }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f'Order failed: {result.retcode}')
            botlog.logger.info(f'Order failed: {result.retcode}')
        else:
            print(f'Order placed successfully: {result}')
            botlog.logger.info(f'Order placed successfully: {result}')
            order_ticket = result.order
            if self.trailing_pips:
                self.manage_trailing(order_ticket, order_type)
    
    def bot_loop(self, event_times):
        while True:
            current_time = datetime.now().time()
            self.is_market_open = sessions.market_time_check()

            if not self.is_market_open:
                time.sleep(3600)

            # for t in event_times:
            #     time_diff = timedelta(hours=t.hour, minutes=t.minute) - timedelta(hours=current_time.hour, minutes=current_time.minute)
            #     if time_diff == timedelta(minutes=10):
            #         time.sleep(1200)
            #         break

            balance = mt5.account_info().balance

            if self.lot_size:
                lot_size = self.lot_size
            else:
                lot_size = self.calculate_lot_size(balance)

            data = self.calculate_signals()
            latest = data.iloc[-1]
            print(latest)
            botlog.logger.info(latest)

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
            
            if latest['bullish'] and latest['close'] < latest['ema']:
                sl_price = self.calculate_dynamic_sl(latest, 1.5, 'buy') if not self.sl_pips else ask_price - sl_pips
                tp_price = ask_price + tp_pips if self.tp_pips else ask_price + (sl_pips * self.rr_ratio)
                self.place_order('buy', lot_size, ask_price, sl_price, tp_price)
            elif not latest['bullish'] and latest['close'] > latest['ema']:
                sl_price = self.calculate_dynamic_sl(latest, 1.5, 'sell') if not self.sl_pips else ask_price + sl_pips
                tp_price = bid_price - tp_pips if self.tp_pips else bid_price - (sl_pips * self.rr_ratio)
                self.place_order('sell', lot_size, bid_price, sl_price, tp_price)
            
            time.sleep(180)
    
    def get_events(self):
        return crawler.get_events('https://forexfactory.com/', headers={ 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:129.0) Gecko/20100101 Firefox/129.0' })
    
    def main_loop(self):
        times = self.get_events()

        while True:
            next_loop = datetime.now() + timedelta(hours=24)
            times = self.get_events()
            while datetime.now() < next_loop:
                self.bot_loop(times)