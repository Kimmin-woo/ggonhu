import time
import pyupbit
import datetime
import requests

# K뱅크 값
access = "cHJjMwVsbxZjr98OVPA2smVsvAGjg7wpP5BIeQuC"
secret = "AXh3HuuyfYsOZipUOjkZ0daZvnD0lZVSrX1cR7Sp"
myToken = "xoxb-1730814337234-1985015754823-S0XCF6goocaijlAs3jRbMh27"

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
    # 매수목표가 = 시작가 * 1.049
    before_target_price = df.iloc[0]['close'] * 1.049
    # 매수목표가 = 시작가 * 1.052
    after_target_price = df.iloc[0]['close'] * 1.052 
    # 종가(시작가)
    start_price = df.iloc[0]['close']

    return before_target_price, after_target_price, start_price

def get_sell_price(ticker, spay):
    """매도 목표가 조회"""
    # 매도목표가 = 시작가 * 1.03
    sell_price2 = spay * 1.03
    # 매도목표가 = 시작가 * 1.09
    sell_price9 = spay * 1.09

    return sell_price2, sell_price9

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
bought_list = []
buy_list = []
for ticker in tickers:
    if 'KRW-' in ticker:
        try:
            df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
            print(type(df.iloc[0]['close']))
        except Exception as ex:
            df = None

        if df is not None:
            if 100 < df.iloc[0]['close'] < 1000:
                symbol_list.append(ticker)

###################################
# 시작 메세지 슬랙 전송
###################################
post_message(myToken,"#volvobit", "볼보-비트 자동매매 시작합니다.")

###################################
# 자동매매로직
###################################
upbitYn = 'N'
while True:
    try:
        #now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)
        #print(now)

        for code in symbol_list:
            #print("code : ", code)

            #print("start_time : ", start_time)
            #print("datetime.datetime.now() : ", datetime.datetime.now())
            #print("end_time : ", end_time - datetime.timedelta(seconds=10))

            # 오늘 9시 < 현재 < 내일 8시59분
            if start_time < datetime.datetime.now() < end_time - datetime.timedelta(seconds=10):

                before_target_price, after_target_price, start_price = get_target_price(code, 0.5)
                current_price = get_current_price(code)
                #print("현재가 : ", current_price)
                #ma15 = get_ma15("KRW-BTC")
                #if target_price < current_price and ma15 < current_price:

                # 매도로직
                if any(code in volvo for volvo in buy_list):

                    sell_price2, sell_price9 = get_sell_price(code, start_price)
                    # 시작가 <= 현재가 * 1.03 or 시작가 * 1.09 >= 현재가
                    if current_price <= sell_price2 or current_price >= sell_price9:

                        if current_price <= sell_price2:
                            print("3% 매도시작")
                            post_message(myToken,"#volvobit", "`3% 매도`")

                        if current_price >= sell_price9:
                            print("9% 매도시작")
                            post_message(myToken,"#volvobit", "`9% 매도`")

                        sell_result = upbit.sell_market_order(code, upbit.get_balance(code))
                        post_message(myToken,"#volvobit", "매도완료, 종목 : " + code + ", 가격 : " + str(current_price))
                        upbitYn = 'N'

                        index = 0
                        for minwoo in buy_list:    
                            if minwoo == code:
                                del buy_list[index]
                            index = index + 1      

                # 금일 매수한 종목은 매수하지 않습니다.
                if code in bought_list: 
                    continue

                # 매수로직
                if upbitYn == 'N':
                    if before_target_price < current_price < after_target_price:
                        print("매수시작 : ", code)
                        krw = upbit.get_balance("KRW")
                        print("krw : ", krw)
                        buy_result = upbit.buy_market_order(code, krw-3000)
                        post_message(myToken,"#volvobit", "매수완료, 종목 : " + code + ", 가격 : " + str(current_price))
                        buy_list.append(code)
                        bought_list.append(code)
                        upbitYn = 'Y'                

            else:
                bought_list = []

        time.sleep(1)

    except Exception as e:
        #print(e)
        #post_message(myToken,"#비트", e)
        time.sleep(1)