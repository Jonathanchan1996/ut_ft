# bokeh serve --show udpPlot.py --port 5007 --args 7
import socket
from bokeh.plotting import figure, curdoc
from bokeh.driving import linear
from bokeh.models import DatetimeTickFormatter, Div
from bokeh.layouts import column,row, gridplot

from datetime import datetime

import argparse
parser = argparse.ArgumentParser()
#parser.add_argument("numberOfComPort")
parser.add_argument("comPort1")

args = parser.parse_args()
print(len(vars(args)))
shownDataLength = 60*10
UDP_Port = 9900+int(args.comPort1)
resistSca= [10,10]
#sensorName = [args.sensorName1, args.sensorName2]

class bkPlot:
    def __init__(self, title='my plot', ylabel="Y", width=400, height=200):
        self.title = title
        self.p=figure(title=self.title, plot_width=width, plot_height=height) #, x_axis_type='datetime'
        self.p.yaxis.axis_label = ylabel
        self.p.xaxis.major_label_orientation = 3.14/4
        self.r=self.p.line([], [], color="firebrick", line_width=2)
        self.ds=self.r.data_source

webTitle = Div(text='<h1 style="text-align: center">PALM Sensor, Center on Smart Sensors and Environmental Technologies, HKUST</h1>')
vocPlot =[]
for i in range(4):
    vocPlot.append(bkPlot(title='sensor '+str(i), height=300, width=1400)) 
tnRhPlot=[]
tnRhPlot.append(bkPlot(title='Temperature',ylabel="deg C", width=800))
tnRhPlot.append(bkPlot(title='Humidity',ylabel="%", width=800))
#####################################################################
timeDic = {}
def unpackMsg(msg):
    rxBuff = msg.split(b',')
    ts   = int(rxBuff[0], 16)
    temp = float(rxBuff[1])
    rh   = float(rxBuff[2])
    adc0 = int(rxBuff[3], 16)
    adc1 = int(rxBuff[4], 16)
    adc2 = int(rxBuff[5], 16)
    adc3 = int(rxBuff[6], 16)

    return (ts, temp, rh, adc0, adc1, adc2, adc3)

@linear()
def update(step):
    #receive udp
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('127.0.0.2', UDP_Port))
    data, addr = s.recvfrom(1024)
    s.close()
    
    #print("Msg from COM",(UDP_Port[i]-9900), ":", unpackMsg(data))
    timestamp, temp, rh, adc0, adc1, adc2, adc3 = unpackMsg(data)
    adc = [adc0, adc1, adc2, adc3]
    adc = [(3.3*(i-1.0)/4095.0) for i in adc] #(10*i/(4095.0-(i-1)))
    adc = [10.0*V/(3.3-V) for V in adc]
    #date_time = datetime.fromtimestamp(timestamp).strftime("%H:%M")
    #timeDic.update({timestamp:date_time})
    for i in range(4):
        vocPlot[i].ds.data['x'].append(step)
        cct = adc[i]
        vocPlot[i].ds.data['y'].append(cct)


        if len(vocPlot[i].ds.data['x'])>shownDataLength:
            vocPlot[i].ds.data['x'].pop(0)
            vocPlot[i].ds.data['y'].pop(0)
            
        vocPlot[i].ds.trigger('data', vocPlot[i].ds.data, vocPlot[i].ds.data)
   
    tnRhPlot[0].ds.data['y'].append(temp)
    tnRhPlot[1].ds.data['y'].append(rh)
    for i in range(2):
        tnRhPlot[i].ds.data['x'].append(step)
        if len(tnRhPlot[i].ds.data['x'])>shownDataLength:
            tnRhPlot[i].ds.data['x'].pop(0)
            tnRhPlot[i].ds.data['y'].pop(0)
            
        tnRhPlot[i].ds.trigger('data', tnRhPlot[i].ds.data, tnRhPlot[i].ds.data)


ptot = column(webTitle, row(tnRhPlot[0].p, tnRhPlot[1].p), row(vocPlot[0].p), row(vocPlot[1].p), row(vocPlot[2].p), row(vocPlot[3].p))
#gridplot([[webTitle],[vocPlot[0].p,vocPlot[1].p,vocPlot[2].p,vocPlot[3].p]])

curdoc().add_root(ptot)
#curdoc().add_root(vocPlot.p)
# Add a periodic callback to be run every 50 milliseconds
curdoc().add_periodic_callback(update, 50)