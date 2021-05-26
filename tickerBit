import time
import pyupbit
import datetime
import requests
from fbprophet import Prophet

# K뱅크 값
access = "cHJjMwVsbxZjr98OVPA2smVsvAGjg7wpP5BIeQuC"
secret = "AXh3HuuyfYsOZipUOjkZ0daZvnD0lZVSrX1cR7Sp"
myToken = "xoxb-1730814337234-1985015754823-uI1neavK3MM3vPiB8cdFLjS1"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k):
    """민우 전략으로 매수 목표가 조회"""

    # 전날데이터를 가져옵니다.
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    # 매수목표가 = 시작가 * 1.007
    before_target_price = df.iloc[0]['close'] * 1.007
    # 매수목표가 = 시작가 * 1.011
    after_target_price = df.iloc[0]['close'] * 1.011
    # 종가(시작가)
    start_price = df.iloc[0]['close']

    return before_target_price, after_target_price, start_price

def get_sell_price(ticker, spay):
    """매도 목표가 조회"""
    # 매도목표가 = 시작가 * 0.99
    sell_price2 = spay * 0.99
    # 매도목표가 = 시작가 * 1.02
    sell_price8 = spay * 1.02

    return sell_price2, sell_price8

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(coin):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == coin:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def predict_price(ticker):
    """Prophet으로 당일 종가 가격 예측"""
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute60")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
    if len(closeDf) == 0:
        closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
    closeValue = closeDf['yhat'].values[0]
    predicted_close_price = closeValue


###################################
# 로그인
###################################
upbit = pyupbit.Upbit(access, secret)
print("업비트 자동매매 시작합니다.")

###################################
# 대상종목 추출
###################################
tickers = pyupbit.get_tickers()
symbol_list = []
buy_list = []
today_list = []
sell_krw = 0
buy_krw = 0
total_krw = 0
profit_price = 0
buy_price = 0
predicted_close_price = 0
close_price = 0

###################################
# 시작 메세지 슬랙 전송
###################################
post_message(myToken,"#volvobit", "볼보-비트 자동매매 시작합니다.")

for ticker in tickers:
    if 'KRW-' in ticker:
        '''        
        try:
            df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
            #print(type(df.iloc[0]['close']))
        except Exception as ex:
            df = None

        if df is not None:
            predict_price(ticker)
            
            if 10 < df.iloc[0]['close'] < 10000 and predicted_close_price > df.iloc[0]['close']:
                symbol_list.append(ticker)
                #print("가격 : ", predicted_close_price)
                current_price = get_current_price(ticker)
                post_message(myToken,"#volvobit", "`예측종목 : "+ ticker + "`")
                post_message(myToken,"#volvobit", "현재가/예측가격 : " + str(current_price) + "/" + str(predicted_close_price))
        '''

        predict_price(ticker)
        current_price = get_current_price(ticker)
        close_price = ((predicted_close_price/current_price)-1)*100
        if 10 < current_price < 10000 and predicted_close_price > current_price and close_price > 10:
            symbol_list.append(ticker)
            #print("가격 : ", predicted_close_price)
            current_price = get_current_price(ticker)
            close_price = ((predicted_close_price/current_price)-1)*100
            post_message(myToken,"#volvobit", "`예측종목 : "+ ticker + ", 예상수익율 : " + str(round(close_price,1)) + "%`")
            post_message(myToken,"#volvobit", "현재가/예측가격 : " + str(current_price) + "/" + str(round(predicted_close_price, 0)))


post_message(myToken,"#volvobit", "대상종목 : "+ str(len(symbol_list)) + "건")
