# Unofficial unitree python SDK for HKUST research purpose  
import socket
import time
import json
import numpy as np

#HOST = '192.168.123.162'# my own address, need to update in c++
#PORT = 4141 #Dummy, init used
class controller():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.addr = (self.host, self.port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(5)
        self.imu = 0 # It will be a json packet
        self.rawData = " "
        self.cmd = {}
        self.cmd['mode'] = 1
        self.cmd['forwardSpeed'] = 0.0
        self.cmd['sideSpeed'] = 0.0
        self.cmd['rotateSpeed'] = 0.0
        #Disabled in c++ side
        self.cmd['bodyHeight'] = 0.0
        self.cmd['roll'] = 0.0
        self.cmd['pitch'] = 0.0
        self.cmd['yaw'] = 0.0
        
        #Limits 
        self.maxForwardSpeed = 0.9
        self.maxSideSpeed    = 0.8
        self.maxRotateSpeed  = 0.8
        #self.cmd = json.dumps(self.cmd)
    def __del__(self):
        self.sock.close()
    def getState(self): #Get IMU data
        self.rawData, self.addr = self.sock.recvfrom(1024)
        #print(self.rawData)
        self.imu = json.loads(self.rawData.decode())
        #print(self.imu)
    def setCmd(self): #Run to send command to unitree
        cmdMsg = "{mode},{forwardSpeed},{sideSpeed},{rotateSpeed},{bodyHeight},{roll},{pitch},{yaw}".format(mode=int(self.cmd['mode']),forwardSpeed=self.cmd['forwardSpeed'],sideSpeed=self.cmd['sideSpeed'],rotateSpeed=self.cmd['rotateSpeed'],bodyHeight=self.cmd['bodyHeight'],roll=self.cmd['roll'],pitch=self.cmd['pitch'],yaw=self.cmd['yaw'])
        self.sock.sendto(cmdMsg.encode(), self.addr)
        
    def runSpeed(self, forwardSpeed, sideSpeed, rotateSpeed):
        self.cmd['mode']=2
        self.cmd['forwardSpeed'] = speedLim(forwardSpeed, self.maxForwardSpeed) 
        self.cmd['sideSpeed']    = speedLim(sideSpeed,    self.maxSideSpeed) 
        self.cmd['rotateSpeed']  = speedLim(rotateSpeed,  self.maxRotateSpeed) 
        self.setCmd()

class rawPath():
    def __init__(self):
        self.loc_x=[] #local
        self.loc_y=[]
        self.loc_yaw=[]
        self.glo_x=[] #global
        self.glo_y=[]
        self.glo_yaw=[]
        
        self.err_x=[]
        self.err_y=[]
        self.err_yaw=[]
        
        self.t=[]
    def record(self, x, y, yaw, t=0):
        self.loc_x.append(x)
        self.loc_y.append(y)
        self.loc_yaw.append(yaw)
        self.t.append(t)
    def recordErr(self, x, y, yaw, t=0):
        self.err_x.append(x)
        self.err_y.append(y)
        self.err_yaw.append(yaw)
    def setGloPos(self):
        self.glo_x = self.loc_x*np.cos(self.loc_yaw)+self.loc_y*np.sin(self.loc_yaw)
        self.glo_y = self.loc_x*np.sin(self.loc_yaw)+self.loc_y*np.cos(self.loc_yaw)


class setPoint:
     def __init__(self, x=0, y=0, yaw=0,timeStep=0.01,maxRunCnt=10000, toleranceCm=0.1, stopMs=0):
            self.x   = x   #Local frame
            self.y   = y   #local frame
            self.yaw = yaw #Global frame
            self.timeStep = timeStep #sec
            self.maxRunCnt = maxRunCnt #per keyprint -> Runtime is timeStep*maxRunCnt
            self.toleCm = toleranceCm #tolerance cm 
            self.stopMs = stopMs #10ms resolution
            

def speedLim(x, lim):
    return np.sign(x)*np.min([np.abs(x), lim])

def roundYawCtrl(yaw_err):
    if np.abs(yaw_err)>np.pi:
        yaw_err = -(yaw_err)
    return yaw_err