import serial 
import time
ser = serial.Serial("COM5", 9600)
# try :
    
#     # time.sleep(1)
#     print("Cổng COM đã được mở")
# except : print("Không mở được cổng COM")