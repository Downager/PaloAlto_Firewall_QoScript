# coding=UTF8
import datetime
import os
import time
import xml.etree.ElementTree as ET

import pandas as pd
import configparser
import requests
# disable https request warnings
requests.packages.urllib3.disable_warnings()


# 讀取 config.ini
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf8')

# 設定基本參數 [Default]
FireWallAddr = str(config['Default']['FireWallAddr'])
UserName = str(config['Default']['UserName'])
PassWord = str(config['Default']['PassWord'])

# 設定超流鎖定參數 [OverFlow Setting]
# Quota 將 GigaBytes 轉成 Bytes
Quota = (int(config['OverFlow Setting']['Quota']) * 1000000000)
TriggerDateRange = int(config['OverFlow Setting']['TriggerDateRange'])
TriggerCount = int(config['OverFlow Setting']['TriggerCount'])
DaysofLock = int(config['OverFlow Setting']['DaysofLock'])


# 增加時間戳
def timestamp():
    ts = '[' + datetime.datetime.now().strftime("%m-%d %H:%M:%S") + '] '
    return ts


# 定義 getKey 函式取得 API Key, 發出以下 URL 來取得包含 API Key 的 XML 格式, 再經由處理後回傳 key 字串
# https://<hostip>/api/?type=keygen&user=<username>&password=<password>
def getKey(username, password, hostip):

    paramsAPIkey = {'type': 'keygen', 'user': username, 'password': password}
    xmlAPIKey = requests.get(
        "https://" + hostip + "/api/", params=paramsAPIkey, verify=False)

    # 處理 XML 格式
    '''
    <response status = 'success'>
        <result>
        <key>LUFRPT1RN1VUdWhpdVl3N2tUUjJUSWdPbEdFYzZ1Q009enV1VUdra3pHaVJ2aUQxc3dmWThvc1oyU1FJazNTMnpQK2gzVCtxdjlKTT0=</key>
        </result>
    </response>
    '''
    root = ET.fromstring(xmlAPIKey.text)
    for result in root.findall('result'):
        key = result.find('key').text

    return key


# 定義 getJobid 函式取得 Report Job ID, 發出以下 URL 來取得包含 Job ID 的 XML 格式, 再經由處理後回傳 jobid 字串
# https://<hostip>/api/?type=report&async=yes&reporttype=<reporttype>&reportname=<reportname>&key=<key>
def getJobid(reporttype, reportname, key, hostip):

    paramsJobID = {
        'type': 'report',
        'async': 'yes',
        'reporttype': reporttype,
        'reportname': reportname,
        'key': key
    }
    xmlJobID = requests.get(
        "https://" + hostip + "/api/", params=paramsJobID, verify=False)

    root = ET.fromstring(xmlJobID.text)
    for result in root.findall('result'):
        jobid = result.find('job').text

    return jobid


# 定義 getReportstatus 函式取得 Report 目前狀態(reponse.status & job.status)
# 發出以下 URL 來取得包含 report status 的 XML 格式, 再經由處理後回傳 respStatus、jobStatus 字串
# https://<hostip>/api/?type=report&action=get&job-id=<jobid>&key=<key>
def getReportstatus(jobid, key, hostip):
    paramsReport = {
        'type': 'report',
        'action': 'get',
        'job-id': jobid,
        'key': key
    }
    xmlReport = requests.get(
        "https://" + hostip + "/api/", params=paramsReport, verify=False)

    root = ET.fromstring(xmlReport.text)
    # 查看 XML 報告 <response status="success"> 為 sucess or error
    for response in root.iter('response'):
        respStatus = response.get('status')

    # 查看 XML 報告 <response status="success"><result><job><status>ACT</status></job></result></response> 為 ACT or FIN
    for result in root.findall('result'):
        for job in result.findall('job'):
            jobStatus = job.find('status').text

    return respStatus, jobStatus


# 定義 getReport 函式取得 (day_of_receive_time, srcuser, bytes_received, bytes_sent)
# 發出以下 URL 來取得包含 report status 的 XML 格式, 再經由處理後回傳 respStatus、jobStatus 字串
# https://<hostip>/api/?type=report&action=get&job-id=<jobid>&key=<key>
def getReport(jobid, key, hostip):
    paramsReport = {
        'type': 'report',
        'action': 'get',
        'job-id': jobid,
        'key': key
    }
    xmlReport = requests.get(
        "https://" + hostip + "/api/", params=paramsReport, verify=False)

    root = ET.fromstring(xmlReport.text)

    # XML 結構內尋找 (day_of_receive_time, srcuser, int(bytes_total), int(bytes_received), int(bytes_sent)) 並回傳
    # <response><result><report><entry>{day_of_receive_time, srcuser, bytes_received, bytes_sent}</entry></report></result></response>
    day_of_receive_time = []
    srcuser = []
    bytes_total = []
    bytes_received = []
    bytes_sent = []
    for result in root.findall('result'):
        for report in result.findall('report'):
            for entry in report.findall('entry'):
                day_of_receive_time.append(entry.find('day-of-receive_time').text)
                srcuser.append(entry.find('srcuser').text)
                bytes_total.append(int(entry.find('bytes').text))
                bytes_received.append(int(entry.find('bytes_received').text))
                bytes_sent.append(int(entry.find('bytes_sent').text))

    return day_of_receive_time, srcuser, bytes_total, bytes_received, bytes_sent


# 定義 pushOverflowuser 函式將超流名單推送至 PA QoS Policy
# 發出以下 URL 來推送超流名單，並取得包含 report status 的 XML 格式, 再經由處理後回傳 resultStatus = sucess or error
# https://<hostip>/api/?type=config&action=edit&xpath=<xpath>&element=<'<source-user> + member + </source-user>'>&key=<key>
def pushOverflowuser(userlist, key, hostip):
    member = ""
    for user in userlist:
        member += "<member>" + user + "</member>"

    paramsPush = {
        'type': 'config',
        'action': 'edit',
        'xpath': "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/qos/rules/entry[@name='Rate limit-WiFi']/source-user",
        'element': "<source-user>" + member + "</source-user>",
        'key': key
    }
    xmlPush = requests.get(
        "https://" + hostip + "/api/", params=paramsPush, verify=False)

    root = ET.fromstring(xmlPush.text)
    # 查看 XML 報告 <response status="success"> 為 sucess or error
    for response in root.iter('response'):
        resultStatus = response.get('status')

    return resultStatus


# 定義 pushCommit 函式推送 Commit & Description
# 發出以下 URL 來取得包含 commit status 的 XML 格式, 再經由處理後回傳 commitStatus 字串
# https://<hostip>/api/?type=commit&xpath=/config/devices/&cmd=<'<commit><description>' + description + '</description></commit>'>&key=<key>
def pushCommit(description, key, hostip):
    paramsCommit = {
        'type': 'commit',
        'xpath': '/config/devices/',
        'cmd':
        '<commit><description>' + description + '</description></commit>',
        'key': key
    }
    xmlCommit = requests.get(
        "https://" + hostip + "/api/", params=paramsCommit, verify=False)

    root = ET.fromstring(xmlCommit.text)
    # 查看 XML 報告 <response status="success"> 為 sucess or error
    for response in root.iter('response'):
        commitStatus = response.get('status')

    return commitStatus


# 讀取 report.csv，刪除超過 M 天以前結果
def delete_Ndaysago_report(dfUserList):

    # 取得 M 日前日期（以今日為基準）
    # 修改 days=TriggerDateRange (config: TriggerDateRange) 調整資料要保留 M 天
    keepdate = pd.Timestamp(datetime.date.today() - datetime.timedelta(days=TriggerDateRange))
    dfUserList = (dfUserList[dfUserList['日期'] >= keepdate])

    # 將刪除 M 日前資料之 dataframe 覆蓋 report.csv (mode: 'w', 刪除舊資料後存入)
    f = open('report.csv', 'w')
    f.write(pd.DataFrame.to_csv(dfUserList, index=False, header=False))
    f.close()

    return dfUserList


# 傳入 report.csv M 日內超流名單，並提取 nowlock.csv [鎖定日期, 超流使用者]
def create_nowlock(dfUserList):

    # 取得歷史資料內 M 日內超流 N 次名單
    usercount = dfUserList.groupby('使用者名稱').size()
    # 修改 usercount == TriggerCount (config: TriggerCount) 調整 M 日內超流 N 次便鎖定
    overflowlist = usercount[usercount == TriggerCount].index.tolist()
    dictNewlock = {
        '鎖定日期': (datetime.date.today()),
        '超流使用者': overflowlist
    }
    dfNewlock = pd.DataFrame(dictNewlock)

    # 建立 nowlock.csv (mode: 'a', 寫入資料在檔案末端)
    f = open('nowlock.csv', 'a')
    f.write(pd.DataFrame.to_csv(dfNewlock, index=False, header=False))
    f.close()
    print(timestamp(), 'create_nowlock(): 已更新 nowlock.csv \n 連續超流三日名單: \n', dfNewlock)


# 讀取 nowlock.csv，刪除已鎖定 O 天以上帳號，並回傳刪除過後之 dataframe
def delete_lockedNdays(dfLocked):
    # 刪除已鎖定三天的帳號
    # 修改 days=DaysofLock 調整超流使用者鎖定 O 天
    lockeddate = pd.Timestamp(datetime.date.today() - datetime.timedelta(days=DaysofLock))

    dfLocked = (dfLocked[dfLocked['鎖定日期'] > lockeddate])

    # 建立 nowlock.csv (mode: 'w', 刪除舊資料後存入)
    f = open('nowlock.csv', 'w')
    f.write(pd.DataFrame.to_csv(dfLocked, index=False, header=False))
    f.close()
    return dfLocked


# 取得 API Key & JobID
apikey = (getKey(UserName, PassWord, FireWallAddr))
jobid = (getJobid('custom', 'Top 50 Wireless User traffic daily report', apikey, FireWallAddr))
reportstatus = (getReportstatus(jobid, apikey, FireWallAddr))
print(timestamp(), 'apikey: ', apikey, 'jobid, ', jobid)
print(timestamp(), reportstatus)

errorCount = 0
actCount = 0
# 若 response status 異常 (response.status = 'error')，重新產生新 job-id
while reportstatus[0] != 'success':
    jobid = (getJobid('custom', 'Top 50 Wireless User traffic daily report',
                      apikey, FireWallAddr))
    errorCount += 1
    print(timestamp(), 'response.status = error, 重新產生job-id', '\n', 'new-jobid: ',
          jobid, '\n Count: ', errorCount)
# 若 job status 異常 (job.status = 'ACT')，間隔一秒重新取得狀態確認是否已完成 (job.status = 'FIN')
while reportstatus[1] != 'FIN':
    reportstatus = (getReportstatus(jobid, apikey, FireWallAddr))
    actCount += 1
    print(
        timestamp(),
        'job.status = ACT, 每15秒更新狀態直到 job.status = FIN. \n new-jobstatus: ',
        reportstatus, '\n Count: ', actCount, ' jobid: ', jobid)
    time.sleep(15)

    if actCount == 30:
        jobid = (getJobid('custom', 'Top 50 Wireless User traffic daily report', apikey, FireWallAddr))
        actCount = 0
        print(timestamp(), '超過重試次數 30 (15秒*30次), 重新產生job-id', '\n new-jobid: ', jobid)

# 取得報告回傳值 (day_of_receive_time, srcuser, bytes_total , bytes_received, bytes_sent)
day_of_receive_time, srcuser, bytes_total, bytes_received, bytes_sent = (getReport(jobid, apikey, FireWallAddr))

# 將 dict 結構轉成 dataframe 結構，方便進行篩選及處理
dictOverFlow = {
    '日期': day_of_receive_time,
    '使用者名稱': srcuser,
    '總流量': bytes_total,
    '下載量': bytes_received,
    '上傳量': bytes_sent
}
# dropna(): 除去 srcuser = None
dfOverFlow = pd.DataFrame(dictOverFlow).dropna()
# .map(lambda x: str(x)[5:]) 除去左邊五個字元
dfOverFlow['日期'] = dfOverFlow['日期'].map(lambda x: str(x)[5:])
# 格式化日期輸出
dfOverFlow['日期'] = pd.to_datetime(dfOverFlow['日期'], format='%b %d, %Y')

# 新增篩選條件  總流量 > 50G & 正規表達式篩選出學生帳號
mask = dfOverFlow['總流量'] >= Quota
regex = dfOverFlow['使用者名稱'].str.contains('^[a-z]{1}[0-9]{9}|^[u]{1}[0-9]{7}')
dfOverFlowFiltered = (dfOverFlow[mask & regex])

# 建立 report.csv (mode: 'a', 寫入資料在檔案末端)
f = open('report.csv', 'a')
f.write(pd.DataFrame.to_csv(dfOverFlowFiltered, index=False, header=False))
f.close()
print(timestamp(), '已寫入單日超流名單至 report.csv \n', dfOverFlowFiltered)

# 檢查 report.csv 是否存在
while not (os.path.exists('report.csv')) and (os.path.getsize('report.csv')):
    time.sleep(3)
    print(timestamp(), 'report.csv 不存在，三秒後重試')

# 讀取 report.csv
dfUserList = pd.read_csv('report.csv', names=['日期', '使用者名稱', '總流量', '下載量', '上傳量'])
# str 轉換成日期格式
dfUserList['日期'] = pd.to_datetime(dfUserList['日期'])

# 移除超過三日 report.csv
dfUserListRemoved = delete_Ndaysago_report(dfUserList)
print(timestamp(), 'delete_Ndaysago_report(): 已移除超過三日之歷史超流名單: report.csv')

# 取得歷史資料內連續超流三日名單
create_nowlock(dfUserListRemoved)

# 檢查 nowlock.csv 是否存在
while not (os.path.exists('nowlock.csv')) and (os.path.getsize('nowlock.csv')):
    time.sleep(3)
    print(timestamp(), 'nowlock.csv 不存在，三秒後重試')


# 刪除已鎖定三天的帳號
dfLocked = pd.read_csv('nowlock.csv', names=['鎖定日期', '超流使用者'])
dfLocked['鎖定日期'] = pd.to_datetime(dfLocked['鎖定日期'])
dfLockedremoved = delete_lockedNdays(dfLocked)
print(timestamp(), 'delete_lockedNdays()，已移除鎖定三天以上帳號: nowlock.csv')

overflowuser = dfLockedremoved['超流使用者'].values.tolist()
print(timestamp(), '超流名單', overflowuser)


# 確認超流 list是否為空，若為空則只推送使用者'11111'進去
if overflowuser:
    # 推送超流名單進 PA 以及取得 response.status 回傳值
    pushResult = pushOverflowuser(overflowuser, apikey, FireWallAddr)

    while pushResult != 'success':
        pushResult = pushOverflowuser(overflowuser, apikey, FireWallAddr)
        print(timestamp(), '推送失敗，間隔一秒後重新推送 \n new-pushResult: ', pushResult)
        time.sleep(1)
else:
    emptylist = ['11111']
    pushResult = pushOverflowuser(emptylist, apikey, FireWallAddr)

    while pushResult != 'success':
        pushResult = pushOverflowuser(overflowuser, apikey, FireWallAddr)
        print(timestamp(), '推送失敗，間隔一秒後重新推送 \n new-pushResult: ', pushResult)
        time.sleep(1)

print(timestamp(), 'pushCommit() 結果: ', pushCommit('', apikey, FireWallAddr))
