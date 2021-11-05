import sys
print(sys.executable)
import csv
import serial
#from IPython.display import display, clear_output
import numpy as np
import time
import socket
from datetime import datetime

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("comPort")
#parser.add_argument("fileName")
args = parser.parse_args()
myCOM = 'COM'+str(args.comPort)
print('Com port = ', myCOM)

UDP_IP = "127.0.0.2"
COM_ID = (lambda myCom: int(myCom[-1]) if len(myCom)==4 else int(myCom[-2])*10+int(myCom[-1]))(myCOM)
UDP_PORT = 9900+COM_ID
print("UDP channel is ", UDP_IP, UDP_PORT)
def write_csv(fileName,data):
    with open(fileName, 'a') as outfile:
        writer = csv.writer(outfile,  lineterminator='\n')
        writer.writerow(data)


ser = serial.Serial(myCOM, baudrate=115200)

#fileName = args.fileName
timestr = time.strftime("%Y%m%d")
fileName = "D"+str(myCOM)+"/D"+str(myCOM)+"_"+timestr+".csv"
print("File created:", fileName)
while(1):
    timestr = time.strftime("%Y%m%d")
    fileName = "D"+str(myCOM)+"/D"+str(myCOM)+"_"+timestr+".csv"


    msgByte=ser.readline()
    msg=str(msgByte)\
        .replace('b\'', '')\
        .replace('\\n', '')\
        .replace('\\r', '')\
        .replace('\\x', '')\
        .replace('\'', '')\
        .split(',')
    msg.insert(0,str(int(time.time())))
    
    udpMsg=','.join(msg)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.sendto(udpMsg.encode(), (UDP_IP, UDP_PORT))
    print(udpMsg)
    
    data = np.array([int(time.time())])
    data = np.concatenate((data, np.array([int(i, 16) for i in msg[3:7]], dtype=float)))
    volt= [3.3*int(i, 16)/4095.0 for i in msg[3:7]]
    res =  [10.0*v/(3.3001-v) for v in volt]
    data = np.concatenate((data, np.array(res, dtype=float)))
    write_csv(fileName,data)
    '''
    msg.insert(0,str(int(time.time()*10)))
    msg.pop(1)
    udpMsg=','.join(msg[0:])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.sendto(udpMsg.encode(), (UDP_IP, UDP_PORT))
    print(myCOM, datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    print(udpMsg)#data)
    '''
ser.close()