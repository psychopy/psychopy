"""
ioHub
Common Eye Tracker Interface
.. file: ioHub/devices/eyeTracker/hw/sr_research/eyelink/eyeLinkCoreGraphicsIOHubPsychopy.py

Copyright (C) 2012-2013 iSolver Software Solutions

Copyright (C) 2012 Sol Simpson
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

---------------------------------------------------------------------------------------------------------------------
This file uses the pylink module, Copyright (C) SR Research Ltd. License type unknown as it is not provided in the
pylink distribution (atleast when downloaded May 2012). At the time of writing, Pylink is freely avalaible for
download from  www.sr-support.com once you are registered and includes the necessary C DLLs.
---------------------------------------------------------------------------------------------------------------------

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

from psychopy import visual
import sys, array
import copy

from ..... import DeviceEvent, Computer
from ......constants import EventConstants, KeyboardConstants #, #DeviceConstants, EyeTrackerConstants
from ...... import convertCamelToSnake, print2err
from ......util import OrderedDict

import pylink
from pylink import EyeLinkCustomDisplay

currentSecTime=Computer.getTime

class EyeLinkCoreGraphicsIOHubPsychopy(EyeLinkCustomDisplay):
    IOHUB_HEARTBEAT_INTERVAL=0.050   # seconds between forced run through of
                                     # micro threads, since one is blocking
                                     # on camera setup.

    IOHUB2PYLINK_KB_MAPPING={
            KeyboardConstants._virtualKeyCodes.VK_F1: pylink.F1_KEY,
            KeyboardConstants._virtualKeyCodes.VK_F2: pylink.F2_KEY,
            KeyboardConstants._virtualKeyCodes.VK_F3: pylink.F3_KEY,
            KeyboardConstants._virtualKeyCodes.VK_F4: pylink.F4_KEY,
            KeyboardConstants._virtualKeyCodes.VK_F5: pylink.F5_KEY,
            KeyboardConstants._virtualKeyCodes.VK_F6: pylink.F6_KEY,
            KeyboardConstants._virtualKeyCodes.VK_F7: pylink.F7_KEY,
            KeyboardConstants._virtualKeyCodes.VK_F8: pylink.F8_KEY,
            KeyboardConstants._virtualKeyCodes.VK_F9: pylink.F9_KEY,
            KeyboardConstants._virtualKeyCodes.VK_F10: pylink.F10_KEY,
            KeyboardConstants._virtualKeyCodes.VK_PAGE_UP: pylink.PAGE_UP,
            KeyboardConstants._virtualKeyCodes.VK_PAGE_UP: pylink.PAGE_DOWN,
            KeyboardConstants._virtualKeyCodes.VK_UP: pylink.CURS_UP,
            KeyboardConstants._virtualKeyCodes.VK_DOWN: pylink.CURS_DOWN,
            KeyboardConstants._virtualKeyCodes.VK_LEFT: pylink.CURS_LEFT,
            KeyboardConstants._virtualKeyCodes.VK_RIGHT: pylink.CURS_RIGHT,
            KeyboardConstants._asciiKeyCodes.BACKSPACE: '\b',
            KeyboardConstants._asciiKeyCodes.RETURN: pylink.ENTER_KEY,
            KeyboardConstants._asciiKeyCodes.ESCAPE: pylink.ESC_KEY,
            KeyboardConstants._virtualKeyCodes.VK_F10: pylink.F10_KEY,
            KeyboardConstants._virtualKeyCodes.VK_F10: pylink.F10_KEY,
            }                                 

    WINDOW_BACKGROUND_COLOR=(128,128,128)
    CALIBRATION_POINT_OUTER_RADIUS=15.0,15.0
    CALIBRATION_POINT_OUTER_EDGE_COUNT=64
    CALIBRATION_POINT_OUTER_COLOR=(255,255,255)
    CALIBRATION_POINT_INNER_RADIUS=3.0,3.0
    CALIBRATION_POINT_INNER_EDGE_COUNT=32
    CALIBRATION_POINT_INNER_COLOR=(25,25,25)

    def __init__(self, eyetrackerInterface, targetForegroundColor=None, 
                 targetBackgroundColor=None, screenColor=None, targetOuterDiameter=None, 
                 targetInnerDiameter=None, dc_sounds=["","",""], cal_sounds=["","",""]):
        EyeLinkCustomDisplay.__init__(self)

        self._eyetrackerinterface=eyetrackerInterface
        self.tracker = eyetrackerInterface._eyelink
        self._ioKeyboard=None
        self._ioMouse=None
        
        self.img_size=None
 
        self.imagebuffer = array.array('I')
        self.pal = None

        self.screenSize = self._eyetrackerinterface._display_device.getPixelResolution()
        self.width=self.screenSize[0]
        self.height=self.screenSize[1]

        self.keys=[]
        self.pos = []
        self.state = 0
        
        if sys.byteorder == 'little':
            self.byteorder = 1
        else:
            self.byteorder = 0

        EyeLinkCoreGraphicsIOHubPsychopy.CALIBRATION_POINT_OUTER_COLOR=targetForegroundColor
        EyeLinkCoreGraphicsIOHubPsychopy.CALIBRATION_POINT_INNER_COLOR=targetBackgroundColor
        EyeLinkCoreGraphicsIOHubPsychopy.WINDOW_BACKGROUND_COLOR=screenColor
        EyeLinkCoreGraphicsIOHubPsychopy.CALIBRATION_POINT_OUTER_RADIUS=targetOuterDiameter/2.0,targetOuterDiameter/2.0
        EyeLinkCoreGraphicsIOHubPsychopy.CALIBRATION_POINT_INNER_RADIUS=targetInnerDiameter/2.0,targetInnerDiameter/2.0
 
        self.tracker.setOfflineMode();           
        
        display=self._eyetrackerinterface._display_device
        self.window=visual.Window(display.getPixelResolution(),
                                  monitor=display.getPsychopyMonitorName(),
                                  units=display.getCoordinateType(),
                                  fullscr=True,
                                  allowGUI=False,
                                  screen=display.getIndex()
                                  )
        self.window.setColor(color=self.WINDOW_BACKGROUND_COLOR,
                             colorSpace='rgb255')        
        self.window.flip(clearBuffer=True)
        
        self._createStim()
        
        self._registerEventMonitors()
        self._ioMouse.setSystemCursorVisibility(False)
        self._lastMsgPumpTime=currentSecTime()
        
        self.clearAllEventBuffers()

    def clearAllEventBuffers(self):
        pylink.flushGetkeyQueue();
        self.tracker.resetData()
        self._iohub_server.eventBuffer.clear()
        for d in self._iohub_server.devices:
            d.clearEvents()
            
    def _registerEventMonitors(self):
        self._iohub_server=self._eyetrackerinterface._iohub_server

        if self._iohub_server:
            for dev in self._iohub_server.devices:
                #print2err("dev: ",dev.__class__.__name__)
                if dev.__class__.__name__ == 'Keyboard':
                    kbDevice=dev
                elif dev.__class__.__name__ == 'Mouse':
                    mouseDevice=dev

        if kbDevice:
            eventIDs=[]
            for event_class_name in kbDevice.__class__.EVENT_CLASS_NAMES:
                eventIDs.append(getattr(EventConstants,convertCamelToSnake(event_class_name[:-5],False)))

            self._ioKeyboard=kbDevice
            self._ioKeyboard._addEventListener(self,eventIDs)
        else:
            print2err("Warning: elCG could not connect to Keyboard device for events.")

        if mouseDevice:
            eventIDs=[]
            for event_class_name in mouseDevice.__class__.EVENT_CLASS_NAMES:
                eventIDs.append(getattr(EventConstants,convertCamelToSnake(event_class_name[:-5],False)))

            self._ioMouse=mouseDevice
            self._ioMouse._addEventListener(self,eventIDs)
        else:
            print2err("Warning: elCG could not connect to Mouse device for events.")

    def _unregisterEventMonitors(self):
#       print2err('_unregisterEventMonitors')
        if self._ioKeyboard:
            self._ioKeyboard._removeEventListener(self)
        if self._ioMouse:
            self._ioMouse._removeEventListener(self)
     
    def _handleEvent(self,ioe):
        event=copy.deepcopy(ioe)
        event_type_index=DeviceEvent.EVENT_TYPE_ID_INDEX
        if event[event_type_index] == EventConstants.KEYBOARD_PRESS:
            self.translate_key_message((event[-5],event[-2]))
                
        elif event[event_type_index] == EventConstants.MOUSE_BUTTON_PRESS:
            self.state=1
        elif event[event_type_index] == EventConstants.MOUSE_BUTTON_RELEASE:
            self.state=0            
        elif event[event_type_index] == EventConstants.MOUSE_MOVE:
            self.pos=self._ioMouse.getPosition()
        
    def translate_key_message(self,event):
        key = 0
        mod = 0
        if len(event) >0 :
            key = event[0]           
            self.keys.append(pylink.KeyInput(key,mod))
        return key

    def get_input_key(self):
        #keep the psychopy window happy ;)
        if currentSecTime()-self._lastMsgPumpTime>self.IOHUB_HEARTBEAT_INTERVAL:                
            # try to keep ioHub, being blocked. ;(
            if self._iohub_server:
                for dm in self._iohub_server.deviceMonitors:
                    dm.device._poll()
                self._iohub_server._processDeviceEventIteration()
            self._lastMsgPumpTime=currentSecTime()                
        if len(self.keys) > 0:
            k= self.keys
            self.keys=[]
            return k
        else:
            return None

    def _createStim(self):        

        class StimSet(object):
            def __setattr__(self, item, value):
                if item in self.__dict__: 
                    i=self.__dict__['_stimNameList'].find(item)
                    self.__dict__['_stimValueList'][i]=value
                else:
                    if '_stimNameList' not in self.__dict__:
                        self.__dict__['_stimNameList']=[]
                        self.__dict__['_stimValueList']=[]
                        self.__dict__['_stimNameList'].append(item)
                        self.__dict__['_stimValueList'].append(value)
                self.__dict__[item]=value
            
            def updateStim(self,name,**kwargs):
                astim=getattr(self,name)
                if isinstance(astim,OrderedDict):
                    for stimpart in astim.itervalues():
                        for argName,argValue in kwargs.iteritems():
                            a=getattr(stimpart,argName)
                            if callable(a):
                                a(argValue)
                            else:    
                                setattr(stimpart,argName,argValue)
                else:
                    for argName,argValue in kwargs.iteritems():
                        a=getattr(astim,argName)
                        if callable(a):
                            a(argValue)
                        else:    
                            setattr(astim,argName,argValue)

            def draw(self):
                for s in self._stimValueList:                    
                    if isinstance(s,OrderedDict):
                        for stimpart in s.itervalues():
                            stimpart.draw()
                    else:
                        s.draw()
                        
        self.calStim=StimSet()
                
        self.calStim.calibrationPoint=OrderedDict()
        self.calStim.calibrationPoint['OUTER'] = visual.Circle(
                                self.window,
                                pos=(0,0),
                                lineWidth=1.0, 
                                lineColor=self.CALIBRATION_POINT_OUTER_COLOR, 
                                lineColorSpace='rgb255',
                                fillColor=self.CALIBRATION_POINT_OUTER_COLOR, 
                                fillColorSpace='rgb255',
                                radius=self.CALIBRATION_POINT_OUTER_RADIUS,                    
                                name='CP_OUTER', 
                                units='pix',
                                opacity=1.0, 
                                interpolate=False)

        self.calStim.calibrationPoint['INNER'] = visual.Circle(
                                self.window,
                                pos=(0,0),lineWidth=1.0,
                                lineColor=self.CALIBRATION_POINT_INNER_COLOR, 
                                lineColorSpace='rgb255',
                                fillColor=self.CALIBRATION_POINT_INNER_COLOR, 
                                fillColorSpace='rgb255', 
                                radius=self.CALIBRATION_POINT_INNER_RADIUS,
                                name='CP_INNER',
                                units='pix',
                                opacity=1.0, 
                                interpolate=False)

        self.imageStim=StimSet()
        self.imageStim.imageTitle = visual.TextStim(self.window, 
                                                    text = "EL CAL", 
                                                    pos=(0,0), 
                                                    units='pix', 
                                                    alignHoriz='center')        
        
    def setup_cal_display(self):
        self.window.flip(clearBuffer=True)

    def exit_cal_display(self):
        self.window.flip(clearBuffer=True)

    def record_abort_hide(self):
        pass

    def clear_cal_display(self):
        self.window.flip(clearBuffer=True)
        
    def erase_cal_target(self):
        self.window.flip(clearBuffer=True)
        
    def draw_cal_target(self, x, y):
        self.width/2
        self.calStim.updateStim('calibrationPoint',
                                setPos=(x-self.width/2,-(y-self.height/2)))  
        self.calStim.draw()
        self.window.flip(clearBuffer=True)
        
    def play_beep(self, beepid):
        pass
                    
    def exit_image_display(self):
        self.window.flip(clearBuffer=True)

    def alert_printf(self,msg):
        print2err('**************************************************')
        print2err('EYELINK CG ERROR: %s'%(msg))
        print2err('**************************************************')
        
    def image_title(self, text):
        self.imageStim.updateStim('imageTitle',setText=text)
        self.imageStim.draw()        
        self.window.flip(clearBuffer=True)

############# From Pyglet Custom Graphics #####################################
#
## NOT YET CONVERTED
#
#
#
###############################################################################
#
#
#   pyglet impl.
    def get_mouse_state(self):
        #print2err('get_mouse_state entered')
        if len(self.pos) > 0 :
            l = (int)(self.width*0.5-self.width*0.5*0.75)
            r = (int)(self.width*0.5+self.width*0.5*0.75)
            b = (int)(self.height*0.5-self.height*0.5*0.75)
            t = (int)(self.height*0.5+self.height*0.5*0.75)

            mx, my = 0,0
            if self.pos[0]<l:
                mx = l
            elif self.pos[0] >r:
                mx = r
            else:
                mx = self.pos[0]

            if self.pos[1]<b:
                my = b
            elif self.pos[1]>t:
                my = t
            else:
                my = self.pos[1]

            mx = (int)((mx-l)*self.img_size[0]//(r-l))
            my = self.img_size[1] - (int)((my-b)*self.img_size[1]//(t-b))
            #ioHub.print2err('get_mouse_state exiting')
            return ((mx, my),self.state)
        else:
            #ioHub.print2err('get_mouse_state exiting')
            return((0,0), 0)

###############################################################################
#
#
#   PYGLET IMP.
    def setup_image_display(self, width, height):
        #ioHub.print2err('setup_image_display entered')
        self.img_size = (width,height)
        self.window.clearBuffer()
        self.window.flip(clearBuffer=True)
        #ioHub.print2err('setup_image_display exiting')
      
###############################################################################
#
#   PYGLET Imp.
    def draw_image_line(self, width, line, totlines,buff):
        pass
#        ioHub.print2err('draw_image_line entered')
#        i =0
#        while i <width:
#            if buff[i]>=len(self.pal):
#                buff[i]=len(self.pal)-1
#            self.imagebuffer.append(self.pal[buff[i]&0x000000FF])
#            i = i+1
#        if line == totlines:
#            #asp = ((float)(self.size[1]))/((float)(self.size[0]))
#            asp = 1
#            r = (float)(self.width*0.5-self.width*0.5*0.75)
#            l = (float)(self.width*0.5+self.width*0.5*0.75)
#            t = (float)(self.height*0.5+self.height*0.5*asp*0.75)
#            b = (float)(self.height*0.5-self.height*0.5*asp*0.75)
#
#            self.window.clearBuffer()
#            
#            tx = (int)(self.width*0.5)
#            ty = b - 30
#            self.stim.drawStim('imageTitle',{'setPos':(tx,ty)})            
#
#            self.draw_cross_hair()
#            glEnable(GL_TEXTURE_RECTANGLE_ARB)
#            glBindTexture(GL_TEXTURE_RECTANGLE_ARB, self.texid.value)
#            glTexParameteri(GL_TEXTURE_RECTANGLE_ARB, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
#            glTexParameteri(GL_TEXTURE_RECTANGLE_ARB, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
#            glTexEnvi( GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE, GL_REPLACE )
#            glTexImage2D( GL_TEXTURE_RECTANGLE_ARB, 0,GL_RGBA8, width, totlines, 0, GL_RGBA, GL_UNSIGNED_BYTE, self.imagebuffer.tostring())
#
#            glBegin(GL_QUADS)
#            glTexCoord2i(0, 0)
#            glVertex2f(r,t)
#            glTexCoord2i(0, self.img_size[1])
#            glVertex2f(r, b)
#            glTexCoord2i(self.img_size[0],self.img_size[1])
#            glVertex2f(l, b)
#            glTexCoord2i(self.img_size[1],0)
#            glVertex2f(l, t)
#            glEnd()
#            glDisable(GL_TEXTURE_RECTANGLE_ARB)
#            self.draw_cross_hair()
#
#            self.window.flip(clearBuffer=True)
#            
#            self.imagebuffer = array.array('I')
#        ioHub.print2err('draw_image_line exiting')


###############################################################################
#
#   Pyglet impl.
    def draw_line(self,x1,y1,x2,y2,colorindex):
        pass
#    
#        ioHub.print2err('draw_line entered')
#        if colorindex   ==  pylink.CR_HAIR_COLOR:          color = (1.0,1.0,1.0,1.0)
#        elif colorindex ==  pylink.PUPIL_HAIR_COLOR:       color = (1.0,1.0,1.0,1.0)
#        elif colorindex ==  pylink.PUPIL_BOX_COLOR:        color = (0.0,1.0,0.0,1.0)
#        elif colorindex ==  pylink.SEARCH_LIMIT_BOX_COLOR: color = (1.0,0.0,0.0,1.0)
#        elif colorindex ==  pylink.MOUSE_CURSOR_COLOR:     color = (1.0,0.0,0.0,1.0)
#        else: color =(0.0,0.0,0.0,0.0)
#
#        #asp = ((float)(self.size[1]))/((float)(self.size[0]))
#        asp = 1
#        r = (float)(self.width*0.5-self.width*0.5*0.75)
#        l = (float)(self.width*0.5+self.width*0.5*0.75)
#        t = (float)(self.height*0.5+self.height*0.5*asp*0.75)
#        b = (float)(self.height*0.5-self.height*0.5*asp*0.75)
#
#        x11= float(float(x1)*(l-r)/float(self.img_size[0]) + r)
#        x22= float(float(x2)*(l-r)/float(self.img_size[0]) + r)
#        y11= float(float(y1)*(b-t)/float(self.img_size[1]) + t)
#        y22= float(float(y2)*(b-t)/float(self.img_size[1]) + t)
#
##        glBegin(GL_LINES)
##        glColor4f(color[0],color[1],color[2],color[3] )
##        glVertex2f(x11,y11)
##        glVertex2f(x22,y22)
##        glEnd()
#        ioHub.print2err('draw_line exiting')
#        

###############################################################################
#
#   Pyglet Implementation
    def draw_lozenge(self,x,y,width,height,colorindex):
        pass
#        ioHub.print2err('draw_lozenge entered')
#        if colorindex   ==  pylink.CR_HAIR_COLOR:          color = (1.0,1.0,1.0,1.0)
#        elif colorindex ==  pylink.PUPIL_HAIR_COLOR:       color = (1.0,1.0,1.0,1.0)
#        elif colorindex ==  pylink.PUPIL_BOX_COLOR:        color = (0.0,1.0,0.0,1.0)
#        elif colorindex ==  pylink.SEARCH_LIMIT_BOX_COLOR: color = (1.0,0.0,0.0,1.0)
#        elif colorindex ==  pylink.MOUSE_CURSOR_COLOR:     color = (1.0,0.0,0.0,1.0)
#        else: color =(0.0,0.0,0.0,0.0)
#
#        width=int((float(width)/float(self.img_size[0]))*self.img_size[0])
#        height=int((float(height)/float(self.img_size[1]))*self.img_size[1])
#
#        #asp = ((float)(self.size[1]))/((float)(self.size[0]))
#        asp = 1
#        r = (float)(self.width*0.5-self.width*0.5*0.75)
#        l = (float)(self.width*0.5+self.width*0.5*0.75)
#        t = (float)(self.height*0.5+self.height*0.5*asp*0.75)
#        b = (float)(self.height*0.5-self.height*0.5*asp*0.75)
#
#        x11= float(float(x)*(l-r)/float(self.img_size[0]) + r)
#        x22= float(float(x+width)*(l-r)/float(self.img_size[0]) + r)
#        y11= float(float(y)*(b-t)/float(self.img_size[1]) + t)
#        y22= float(float(y+height)*(b-t)/float(self.img_size[1]) + t)
#
#        r=x11
#        l=x22
#        b=y11
#        t=y22
#
#        #glColor4f(color[0],color[1],color[2],color[3])
#
#        xw = math.fabs(float(l-r))
#        yw = math.fabs(float(b-t))
#        sh = min(xw,yw)
#        rad = float(sh*0.5)
#
#        x = float(min(l,r)+rad)
#        y = float(min(t,b)+rad)
#
#        if xw==sh:
#            st = 180
#        else:
#            st = 90
#        glBegin(GL_LINE_LOOP)
#        i=st
#        degInRad = (float)(float(i)*(3.14159/180.0))
#
#        for i in range (st, st+180):
#            degInRad = (float)(float(i)*(3.14159/180.0))
#            glVertex2f((float)(float(x)+math.cos(degInRad)*rad),float(y)+(float)(math.sin(degInRad)*rad))
#
#        if xw == sh:    #short horizontally
#            y = (float)(max(t,b)-rad)
#        else:  		  # short vertically
#            x = (float)(max(l,r)-rad)
#
#        i = st+180
#        for i in range (st+180, st+360):
#            degInRad = (float)(float(i)*(3.14159/180.0))
#            glVertex2f((float)(float(x)+math.cos(degInRad)*rad),float(y)+(float)(math.sin(degInRad)*rad))
#
#        glEnd()
#        ioHub.print2err('draw_lozenge exiting')

###############################################################################
#
#   PYGLET Imp.
    def set_image_palette(self, r,g,b):
        #ioHub.print2err('set_image_palette entered')
        self.imagebuffer = array.array('I')
        self.clear_cal_display()
        sz = len(r)
        i =0
        self.pal = []
        while i < sz:
            rf = int(r[i])
            gf = int(g[i])
            bf = int(b[i])
            if self.byteorder:
                self.pal.append(0xff<<24|(bf<<16)|(gf<<8)|(rf))
            else:
                self.pal.append((rf<<24)|(gf<<16)|(bf<<8)|0xff)
            i = i+1
        #ioHub.print2err('set_image_palette exiting')
        
