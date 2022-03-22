import cv2 as cv
from scipy.signal import find_peaks
from matplotlib import pyplot as plt
import numpy as np

class cvFindLine():
    def __init__(self,videoSrc):
        self.cam = cv.VideoCapture(videoSrc)
        ret, img = self.cam.read()
        self.h,self.w, _ = img.shape
        self.h_half, self.w_half = int(self.h/2), int(self.w/2)
        self.upLim, self.lwLim = self.h_half+50, self.h_half+100
        self.last_l_pos, self.last_r_pos = 0, self.w
        self.centerPt = self.w_half
    
    def run(self, isPlot=False):
        ret, img = self.cam.read()
        l_pos, r_pos = [],[]
        ddmean = 0
        for j in range(3): #rgb
            meanVec = []
            for i in range(self.upLim,self.lwLim, 3):
                meanVec.append(img[i,:, j])
            ddmean = np.diff(np.mean(meanVec, axis=0)) #dy/dx
            #ddmean = np.convolve(meanVec,[-1,0,1])
            ddmean = np.abs(np.convolve(ddmean,(1/9)*np.ones(9))) #mean+abs filter
            peaks, _ = find_peaks(ddmean[0:int(self.centerPt)], prominence=1,width=5) #left image
            peaks2, _ = find_peaks(ddmean[self.centerPt:-1], prominence=1,width=5) #Right image 
            if len(peaks)>0:
                l_pos.append(peaks[-1])
            if len(peaks2)>0:
                r_pos.append(peaks2[0])
        cen = 0
        if len(l_pos)>0:
            cen = 0.2*self.last_l_pos+0.8*np.mean(l_pos, dtype=int) #complementary fiter, weighted mean
            cen = int(cen)
        else:
            cen = 0
        if isPlot:
            cv.line(img, (cen,0),(cen,self.w), (0,0,255), 3)
        self.last_l_pos=cen
        if len(r_pos)>0:
            cen = 0.2*self.last_r_pos+0.8*(self.w_half+np.mean(r_pos, dtype=int))
            cen = int(cen)
        else:
            cen = self.w
        if isPlot:
            cv.line(img, (cen,0),(cen,self.w), (0,255,0), 3)
        self.last_r_pos=cen
        self.rbtCenter=int((self.last_r_pos+self.last_l_pos)/2)
        lineDistance=0
        centerErr = self.centerPt-self.rbtCenter
        if len(peaks)>0 and len(peaks2)>0:
            lineDistance = (self.last_r_pos-self.last_l_pos)
        if isPlot:
            cv.line(img, (self.rbtCenter,0), (self.rbtCenter,self.w) , (255,255,0), 2) #middle line
            cv.line(img, (self.centerPt,0) , (self.centerPt,self.w)  , (255,0,0), 1)   #middle line
            cv.line(img, (0,self.upLim), (self.w,self.upLim), (255,0,0), 1)   #middle line
            cv.line(img, (0,self.lwLim), (self.w,self.lwLim), (255,0,0), 1)   #middle line
            cv.putText(img, str(centerErr)+',  '+str(lineDistance), (self.h,self.h-10), cv.FONT_HERSHEY_SIMPLEX, 1
                       ,(255,0,0),2,cv.LINE_AA)
            cv.imshow('D435 image', img)

        return centerErr, lineDistance
    def exitCv(self):
        return (0xFF & cv.waitKey(5) == 27)
    def __del__(self):
        cv.destroyAllWindows()
        
        
class cvFindCircle():
    def __init__(self,videoSrc):
        self.cam = cv.VideoCapture(videoSrc)
        ret, img = self.cam.read()
        self.h,self.w, _ = img.shape
        self.h_half, self.w_half = int(self.h/2), int(self.w/2)
        self.upLim, self.lwLim = self.h_half+50, self.h_half+100
        self.last_l_pos, self.last_r_pos = 0, self.w
        self.centerPt = self.w_half
        
    def run(self, isPlot=False):
        ret, img = self.cam.read()
        cimg = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        circles = cv.HoughCircles(cimg,cv.HOUGH_GRADIENT,1,40,
                                param1=100,param2=100,minRadius=80,maxRadius=1000)
        if circles is not None:
            circles = np.uint16(np.around(circles))
            if isPlot:
                for i in circles[0,:]:
                    cv.circle(img,(i[0],i[1]),i[2],(0,255,0),2)
                # cv.circle(img,(i[0],i[1]),2,(0,0,255),3)
            #print(circles[0,:][0][1]-h_half,circles[0,:][0][0]-w_half)
                cv.imshow("Live", img)
            return circles[0,:][0][0]-self.w_half, circles[0,:][0][1]-self.h_half
        else:
            if isPlot:
                cv.imshow("Live", img)
            return 0,0
    
    def exitCv(self):
        return (0xFF & cv.waitKey(5) == 27)
    def __del__(self):
        cv.destroyAllWindows()
        