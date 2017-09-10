import pandas as pd
import quandl
from arctic import Arctic
store = Arctic('localhost')
price_table = store['CHINA_PX']
OI_table = store['CHINA_OI']
static_table = store['CHINA_STATIC']
import math
from datetime import datetime
import numpy as np
token="Us3wFmXGgAj_1cUtHAAR"

# Currently returns a Series with just the adjusted price.
# We could think about adding the 'adjusted' or total volume

def get_timeseries(market):
    price=load_market_price(market)
    price=price.replace(0, np.nan).ffill()
    volume=load_market_open_interest(market)
    return adjusted_returns(price,volume).dropna().astype(dtype='float').fillna(0)

def compare(last,this):
    if this[1:]>last[1:] or this[0] > last[0]:
        return this
    else:
        return last

def intital_load(mkt,price,OI):
	price_table.write(mkt, price)
	OI_table.write(mkt, OI)

def get_market_static_data():
    return static_table.read('Markets').data

def get_market_list(how='live'):
    mkts=static_table.read('Markets').data
    if how=='all':
    	return mkts.index
    else:
    	return ['A', 'AG', 'AL', 'AU', 'BU', 'C', 'CF', 'CS', 'CU',  
      'FG',  'HC', 'I', 'J', 'L', 'M', 'MA', 'NI', 'P',
      'PB', 'PP', 'RB', 'RM', 'SR', 'TA', 'V', 'SN' ]
      # Not enough liquidity: 'B'
      #'Y','GN','WH','ZN','JM','FB','JD','ER','WT,'ME','RO','WS']

def load_market_price(market):
	return price_table.read(market).data

def load_market_open_interest(market):
	return OI_table.read(market).data

def get_contract_multipliers():
	mkts=get_market_static_data()
	return mkts.contract_multiplier

def adjusted_returns(price,volume):
    rtn=price.pct_change()
    ww=volume.apply(lambda s: s.nlargest(2).index.tolist(), axis=1)
    s=pd.Series()
    mon='A00'
    spread=0
    for ind, val in ww.iteritems():
        mon=compare(mon,val[0])
        if ind in rtn.index:
            s.ix[ind]=rtn[val[0]].ix[ind]
    return s.dropna()

# To impliment 
def update_data():
    mkts=static_table.read('Markets').data
    for exchange in mkts.exchange.unique():
        list_of_markets=mkts[mkts.exchange==exchange].index
        for mkt in list_of_markets:
            price, OI = quandl_load_data(mkt,exchange)
            intital_load(mkt,price,OI)

def get_quandl_fields(exchange):
    field ={'DCE':['Close','Volume','Turnover','Open Interest'],
            'SHFE':['Close','Volume','O.I.'],
            'CZCE':['Close','Volume','Turnover','Open Interest'],
           'CFFEX':['Close','Volume','Turnover','Open Interest']}
    return field[exchange]

def _most_liquid_price(mkt):
    OI = load_market_open_interest(mkt).dropna(how='all')
    px= load_market_price(mkt).dropna(how='all')
    s=pd.Series()
    if px.size != 0:
        maxContract=OI.idxmax(axis=1)
        for row in maxContract.iteritems():
            try:
                s[row[0]]=px.ix[row[0]][row[1]]
            except:
                continue
    return s.replace(0)

def remove_inf(pnl):
    return pnl.replace(np.inf,0).replace(-np.inf,0)

def get_most_liquid_price(mkt):
    if type(mkt)==str:
        return _most_liquid_price(mkt)
    else:
        dic={}
        for m in mkt:
            dic[m]=get_most_liquid_price(m)
        return pd.DataFrame().from_dict(dic)

def quandl_load_data(market,exchange):
    list_of_months = ['F','G','H','J','K','M','N',
                        'Q','U','V','X','Z']
    fields=get_quandl_fields(exchange)
    if exchange=='CZCE':
        exchange='ZCE'
    ticker = exchange + '/' + market
    ddf={}
    mini_list = list(list_of_months)
    for y in range(2018,2000,-1):
        for m in mini_list:
            try:
                ddf[m + str(y)[2:]]=quandl.get(ticker + m + str(y),authtoken=token)[fields]
            except:
                if y != 2018:
                    mini_list.remove(m)
                print 'Missing '+m + ' '+ str(y) + ' for market '+ market
    ix = pd.DatetimeIndex(start=datetime(2000, 1, 1), end=datetime(2018, 12, 31), freq='D')
    price=pd.DataFrame(index=ix)
    for k in ddf.keys():
        price[k]=ddf[k].Close
    price=price.dropna(how='all')
    OI=pd.DataFrame(index=ix)
    for k in ddf.keys():
        try:
            OI[k]=ddf[k]['Open Interest']
        except:
            OI[k]=ddf[k]['O.I.']
    OI=OI.dropna(how='all')
    return price,OI

def get_traded_contract(mkt):
    OI=load_market_open_interest(mkt).dropna(how='all')
    return OI.idxmax(axis=1).tail(1).ix[0]






