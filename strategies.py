'''
Created on 23.12.2021

@author: usam
'''

import numpy as np

def SMA(DF, sma_s=50, sma_l=200):
    signal = ""
    df = DF.copy()
    df["EMA_S"] = df["Close"].rolling(sma_s).mean()
    df["EMA_L"] = df["Close"].rolling(sma_l).mean()
    
    if df["EMA_S"].iloc[-1] > df["EMA_L"].iloc[-1]: 
        signal = "Buy"
        
    if df["EMA_S"].iloc[-1] < df["EMA_L"].iloc[-1]:
        signal = "Sell"
    
    return signal


def EMA(DF, ema_s=50, ema_l=200):
    
    signal = ""
    df = DF.copy()
    df["EMA_S"] = df["Close"].ewm(span = ema_s, min_periods = ema_s).mean() 
    df["EMA_L"] = df["Close"].ewm(span = ema_l, min_periods = ema_l).mean() 
    
    if df["EMA_S"].iloc[-1] > df["EMA_L"].iloc[-1]: 
        signal = "Buy"
        
    if df["EMA_S"].iloc[-1] < df["EMA_L"].iloc[-1]:
        signal = "Sell"
    
    return signal

def MACD(DF, a=12, b=26, c=9):
        
    """function to calculate MACD
   typical values a = 12; b =26, c =9"""
    signal = ""
    df = DF.copy()
    #a,b,c = 12, 26, 9
    df["MA_Fast"]=df["Close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["Close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace=True)
    
    if df["MACD"].iloc[-1] > df["Signal"].iloc[-1]: 
        signal = "Buy"
    elif df["MACD"].iloc[-1] < df["Signal"].iloc[-1]:
        signal = "Sell"
        
    return signal

def BB(DF,last_price, n=20, dev=2):
    "function to calculate Bollinger Band"

    signal = ""
    df = DF.copy()
    #df["MA"] = df['close'].rolling(n).mean()
    df["MA"] = df['Close'].ewm(span=n,min_periods=n).mean()
    df["BB_up"] = df["MA"] + dev*df['Close'].rolling(n).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
    df["BB_dn"] = df["MA"] - dev*df['Close'].rolling(n).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
    df["BB_width"] = df["BB_up"] - df["BB_dn"]
    
    if df["BB_up"].iloc[-1] > last_price: 
        signal =  "Sell"
    elif df["BB_dn"].iloc[-1] < last_price:
        signal =  "Buy"
    
    return signal

def RSI(DF, n=20, lower=30, upper=70):
    "function to calculate RSI"
    signal = ""
    df = DF.copy()
    df['delta']=df['Close'] - df['Close'].shift(1)
    df['gain']=np.where(df['delta']>=0,df['delta'],0)
    df['loss']=np.where(df['delta']<0,abs(df['delta']),0)
    avg_gain = []
    avg_loss = []
    gain = df['gain'].tolist()
    loss = df['loss'].tolist()
    for i in range(len(df)):
        if i < n:
            avg_gain.append(np.NaN)
            avg_loss.append(np.NaN)
        elif i == n:
            avg_gain.append(df['gain'].rolling(n).mean().iloc[n])
            avg_loss.append(df['loss'].rolling(n).mean().iloc[n])
        elif i > n:
            avg_gain.append(((n-1)*avg_gain[i-1] + gain[i])/n)
            avg_loss.append(((n-1)*avg_loss[i-1] + loss[i])/n)
    df['avg_gain']=np.array(avg_gain)
    df['avg_loss']=np.array(avg_loss)
    df['RS'] = df['avg_gain']/df['avg_loss']
    df['RSI'] = 100 - (100/(1+df['RS']))
    
    if df['RSI'].iloc[-1] > upper: 
        signal = "Sell"
    
    elif df['RSI'].iloc[-1] < lower: 
        signal = "Buy"

    return signal

def SO(DF,a=20,b=3):
    """function to calculate Stochastics
       a = lookback period
       b = moving average window for %D"""
       
    signal = ""
    df = DF.copy()
    df['C-L'] = df['Close'] - df['Low'].rolling(a).min()
    df['H-L'] = df['High'].rolling(a).max() - df['Low'].rolling(a).min()
    df['%K'] = df['C-L']/df['H-L']*100
    df['%D'] = df['%K'].ewm(span=b,min_periods=b).mean()
    
    if (df["%K"].iloc[-1] < 20 and  df["%D"].iloc[-1] < 20) and (df["%K"].iloc[-1] > df["%D"].iloc[-1]): 
        signal = "Buy"
        
    elif (df["%K"].iloc[-1] > 80 and  df["%D"].iloc[-1] > 80) and (df["%K"].iloc[-1] < df["%D"].iloc[-1]): 
        signal = "Sell"
        

    return signal

def ADX(DF,n=20):
    "function to calculate ADX"
    
    signal = ""
    df2 = DF.copy()
    df2['H-L']=abs(df2['High']-df2['Low'])
    df2['H-PC']=abs(df2['High']-df2['Close'].shift(1))
    df2['L-PC']=abs(df2['Low']-df2['Close'].shift(1))
    df2['TR']=df2[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df2['+DM']=np.where((df2['High']-df2['High'].shift(1))>(df2['Low'].shift(1)-df2['Low']),df2['High']-df2['High'].shift(1),0)
    df2['+DM']=np.where(df2['+DM']<0,0,df2['+DM'])
    df2['-DM']=np.where((df2['Low'].shift(1)-df2['Low'])>(df2['High']-df2['High'].shift(1)),df2['Low'].shift(1)-df2['Low'],0)
    df2['-DM']=np.where(df2['-DM']<0,0,df2['-DM'])

    df2["+DMMA"]=df2['+DM'].ewm(span=n,min_periods=n).mean()
    df2["-DMMA"]=df2['-DM'].ewm(span=n,min_periods=n).mean()
    df2["TRMA"]=df2['TR'].ewm(span=n,min_periods=n).mean()

    df2["+DI"]=100*(df2["+DMMA"]/df2["TRMA"])
    df2["-DI"]=100*(df2["-DMMA"]/df2["TRMA"])
    df2["DX"]=100*(abs(df2["+DI"]-df2["-DI"])/(df2["+DI"]+df2["-DI"]))
    
    df2["ADX"]=df2["DX"].ewm(span=n,min_periods=n).mean()
    
    if df2["ADX"].iloc[-2] < 25 and df2["ADX"].iloc[-1] > 25 and df2["+DI"].iloc[-1] > df2["-DI"].iloc[-1]:
        signal = "Buy"
        
    elif df2["ADX"].iloc[-2] < 25 and df2["ADX"].iloc[-1] > 25 and df2["+DI"].iloc[-1] < df2["-DI"].iloc[-1]:
        signal = "Sell"

    return signal

    