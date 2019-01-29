# WiFi_QoS_Script 說明

## 執行環境 Python3.6 virtualenv
sudo yum install centos-release-scl
sudo yum install rh-python36
scl enable rh-python36 bash
mkdir /home/logicalis/WiFi_QoS_Script
python -m venv /home/logicalis/WiFi_QoS_Script
source /home/logicalis/WiFi_QoS_Script/bin/activate

pip install pandas configparser requests

## 排程腳本
0 3 * * * /home/logicalis/QoScript_Venv.sh

## config.ini
從外部讀取 QoScript.py 運作參數，一般調整只需要修改此檔案即可
[Default]: 設定帳號密碼IP
[OverFlow Setting]: 設定超流細項
> M 天內超流 N 次便鎖定 O 天


## report.csv 
儲存每日流量 > 50G 的學生帳號（排除非學生帳號），並且會自動清除超過三日之超流紀錄
欄位分別是 '日期', '使用者名稱', '總流量', '下載量', '上傳量'

## nowlock.csv 
儲存著從 report.csv 內撈出次數 == N 次的帳號（三日內超流三次），並自動推送至 Paloalto QoS 名單內
鎖定三日後會自動從名單中移除
欄位分別是 '鎖定日期', '使用者名稱'

## generateHTML.csv
GenerateHTML.py: 讀取 report.csv & nowlock.csv，傳輸量轉換為 GB 並加上鎖定日期
保存六天內資料（三日內超流三次 + 鎖定三天），修改 config.ini 會自動調整保存日期長度（M + O 天）
欄位分別是 '日期', '使用者名稱', '總流量', '下載量', '上傳量', '鎖定日期'

## /var/www/public/index.html
讀取 generateHTML.csv 後產生出 html 檔案（保留六天）
Web server: Nginx

## LOGS
每日執行結果備存

## 參數調整說明
修改 config.ini 即可