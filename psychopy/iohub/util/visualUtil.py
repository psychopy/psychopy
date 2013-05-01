# -*- coding: utf-8 -*-
"""
Created on Wed Nov 07 20:58:25 2012

@author: Sol

"""
from __future__ import division

import time
import weakref

import scipy
from ... import visual

from ..devices import Computer

from .exception_tools import ioHubError
from . import win32MessagePump
 
#
## Create a FullScreenWindow based on an ioHub Displays settings
# 

class FullScreenWindow(visual.Window):
    def __init__(self,iohub_display,res=None,color=[128,128,128], colorSpace='rgb255',
                 winType='pyglet',gamma=1.0,fullscr=True,allowGUI=False,
                 waitBlanking=True):
        if res == None:
            res=iohub_display.getPixelResolution()
        visual.Window.__init__(self,res,monitor=iohub_display.getPsychopyMonitorName(),
                                    units=iohub_display.getCoordinateType(),
                                    color=color, colorSpace=colorSpace,
                                    fullscr=fullscr,
                                    allowGUI=allowGUI,
                                    screen=iohub_display.getIndex(),
                                    waitBlanking=waitBlanking,
                                    winType=winType, 
                                    gamma=gamma
                                    )
            
    def flip(self,clearBuffer=True):
        visual.Window.flip(self,clearBuffer)
        return Computer.getTime()

###########################################
#
# ScreenState Class------------------------------------------------------------
#
class ScreenState(object):
    _currentState=None
    experimentRuntime=None
    window=None
    def __init__(self,experimentRuntime=None, eventTriggers=None, timeout=None, 
                 background_color=(255,255,255)):
                                 
        if ScreenState.experimentRuntime is None:
            ScreenState.experimentRuntime=weakref.ref(experimentRuntime)
            ScreenState.window=weakref.ref(experimentRuntime.window)
            
        w,h=self.experimentRuntime().devices.display.getPixelResolution()
        self._screen_background_fill=visual.Rect(self.window(), w, h, 
                                     lineColor=background_color, lineColorSpace='rgb255',
                                     fillColor=background_color, fillColorSpace='rgb255',
                                     units='pix',name='BACKGROUND', 
                                     opacity=1.0, interpolate=False)

        self.stim=dict()
        self.stimNames=[]

        if isinstance(eventTriggers,Trigger):
            eventTriggers=[eventTriggers,]
        elif eventTriggers is None:
            eventTriggers=[]
            
        self.event_triggers=eventTriggers
        self._start_time=None
        self.timeout=timeout
        self.dirty=True

    def setScreenColor(self,rgbColor):
        #self.window().setColor(rgbColor,'rgb255')
        self._screen_background_fill.setFillColor(color=rgbColor,colorSpace='rgb255')
        self._screen_background_fill.setLineColor(color=rgbColor,colorSpace='rgb255')
        self.dirty=True

    def setEventTriggers(self,triggers):
        self.event_triggers=[]
        if isinstance(triggers,Trigger):
            triggers=[triggers,]
        self.event_triggers=triggers

    def addEventTrigger(self,trigger):
        if isinstance(trigger,Trigger):
            self.event_triggers.append(trigger)
        else:
            raise ioHubError("Triggers added to a screen state object must be of type DeviceEventTrigger.")

    def getStateStartTime(self):
        return self._start_time
        
    def getEventTriggers(self):
        return self.event_triggers
        
    def setTimeout(self,timeout):
        self.timeout=timeout

    # switches to screen state (draws and flips)
    # records flip time as start time for timer if timeout has been specified.
    # monitors the device.getEvents function ptrs that are available and if any events are returned,
    # checks the events against the event masks dict provided. If an event matches, it causes method to return
    # then, if no event masks are provided and an event is received, it will cause the method to return regardless
    # of event type for that device.
    # Otherwise method does not reurn until timeout seconds has passed.
    # Returns: [flip_time, time_since_flip, event]
    #          all elements but flip_time may be None. All times are in sec.msec
    def switchTo(self,clearEvents=True,msg=None):
        """
        Switches to the screen state defined by the class instance. The screen
        stim and built and a flip occurs. 
        
        Three conditions can cause the switchTo method to then return, 
        based on whether a timeout and / or DeviceEventTriggers
        have been set with the Screen state when switchTo is called. In all cases 
        a tuple of three values is returned, some elements of which may be None
        depending on what resulted in the state exit. The three conditions are:
            
            #. If no timeout or DeviceEventTriggers have been specified with the ScreenState, switchto() returns after the window.flip() with::
                
                    (stateStartTime, None, None)
                
               where stateStartTime is the time the call to flip() returned.
            
            #. If a timeout has been specified, and that amount of time elapses from the startStartTime, then switchTo() returns with::

                    (stateStartTime, stateDuration, None)
                
               where:
                   
                      * stateStartTime is the time the call to flip() returned.
                      * stateDuration is the time switchTo() returned minus
                      * stateStartTime; so it should be close to the timeout specified. It may be rounded to the next flip() time interval if something in the state is causing the screen to be updated each frame.
            
            #. If 1 - N DeviceEventTriggers have been set with the ScreenState, they are monitored to determine if any have triggered. 
               If a DeviceEventTrigger has triggered, the triggering event and the triggers callback function are retrieved. 
               The deviceEventTrigger is then reset, and the callback is called.
            
        If a callback returns True, the ScreenState is exited, returning (stateStartTime, stateDuration, exitTriggeringEvent), where:

                * **stateStartTime** is the time the call to flip() returned.
                * **stateDuration** is the time switchTo() returned minus stateStartTime; so it should be close to the timeout specified. It may be rounded to the next flip() time interval if something in the state is causing the screen to be updated each frame.
                * **exitTriggeringEvent** is the Device event (in dict form) that caused the ScreenState to exit.
            
        If the callback returns False, the ScreenState is not exited, and the the timeout period and DeviceEventTriggers cintinue to be checked.
         """       
        ER=self.experimentRuntime()
        localClearEvents=ER.hub.clearEvents
        if clearEvents is False:
            localClearEvents = lambda clearEvents: clearEvents==None

        event_triggers=self.event_triggers

        for trigger in event_triggers:        
            trigger.resetTrigger()

        currentSec=Computer.currentSec        
        lastMsgPumpTime=0
        self.build()
        self._start_time=self.flip(text=msg)
        endTime=self._start_time+self.timeout
        localClearEvents('all')

        if event_triggers and len(event_triggers)>0:
            while currentSec()+0.002<endTime:
                for trigger in event_triggers:
                    if trigger.triggered() is True:

                        event=trigger.getTriggeringEvent()
                        functionToCall,kwargs=trigger.getTriggeredStateCallback()

                        trigger.resetLastTriggeredInfo()

                        if functionToCall:
                            exitState=functionToCall(self._start_time, currentSec()-self._start_time, event, **kwargs)
                            if exitState is True:
                                localClearEvents('all')
                                Trigger.clearEventHistory()
                                return self._start_time, currentSec()-self._start_time, event
                        break

                Trigger.clearEventHistory()

                tempTime=currentSec()
                if tempTime+0.002<endTime:
                    time.sleep(0.001)

                    if tempTime-lastMsgPumpTime>0.5:
                        win32MessagePump()
                        lastMsgPumpTime=tempTime

            localClearEvents('all')
            while currentSec()<endTime:
                pass
            return self._start_time, currentSec()-self._start_time, None

        elif self.timeout is not None:
            ER.hub.wait(self.timeout-0.002)
            localClearEvents('all')

            while currentSec()<endTime:
                pass

            return self._start_time,currentSec()-self._start_time,None

        return self._start_time, None, None

    def build(self):
        self._screen_background_fill.draw()
        for stimName in self.stimNames:
            self.stim[stimName].draw()
        self.dirty=False

    def flip(self,text=None):
        if self.dirty:
            self.build()
        ftime=self.window().flip()
        ScreenState._currentState=self
        if text is not None:
            flipText="%s : flip_time [%.6f]"%(text,ftime)
            self.sendMessage(flipText,ftime)
        return ftime

    def sendMessage(self, text, mtime=None):
        if mtime is None:
            mtime=Computer.currentSec()
        mtext=text
        try:
            tracker=self.experimentRuntime().getDevice('tracker')
            if tracker is not None and tracker.isConnected() is True:
                mtext="%s : tracker_time [%.6f]"%(mtext, tracker.trackerSec())
                tracker.sendMessage(mtext)
            else:
                print '----------------------'
                print 'Warning: eyetracker is not connected.'
                print 'Msg not sent to eyetracker datafile: '
                print mtext
                print '----------------------'
        except:
            pass
        self.experimentRuntime().hub.sendMessageEvent(mtext,sec_time=mtime)

    @classmethod
    def getCurrentScreenState(cls):
        return cls._currentState

class ClearScreen(ScreenState):
    def __init__(self,experimentRuntime, eventTriggers=None, timeout=None, background_color=(255,255,255)):
        ScreenState.__init__(self,experimentRuntime, eventTriggers, timeout,background_color)

    def flip(self, text=None):
        if text is None:
            text="CLR_SCREEN SYNC: [%s] "%(text)
        return ScreenState.flip(self,text)
        

class InstructionScreen(ScreenState):
    def __init__(self,experimentRuntime, text='Default Text', eventTriggers=None, timeout=None, 
                 text_color=[0,0,0], text_pos=[0,0], text_height=32, background_color=(255,255,255)):
        
        ScreenState.__init__(self,experimentRuntime, eventTriggers, timeout, background_color)

        l,t,r,b=self.experimentRuntime().devices.display.getBounds()
        self.stim['TEXTLINE']=visual.TextStim(self.window(), text=text, 
                    pos = text_pos, height=text_height, color=text_color,
                    colorSpace='rgb255',alignHoriz='center',alignVert='center',units='pix',
                    wrapWidth=(r-l)*.9)                    
        self.stimNames.append('TEXTLINE')

    def setText(self,text):
        self.stim['TEXTLINE'].setText(text)
        self.dirty=True

    def setTextColor(self,rgbColor):
        self.stim['TEXTLINE'].setColor(rgbColor,'rgb255')
        self.dirty=True

    def setTextSize(self,size):
        self.stim['TEXTLINE'].setSize(size)
        self.dirty=True

    def setTextPosition(self,pos):
        self.stim['TEXTLINE'].setPos(pos)

    def flip(self, text=''):
        if text is None:
            text="INSTRUCT_SCREEN SYNC: [%s] [%s] "%(self.stim['TEXTLINE'].text[0:30],text)
        return ScreenState.flip(self,text)


class ImageScreen(ScreenState):
    def __init__(self, experimentRuntime, imageName, imagePos=(0,0), 
                 imageSize=None, eventTriggers=None, timeout=None, 
                 background_color=(255,255,255)):
        
        ScreenState.__init__(self, experimentRuntime, eventTriggers, 
                             timeout, background_color)
                             
        w, h = self.experimentRuntime().devices.display.getPixelResolution()

        if imageSize is None:
            from PIL import Image
            imageSize=Image.open(imageName).size

        self.stim['IMAGE'] = visual.ImageStim(self.window(), image=imageName, 
                                pos=imagePos, size=imageSize,name=imageName)
                                
        self.stim['IMAGE'].imageName=imageName        
        self.stimNames.append('IMAGE')

    def setImage(self, imageName):
        self.stim['IMAGE'].setImage(imageName)
        self.stim['IMAGE'].imageName=imageName 
        self.dirty = True

    def setImageSize(self, size=None):
        if size is None:
            from PIL import Image
            size=Image.open(self.stim['IMAGE'].imageName).size

        self.stim['IMAGE'].setSize(size)
        self.dirty = True

    def setImagePosition(self, pos):
        self.stim['IMAGE'].setPos(pos)

    def flip(self, text=''):
        if text is None:
            text = "IMAGE_SCREEN SYNC: [%s] [%s] " % (self.stim['IMAGE'].imageName, text)
        return ScreenState.flip(self, text)


# Trigger Classes ---------------------------------------------------

class Trigger(object):
    __slots__=['trigger_function', 'user_kwargs', '_last_triggered_event','repeat_count','triggerred_count']
    
    def __init__(self,trigger_function = lambda a,b,c: True==True, user_kwargs={}, repeat_count=0):
        self.trigger_function=trigger_function
        self.user_kwargs=user_kwargs
        self._last_triggered_event=None
        self.repeat_count=repeat_count
        self.triggerred_count=0
        
    def triggered(self):
        if self.repeat_count >=0 and self.triggerred_count>self.repeat_count:
            return False
        return True

    def getTriggeringEvent(self):
        return self._last_triggered_event
        
    def getTriggeredStateCallback(self):
        return self.trigger_function,self.user_kwargs

    def resetLastTriggeredInfo(self):
        self._last_triggered_event=None
        
    def resetTrigger(self):
        self.resetLastTriggeredInfo()
        self.triggerred_count=0

    @classmethod
    def clearEventHistory(cls):
        pass

    
# Device EventTrigger Class ---------------------------------------------------

class DeviceEventTrigger(Trigger):
    """
    DeviceEventTrigger are used by SCreenState objects. A DeviceEventTrigger
    associates a set of conditions for a DeviceEvent that must be met before
    the classes triggered() method returns True. 
    """
    _lastEventsByDevice=dict()
    __slots__=['device','event_type','event_attribute_conditions']
    def __init__(self, device, event_type, event_attribute_conditions={}, repeat_count=-1,
                     trigger_function = lambda a,b,c: True==True, user_kwargs={} ):
        Trigger.__init__(self,trigger_function,user_kwargs,repeat_count)

        self.device=device
        self.event_type=event_type
        self.event_attribute_conditions=event_attribute_conditions

    def triggered(self):
        if Trigger.triggered(self) is False:
            return False
            
        events=self.device.getEvents()

        if events is None:
            events=[]
        newEventCount=len(events)

        unhandledEvents=[]

        if newEventCount > 0:
            if self.device in self._lastEventsByDevice:
                self._lastEventsByDevice[self.device].extend(events)
            else:
                self._lastEventsByDevice[self.device]=events
            unhandledEvents=self._lastEventsByDevice[self.device]

        elif self.device in self._lastEventsByDevice:
            unhandledEvents=self._lastEventsByDevice[self.device]


        for event in unhandledEvents:
            foundEvent=True

            if event.type != self.event_type:
                foundEvent=False
            else:
                for attrib_name,the_conditions in self.event_attribute_conditions.iteritems():
                    if isinstance(the_conditions,(list,tuple)) and getattr(event,attrib_name) in the_conditions:
                        # event_value is a list or tuple of possible values that are OK
                        pass
                    elif getattr(event,attrib_name) is the_conditions or getattr(event,attrib_name) == the_conditions:
                        # event_value is a single value
                        pass
                    else:
                        foundEvent=False
                        
            if foundEvent is True:
                self._last_triggered_event=event
                self.triggerred_count+=1
                return True

        return False

    @classmethod
    def clearEventHistory(cls):
        cls._lastEventsByDevice.clear()

    def resetLastTriggeredInfo(self):
        Trigger.resetLastTriggeredInfo(self)
        if self.device in self._lastEventsByDevice:
            self._lastEventsByDevice[self.device]=None
            del self._lastEventsByDevice[self.device]


   
class TimeTrigger(Trigger):
    """
    TimeTrigger's are used by ScreenState objects. A TimeTrigger
    associates a delay from the provided start_time parameter to when
    the classes triggered() method returns True. start_time and delay can each be
    sec.msec float, or a callable object (that takes no parameters).
    """
    __slots__=['start_time','delay']
    def __init__(self, start_time, delay, repeat_count=0, trigger_function = lambda a,b,c: True==True, user_kwargs={}):
        Trigger.__init__(self,trigger_function,user_kwargs,repeat_count=0)

        sFunc=start_time
        if not callable(start_time):
            def startTimeFunc():
                return start_time
            sFunc=startTimeFunc
        self.start_time=sFunc
        
        dFunc=delay
        if not callable(delay):
            def delayFunc():
                return delay
            dFunc=delayFunc
        self.delay=dFunc
        
    def triggered(self):
        if Trigger.triggered(self) is False:
            return False
            
        ct=Computer.getTime()
        if ct-self.start_time()>=self.delay():
            self._last_triggered_event=ct
            self.triggerred_count+=1
            return True
        return False


####################################################################################

#
## MovementPatterns for Visual Stimuli
#

# sinusoidal movement pattern, based on code posted by
# Michael MacAskill @ psychopy-users:
# https://groups.google.com/forum/psychopy-users

# Changed:
#   - made code class based
#   - does not use current time for target position calc, but time of next
#    retrace start
#   -this tries to ensure a more consistent motion, regardless of when the
#    position update is applied to the stimulus during the retrace interval


pi     = scipy.pi
dot    = scipy.dot
sin    = scipy.sin
cos    = scipy.cos
ar     = scipy.array
rand   = scipy.rand
arange = scipy.arange
rad    = scipy.deg2rad

  
class SinusoidalMotion(object):
    def __init__(self, 
                 amplitude_xy=(15.0,0.0), # max horizontal, vertical excursion
                 peak_velocity_xy=(10.0,10.0), # deg/s peak velocity x , y
                 phase_xy=(90.0,90.0),      # in degrees for x, y
                 display=None,              # ioHub display class
                 start_time=0.0,             # in seconds , 0.0 means use first flip time
                 ):       
        self.amplX , self.amplY = amplitude_xy 
        self.peakVelX, self.peakVelY = peak_velocity_xy
        self.phaseX, self.phaseY = rad(phase_xy[0]), rad(phase_xy[1])
        self.startTime=start_time        
        self.lastPositionTime = None
        self.nextFlipTimeEstimate=None

        self.reportedRetraceInterval=display.getRetraceInterval()
        print "Display retrace interval: ", self.reportedRetraceInterval
        
        # calculate the omega constants needed for the simple 
        # harmonic motion equations: 
        
        self.wX = 0.0         
        if self.amplX != 0.0: 
            self.freqX = self.peakVelX/(-2.0*self.amplX*pi)
            self.wX = 2.0*pi*self.freqX

        self.wY = 0.0 
        if self.amplY != 0: 
            self.freqY = self.peakVelY/(-2.0*self.amplY*pi)
            self.wY = 2.0*pi*self.freqY

    def getPos(self):
        t=0.0
        if self.lastPositionTime:

            nextFlipTimeEstimate=self.lastPositionTime+self.reportedRetraceInterval
            while nextFlipTimeEstimate < Computer.getTime():
                nextFlipTimeEstimate+=self.reportedRetraceInterval
            self.nextFlipTimeEstimate=nextFlipTimeEstimate

            t=nextFlipTimeEstimate-self.startTime

        self.pos=(self.amplX*cos(self.wX*t + self.phaseX),
                  self.amplY*sin(self.wY*t + self.phaseY))

        return self.pos

    def setLastFlipTime(self,t):
        if self.lastPositionTime is None:
            self.startTime=t
        self.lastPositionTime=t
