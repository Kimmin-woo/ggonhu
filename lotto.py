import os, sys, ctypes
import time
import datetime
import calendar
import requests
import random

myToken = "xoxb-1730814337234-1743490164897-5GZq1QytqcBK6q1SqIUmlMj4"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

###################################
# 변수선언
###################################
curr_date = datetime.datetime.today()

###################################
# 시작 메세지 슬랙 전송
###################################
post_message(myToken,"#lotto", "$일확천금$ 오늘은 "+ calendar.day_name[curr_date.weekday()] + "입니다.
post_message(myToken,"#lotto", "로또 자동번호 생성 시작합니다.")

###################################
# 자동번호 생성
###################################
post_message(myToken,"#lotto", "`미리 축하합니다.`")
post_message(myToken,"#lotto", "라푼젤 당첨번호 :" + str(sorted(random.sample(range(1,46),6))))
post_message(myToken,"#lotto", "가가멜 당첨번호 :" + str(sorted(random.sample(range(1,46),6))))
post_message(myToken,"#lotto", "버즈 당첨번호 :" + str(sorted(random.sample(range(1,46),6))))
post_message(myToken,"#lotto", "쥬디 당첨번호 :" + str(sorted(random.sample(range(1,46),6))))
post_message(myToken,"#lotto", "찰스 당첨번호 :" + str(sorted(random.sample(range(1,46),6))))
post_message(myToken,"#lotto", "`앞날은 꽃길만 걸으세요.`")
sys.exit(0)

"""
while True:
    try:
        t_now = datetime.datetime.now()
        t_start = t_now.replace(hour=10, minute=5, second=0, microsecond=0)
        t_end = t_now.replace(hour=10, minute=5, second=2, microsecond=0)

        if t_start < datetime.datetime.now() < t_end:
            post_message(myToken,"#lotto", "$일확천금$ 로또 자동번호 생성 시작합니다.")
            post_message(myToken,"#lotto", "`미리 축하합니다.`")
            post_message(myToken,"#lotto", "은진b 당첨번호 : " + str(random.sample(range(1,46),7)))
            post_message(myToken,"#lotto", "상현b 당첨번호 : " + str(random.sample(range(1,46),7)))
            post_message(myToken,"#lotto", "민우 당첨번호 : " + str(random.sample(range(1,46),7)))
            post_message(myToken,"#lotto", "효길 당첨번호 : " + str(random.sample(range(1,46),7)))
            post_message(myToken,"#lotto", "`앞날은 꽃길만 걸으세요.`")

    except Exception as e:
        time.sleep(1)
"""
