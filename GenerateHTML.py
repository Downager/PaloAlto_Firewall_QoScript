# coding=UTF8
import datetime

import configparser
import pandas as pd


# 增加時間戳
def timestamp():
    ts = '[' + datetime.datetime.now().strftime("%m-%d %H:%M:%S") + '] '
    return ts


# 讀取 config.ini
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf8')

# 讀取超流鎖定參數 [OverFlow Setting]
DaysofOverFlow = int(config['OverFlow Setting']['DaysofOverFlow'])
DaysofLock = int(config['OverFlow Setting']['DaysofLock'])
# DaysofKeepHTML = 超流 N 天 + 鎖定 O 天
DaysofKeepHTML = DaysofOverFlow + DaysofLock

# 設置只輸出到小數第二位
pd.set_option('precision', 2)

# 讀取 report.csv，取得歷史超流名單
dfReport = pd.read_csv('report.csv', names=['日期', '使用者名稱', '總流量', '下載量', '上傳量'])
dfReport['日期'] = pd.to_datetime(dfReport['日期'])
# 只取得昨日資料
readdate = pd.Timestamp(datetime.date.today() - datetime.timedelta(days=1))
dfReport = (dfReport[dfReport['日期'] == readdate])

print(timestamp(), 'HTML - 讀取 report.csv: \n', dfReport)

# nowlock.csv，超流使用者名稱
dfLocked = pd.read_csv('nowlock.csv', names=['鎖定日期', '使用者名稱'])
print(timestamp(), 'HTML - 讀取 nowlock.csv: \n', dfLocked)
# 將 nowlock.csv 與昨日超流資訊合併
dfReport = dfReport.merge(dfLocked, left_on='使用者名稱', right_on='使用者名稱',
                          sort=False, how='outer')
print(timestamp(), 'HTML - Merge report.csv & nowlock.csv: \n', dfReport)


# Convert Bytes to GigaBytes
dfReport['總流量'] = dfReport['總流量'] / (1000 ** 3)
dfReport['下載量'] = dfReport['下載量'] / (1000 ** 3)
dfReport['上傳量'] = dfReport['上傳量'] / (1000 ** 3)

# 將昨日超流資料寫入 generateHTML.csv（mode a: 在尾端新增）
f = open('generateHTML.csv', 'a')
f.write(pd.DataFrame.to_csv(dfReport, index=False, header=False))
f.close()

# 移除 generate.csv 超過 N + O 天前的資料（連續超流 N 天 + 鎖定 O 天）
dfRemoved = pd.read_csv('generateHTML.csv', names=['日期', '使用者名稱', '總流量', '下載量', '上傳量', '鎖定日期'])
dfRemoved['日期'] = pd.to_datetime(dfRemoved['日期'])
# 保留日期 = 今天日期 - DaysofKeepHTML（連續超流 N 天 + 鎖定 O 天）
keepdate = pd.Timestamp(datetime.date.today() - datetime.timedelta(days=DaysofKeepHTML))
dfRemoved = (dfRemoved[dfRemoved['日期'] >= keepdate])
f = open('generateHTML.csv', 'w')
f.write(pd.DataFrame.to_csv(dfRemoved, index=False, header=False))
f.close()

# 讀取 generateHTML.csv，產生 OverFlow.html
dfHTML = pd.read_csv('generateHTML.csv', names=['超流日期', '使用者名稱', '總流量(GB)', '下載量(GB)', '上傳量(GB)', '鎖定日期'])
f = open('index.html', 'w')
f.write(pd.DataFrame.to_html(dfHTML, index=False))
f.close()

print(timestamp(), '/var/www/public/index.html 已產生 \n', dfHTML)
