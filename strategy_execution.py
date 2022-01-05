'''
Created on 25.12.2021

@author: usam
'''
from strategies import *
from renko_macd_functions import renko_macd
from IterativeBase2 import IterativeBase2
import time

from strategies_pkg.EMABacktester import EMABacktester 

from strategies_pkg.RSIBacktester import RSIBacktester 
from strategies_pkg.BBBacktester import BBBacktester
from strategies_pkg.SMABacktester import SMABacktester
from strategies_pkg.MACDBacktester import MACDBacktester
from strategies_pkg.SOBacktester import SOBacktester
import os

class StrategyExecutor(IterativeBase2):
    
    def __init__(self, units, symbol=None, strategy=None, path=None):
        super().__init__(symbol=symbol, strategy=strategy, units=units, path=path)

        self.position = 0  # initial neutral position
        self.trades = 0  # no trades yet
        self.macd_str = MACDBacktester(EMA_S=12, EMA_L=26, signal_mw=9)
        self.ema_str = EMABacktester()
        self.rsi_str = RSIBacktester()
        self.so_str = SOBacktester()
        self.bb_str = BBBacktester()
        self.sma_str = SMABacktester()
        
        
        self.str_params = {}
        
        self.updated_params = False
        
    def update_strategy_parameters(self):
        
        #Optimize MACD 
        self.macd_str.set_df(self.strategy_df)
        self.macd_str.optimize_parameters((5,20,1), (21,50,1), (5,20,1))
        self.str_params["MACD"] = self.macd_str.get_parameters()
        print("MACD test results: ", self.macd_str.test_strategy())
        print("MACD parameters: ", self.macd_str.get_parameters())
        
        #Optimize RSI
        self.rsi_str.set_df(self.strategy_df)
        self.rsi_str.optimize_parameters((5, 20, 1), (65, 80, 1), (20, 35, 1))
        self.str_params["RSI"] = self.rsi_str.get_parameters()
        print("RSI test results: ", self.rsi_str.test_strategy())
        print("RSI parameters: ", self.rsi_str.get_parameters())
        
        #Optimize SO parameters
        self.so_str.set_df(self.strategy_df)
        self.so_str.optimize_parameters((10,100,1), (3,50,1))
        self.str_params["SO"] = self.so_str.get_parameters()
        print("SO test results: ", self.so_str.test_strategy())
        print("SO parameters: ", self.so_str.get_parameters())   
        
        # Optimize BB parameters
        self.bb_str.set_df(self.strategy_df)
        self.bb_str.optimize_parameters((25, 100, 1), (1,5,1))
        self.str_params["BB"] = self.bb_str.get_parameters()
        print("BB test results: ", self.bb_str.test_strategy())
        print("BB parameters: ", self.bb_str.get_parameters())           
           
        # Optimize EMA parameters
        self.ema_str.set_df(self.strategy_df)
        self.ema_str.optimize_parameters((25,75,1), (100,200,1))
        self.str_params["EMA"] = self.ema_str.get_parameters()
        print("EMA test results: ", self.ema_str.test_strategy())
        print("EMA parameters: ", self.ema_str.get_parameters())
        
        # Optimize SMA parameters
        self.sma_str.set_df(self.strategy_df)
        self.sma_str.optimize_parameters((25,75,1), (100,200,1))
        self.str_params["SMA"] = self.sma_str.get_parameters()
        print("SMA test results: ", self.sma_str.test_strategy())
        print("SMA parameters: ", self.sma_str.get_parameters())
        
        
        for key, value in self.str_params.items():
            print(key, value)
        
    def store_position_data(self, price):
        
        stop_loss = round(price - (price * self.stop_loss_pct), 2)
        take_profit = round(price + (price * self.take_profit_pct), 2)     
        self.position_info['profit'] = take_profit
        self.position_info['loss'] = stop_loss
        #print(f"New position data || {price}, stop_loss: {stop_loss}, take_profit: {take_profit}")
      
    def execute_SMA(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif SMA(self.cur_df, self.sma_str.SMA_S, self.sma_str.SMA_L) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif SMA(self.cur_df, self.sma_str.SMA_S, self.sma_str.SMA_L) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
            
    def execute_EMA(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif EMA(self.cur_df, self.ema_str.EMA_S, self.ema_str.EMA_L) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif EMA(self.cur_df, self.ema_str.EMA_S, self.ema_str.EMA_L) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
              
    def execute_BB(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif BB(DF=self.cur_df, last_price=price, n=self.bb_str.SMA, dev=self.bb_str.dev) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif BB(DF=self.cur_df, last_price=price, n=self.bb_str.SMA, dev=self.bb_str.dev) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")  
             
    def execute_MACD(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif MACD(self.cur_df, self.macd_str.EMA_S, self.macd_str.EMA_L, self.macd_str.signal_mw)  == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif MACD(self.cur_df, self.macd_str.EMA_S, self.macd_str.EMA_L, self.macd_str.signal_mw) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
            
            
    def execute_ADX(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif ADX(DF=self.cur_df) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  ADX(DF=self.cur_df) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
            
    def execute_RSI(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif RSI(self.cur_df, self.rsi_str.periods, self.rsi_str.rsi_lower, self.rsi_str.rsi_upper) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  RSI(self.cur_df, self.rsi_str.periods, self.rsi_str.rsi_lower, self.rsi_str.rsi_upper) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
            
    
    def execute_SO(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif SO(self.cur_df, self.so_str.periods, self.so_str.D_mw) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  SO(self.cur_df, self.so_str.periods, self.so_str.D_mw) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
            
    def execute_RENKO_and_MACD(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif renko_macd(DF=self.cur_df) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  renko_macd(DF=self.cur_df) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
            
    ######################################################################################
    #Combined Strategies   
    ######################################################################################

    def execute_SMA_and_RSI(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif RSI(self.cur_df, self.rsi_str.periods, self.rsi_str.rsi_lower, self.rsi_str.rsi_upper) == "Sell" and SMA(self.cur_df, self.sma_str.SMA_S, self.sma_str.SMA_L) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  RSI(self.cur_df, self.rsi_str.periods, self.rsi_str.rsi_lower, self.rsi_str.rsi_upper) == "Buy" and SMA(self.cur_df, self.sma_str.SMA_S, self.sma_str.SMA_L) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")     
                         
    def execute_EMA_and_RSI(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif RSI(self.cur_df, self.rsi_str.periods, self.rsi_str.rsi_lower, self.rsi_str.rsi_upper) == "Sell" and EMA(self.cur_df, self.ema_str.EMA_S, self.ema_str.EMA_L) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  RSI(self.cur_df, self.rsi_str.periods, self.rsi_str.rsi_lower, self.rsi_str.rsi_upper) == "Buy" and EMA(self.cur_df, self.ema_str.EMA_S, self.ema_str.EMA_L) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
            
                         
    def execute_EMA_and_SO(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif SO(self.cur_df, self.so_str.periods, self.so_str.D_mw) == "Sell" and EMA(self.cur_df, self.ema_str.EMA_S, self.ema_str.EMA_L) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  SO(self.cur_df, self.so_str.periods, self.so_str.D_mw) == "Buy" and EMA(self.cur_df, self.ema_str.EMA_S, self.ema_str.EMA_L) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
            
          
    def execute_BB_and_RSI(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif RSI(self.cur_df, self.rsi_str.periods, self.rsi_str.rsi_lower, self.rsi_str.rsi_upper) == "Sell" and BB(DF=self.cur_df, last_price=price, n=self.bb_str.SMA, dev=self.bb_str.dev) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  RSI(self.cur_df, self.rsi_str.periods, self.rsi_str.rsi_lower, self.rsi_str.rsi_upper) == "Buy" and BB(DF=self.cur_df, last_price=price, n=self.bb_str.SMA, dev=self.bb_str.dev) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")

 
    def execute_BB_and_SO(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif SO(self.cur_df, self.so_str.periods, self.so_str.D_mw) == "Sell" and BB(DF=self.cur_df, last_price=price, n=self.bb_str.SMA, dev=self.bb_str.dev) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  SO(self.cur_df, self.so_str.periods, self.so_str.D_mw) == "Buy" and BB(DF=self.cur_df, last_price=price, n=self.bb_str.SMA, dev=self.bb_str.dev) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
 

    def execute_MACD_and_RSI(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif MACD(self.cur_df, self.macd_str.EMA_S, self.macd_str.EMA_L, self.macd_str.signal_mw) == "Sell" and RSI(self.cur_df, self.rsi_str.periods, self.rsi_str.rsi_lower, self.rsi_str.rsi_upper) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  MACD(self.cur_df, self.macd_str.EMA_S, self.macd_str.EMA_L, self.macd_str.signal_mw) == "Buy" and RSI(self.cur_df, self.rsi_str.periods, self.rsi_str.rsi_lower, self.rsi_str.rsi_upper) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
 
                      
    def execute_MACD_and_SO(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif MACD(self.cur_df, self.macd_str.EMA_S, self.macd_str.EMA_L, self.macd_str.signal_mw) == "Sell" and SO(self.cur_df, self.so_str.periods, self.so_str.D_mw) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  MACD(self.cur_df, self.macd_str.EMA_S, self.macd_str.EMA_L, self.macd_str.signal_mw) == "Buy" and SO(self.cur_df, self.so_str.periods, self.so_str.D_mw) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
            
           
    def execute_ADX_and_EMA(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif EMA(self.cur_df, self.ema_str.EMA_S, self.ema_str.EMA_L) == "Sell" and ADX(DF=self.cur_df) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # utral position
                        self.trades += 1
                elif  EMA(self.cur_df, self.ema_str.EMA_S, self.ema_str.EMA_L) == "Buy" and ADX(DF=self.cur_df) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")
            
    def execute_ADX_and_MACD(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif MACD(self.cur_df, self.macd_str.EMA_S, self.macd_str.EMA_L, self.macd_str.signal_mw) == "Sell" and ADX(DF=self.cur_df) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  MACD(self.cur_df, self.macd_str.EMA_S, self.macd_str.EMA_L, self.macd_str.signal_mw) == "Buy" and ADX(DF=self.cur_df) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")   
            
    def execute_RENKO_and_MACD_and_SO(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif renko_macd(self.cur_df,self.macd_str.EMA_S, self.macd_str.EMA_L, self.macd_str.signal_mw) == "Sell" and SO(self.cur_df, self.so_str.periods, self.so_str.D_mw) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  renko_macd(self.cur_df,self.macd_str.EMA_S, self.macd_str.EMA_L, self.macd_str.signal_mw) == "Buy" and SO(self.cur_df, self.so_str.periods, self.so_str.D_mw) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")  
            
    def execute_RENKO_and_MACD_and_RSI(self):
        test_data_len = len(self.df) - self.end_idx - 1
        if test_data_len > 0:
            for _ in range(test_data_len): # all bars (except the last bar)
                self.update_current_df()
                price = self.cur_df["Close"].iloc[-1]    
                if self.position: 
                    if price <= self.position_info["loss"]:
                        print(f"Stop loss triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1   
                    elif price >= self.position_info["profit"]:
                        print(f"Take profit triggered.")
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                    elif renko_macd(self.cur_df,self.macd_str.EMA_S, self.macd_str.EMA_L, self.macd_str.signal_mw) == "Sell" and RSI(self.cur_df, self.rsi_str.periods, self.rsi_str.rsi_lower, self.rsi_str.rsi_upper) == "Sell":
                        self.sell_instrument(price)
                        self.position = 0  # neutral position
                        self.trades += 1
                elif  renko_macd(self.cur_df, self.macd_str.EMA_S, self.macd_str.EMA_L, self.macd_str.signal_mw) == "Buy" and RSI(self.cur_df, self.rsi_str.periods, self.rsi_str.rsi_lower, self.rsi_str.rsi_upper) == "Buy": # Signal to go long
                        self.position_info = {}
                        self.store_position_data(price)
                        self.buy_instrument(price) # go long with full amount
                        self.position = 1  # long position
                        self.trades += 1
            self.close_pos(self.df["Close"].iloc[-1]) # close position at the last bar   
        else: 
            print("Not enough data for backtest..")         


units_per_symbol = {"EOS":200, "ETH":1, "LTC":10, "BCH":1, "XRP":500}
                  
def execute_combined_strategies(ib, symbol, path, strategies, interval, optimized=False):
        
        ib.set_path(path)
        ib.set_symbol(symbol)
        ib.set_interval(interval)
        #ib.set_units()
        
        if optimized:
            ib.update_strategy_parameters()
        # Iterate over the strategie list and execute strategies
        for strategy in strategies:
            
            print(2 * "\n" + 100* "-")
            print(f"Executing strategy: {strategy} for {symbol} with {interval} interval.")
            print(2 * "\n" + 100* "-")
            ib.reset(units_per_symbol[symbol])
            if strategy == "EMA_and_SO": 
                #print(f"Execute backtest with {strategy}")
                ib.execute_EMA_and_SO()
                
            elif strategy == "SMA_and_RSI":
                #print(f"Execute backtest with {strategy}") 
                ib.execute_SMA_and_RSI()
            elif strategy == "EMA_and_RSI":
                #print(f"Execute backtest with {strategy}") 
                ib.execute_EMA_and_RSI()
        
            elif strategy == "BB_and_SO": 
                #print(f"Execute backtest with {strategy}")
                ib.execute_BB_and_SO()
                
            elif strategy == "BB_and_RSI": 
                #print(f"Execute backtest with {strategy}")
                ib.execute_BB_and_RSI()
                
            elif strategy == "MACD_and_RSI":
                #print(f"Execute backtest with {strategy}") 
                ib.execute_MACD_and_RSI()
                
            elif strategy == "MACD_and_SO":
                #print(f"Execute backtest with {strategy}") 
                ib.execute_MACD_and_SO()
                
            elif strategy == "ADX_and_EMA": 
                #print(f"Execute backtest with {strategy}")
                ib.execute_ADX_and_EMA()
                
            elif strategy == "ADX_and_MACD": 
                #print(f"Execute backtest with {strategy}")
                ib.execute_ADX_and_MACD()
                
            elif strategy == "RENKO_MACD_and_RSI": 
                #print(f"Execute backtest with {strategy}")
                ib.execute_RENKO_and_MACD_and_RSI()
                
            elif strategy == "RENKO_MACD_RSO": 
                #print(f"Execute backtest with {strategy}")
                ib.execute_RENKO_and_MACD_and_SO()

            if optimized:
                strategy = str(strategy + "_opt") 
            
            
            ib.set_strategy(strategy) 

            ib.store_results()  
  

        
def execute_single_strategies(ib, symbol, path, strategies, interval, optimized=False):
    
        ib.set_path(path)
        ib.set_symbol(symbol)
        ib.set_interval(interval)
        #ib.set_units(units_per_symbol[symbol])
        #ib.reset()
        if optimized:
            ib.update_strategy_parameters()

        # Iterate over the strategie list and execute strategies
        for strategy in strategies:
            #ib.set_units()

            print(2 * "\n" + 100* "-")
            print(f"Executing strategy: {strategy} for {symbol} with {interval} interval.")
            print(2 * "\n" + 100* "-")
            ib.reset(units_per_symbol[symbol])          
            #ib.init_initial_balance()
            if strategy == "SMA": 
                #print(f"Execute backtest with {strategy}")
                ib.execute_SMA()
            elif strategy == "RSI": 
                #print(f"Execute backtest with {strategy}")
                ib.execute_RSI()
    
            elif strategy == "SO":
                #print(f"Execute backtest with {strategy}") 
                ib.execute_SO()
                
            elif strategy == "MACD": 
                #print(f"Execute backtest with {strategy}")
                ib.execute_MACD()
                
            elif strategy == "RENKO_MACD_2": 
                #print(f"Execute backtest with {strategy}")
                ib.execute_RENKO_and_MACD()
                
            elif strategy == "BB":
                #print(f"Execute backtest with {strategy}") 
                ib.execute_BB()
                
            elif strategy == "EMA":
                #print(f"Execute backtest with {strategy}") 
                ib.execute_EMA()
                
            elif strategy == "ADX": 
                #print(f"Execute backtest with {strategy}")
                ib.execute_ADX()

            if optimized:
                strategy = str(strategy + "_opt")
            ib.set_strategy(strategy)  
            ib.store_results()    


def get_df_path(symbol, interval):
    parent_dir = "hist_data"
    folder = str(symbol + "/" + interval.strip())
    file_name = str(symbol + "_" + interval.strip() +".csv")
    path = os.path.join(parent_dir, folder, file_name)
    return path  
              
if __name__ == "__main__":
    
    symbols = ["EOS", "ETH", "LTC", "BCH", "XRP"]
    #symbols = ["XRP"]
    
    intervals_str = "5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h"
    #intervals_str = "8h"

    intervals = intervals_str.split(",")
    #
    single_strategies = ["SMA","RSI", "SO", "EMA", "MACD", "ADX", "BB", "RENKO_MACD"]
    #single_strategies = ["RENKO_MACD_2"]
    #combined_strategies = ["SMA_and_RSI","EMA_and_SO", "EMA_and_RSI", "BB_and_SO", "BB_and_RSI", "MACD_and_RSI","MACD_and_SO", 
    #                       "ADX_and_EMA", "ADX_and_MACD"]
    #===========================================================================
    combined_strategies = ["SMA_and_RSI","EMA_and_SO", "EMA_and_RSI", "BB_and_SO", "BB_and_RSI", "MACD_and_RSI","MACD_and_SO", "ADX_and_EMA", "ADX_and_MACD"]
    #===========================================================================
    #strategies = ["RSI", "so"]
    ib= StrategyExecutor(units=1)
    start_t = time.time()
    for symbol in symbols: 
        for interval in intervals: 
            path = get_df_path(symbol, interval)
            execute_single_strategies(ib, symbol, path, single_strategies, interval)
            execute_combined_strategies(ib,symbol,path, combined_strategies, interval)
    #===========================================================================
    # ib.init_initial_balance()
    # for symbol in symbols:
    #     print(f"Executing Single Strategy Backtesting with parameter optimization for: {symbol}")
    #     execute_single_strategies(ib, symbol, paths[symbol], single_strategies, optimized=True)
    #     print(f"Executing Multiple Strategy Backtesting with parameter optimization for: {symbol}")
    #     execute_combined_strategies(ib,symbol, paths[symbol], combined_strategies, optimized=True)
    #===========================================================================
    #execute_single_strategies(single_strategies)
    #execute_combined_strategies(combined_strategies)
    #===========================================================================
    # ib = StrategyExecutor(symbol = "ETH", strategy="adx", units=1, path="./hist_data/ETH/m5/ETH_m5.csv")
    # ib.init_initial_balance()
    # print(f"Initial balance: {ib.initial_balance}")
    # #ib.test_macd_strategy_bracket(12, 26, 9)
    # ib.execute_adx()
    # ib.store_results()
    #===========================================================================
    end_t = time.time()
    dur_t = end_t - start_t
    print(f"Total time took for BackTestings: {dur_t/60} mins.")