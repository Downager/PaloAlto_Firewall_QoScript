#! /bin/bash
cd /home/logicalis/WiFi_QoS_Script
source WiFi_QoS_Script/bin/activate

# virtualenv is now active, which means your PATH has been modified.
# Don't try to run python from /usr/bin/python, just run "python" and
# let the PATH figure out which version to run (based on what your
# virtualenv has configured).

python ./QoScript.py >> ./LOGS/QoScript.$(date +"%Y%m%d").log
python ./GenerateHTML.py >> ./LOGS/QoScript.$(date +"%Y%m%d").log
deactivate
