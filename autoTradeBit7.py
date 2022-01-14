import os, sys, ctypes
import time
import pyupbit
import datetime
import requests
from fbprophet import Prophet

# K뱅크 값
access = "AbcCsTmtpOFUPUz86ZNsP5F8w6VdjU8Z7UGFs81G"
secret = "8aqhI3xUOFBkXelGWJPvhSd9lxFjhexE17tKSeIp"
myToken = "xoxb-1730814337234-1985015754823-uI1neavK3MM3vPiB8cdFLjSF"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_btc_price(code, k):
    """민우 전략으로 매수 목표가 조회"""

    # 전날데이터를 가져옵니다.
    df = pyupbit.get_ohlcv(code, interval="day", count=2)
    # 종가(시작가)
    btc_start_price = df.iloc[0]['close']

    return btc_start_price

def get_target_price(code, k):
    """민우 전략으로 매수 목표가 조회"""

    # 전날데이터를 가져옵니다.
    df = pyupbit.get_ohlcv(code, interval="day", count=2)
    # 매수목표가 = 시작가 * 1.009
    before_target_price = df.iloc[0]['close'] * 1.009
    # 매수목표가 = 시작가 * 1.019
    after_target_price = df.iloc[0]['close'] * 1.019
    # 종가(시작가)
    start_price = df.iloc[0]['close']

    return before_target_price, after_target_price, start_price

def get_sell_price(spay):
    """매도 목표가 조회"""
    # 매도목표가 = 시작가 * 0.98
    sell_price2 = spay * 0.98
    # 매도목표가 = 시작가 * 1.04
    sell_price8 = spay * 1.04

    return sell_price2, sell_price8

def get_start_time():
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=1)
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

def get_current_price(code):
    """현재가 조회"""
    return pyupbit.get_current_price(code)

def predict_price(ticker, val):
    """Prophet으로 당일 종가 가격 예측"""
    predicted_close_price = 0

    #최근 200시간으로 학습
    df = pyupbit.get_ohlcv(ticker, interval="minute60")
    df = df.reset_index()
    #시간
    df['ds'] = df['index']
    #종가 
    df['y'] = df['close']
    data = df[['ds','y']]
    #학습시작
    model = Prophet()
    model.fit(data)
    #미래 예측
    if val == '1':
        #24시간
        future = model.make_future_dataframe(periods=24, freq='H')
    else:
        #1시간
        future = model.make_future_dataframe(periods=1, freq='H')
        
    forecast = model.predict(future)
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
    if len(closeDf) == 0:
        closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]

    predicted_close_price = closeDf['yhat'].values[0]
    return predicted_close_price

def get_code_list():
    """학습을 통한 예측종목 추출"""
    symbol_list = []
    tickers = pyupbit.get_tickers(fiat="KRW")
    print('전체종목수 : ', len(tickers))

    for ticker in tickers:
        if 'KRW-' in ticker:
            print('ticker : ', ticker)
            predicted_close_price = predict_price(ticker, "1")
            print('predicted_close_price : ', predicted_close_price)
            ticker_current_price = get_current_price(ticker)
            close_price = ((predicted_close_price/ticker_current_price)-1)*100
            if 10 < ticker_current_price < 10000 and predicted_close_price > ticker_current_price and close_price > 5:
                symbol_list.append(ticker)
                #print("가격 : ", predicted_close_price)
                post_message(myToken,"#volvobit", "`예측종목 : "+ ticker + ", 예상수익율 : " + str(round(close_price,1)) + "%`")
                #post_message(myToken,"#volvobit", "현재가/예측가격 : " + str(ticker_current_price) + "/" + str(round(predicted_close_price, 0)))

    post_message(myToken,"#volvobit", "대상종목 : "+ str(len(symbol_list)) + "건")
    return symbol_list

###################################
# 로그인
###################################
upbit = pyupbit.Upbit(access, secret)
print("볼보비트 자동매매 시작합니다.")
post_message(myToken,"#volvobit", "볼보-비트 자동매매 시작합니다.")
###################################
# 대상종목 추출
###################################
#tickers = pyupbit.get_tickers(fiat="KRW")
symbol_list = get_code_list()
#symbol_list = ['KRW-PLA','KRW-QKC','KRW-HUM','KRW-IOST','KRW-HUNT','KRW-OMG','KRW-AQT','KRW-HIVE','KRW-OMG','KRW-ATOM','KRW-AXS']
today_list = []
sell_krw = 0
buy_krw = 0
code_close_price = 0
today_krw = 766185
target_krw = 83999999
total_krw = 0
profit_price = 0
buy_price = 0
btc_price = 0
btc_close_price = 0
btc_start_price = 0
buy_code = ''

###################################
# 시작 메세지 슬랙 전송
###################################
btc_start_price = get_btc_price("KRW-BTC", 0.5)

###################################
# 자동매매로직
###################################
upbitYn = 'N'
startYn = 'Y'
breakYn = 'N'
while True:
    try:
        #now = datetime.datetime.now()
        start_time = get_start_time()
        end_time = start_time + datetime.timedelta(days=1)
        s_time = start_time - datetime.timedelta(hours=1)
        d_time = start_time + datetime.timedelta(hours=4)
        #print(now)
                
        for code in symbol_list:
            #print("code : ", code)
            #print("start_time : ", start_time)
            #print("datetime.datetime.now() : ", datetime.datetime.now())
            #print("end_time : ", end_time - datetime.timedelta(seconds=10))
            
            # 오늘 9시 < 현재 < 내일 8시50분
            if start_time < datetime.datetime.now() < end_time - datetime.timedelta(seconds=600):
            # 오늘 8시 < 현재 < 13시까지
            #if s_time < datetime.datetime.now() < d_time:

                btc_price = get_current_price("KRW-BTC")
                btc_close_price = ((btc_price-btc_start_price)/btc_start_price)*100
                if breakYn == 'N' and btc_close_price < -2.4:
                    post_message(myToken,"#volvobit", "`위험감지!! 브레이크발동!! 오전9시 재기동합니다.`")
                    post_message(myToken,"#volvobit", "비트코인 : " + str(round(btc_close_price,2)) + ", 시세 : " + str(round(btc_price,2)))
                    breakYn = 'Y'
                
                if breakYn == 'N' and buy_krw > target_krw:
                    post_message(myToken,"#volvobit", "`20% 목표달성!!! $축$ 정산 후 내일 뵙겠습니다.`")
                    breakYn = 'Y'                
                
                startYn = 'Y'
                before_target_price, after_target_price, start_price = get_target_price(code, 0.5)
                current_price = get_current_price(code)
                #print("현재가 : ", current_price)
                #ma15 = get_ma15("KRW-BTC")
                #if target_price < current_price and ma15 < current_price:

                # 금일 매수한 종목은 매수하지 않습니다.
                #if code in today_list: 
                #    continue

                # 매수로직
                #if upbitYn == 'N' and btc_close_price > 0 and buy_price < 30001:
                if upbitYn == 'N' and buy_price < today_krw:
                    if before_target_price < current_price < after_target_price:
                        predicted_close_price = predict_price(code, "2")
                        code_close_price = ((predicted_close_price/current_price)-1)*100
                        post_message(myToken,"#volvobit", "`대상종목 : "+ code + ", 예상수익율 : " + str(round(code_close_price,1)) + "%`")
                        if code_close_price > 5:
                            #print("매수시작 : ", code)
                            #print("[첫시작] 매수금액 : ", current_price)
                            profit_price = current_price
                            buy_krw = upbit.get_balance("KRW")
                            post_message(myToken,"#volvobit", "매수완료, 종목 : " + code + ", 잔고 : " + str(round(buy_krw,0)))
                            buy_result = upbit.buy_market_order(code, buy_krw-(buy_krw*0.1))
                            buy_code = code
                            today_list.append(code)
                            upbitYn = 'Y'
                
                # 매도로직
                if upbitYn == 'Y':
                    
                    while True:
                        
                        if not start_time < datetime.datetime.now() < end_time - datetime.timedelta(seconds=600):
                            break
                        
                        current_price = get_current_price(buy_code)
                        sell_price2, sell_price8 = get_sell_price(start_price)

                        # 1 : 매매가에서 1프로 하락했을 경우
                        # 시작가 <= 현재가 * 0.09
                        if current_price <= sell_price2:

                            sell_result = upbit.sell_market_order(buy_code, upbit.get_balance(buy_code))

                            time.sleep(5)
                            sell_krw = upbit.get_balance("KRW")

                            #print("-1% 매도시작")
                            #print("sell_krw : ", sell_krw)
                            post_message(myToken,"#volvobit", "매도완료, 종목 : " + buy_code + ", 잔고 : " + str(round(sell_krw,0)))
                            total_krw = buy_krw-sell_krw
                            buy_price = buy_price - total_krw
                            post_message(myToken,"#volvobit", "`노인정, 손해 : " + str(round(total_krw,0)) + "`")
                            post_message(myToken,"#volvobit", "`오늘 하루 현재수익 : " + str(round(buy_price,0)) + "`")

                            upbitYn = 'N'
                            buy_code = ''
                            sell_krw = 0
                            total_krw = 0
                            profit_price = 0
                            break

                        if sell_price8 <= current_price:

                            # 현재가 < 이익금액
                            if current_price < profit_price:

                                sell_result = upbit.sell_market_order(buy_code, upbit.get_balance(buy_code))

                                time.sleep(10)
                                sell_krw = upbit.get_balance("KRW")

                                #print("승 매도시작")
                                #print("sell_krw : ", sell_krw)
                                post_message(myToken,"#volvobit", "매도완료, 종목 : " + buy_code + ", 잔고 : " + str(round(sell_krw,0)))
                                total_krw = sell_krw-buy_krw
                                buy_price = buy_price + total_krw
                                post_message(myToken,"#volvobit", "`유야호, 이익 : " + str(round(total_krw,0)) + "`")
                                post_message(myToken,"#volvobit", "`오늘 하루 현재수익 : " + str(round(buy_price,0)) + "`")

                                upbitYn = 'N'
                                buy_code = ''
                                sell_krw = 0
                                total_krw = 0
                                profit_price = 0                            

                                if buy_price > today_krw:
                                    breakYn = 'Y'
                                    post_message(myToken,"#volvobit", "`목표달성!!! $축$ 내일 뵙겠습니다.`")

                                break
                            else:
                                profit_price = current_price
                                #print("[담는중] 이익금액 : ", profit_price)
                                
                        time.sleep(1)
                        
            else:
                                    
                if len(buy_code) > 0:
                    sell_result = upbit.sell_market_order(buy_code, upbit.get_balance(buy_code))
       
                    sell_krw = upbit.get_balance("KRW")
                    post_message(myToken,"#volvobit", "정리매도, 종목 : " + buy_code + ", 잔고 : " + str(round(sell_krw,0)))
                    
                    if buy_krw > sell_krw:
                        total_krw = buy_krw-sell_krw
                        buy_price = buy_price - total_krw
                        post_message(myToken,"#volvobit", "`노인정, 손해 : " + str(round(total_krw,0)) + "`")
                        post_message(myToken,"#volvobit", "`오늘 하루 현재수익 : " + str(round(buy_price,0)) + "`")
                    else:
                        total_krw = sell_krw-buy_krw
                        buy_price = buy_price + total_krw
                        post_message(myToken,"#volvobit", "`유야호, 이익 : " + str(round(total_krw,0)) + "`")
                        post_message(myToken,"#volvobit", "`오늘 하루 현재수익 : " + str(round(buy_price,0)) + "`")
                        
                if startYn == 'Y':
                    total_krw = upbit.get_balance("KRW")
                    today_krw = total_krw*0.1
                    btc_start_price = get_current_price("KRW-BTC")
                    post_message(myToken,"#volvobit", "전일자 종가, 비트코인 : " + str(round(btc_start_price,0)))
                    post_message(myToken,"#volvobit", "`아자아자!! 오늘 하루 파이팅!!!`")
                    symbol_list = get_code_list()
                    startYn = 'N'

                today_list = []
                upbitYn = 'N'
                breakYn = 'N'
                sell_krw = 0
                total_krw = 0
                profit_price = 0
                buy_price = 0
                buy_code = ''

        time.sleep(1)

    except Exception as e:
        #print(e)
        #post_message(myToken,"#비트", e)
        time.sleep(1)
