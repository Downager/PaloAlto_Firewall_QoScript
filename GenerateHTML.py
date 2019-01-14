# coding=UTF8
import pandas as pd
import datetime

# 設置只輸出到小數第二位
pd.set_option('precision', 2)

# 讀取 report.csv，取得歷史超流名單
dfReport = pd.read_csv('report.csv', names=['日期', '使用者名稱', '總流量', '下載量', '上傳量'])
dfReport['日期'] = pd.to_datetime(dfReport['日期'])
# 只取得昨日資料
readdate = pd.Timestamp(datetime.date.today() - datetime.timedelta(days=1))
dfReport = (dfReport[dfReport['日期'] == readdate])

print('HTML - 讀取 report.csv: \n', dfReport)

# nowlock.csv，超流使用者名稱
dfLocked = pd.read_csv('nowlock.csv', names=['鎖定日期', '使用者名稱'])
print('HTML - 讀取 nowlock.csv: \n', dfLocked)
dfReport = dfReport.merge(dfLocked, left_on='使用者名稱', right_on='使用者名稱', 
                          sort=False, how='outer')
print('HTML - Merge report.csv & nowlock.csv: \n', dfReport)


# Convert Bytes to GigaBytes
dfReport['總流量'] = dfReport['總流量'] / (1000 ** 3)
dfReport['下載量'] = dfReport['下載量'] / (1000 ** 3)
dfReport['上傳量'] = dfReport['上傳量'] / (1000 ** 3)

# 將昨日超流資料寫入 generateHTML.csv（mode a: 在尾端新增）
f = open('generateHTML.csv', 'a')
f.write(pd.DataFrame.to_csv(dfReport, index=False, header=False))
f.close()

# 移除 generate.csv 超過 N + M 天前的資料（連續超流 N 天 + 鎖定 M 天）
dfRemoved = pd.read_csv('generateHTML.csv', names=['日期', '使用者名稱', '總流量', '下載量', '上傳量', '鎖定日期'])
dfRemoved['日期'] = pd.to_datetime(dfRemoved['日期'])
# 若連續超流日數 or 鎖定日數有修改，請調整 days=6 為 N + M 天
keepdate = pd.Timestamp(datetime.date.today() - datetime.timedelta(days=6))
dfRemoved = (dfRemoved[dfRemoved['日期'] >= keepdate])
f = open('generateHTML.csv', 'w')
f.write(pd.DataFrame.to_csv(dfRemoved, index=False, header=False))
f.close()

# 讀取 generateHTML.csv，產生 OverFlow.html
dfHTML = pd.read_csv('generateHTML.csv', names=['超流日期', '使用者名稱', '總流量(GB)', '下載量(GB)', '上傳量(GB)', '鎖定日期'])
f = open('/var/www/public/index.html', 'w')
f.write(pd.DataFrame.to_html(dfHTML, index=False))
f.close()

print('/var/www/public/index.html 已產生 \n', dfHTML)
