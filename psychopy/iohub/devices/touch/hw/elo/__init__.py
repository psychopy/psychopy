# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/touch/hw/elo/__init__.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""
from psychopy.iohub.devices import Computer
from ..... import printExceptionDetailsToStdErr,print2err
from .....constants import EventConstants, DeviceConstants
from ... import TouchDevice, TouchEvent,TouchMoveEvent,TouchPressEvent,TouchReleaseEvent
import serial
from serial.tools import list_ports
import math
from collections import deque
from .elo_serial import *
import gevent

currentSec=Computer.currentSec
getTime=Computer.currentSec

# OS ' independent' view of the Elo Touch Device

class Touch(TouchDevice):
    """
    The Touch class represents a touch screen input device. The Elo implementation
    of the Touch Dveice uses a Serial interface for communication between
    the Host Computer running ioHub and the Elo Touch Controller. A Serial - USB
    converter is generally also used so that any computer with a free USB 2.0 
    port, running an operating system supported by the Serial - USB
    converter and PsychoPy.iohub, can be used as the Host.
    
    Touch position data is mapped to the coordinate space defined in the ioHub 
    configuration file for the Display index specified. If the touch device is 
    on a display other than the PsychoPy full screen window Display, then 
    positional data is returned using the OS desktop pixel bounds for the given 
    display.

    Touch Events are generated independantly of other device events, including 
    a mouse device. Therefore touch data can be used in parallel to mouse data.
    
    The Elo Touch Device does not require any external driver or native library
    other than the pyserial Python package. Infact, unless you wish the 
    touch device to be registered as a Mouse Device, it is important **not**
    to install any additional drivers or software for the Elo Screen. 
    
    When using a Serial - USB converter to connect the Elo Device to a Host 
    Computer USB port, please ensure any required driver or software for
    the converter is installed on the Host PC. The converter should create an
    active Serial Port on the Host Computer.
    
    Configure the serial port created by the Serial - USB converter as follows:
    
         *. 9600 Baud
         *. 8 Data Bits
         *. 1 Stop Bit
         *. No Parity
         *. Hardware Handshaking enabled
         *. Software Handshaking disabled
         *. Half Duplex
      
    """
    LEAD_IN_BYTE='U'

    EVENT_CLASS_NAMES=['TouchEvent','TouchMoveEvent','TouchPressEvent','TouchReleaseEvent']                       
    DEVICE_TYPE_ID=DeviceConstants.TOUCH
    DEVICE_TYPE_STRING='TOUCH'
    __slots__=['_elo_hw_config','_non_touch_events','_rx_data','_serial_port_hw','serial_port_num','_raw_positions']
    def __init__(self,*args,**kwargs):   
        TouchDevice.__init__(self,*args,**kwargs)
        self._non_touch_events=deque(maxlen=64)
        serial_config=self.getConfiguration().get('serial')
        if serial_config:
            sport=serial_config.get('port')
            try:
                sport=int(sport)-1
            except Exception:
                sport=sport
            self.serial_port_num=sport
            
        self._raw_positions=False
        self._rx_data=''
        self._serial_port_hw=None
        self._connectSerial()
        
        self._elo_hw_config=dict(JUMPERS=self.queryDevice('Jumpers'))#_getJumpers())        
        self._elo_hw_config['OWNER']=self.queryDevice('Owner')
        self._elo_hw_config['ID']=self.queryDevice('ID')
        self._elo_hw_config['REPORT']=self.queryDevice('Report')
        self._elo_hw_config['DIAGNOSTICS']=self.queryDevice('Diagnostics')        
    
    def getHardwareConfiguration(self):
        return self._elo_hw_config
        
    def queryDevice(self,query_type, *args,**kwargs):
        """
        Send the underlying touch screen device a query request and return the response.
        """
        self._query(query_type,*args,**kwargs)
        if query_type in RESPONSE_PACKET_TYPES.keys():
            stime=getTime()
            while getTime()-stime<0.10:
                self._poll()
                while len(self._non_touch_events):
                    reply=self._non_touch_events.popleft()
                    if reply.__class__.__name__.endswith(query_type):
                        return reply.asdict()
                gevent.sleep(0)


        return None
        
    def commandDevice(self,cmd_type, *args,**kwargs):
        """
        Send the underlying touch screen device a command and return the response.
        """
        self._command(cmd_type,*args,**kwargs)
        if cmd_type in RESPONSE_PACKET_TYPES.keys():
            stime=getTime()
            while getTime()-stime<0.010:
                self._poll()
                while len(self._non_touch_events):
                    reply=self._non_touch_events.popleft()
                    if reply.__class__.__name__.endswith(cmd_type):
                        return reply.asdict()
                gevent.sleep(0)
        return None
    
    def getPositionType(self):
        if self._raw_positions is True:
            return 'RAW'
        return 'CALIBRATED'
        
    def _connectSerial(self):
        self._serial_port_hw = serial.Serial(self.serial_port_num, 9600, timeout=0)
        if self._serial_port_hw is None:
            raise ValueError("Error: Serial Port Connection Failed: %s"%(str(self.serial_port_num)))
        self._flushSerialInput()
        
    def _readAnyRx(self,max_bytes=256):
        self._rx(num_bytes=max_bytes)
        
    def _flushSerialInput(self):
        self._serial_port_hw.flushInput()
        self._readAnyRx(max_bytes=100)
        while self._serial_port_hw.inWaiting():
          self._serial_port_hw.read(self._serial_port_hw.inWaiting())

    def _tx(self,packet_bytes):
        tx_count=self._serial_port_hw.write(packet_bytes)
        self._serial_port_hw.flush()
        return tx_count

    def _query(self,query_type,*args,**kwargs):
        qpkt=query_type
        if isinstance(query_type,basestring):
            qpkt=QUERY_PACKET_TYPES[query_type](*args,**kwargs)
        self._tx(qpkt._packet_bytes)
        return qpkt
        
    def _command(self,cmd_type,*args,**kwargs):
        qpkt=cmd_type
        if isinstance(cmd_type,basestring):
            qpkt=COMMAND_PACKET_TYPES[cmd_type](*args,**kwargs)
        self._tx(qpkt._packet_bytes)
        return qpkt
   
    def _rx(self,async=False,num_bytes=10):
        if async:
            while self._serial_port_hw.inWaiting()>0:
                self._rx_data+=self._serial_port_hw.read(self._serial_port_hw.inWaiting())
        else:
                self._rx_data+=self._serial_port_hw.read(num_bytes) 

    def saveConfiguration(self):
        # Save elo device settings to NVRAM
        pkt=self._command('N',*(1,7,0))
        reply_packets=self._poll()

    def restoreConfiguration(self):
        # Save elo device settings to NVRAM
        pkt=self._command('N',*(0,7,0))
        reply_packets=self._poll()
        
    def initCalibration(self):
        try:
            # set flag indicating raw touch coords should be used in touch events, as 
            # data is not calibrated
            self.clearEvents()
            self._raw_positions=True
            
            # To acquire calibration points, controller must be in raw coordinate
            # mode. We use the point of untouch as our calibration point. */
    
            # Get current Mode settings
            pkt=self._query('m')
            reply_packets=self._poll()
            
            # Set Mode to utouch events only
            pkt=self._command('M',*(132,))
            reply_packets=self._poll()
    
            # Get current swap-axis state
            pkt=self._query('c',*(0,True))
            reply_packets=self._poll()
    
            # Disable swap-axis
            pkt=self._command('C',*(0,0,0,0,0,0,False))
            reply_packets=self._poll()
            
            # Get current mode settings
            pkt=self._query('m')
            reply_packets=self._poll()
        except Exception, e:
            print2err("Exception During Touch.initCalibration: ",str(e))
            
    def applyCalibrationData(self,xmin,xmax,ymin,ymax,x1,y1,x2,y2,sx,sy,leftx,uppery,rightx,lowery):
        # set calibration and scaling params on controller */
        try:
            # compute number of touch points per screen coordinate */
            xunit = (x2-x1) / (rightx-leftx)
            yunit = (y2-y1) / (lowery-uppery)
    
            #/* extrapolate the calibration points to corner points of screen image */
            xhigh = x2 + (xunit * (xmax-rightx))
            xlow = x1 - (xunit * (leftx-xmin))
            if xlow < 1:
                xlow = 1
            if xhigh < 1:
                xhigh = 1 # in case axis inverted */
            yhigh = y2 + (yunit * (ymax - lowery))
            ylow = y1 - (yunit * (uppery - ymin))
            if ylow < 1: 
                ylow = 1
            if yhigh < 1: 
                yhigh = 1
    
            # detect touchscreen orientation corrections */
            xyswap = math.fabs(sx-x1) < math.fabs(sy-y1)
    
            #xinv = xhigh < xlow
            #yinv = yhigh < ylow
    
            # set calibration x, y data        
            pkt=self._command('C',*('X',xlow,xhigh,0,0,0,False))
            reply_packets=self._poll()
    
            pkt=self._command('C',*('Y',ylow,yhigh,0,0,0,False))
            reply_packets=self._poll()
            
            # set swap_axis flag       
            pkt=self._command('C',*(0,0,0,0,0,0,xyswap))
            reply_packets=self._poll()
        
            # set scaling .....
            pkt=self._command('S',*('X',xmin,xmax))
            reply_packets=self._poll()
    
            # set scaling .....
            pkt=self._command('S',*('Y',ymin,ymax))
            reply_packets=self._poll()       
            
            # Change mode to send touch, untouch, and touch movement events
            pkt=self._command('M',*( 199,14))
            reply_packets=self._poll()
    
            # Get current Mode settings
            pkt=self._query('m')
            reply_packets=self._poll()
    
            # set flag indicating calibrated touch coords should be 
            # used in touch events, as data is not calibrated
            self.clearEvents()
            self._raw_positions=False
            
        except Exception, e:
            print2err("Exception During Touch.applyCalibrationData: ",str(e))

    def clearEvents(self):
        try:
            self._non_touch_events.clear()
            self._flushSerialInput()
            TouchDevice.clearEvents(self)
        except Exception, e:
            print2err("Exception During Touch.clearEvents: ",str(e))
            
    def _poll(self):
        """
        Checks for any new Touch Response Packets...
        """
        try:
            poll_time=currentSec()
            self._rx()
            while self._rx_data or self._serial_port_hw.inWaiting():
                self._rx(num_bytes=self._serial_port_hw.inWaiting())
                while self._rx_data:
                    while self._rx_data and self._rx_data[0]!=self.LEAD_IN_BYTE:
                        #print2err('Non LEAD_IN_BYTE: ',ord(self._rx_data[0]))
                        self._rx_data=self._rx_data[1:]
                    rx_size=len(self._rx_data)
                    
                    if rx_size<10:
                        self._rx(num_bytes=10-len(self._rx_data))
                        if len(self._rx_data)<10:
                            self._last_poll_time=poll_time
                            #print2err('Poll < 10 bytes: ',currentSec()-poll_time)
                            return self._non_touch_events
                            
                    if self._rx_data[0]=='U' and self._rx_data[1] == 'T':
                        response_class=RESPONSE_PACKET_TYPES.get('T')
                        touch_event=response_class(poll_time,bytearray(self._rx_data[:10]))
                        #print2err('packet_bytes: ',[b for b in touch_event._packet_bytes])
                        self._rx_data=self._rx_data[10:]
                        if touch_event._valid_response is True:
                            etype=EventConstants.TOUCH_MOVE
                            if touch_event.touch_type==touch_event.TOUCH_PRESS:                    
                                etype=EventConstants.TOUCH_PRESS
                            elif touch_event.touch_type==touch_event.TOUCH_RELEASE:
                                etype=EventConstants.TOUCH_RELEASE
                            confidence_interval=poll_time-self._last_poll_time # confidence interval                    
                            # TODO: Calculate Delay more accurately if possible                    
                            delay=poll_time-touch_event.time # delay   
                            # TODO: Set Display ID correctly                    
                            display_id=0
        
                            self._lastPosition=self._position
                            if self._raw_positions is True:
                                self._position=touch_event.x,touch_event.y
                            else:
                                self._position=self._pixelToDisplayCoords(touch_event.x,touch_event.y)
                            
                            event =[            
                                    0, # exp id
                                    0, # session id
                                    0, #device id (not currently used)
                                    0, # event id
                                    etype, # event type
                                    touch_event.time, # device time
                                    poll_time, # logged time
                                    touch_event.time, # hub time
                                    confidence_interval, # confidence interval
                                    delay, # delay
                                    0, # filter_id
                                    display_id,
                                    self._position[0],
                                    self._position[1],
                                    touch_event.z
                                    ]
        
                            #print2err('Poll TouchEvent: ',currentSec()-poll_time)
                            self._addNativeEventToBuffer(event)
                    elif self._rx_data[0]=='U': 
                        response_class=RESPONSE_PACKET_TYPES.get(self._rx_data[1])
                        # TODO: Checksum validation should be done here.
                        if response_class:
                            rc=response_class(poll_time,bytearray(self._rx_data[:10]))
                            self._rx_data=self._rx_data[10:]
                            if rc._valid_response is True:
                                self._non_touch_events.append(rc)
                            else:
                                print2err("Invalid Response:",rc.asdict())
                        else:
                            print2err('Warning: UNHANDLED RX PACKET TYPE: %d %s'%(poll_time,str([c for c in self._rx_data[:10]])))
                            self._rx_data=self._rx_data[10:]
                        #print2err('Poll Non TouchEvent: ',currentSec()-poll_time)

#            if self._non_touch_events or touch_event_received:
#                print2err('Poll end: %.6f %.6f'%(currentSec()-poll_time,poll_time-self._last_poll_time))
            self._last_poll_time=poll_time
            return self._non_touch_events
        except Exception:
            print2err("Exception During Touch._poll: ")
            printExceptionDetailsToStdErr()            
                
    def _pixelToDisplayCoords(self,px,py):
        """
        Converts 0,0,pix_width,pix_height coord space to display device coord space.  
        """
        try:
            dw,dh=self._display_device.getPixelResolution()
            rx=px/float(dw)
            ry=py/float(dh)
            left,top,right,bottom=self._display_device.getCoordBounds()
            w,h=right-left,top-bottom            
            x,y=left+w*rx,bottom+h*(1.0-ry) 
            return x,y
        except Exception:
            print2err("Error During EloDevice._pixelToDisplayCoords:") 
            printExceptionDetailsToStdErr()
            return px,py
                       
    def _closeSerial(self):
        """
        """
        if self._serial_port_hw:
            self._serial_port_hw.close()
            self._serial_port_hw=None
            return True
        return False

    def _close(self):
        """
        """
        try:
            self._closeSerial()
            Device._close(self)
        except Exception:
            pass


