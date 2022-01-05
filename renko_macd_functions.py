import numpy as np
import pandas as pd
import statsmodels.api as sm
from stocktrends import Renko

import copy



def renko_macd(DF,a=12,b=26,c=9):
    "function to generate signal"
    
    df = renko_merge(DF, a, b, c)
    signal = ""
    
    if df["bar_num"].tolist()[-1]>=2 and df["macd"].tolist()[-1]>df["macd_sig"].tolist()[-1] and df["macd_slope"].tolist()[-1]>df["macd_sig_slope"].tolist()[-1]:
        signal = "Buy"
 
    #elif df["bar_num"].tolist()[-1]<=-2 and df["macd"].tolist()[-1]<df["macd_sig"].tolist()[-1] and df["macd_slope"].tolist()[-1]<df["macd_sig_slope"].tolist()[-1]:
    elif df["macd"].tolist()[-1]<df["macd_sig"].tolist()[-1] and df["macd_slope"].tolist()[-1]<df["macd_sig_slope"].tolist()[-1]:
        signal = "Sell"

    return signal


def MACD(DF, a=12, b=26, c=9):
    """function to calculate MACD
       typical values a = 12; b =26, c =9"""
    df = DF.copy()
    #a,b,c = 12, 26, 9
    df["MA_Fast"]=df["Close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["Close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace=True)
    return (df["MACD"],df["Signal"])

def ATR(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC']=abs(df['High']-df['Close'].shift(1))
    df['L-PC']=abs(df['Low']-df['Close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2

def slope(ser,n):
    "function to calculate the slope of n consecutive points on a plot"
    slopes = [i*0 for i in range(n-1)]
    for i in range(n,len(ser)+1):
        y = ser[i-n:i]
        x = np.array(range(n))
        y_scaled = (y - y.min())/(y.max() - y.min())
        x_scaled = (x - x.min())/(x.max() - x.min())
        x_scaled = sm.add_constant(x_scaled)
        model = sm.OLS(y_scaled,x_scaled)
        results = model.fit()
        slopes.append(results.params[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(slopes))))
    return np.array(slope_angle)

def renko_DF(DF):
    "function to convert ohlc data into renko bricks"
    df = DF.copy()
    #===========================================================================
    df.reset_index(inplace=True, drop=True)
    df = df.iloc[:,[0,1,2,3,4]]
    df.columns = ["date","open","close","high","low"]
    #df.set_index("date",inplace=True)
    #===========================================================================
    df2 = Renko(df)
    df2.brick_size = round(ATR(DF,120)["ATR"].iloc[-1],4)
    renko_df = df2.get_ohlc_data()
    renko_df["bar_num"] = np.where(renko_df["uptrend"]==True,1,np.where(renko_df["uptrend"]==False,-1,0))
    for i in range(1,len(renko_df["bar_num"])):
        if renko_df["bar_num"].iloc[i]>0 and renko_df["bar_num"].iloc[i-1]>0:
            renko_df["bar_num"].iloc[i]+=renko_df["bar_num"].iloc[i-1]
        elif renko_df["bar_num"].iloc[i]<0 and renko_df["bar_num"].iloc[i-1]<0:
            renko_df["bar_num"].iloc[i]+=renko_df["bar_num"].iloc[i-1]
    renko_df.drop_duplicates(subset="date",keep="last",inplace=True)
    return renko_df

def renko_merge(DF,a=12,b=26,c=9):
    "function to merging renko df with original ohlc df"
    df = copy.deepcopy(DF)
    #df["Date"] = df.index
    renko = renko_DF(df)
    renko.columns = ["Date","open","high","low","close","uptrend","bar_num"]
    merged_df = df.merge(renko.loc[:,["Date","bar_num"]],how="outer",on="Date")
    merged_df["bar_num"].fillna(method='ffill',inplace=True)
  
    macd, signal =  MACD(merged_df, a,b,c)
    
    merged_df["macd"]= macd
    merged_df["macd_sig"]= signal
    merged_df["macd_slope"] = slope(merged_df["macd"],5)
    merged_df["macd_sig_slope"] = slope(merged_df["macd_sig"],5)
    return merged_df