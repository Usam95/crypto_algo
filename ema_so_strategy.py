'''
Created on 16.01.2022

@author: usam
'''

from binance.client import Client
from binance import ThreadedWebsocketManager
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import os

class Strategy():
    
    def __init__(self, symbol, bar_length, EMA_S=50, EMA_L=200, SO_periods=14, SO_D_mw=3, position = 0):
        
        self.symbol = symbol
        self.bar_length = bar_length
        self.available_intervals = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
        self.units = {}
        self.trades = 0 
        self.trade_values = []
        self.symbol_position = {}
        
        #*****************add strategy-specific attributes here******************
        '''
        Parameters of EMA Strategy:
            EMA_S (int): time window in days for shorter EMA
            EMA_L (int): time window in days for longer EMA
        '''
        self.EMA_S = EMA_S
        self.EMA_L = EMA_L
        '''
        Parameters of SO Strategy:
            periods (int): time window in days for rolling low/high
            D_mw (int): time window in days for %D line
        '''
        self.SO_periods = SO_periods
        self.SO_D_mw = SO_D_mw
        
        #************************************************************************
        # load the binance client public and secret keys (must be exported previously)
        api_key = os.environ.get('binance_api')
        api_secret = os.environ.get('binance_secret')
        # init the binance client
        self.client = Client(api_key = api_key, api_secret = api_secret, tld = "com", testnet = False)
                
            
        self.orders = {}
        
        self.position_info = {}
        self.take_profit_pct = 0.1
        self.stop_loss_pct = 0.1
        
        
        self.symbols = ["XRPEUR"]
        
        self.units["XRPEUR"] = 25 
        self.symbol_position["XRPEUR"] = 0
        
        # Setupt logging system
        
        self.logSetup(create_file=True)
        
    def start_trading(self, historical_days):
        print("start_trading")
        self.twm = ThreadedWebsocketManager()
        self.twm.start()
        
        for symbol in self.symbols: 
            if self.bar_length in self.available_intervals:
                self.get_most_recent(symbol = symbol, interval = self.bar_length,
                                     days = historical_days)
                self.twm.start_kline_socket(callback = self.stream_candles,
                                            symbol = symbol, interval = self.bar_length)
        # "else" to be added later in the course 
    
    
    def logSetup(self, create_file=False):

        # create logger for prd_ci
        self.log_file_name = datetime.now().strftime('logs/logfile_%d_%m_%Y.log')
        
        log = logging.getLogger(self.log_file_name)
        log.setLevel(level=logging.INFO)

        # create formatter and add it to the handlers
        formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(funcName)-16s %(message)s',
                                      datefmt='%m-%d-%y %H:%M:%S')
        if create_file:
            # create file handler for logger.
            fh = logging.FileHandler(self.log_file_name)
            fh.setLevel(level=logging.INFO)
            fh.setFormatter(formatter)
        # reate console handler for logger.
        ch = logging.StreamHandler()
        ch.setLevel(level=logging.INFO)
        ch.setFormatter(formatter)

        # add handlers to logger.
        if create_file:
            log.addHandler(fh)

        log.addHandler(ch)
        self.logger = log 
        
    def get_most_recent(self, symbol, interval, days):
        print("get_most_recent")
        now = datetime.utcnow()
        past = str(now - timedelta(days = days))
    
        bars = self.client.get_historical_klines(symbol = symbol, interval = interval,
                                            start_str = past, end_str = None, limit = 1000)
        df = pd.DataFrame(bars)
        df["Date"] = pd.to_datetime(df.iloc[:,0], unit = "ms")
        df.columns = ["Open Time", "Open", "High", "Low", "Close", "Volume",
                      "Clos Time", "Quote Asset Volume", "Number of Trades",
                      "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore", "Date"]
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
        df.set_index("Date", inplace = True)
        for column in df.columns:
            df[column] = pd.to_numeric(df[column], errors = "coerce")
        df["Complete"] = [True for row in range(len(df)-1)] + [False]    
        self.data = df
    
    def stream_candles(self, msg):
        #print("stream_candles")
        
        # extract the required items from msg
        event_time = pd.to_datetime(msg["E"], unit = "ms")
        start_time = pd.to_datetime(msg["k"]["t"], unit = "ms")
        first   = float(msg["k"]["o"])
        high    = float(msg["k"]["h"])
        low     = float(msg["k"]["l"])
        close   = float(msg["k"]["c"])
        volume  = float(msg["k"]["v"])
        complete=       msg["k"]["x"]
        
        symbol = msg["s"]
        #print(f"Msg: {msg}")
        #print(f"Symbol: {symbol}, type: {type(symbol)}")
        # feed df (add new bar / update latest bar)
        self.data.loc[start_time] = [first, high, low, close, volume, complete]
        # prepare features and define strategy/trading positions whenever the latest bar is complete
        if complete == True:
            self.execute_strategy(symbol)
        

    def store_position_data(self, price, symbol):

        stop_loss = round(price - (price * self.stop_loss_pct), 2)
        take_profit = round(price + (price * self.take_profit_pct), 2)  
        
        self.position_info[symbol] = {'profit': take_profit}
        self.position_info[symbol] = {'loss': stop_loss}
    
    def execute_EMA_SO_strategy(self, symbol):
        
        print("execute_strategy")
        if len(self.data) > 0:
            price = self.data["Close"].iloc[-1]   
            print(f"Symbol: {symbol}, Price: {price}")
            if self.symbol_position[symbol] == 1:
                # Check wheter stop loss or take profit are triggered.
                if price <= self.position_info[symbol]['loss']:
                    order = self.client.create_order(symbol = symbol, side = "SELL", type = "MARKET", quantity = self.units[symbol])
                    self.symbol_position[symbol] = 0  # neutral position
                    #Report trade
                    self.logger.info(2 * "\n" + 100* "-")
                    self.logger.info(f"STOP LOSS TRIGGERED.")
                    self.report_trade(order, "GOING NEUTRAL") 
                    
                elif price >= self.position_info[symbol]["profit"]:
                    order = self.client.create_order(symbol = symbol, side = "SELL", type = "MARKET", quantity = self.units[symbol])
                    self.symbol_position[symbol] = 0  # neutral position
                    #Report trade
                    self.logger.info(2 * "\n" + 100* "-")
                    self.logger.info(f"TAKE PROFIT TRIGGERED.")
                    self.report_trade(order, "GOING NEUTRAL") 
                    
                if (self.EMA_strategy() == "Sell") and (self.SO_strategy() == "Sell"):
                    order = self.client.create_order(symbol = symbol, side = "SELL", type = "MARKET", quantity = self.units[symbol])
                    self.report_trade(order, "GOING NEUTRAL")                    
                    self.symbol_position[symbol] = 0  # neutral position
                    
            elif self.symbol_position[symbol] == 0:
                if (self.EMA_strategy() == "Buy") and (self.SO_strategy() == "Buy"): # Signal to go long
                    order = self.client.create_order(symbol = symbol, side = "BUY", type = "MARKET", quantity = self.units[symbol])
                    self.report_trade(order, "GOING LONG")  
                    self.symbol_position[symbol] = 1  # long position
                    
                    self.position_info[symbol] = {}
                    self.store_position_data(price, symbol)
        else: 
            self.logger.info("Not enough data to execute strategy..")
    
    def execute_EMA_strategy(self, symbol): 
        if len(self.data) > 0:
            price = self.data["Close"].iloc[-1]   
            
            print(f"Symbol: {symbol}, current price: {price}")
            if self.symbol_position[symbol] == 1:
                # Check wheter stop loss or take profit are triggered.
                if price <= self.position_info[symbol]['loss']:
                    print(2 * "\n" + 100* "-")
                    print(f"STOP LOSS TRIGGERED.")
                    order = self.client.create_order(symbol = symbol, side = "SELL", type = "MARKET", quantity = self.units[symbol])
                    self.report_trade(order, "GOING NEUTRAL") 
                    self.symbol_position[symbol] = 0  # neutral position
                    
                elif price >= self.position_info[symbol]["profit"]:
                    print(2 * "\n" + 100* "-")
                    print(f"TAKE PROFIT TRIGGERED.")
                    order = self.client.create_order(symbol = symbol, side = "SELL", type = "MARKET", quantity = self.units[symbol])
                    self.report_trade(order, "GOING NEUTRAL") 
                    self.symbol_position[symbol] = 0  # neutral position
                    
                if (self.EMA_strategy() == "Sell"):
                    order = self.client.create_order(symbol = symbol, side = "SELL", type = "MARKET", quantity = self.units[symbol])
                    self.report_trade(order, "GOING NEUTRAL")                    
                    self.symbol_position[symbol] = 0  # neutral position
                    
            elif self.symbol_position[symbol] == 0:
                if (self.EMA_strategy() == "Buy"): # Signal to go long
                    order = self.client.create_order(symbol = symbol, side = "BUY", type = "MARKET", quantity = self.units[symbol])
                    self.report_trade(order, "GOING LONG")  
                    self.symbol_position[symbol] = 1  # long position
                    
                    self.position_info[symbol] = {}
                    self.store_position_data(price, symbol)
        else: 
            print("Not enough data to execute strategy..")
            
    def SO_strategy(self):
        signal = ""
        df = self.data.copy()
        df['C-L'] = df['Close'] - df['Low'].rolling(self.SO_periods).min()
        df['H-L'] = df['High'].rolling(self.SO_periods).max() - df['Low'].rolling(self.SO_periods).min()
        df['%K'] = df['C-L']/df['H-L']*100
        df['%D'] = df['%K'].ewm(span=self.SO_D_mw,min_periods=self.SO_D_mw).mean()

        if (df["%K"].iloc[-1] < 20 and  df["%D"].iloc[-1] < 20) and (df["%K"].iloc[-1] > df["%D"].iloc[-1]): 
            signal = "Buy"

        elif (df["%K"].iloc[-1] > 80 and  df["%D"].iloc[-1] > 80) and (df["%K"].iloc[-1] < df["%D"].iloc[-1]): 
            signal = "Sell"
        return signal
    
    
    def EMA_strategy(self):  
        signal = ""
        df = self.data.copy()
        df["EMA_S"] = df["Close"].ewm(span = self.EMA_S, min_periods = self.EMA_S).mean() 
        df["EMA_L"] = df["Close"].ewm(span = self.EMA_L, min_periods = self.EMA_L).mean() 

        if df["EMA_S"].iloc[-1] > df["EMA_L"].iloc[-1]: 
            signal = "Buy"

        if df["EMA_S"].iloc[-1] < df["EMA_L"].iloc[-1]:
            signal = "Sell"
        return signal
    
    def report_trade(self, order, going): 
        
        # extract data from order object
        side = order["side"]
        self.logger.info(order)
        time = pd.to_datetime(order["transactTime"], unit = "ms")
        base_units = float(order["executedQty"])
        quote_units = float(order["cummulativeQuoteQty"])
        price = round(quote_units / base_units, 5)
        
        # calculate trading profits
        self.trades += 1
        if side == "BUY":
            self.trade_values.append(-quote_units)
        elif side == "SELL":
            self.trade_values.append(quote_units) 
        
   
        self.cum_profits = round(np.sum(self.trade_values[:-1]), 3)
        
        # print trade report
        self.logger.info(2 * "\n" + 100* "-")
        self.logger.info("{} | {}".format(time, going)) 
        self.logger.info("{} | Base_Units = {} | Quote_Units = {} | Price = {} ".format(time, base_units, quote_units, price))
        self.logger.info("{} | CumProfits = {} ".format(time, self.cum_profits))
        self.logger.info(100 * "-" + "\n")
        
        
        
if __name__ == "__main__":
    symbol="XRPEUR"
    bar_length="5m"
    position = 1
    trader = Strategy(symbol = symbol, bar_length = bar_length,  position = position)
    trader.start_trading(historical_days=1)
    trader.twm.join()
        