# PZEM_004_Logging
Simple program that logs information from energy monitor PZEM_004 to google sheet with raspberry pi
This is more or less working code. I use this to log the accumilated energy into spreadsheet every hour with cronjob on raspberry pi.
The cronjob is as follows.
0 * * * * * sudo python /home/pi/emon/enmon_gspread.py >> /home/pi/emon/script.log
It runs on first minute of every hour and writes the output to the file script.log 
