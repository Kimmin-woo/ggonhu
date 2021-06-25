import os, sys, ctypes
import win32com.client
import win32event
from datetime import datetime
from slacker import Slacker
import time, calendar

slack = Slacker('xoxb-1730814337234-1743490164897-oE7ea6vwwftsSM4IlhOBXPcj')

def dbgout(message):
    """인자로 받은 문자열을 파이썬 셸과 슬랙으로 동시에 출력한다."""
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
    strbuf = datetime.now().strftime('[%m/%d %H:%M:%S] ') + message
    slack.chat.post_message('#볼보2', strbuf)

def printlog(message, *args):
    """인자로 받은 문자열을 파이썬 셸에 출력한다."""
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message, *args)
 
# 크레온 플러스 공통 OBJECT
cpCodeMgrName = win32com.client.Dispatch('CpUtil.CpStockCode')
cpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
cpTradeUtil = win32com.client.Dispatch('CpTrade.CpTdUtil')
cpStock = win32com.client.Dispatch('DsCbo1.StockMst')
cpOhlc = win32com.client.Dispatch('CpSysDib.StockChart')
cpBalance = win32com.client.Dispatch('CpTrade.CpTd6033')
cpCash = win32com.client.Dispatch('CpTrade.CpTdNew5331A')
cpOrder = win32com.client.Dispatch('CpTrade.CpTd0311')  
cpCodeList = win32com.client.Dispatch('CpUtil.CpCodeMgr')  

def check_creon_system():
    """크레온 플러스 시스템 연결 상태를 점검한다."""
    # 관리자 권한으로 프로세스 실행 여부
    if not ctypes.windll.shell32.IsUserAnAdmin():
        printlog('check_creon_system() : admin user -> FAILED')
        return False
 
    # 연결 여부 체크
    if (cpStatus.IsConnect == 0):
        printlog('check_creon_system() : connect to server -> FAILED')
        return False
 
    # 주문 관련 초기화 - 계좌 관련 코드가 있을 때만 사용
    if (cpTradeUtil.TradeInit(0) != 0):
        printlog('check_creon_system() : init trade -> FAILED')
        return False
    return True

def get_current_price(code):
    """인자로 받은 종목의 현재가, 매수호가, 고가, 거래량를 반환한다."""
    cpStock.SetInputValue(0, code)  # 종목코드에 대한 가격 정보

    remainCount = cpStatus.GetLimitRemainCount(1)   #시세제한함수
    if remainCount <= 0 :
        # printlog('시세 연속 조회 제한 회피를 위해 sleep', cpStatus.LimitRequestRemainTime/900)
        time.sleep(cpStatus.LimitRequestRemainTime/900)

    cpStock.BlockRequest()

    item = {}
    item['cur_price'] = cpStock.GetHeaderValue(11) # 현재가
    item['high'] = cpStock.GetHeaderValue(14)      # 고가
    item['low'] = cpStock.GetHeaderValue(15)      # 저가
    item['ask'] =  cpStock.GetHeaderValue(16)      # 매수호가
    item['vol'] =  cpStock.GetHeaderValue(18)      # 거래량
    return item['cur_price'], item['ask'], item['high'], item['vol'], item['low']

def get_code_list(codeList):
    """인자로 받은 종목의 전일가 1000~10000원의 가격만 list."""
    symbol_list = []
    printlog('전체종목수 : ', len(codeList))

    for i, code in enumerate(codeList):
        # print(i, code, secondCode, stdPrice, name)
        # 시작가
        stdPrice = cpCodeList.GetStockStdPrice(code)
        
        # 1000원과 10000원 사이의 종목만 거래합니다.
        if 1000 < stdPrice < 6000:
            symbol_list.append({'sym': code, 'spay': stdPrice})

    printlog('총(', i ,') 대상종목수 : ', len(symbol_list),'건')
    return symbol_list

def get_all_balance():
    """전체종목의 종목명과 수량을 반환한다."""
    cpTradeUtil.TradeInit()
    acc = cpTradeUtil.AccountNumber[0]      # 계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
    cpBalance.SetInputValue(0, acc)         # 계좌번호
    cpBalance.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
    cpBalance.SetInputValue(2, 50)          # 요청 건수(최대 50)
    cpBalance.BlockRequest()     
    
    dbgout('계좌명: ' + str(cpBalance.GetHeaderValue(0)))
    dbgout('결제잔고수량 : ' + str(cpBalance.GetHeaderValue(1)))
    dbgout('평가금액: ' + str(cpBalance.GetHeaderValue(3)))
    dbgout('평가손익: ' + str(cpBalance.GetHeaderValue(4)))
    dbgout('종목수: ' + str(cpBalance.GetHeaderValue(7)))
    
    stocks = []
    for i in range(cpBalance.GetHeaderValue(7)):
        stock_code = cpBalance.GetDataValue(12, i)  # 종목코드
        stock_name = cpBalance.GetDataValue(0, i)   # 종목명
        stock_qty = cpBalance.GetDataValue(15, i)   # 수량

        dbgout(str(i+1) + '번째 ' + stock_code + '(' + stock_name + ')' 
            + ' : ' + str(stock_qty) + "건")
        stocks.append({'code': stock_code, 'name': stock_name, 'qty': stock_qty})

    return stocks
        
def get_code_balance(code, val):
    """인자로 받은 종목의 종목명과 수량을 반환한다."""
    cpTradeUtil.TradeInit()
    acc = cpTradeUtil.AccountNumber[0]      # 계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
    cpBalance.SetInputValue(0, acc)         # 계좌번호
    cpBalance.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
    cpBalance.SetInputValue(2, 50)          # 요청 건수(최대 50)
    cpBalance.BlockRequest()     

    stocks = []
    for i in range(cpBalance.GetHeaderValue(7)):
        stock_code = cpBalance.GetDataValue(12, i)  # 종목코드
        stock_name = cpBalance.GetDataValue(0, i)   # 종목명
        stock_qty = cpBalance.GetDataValue(15, i)   # 수량
        if stock_code == code:
            if val == '1':
                stocks.append({'code': stock_code, 'name': stock_name, 'qty': stock_qty})
            if val == '2':  
                return stock_name, stock_qty
    if val == '1':
        return stocks
    else:
        stock_name = cpCodeMgrName.CodeToName(code)
        return stock_name, 0

def get_current_cash():
    """증거금 100% 주문 가능 금액을 반환한다."""
    cpTradeUtil.TradeInit()
    acc = cpTradeUtil.AccountNumber[0]      # 계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
    cpCash.SetInputValue(0, acc)            # 계좌번호
    cpCash.SetInputValue(1, accFlag[0])     # 상품구분 - 주식 상품 중 첫번째
    cpCash.BlockRequest() 
    return cpCash.GetHeaderValue(9) # 증거금 100% 주문 가능 금액

def get_target7_price(spay):
    """매수 목표가를 반환한다."""
    try:
        # 매수목표가 = 시작가 * 1.075
        target7_price = spay * 1.075

        return target7_price
    except Exception as ex:
        dbgout("`get_target7_price() -> exception! " + str(ex) + "`")
        return None

def get_target6_price(spay):
    """매수 목표가를 반환한다."""
    try:
        target0_price = spay * 0.99
        target1_price = spay * 1.01
        target6_price = spay * 0.975

        return target0_price, target1_price, target6_price
    except Exception as ex:
        dbgout("`get_target7_price() -> exception! " + str(ex) + "`")
        return None

def get_before_target_price(spay):
    """매수 목표가를 반환한다."""
    try:
        # 매수목표가 = 시작가 * 1.059
        before_target_price = spay * 1.059

        return before_target_price
    except Exception as ex:
        dbgout("`get_before_target_price() -> exception! " + str(ex) + "`")
        return None

def get_after_target_price(spay):
    """매수 목표가를 반환한다."""
    try:
        # 매수목표가 = 시작가 * 1.062
        after_target_price = spay * 1.062

        return after_target_price
    except Exception as ex:
        dbgout("`get_after_target_price() -> exception! " + str(ex) + "`")
        return None

def get_sell_price(spay, val):
    """매도 목표가를 반환한다."""
    try:
        if val == '1':
            # 매도목표가 = 시작가 * 1.042
            sell_price2 = spay * 1.042
            # 매도목표가 = 시작가 * 1.075
            sell_price7 = spay * 1.075
        else:
            # 매도목표가 = 시작가 * 0.98
            sell_price2 = spay * 0.98
            # 매도목표가 = 시작가 * 1.025
            sell_price7 = spay * 1.025

        return sell_price2, sell_price7
    except Exception as ex:
        dbgout("`get_sell_price() -> exception! " + str(ex) + "`")
        return None

def hyesu_etf(code, spay):
    """인자로 받은 종목을 자동매매한다."""
    try:
        global bought_list # 함수 내에서 값 변경을 하기 위해 global로 지정
        global sell_list   # 함수 내에서 값 변경을 하기 위해 global로 지정
        global buy_list    # 함수 내에서 값 변경을 하기 위해 global로 지정

        # 금일 매도한 종목은 매수하지 않습니다.
        if code in sell_list: 
            return False

        # get_current_price : 현재가격
        current_price, ask_price, high_price, vol_value, low_price = get_current_price(code)

        # 매수종목이 매수가의 2.7프로이하, 2.5프로이상일 경우
        if any(code in volvo['sym'] for volvo in buy_list):

            # get_sell_price : 매도목표가
            # sell_price2    : 매수금액의 2프로   떨어진 경우
            # sell_price7    : 매수금액의 1.5프로 올라간 경우
            sell_price2, sell_price7 = get_sell_price(spay, "1")

            # 시작가 <= 현재가 * 1.042 or 시작가 * 1.075 >= 현재가
            if current_price <= sell_price2 or current_price >= sell_price7:   
                
                if current_price <= sell_price2:   
                    dbgout('4.2% 매도종목 : '+ str(code) + ',현재가(' + str(current_price) + '),매도목표가(' + str(sell_price2) + '),거래량(' + str(vol_value) + ')')

                    # 해당 종목을 최유리 FOK로 매도
                    sell_code(code, '2', ask_price)

                if current_price >= sell_price7:   
                    dbgout('7.5% 매도종목 : '+ str(code) + ',현재가(' + str(current_price) + '),매도목표가(' + str(sell_price7) + '),거래량(' + str(vol_value) + ')')
                    
                    # 해당 종목을 최유리 FOK로 매도
                    sell_code(code, '7', ask_price)
                

                # 매도완료리스트 : 매도 후 매수를 안하기 위함
                sell_list.append(code)

                # 매매리스트에서 매도한 종목을 삭제
                index = 0
                for heysu in buy_list:
                    if heysu['sym'] == code:
                        del buy_list[index]
                    
                    index = index + 1

                dbgout("`매도완료!!`")
                               
                return False

        # PM 14:30 < 현재시간
        if t_startStop < datetime.now():
            return False

        # 금일 매수한 종목은 매수하지 않습니다.
        if code in bought_list: 
            return False

        # 매수할 수량이 0일 경우 매수하지 않습니다.
        buy_qty = 0        # 매수할 수량 초기화
        if ask_price > 0:  # 매수호가가 존재하면   
            buy_qty = buy_amount / ask_price            
        if buy_qty < 1:    
            return False

        # get_after_target_price/get_before_target_price : 매수목표가(시작가의 5.9~6.2%)
        after_target_price  = get_after_target_price(spay)
        before_target_price = get_before_target_price(spay)
        target7_price       = get_target7_price(spay)

        # 현재가 매수목표가보다 높고(5.9~6.2%사이)
        if before_target_price < current_price < after_target_price:
            
            # 현재종목의 고가 < 시작가의 7.5프로
            if high_price < target7_price:

                # printlog('매수함수시작')         
                # 최유리 FOK 매수 주문 설정
                # 최유리 : 당장 가장 유리하게 매매할 수 있는 가격                
                cpTradeUtil.TradeInit()
                acc = cpTradeUtil.AccountNumber[0]      # 계좌번호
                accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체,1:주식,2:선물/옵션                
                cpOrder.SetInputValue(0, "2")           # 2: 매수
                cpOrder.SetInputValue(1, acc)           # 계좌번호
                cpOrder.SetInputValue(2, accFlag[0])    # 상품구분 - 주식 상품 중 첫번째
                cpOrder.SetInputValue(3, code)          # 종목코드
                cpOrder.SetInputValue(4, buy_qty)       # 매수할 수량
                cpOrder.SetInputValue(7, "2")           # 주문조건 0:기본, 1:IOC(체결 후 남은 수량취소), 2:FOK(전량 체결되지 않으면 주문자체를 취소)
                cpOrder.SetInputValue(8, "12")          # 주문호가 1:보통, 3:시장가
                                                        # 5:조건부, 12:최유리, 13:최우선 
                # 매수 주문 요청
                ret = cpOrder.BlockRequest() 
                
                printlog('매수 요청종목코드 ->', code, '요청수량 ->',buy_qty)
                printlog('매수 주문 요청(두근두근) ->', ret)
                
                if ret == 4:
                    remain_time = cpStatus.LimitRequestRemainTime
                    printlog('주의: 연속 주문 제한에 걸림. 대기 시간:', remain_time/1000)
                    time.sleep(remain_time/1000) 
                    return False

                rqStatus = cpOrder.GetDibStatus()
                if rqStatus != 0:
                    errMsg = cpOrder.GetDibMsg1()
                    printlog("주문 실패: ", rqStatus, errMsg)
                    
                time.sleep(1)

                # 종목명/수량 조회
                stock_name, bought_qty = get_code_balance(str(code), "2")
                
                #printlog('현금주문 가능금액  :', buy_amount)
                #printlog('보유한 종목과 수량 :', stock_name, bought_qty)

                # 구매수량 있다면 알림 보낸다
                if bought_qty > 0:
                    bought_list.append(code)
                    buy_list.append({'sym': code, 'spay': spay})
                    dbgout(str(stock_name) + "는 현재가(" + str(current_price) + "),매수목표가(" + str(round(before_target_price, 0)) +"~"+ str(round(after_target_price, 0))+ "),거래량(" + str(vol_value) + ")")
                    dbgout("`[볼보2] "+ str(stock_name) + "(" + str(code) + ") -> " + str(bought_qty) + "건 매수완료!" + "`")

    except Exception as ex:
        dbgout("`hyesu_etf("+ str(code) + ") -> exception! " + str(ex) + "`")

def minwoo_etf(code, spay):
    """인자로 받은 종목을 자동매도한다."""
    try:
        # 함수 내에서 값 변경을 하기 위해 global로 지정
        global sell_list
        global buy_list

        # get_current_price : 현재가격
        current_price, ask_price, high_price, vol_value, low_price = get_current_price(code)

        # get_sell_price : 매도목표가
        # sell_price2    : 매수금액의 2프로   떨어진 경우
        # sell_price7    : 매수금액의 1.5프로 올라간 경우
        sell_price2, sell_price7 = get_sell_price(spay, "1")

        # 시작가 <= 현재가 * 1.042 or 시작가 * 1.075 >= 현재가
        if current_price <= sell_price2 or current_price >= sell_price7:   
            
            if current_price <= sell_price2:   
                dbgout('4.2% 매도종목 : '+ str(code) + ',현재가(' + str(current_price) + '),매도목표가(' + str(sell_price2) + '),거래량(' + str(vol_value) + ')')

                # 해당 종목을 최유리 FOK로 매도
                sell_code(code, '2', ask_price)

            if current_price >= sell_price7:   
                dbgout('7.5% 매도종목 : '+ str(code) + ',현재가(' + str(current_price) + '),매도목표가(' + str(sell_price7) + '),거래량(' + str(vol_value) + ')')
                
                # 해당 종목을 최유리 FOK로 매도
                sell_code(code, '7', ask_price)
            

            # 매도완료리스트 : 매도 후 매수를 안하기 위함
            sell_list.append(code)

            # 매매리스트에서 매도한 종목을 삭제
            index = 0
            for heysu in buy_list:    
                if heysu['sym'] == code:
                    del buy_list[index]
                
                index = index + 1

            dbgout("`매도완료!!`")

    except Exception as ex:
        dbgout("`minwoo_etf("+ str(code) + ") -> exception! " + str(ex) + "`")

def chaeu_etf(code, spay):
    """인자로 받은 종목을 자동매매한다."""
    try:
        global bought_list # 함수 내에서 값 변경을 하기 위해 global로 지정
        global sell_list   # 함수 내에서 값 변경을 하기 위해 global로 지정
        global buy_list    # 함수 내에서 값 변경을 하기 위해 global로 지정

        # get_current_price : 현재가격
        current_price, ask_price, high_price, vol_value, low_price = get_current_price(code)

        # 매수종목이 매수가의 2.7프로이하, 2.5프로이상일 경우
        for volvo in buy_list:
            if code == volvo['sym']:
                # get_sell_price : 매도목표가
                # sell_price2    : 매수금액의 2프로   떨어진 경우
                # sell_price7    : 매수금액의 2프로 올라간 경우
                sell_price2, sell_price7 = get_sell_price(volvo['spay'], "2")
                
                # 시작가 <= 현재가 * 0.98 or 시작가 * 1.02 >= 현재가
                if current_price <= sell_price2 or current_price >= sell_price7:   
                    
                    if current_price <= sell_price2:   
                        dbgout('-2% 매도종목 : '+ str(code) + ',현재가(' + str(current_price) + '),매도목표가(' + str(sell_price2) + '),거래량(' + str(vol_value) + ')')

                        # 해당 종목을 최유리 FOK로 매도
                        sell_code(code, '2', ask_price)

                    if current_price >= sell_price7:   
                        time.sleep(30)
                        dbgout('2% 매도종목 : '+ str(code) + ',현재가(' + str(current_price) + '),매도목표가(' + str(sell_price7) + '),거래량(' + str(vol_value) + ')')
                        
                        # 해당 종목을 최유리 FOK로 매도
                        sell_code(code, '7', ask_price)

                    # 매도완료리스트 : 매도 후 매수를 안하기 위함
                    sell_list.append(code)

                    # 매매리스트에서 매도한 종목을 삭제
                    index = 0
                    for heysu in buy_list:
                        if heysu['sym'] == code:
                            del buy_list[index]
                        
                        index = index + 1

                    dbgout("`매도완료!!`")
                                
                    return False

        # PM 14:30 < 현재시간
        if t_startStop < datetime.now():
            return False

        # 금일 매수한 종목은 매수하지 않습니다.
        if code in bought_list: 
            return False

        # 보유종목수가 설정한종목수와 같으므로 더이상 매수하지 않습니다.
        if len(buy_list) == target_buy_count:
            return False

        # 매수할 수량이 0일 경우 매수하지 않습니다.
        buy_qty = 0        # 매수할 수량 초기화
        if ask_price > 0:  # 매수호가가 존재하면   
            buy_qty = buy_amount / ask_price            
        if buy_qty < 1:    
            return False

        # target0_price/target1_price/target6_price : 매수목표가(시작가의 0~1%)
        #target0_price, target1_price, target6_price = get_target6_price(spay)

        # 현재가 저가보다 높고(1~3%사이)
        if (low_price*1.01) < current_price < (low_price*1.03):
            
            close_price = ((spay/low_price)-1)*100
            # 저가가 시작가 2프로 떨어졌을 경우 and 고가 < 시작가
            if close_price > 1.9 and high_price < spay and vol_value > 999999 :

                # printlog('매수함수시작')         
                # 최유리 FOK 매수 주문 설정
                # 최유리 : 당장 가장 유리하게 매매할 수 있는 가격                
                cpTradeUtil.TradeInit()
                acc = cpTradeUtil.AccountNumber[0]      # 계좌번호
                accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체,1:주식,2:선물/옵션                
                cpOrder.SetInputValue(0, "2")           # 2: 매수
                cpOrder.SetInputValue(1, acc)           # 계좌번호
                cpOrder.SetInputValue(2, accFlag[0])    # 상품구분 - 주식 상품 중 첫번째
                cpOrder.SetInputValue(3, code)          # 종목코드
                cpOrder.SetInputValue(4, buy_qty)       # 매수할 수량
                cpOrder.SetInputValue(7, "2")           # 주문조건 0:기본, 1:IOC(체결 후 남은 수량취소), 2:FOK(전량 체결되지 않으면 주문자체를 취소)
                cpOrder.SetInputValue(8, "12")          # 주문호가 1:보통, 3:시장가
                                                        # 5:조건부, 12:최유리, 13:최우선 
                # 매수 주문 요청
                ret = cpOrder.BlockRequest() 
                
                printlog('매수 요청종목코드 ->', code, '요청수량 ->',buy_qty)
                printlog('매수 주문 요청(두근두근) ->', ret)
                
                if ret == 4:
                    remain_time = cpStatus.LimitRequestRemainTime
                    printlog('주의: 연속 주문 제한에 걸림. 대기 시간:', remain_time/1000)
                    time.sleep(remain_time/1000) 
                    return False

                rqStatus = cpOrder.GetDibStatus()
                if rqStatus != 0:
                    errMsg = cpOrder.GetDibMsg1()
                    printlog("주문 실패: ", rqStatus, errMsg)
                    
                time.sleep(1)

                # 종목명/수량 조회
                stock_name, bought_qty = get_code_balance(str(code), "2")
                
                #printlog('현금주문 가능금액  :', buy_amount)
                #printlog('보유한 종목과 수량 :', stock_name, bought_qty)

                # 구매수량 있다면 알림 보낸다
                if bought_qty > 0:
                    bought_list.append(code)
                    buy_list.append({'sym': code, 'spay': current_price})
                    dbgout(str(stock_name) + "는 현재가(" + str(current_price) + "),매수목표가(" + str(round(low_price*1.01, 0)) +"~"+ str(round(low_price*1.03, 0))+ "),거래량(" + str(vol_value) + ")")
                    dbgout("`[볼보2] "+ str(stock_name) + "(" + str(code) + ") -> " + str(bought_qty) + "건 매수완료!" + "`")

    except Exception as ex:
        dbgout("`hyesu_etf("+ str(code) + ") -> exception! " + str(ex) + "`")

def sell_code(code, val, ask_price):
    """선택한 종목을 최유리 지정가 FOK 조건으로 매도한다."""
    try:
        cpTradeUtil.TradeInit()
        acc = cpTradeUtil.AccountNumber[0]       # 계좌번호
        accFlag = cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션 
        hit = 0
        while True:    
            stocks = get_code_balance(str(code), "1") 
            total_qty = 0 
            for s in stocks:
                total_qty += s['qty'] 
            if total_qty == 0:
                return True
            for s in stocks:
                if s['qty'] != 0:           
                    cpOrder.SetInputValue(0, "1")           # 1:매도, 2:매수
                    cpOrder.SetInputValue(1, acc)           # 계좌번호
                    cpOrder.SetInputValue(2, accFlag[0])    # 주식상품 중 첫번째
                    cpOrder.SetInputValue(3, s['code'])     # 종목코드
                    cpOrder.SetInputValue(4, s['qty'])      # 매도수량
                    cpOrder.SetInputValue(7, "2")           # 조건 0:기본, 1:IOC(체결 후 남은 수량취소), 2:FOK(전량 체결되지 않으면 주문자체를 취소)
                    cpOrder.SetInputValue(8, "12")          # 호가 01:보통 12:최유리 13:최우선

                    # 최유리 FOK 매도 주문 요청
                    ret = cpOrder.BlockRequest()

                    printlog('최유리 FOK 매도', s['code'], s['name'], s['qty'], 
                        '-> cpOrder.BlockRequest() -> returned', ret)

                    if ret == 4:
                        remain_time = cpStatus.LimitRequestRemainTime
                        printlog('주의: 연속 주문 제한, 대기시간:', remain_time/1000)

                    if hit == 0:
                        dbgout("`[볼보2] "+ str(s['name']) + "(" + str(s['code']) + ") -> " + str(s['qty']) + "건 매도중.." + "`")
                        hit = hit + 1

            time.sleep(1)

    except Exception as ex:
        dbgout("sell_code() -> exception! " + str(ex))

def sell_all():
    """보유한 모든 종목을 최유리 지정가 IOC 조건으로 매도한다."""
    try:
        cpTradeUtil.TradeInit()
        acc = cpTradeUtil.AccountNumber[0]       # 계좌번호
        accFlag = cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션   
        while True:    
            stocks = get_all_balance() 
            total_qty = 0 
            for s in stocks:
                total_qty += s['qty'] 
            if total_qty == 0:
                return True
            for s in stocks:
                if s['qty'] != 0:                  
                    cpOrder.SetInputValue(0, "1")         # 1:매도, 2:매수
                    cpOrder.SetInputValue(1, acc)         # 계좌번호
                    cpOrder.SetInputValue(2, accFlag[0])  # 주식상품 중 첫번째
                    cpOrder.SetInputValue(3, s['code'])   # 종목코드
                    cpOrder.SetInputValue(4, s['qty'])    # 매도수량
                    cpOrder.SetInputValue(7, "1")         # 조건 0:기본, 1:IOC(체결 후 남은 수량취소), 2:FOK(전량 체결되지 않으면 주문자체를 취소)
                    cpOrder.SetInputValue(8, "12")        # 호가 12:최유리, 13:최우선 
                    # 최유리 IOC 매도 주문 요청
                    ret = cpOrder.BlockRequest()
                    printlog('최유리 IOC 매도', s['code'], s['name'], s['qty'], 
                        '-> cpOrder.BlockRequest() -> returned', ret)
                    if ret == 4:
                        remain_time = cpStatus.LimitRequestRemainTime
                        printlog('주의: 연속 주문 제한, 대기시간:', remain_time/1000)
                time.sleep(1)
            time.sleep(30)
    except Exception as ex:
        dbgout("sell_all() -> exception! " + str(ex))

if __name__ == '__main__': 
    try:
        
        # 전체종목리스트 조회(코스닥)
        codeList = cpCodeList.GetStockListByMarket(2)
        #printlog(len(codeList))
        #printlog("거래소 종목코드 : ", codeList)

        dbgout('`민우와혜수 [볼보2] 시작합니다.`')
        # 아래의 종목을 대상으로 매매시작합니다.
        # 제주은행     : A006220
        # 인터파크     : A035080
        # 우리금융지주 : A316140
        # symbol_list = ['A006220'
        #               ,'A035080'
        #               ,'A316140'
        #               ]
        # symbol_list = codeList # 거래소 전체종목 2021.02.16
        symbol_list = get_code_list(codeList) # 리스트 불러오기 2021.02.16
        bought_list = []       # 매수 완료된 종목 리스트
        sell_list = []         # 매도 완료된 종목 리스트
        buy_list = []          # 보유한 종목 리스트
        target_buy_count = 3   # 매수할 종목 수
        buy_percent = 0.33     # 주문가능금액비율

        printlog('크레온 접속 점검 :', check_creon_system())  # 크레온 접속 점검
        
        stocks = get_all_balance()             # 보유한 모든 종목 조회
        total_cash = int(get_current_cash())   # 100% 증거금 주문 가능 금액 조회
        buy_amount = (total_cash-(total_cash*0.1)) * buy_percent  # 종목별 주문 금액 계산
        
        printlog('100% 증거금 주문 가능 금액 :', total_cash)
        printlog('종목별 주문 비율 :', buy_percent)
        printlog('종목별 주문 금액 :', buy_amount)
        printlog('시작 시간 :', datetime.now().strftime('%m/%d %H:%M:%S'))
        soldout = False

        while True:
            t_now = datetime.now()
            t_7 = t_now.replace(hour=7, minute=0, second=0, microsecond=0)
            t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
            t_12 = t_now.replace(hour=12, minute=0, second=0, microsecond=0)

            # 매매시간
            t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
            t_start30 = t_now.replace(hour=9, minute=30, second=0, microsecond=0)
            # 매매중지시간
            t_startStop = t_now.replace(hour=14, minute=30, second=0, microsecond=0)            
            # 매도시간
            t_sell = t_now.replace(hour=15, minute=00, second=0, microsecond=0)
            # 프로그램종료시간
            t_exit = t_now.replace(hour=15, minute=20, second=0,microsecond=0)
            # 오늘날짜
            today = datetime.today().weekday()
            
            if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
                printlog('Today is', 'Saturday.' if today == 5 else 'Sunday.')
                sys.exit(0)

            # 어제 팔지못한 주식이 있다면?
            # AM 09:00 ~ AM 09:05
            if t_9 < t_now < t_start and soldout == False:

                dbgout('[볼보2] 전일 매도 못한 주식을 다 팝니다.')
                soldout = True

                # sell_all : 내가 가진 종목의 주식을 다 판다.
                sell_all()
            
            # AM 09:30 ~ PM 15:00
            if t_start30 < t_now < t_sell:  

                for chaeu in symbol_list:
                    # 민우 전략 시작합니다.
                    chaeu_etf(chaeu['sym'], chaeu['spay'])

            # PM 03:00 ~ PM 03:20 : 일괄 매도
            if t_sell < t_now < t_exit:  

                # 다판다
                if sell_all() == True:
                    dbgout('`[볼보2] 일괄매도하였습니다.`')
                    dbgout('`민우와혜수 [볼보2] 종료합니다.`')
                    sys.exit(0)

            if t_exit < t_now:  # PM 03:20 ~ :프로그램 종료

                dbgout('`민우와혜수 [볼보2] 종료합니다.`')
                sys.exit(0)

            if t_now < t_7:  # PM 07 이전:프로그램 종료
                  
                dbgout('`민우와혜수 [볼보2] 종료합니다.`')
                sys.exit(0)                

            time.sleep(3)

    except Exception as ex:
        dbgout('`main -> exception! ' + str(ex) + '`')
