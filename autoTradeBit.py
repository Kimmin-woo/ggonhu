import time
import pyupbit
import datetime
import requests

# K뱅크 값
access = "cHJjMwVsbxZjr98OVPA2smVsvAGjg7wpP5BIeQuC"
secret = "AXh3HuuyfYsOZipUOjkZ0daZvnD0lZVSrX1cR7Sp"
myToken = "xoxb-1730814337234-1985015754823-o6zgknRzqsgVSAdQ032xUsT7"

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
    # 매수목표가 = 시작가 * 1.03
    before_target_price = df.iloc[0]['close'] * 1.03
    # 매수목표가 = 시작가 * 1.04
    after_target_price = df.iloc[0]['close'] * 1.04
    # 종가(시작가)
    start_price = df.iloc[0]['close']

    return before_target_price, after_target_price, start_price

def get_sell_price(ticker, spay):
    """매도 목표가 조회"""
    # 매도목표가 = 시작가 * 0.99
    sell_price2 = spay * 1
    # 매도목표가 = 시작가 * 1.07
    sell_price8 = spay * 1.07

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

###################################
# 로그인
###################################
upbit = pyupbit.Upbit(access, secret)
print("업비트 자동매매 시작합니다.")

###################################
# 대상종목 추출
###################################
tickers = pyupbit.get_tickers()
symbol_list = ['KRW-MLK','KRW-HIVE','KRW-CHZ','KRW-AXS','KRW-STX','KRW-SAND','KRW-GAS','KRW-AQT','KRW-UPP','KRW-META','KRW-FLOW','KRW-XEM','KRW-BAT']
buy_list = []
today_list = []
sell_krw = 0
buy_krw = 0
total_krw = 0
profit_price = 0
buy_price = 0
"""
for ticker in tickers:
    if 'KRW-' in ticker:
        try:
            df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
            print(type(df.iloc[0]['close']))
        except Exception as ex:
            df = None

        if df is not None:
            if 10 < df.iloc[0]['close'] < 10000:
                symbol_list.append(ticker)
"""
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
            if start_time < datetime.datetime.now() < end_time - datetime.timedelta(seconds=60):

                before_target_price, after_target_price, start_price = get_target_price(code, 0.5)
                current_price = get_current_price(code)
                #print("현재가 : ", current_price)
                #ma15 = get_ma15("KRW-BTC")
                #if target_price < current_price and ma15 < current_price:

                # 매도로직
                if any(code in volvo for volvo in buy_list):

                    sell_price2, sell_price8 = get_sell_price(code, start_price)

                    # 1 : 매매가에서 1프로 하락했을 경우
                    # 시작가 <= 현재가 * 0.09
                    if current_price <= sell_price2:

                        sell_result = upbit.sell_market_order(code, upbit.get_balance(code))

                        #time.sleep(10)
                        sell_krw = upbit.get_balance("KRW")

                        #print("-1% 매도시작")
                        #print("sell_krw : ", sell_krw)
                        post_message(myToken,"#volvobit", "매도완료, 종목 : " + code + ", 잔고 : " + str(round(sell_krw,0)))
                        total_krw = buy_krw-sell_krw
                        post_message(myToken,"#volvobit", "`, 손해 : " + str(round(total_krw,0)) + "`")

                        upbitYn = 'N'
                        buy_list = []
                        buy_krw = 0
                        sell_krw = 0
                        total_krw = 0
                        profit_price = 0
                        buy_price = 0

                    if  sell_price8 <= current_price:

                        # 현재가 < 이익금액
                        if current_price < profit_price:

                            sell_result = upbit.sell_market_order(code, upbit.get_balance(code))

                            time.sleep(10)
                            sell_krw = upbit.get_balance("KRW")

                            #print("승 매도시작")
                            #print("sell_krw : ", sell_krw)
                            post_message(myToken,"#volvobit", "매도완료, 종목 : " + code + ", 잔고 : " + str(round(sell_krw,0)))
                            total_krw = sell_krw-buy_krw
                            post_message(myToken,"#volvobit", "`겸손, 이익 : " + str(round(total_krw,0)) + "`")

                            upbitYn = 'N'
                            buy_list = []
                            buy_krw = 0
                            sell_krw = 0
                            total_krw = 0
                            profit_price = 0
                            buy_price = 0

                        else:
                            profit_price = current_price
                            #print("[담는중] 이익금액 : ", profit_price)                            

                # 금일 매수한 종목은 매수하지 않습니다.
                if code in today_list: 
                    continue
                
                # 매수로직
                if upbitYn == 'N':
                    if before_target_price < current_price < after_target_price:
                        #print("매수시작 : ", code)
                        #print("[첫시작] 매수금액 : ", current_price)
                        buy_price = current_price
                        profit_price = current_price
                        buy_krw = upbit.get_balance("KRW")
                        post_message(myToken,"#volvobit", "매수완료, 종목 : " + code + ", 잔고 : " + str(round(buy_krw,0)))
                        buy_result = upbit.buy_market_order(code, buy_krw-(buy_krw*0.1))
                        buy_list.append(code)
                        today_list.append(code)
                        upbitYn = 'Y'
                   
            else:
                today_list = []
                
                if any(code in volvo for volvo in buy_list):
                    sell_result = upbit.sell_market_order(code, upbit.get_balance(code))

                    upbitYn = 'N'
                    buy_list = []
                    buy_krw = 0
                    sell_krw = 0
                    total_krw = 0
                    profit_price = 0
                    buy_price = 0

        time.sleep(1)

    except Exception as e:
        #print(e)
        #post_message(myToken,"#비트", e)
        time.sleep(1)
