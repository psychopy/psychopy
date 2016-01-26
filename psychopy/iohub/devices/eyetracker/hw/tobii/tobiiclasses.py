"""
ioHub
Common Eye Tracker Interface
.. file: ioHub/devices/eyetracker/hw/tobii/tobiiclasses.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

import Queue
import exceptions
import time
import collections
import copy
import sys

import numpy as np
from psychopy.iohub import Computer, OrderedDict, print2err, printExceptionDetailsToStdErr
from psychopy.iohub.devices import ioDeviceError
getTime=Computer.getTime

_USING_PYTHON_2_7=True
try:
    majorv,minorv=sys.version_info[0:2]
    if majorv == 2 and minorv == 6:
        _USING_PYTHON_2_7=False
        import tobii.sdk as TobiiPy
        from tobii.sdk.mainloop import Mainloop as TobiiPyMainloop
        from tobii.sdk.mainloop import MainloopThread as TobiiPyMainloopThread
        from tobii.sdk.browsing import EyetrackerBrowser as TobiiPyEyetrackerBrowser
        from tobii.sdk.eyetracker import EyeTracker as TobiiPyEyeTracker
        from tobii.sdk.time.clock import Clock as TobiiPyClock
        from tobii.sdk.time.sync import SyncManager as TobiiPySyncManager
        from tobii.sdk.types import Point2D, Point3D
    else:
        import tobii.eye_tracking_io as TobiiPy
        from tobii.eye_tracking_io.mainloop import Mainloop as TobiiPyMainloop
        from tobii.eye_tracking_io.mainloop import MainloopThread as TobiiPyMainloopThread
        from tobii.eye_tracking_io.browsing import EyetrackerBrowser as TobiiPyEyetrackerBrowser
        from tobii.eye_tracking_io.eyetracker import Eyetracker as TobiiPyEyeTracker
        from tobii.eye_tracking_io.time.clock import Clock as TobiiPyClock
        from tobii.eye_tracking_io.time.sync import SyncManager as TobiiPySyncManager
        from tobii.eye_tracking_io.time.sync import State as TobiiPySyncState
        from tobii.eye_tracking_io.types import Point2D, Point3D
except Exception:
    # This only happens when it is Sphinx auto-doc loading the file
    printExceptionDetailsToStdErr()

# Tobii Tracker Browser / Detection Services

class BrowserEvent(object):
    _event_types=dict(BROWSER_EVENT=0,TRACKER_FOUND=1,TRACKER_UPDATE=2,TRACKER_REMOVED=3)
    _event_types.update([(v,k) for k,v in _event_types.iteritems()])
    event_type=_event_types['BROWSER_EVENT']
    def __init__(self,tobii_event_type, tracker_info):
        self._tobii_event_type=tobii_event_type
        self.tracker_info=tracker_info
        
class TrackerFoundEvent(BrowserEvent):
    event_type=BrowserEvent._event_types['TRACKER_FOUND']
    def __init__(self,info):
        BrowserEvent.__init__(self,TobiiPyEyetrackerBrowser.FOUND,info)

class TrackerUpdatedEvent(BrowserEvent):
    event_type=BrowserEvent._event_types['TRACKER_UPDATE']
    def __init__(self,info):
        BrowserEvent.__init__(self,TobiiPyEyetrackerBrowser.UPDATED,info)

class TrackerRemovedEvent(BrowserEvent):
    event_type=BrowserEvent._event_types['TRACKER_REMOVED']
    def __init__(self,info):
        BrowserEvent.__init__(self,TobiiPyEyetrackerBrowser.REMOVED,info)

class EyeTrackerEvent(object):
    _event_types=dict(TRACKER_EVENT=0,EYE_TRACKER_CREATED=1)
    _event_types.update([(v,k) for k,v in _event_types.iteritems()])
    event_type=_event_types['TRACKER_EVENT']
    def __init__(self,tracker_object):
        self.tracker_object=tracker_object
        
    def __del__(self):
        self.tracker_object=None

class TobiiTrackerCreatedEvent(EyeTrackerEvent):
    event_type=EyeTrackerEvent._event_types['EYE_TRACKER_CREATED']
    def __init__(self,tracker_object):
        EyeTrackerEvent.__init__(self,tracker_object)
    
class TobiiTrackerBrowser(object):
    _mainloop = None
    _detectedTrackers = OrderedDict()
    _browser=None
    _event_queue=None
    _active=False
    _mainloop_referenced=False
    
    TRACKER_FOUND=1
    TRACKER_UPDATED=2
    TRACKER_DROPPED=3
    
    @classmethod
    def start(cls):
        if TobiiTrackerBrowser._mainloop is None:
            TobiiPy.init()
            TobiiTrackerBrowser._mainloop = TobiiPyMainloopThread()
            TobiiTrackerBrowser._mainloop.start()
            TobiiTrackerBrowser._event_queue=Queue.Queue()
            TobiiTrackerBrowser._browser = TobiiPyEyetrackerBrowser(TobiiTrackerBrowser._mainloop, TobiiTrackerBrowser.on_eyetracker_browser_event)
            cls._active=True
            
    @classmethod       
    def stop(cls,empty_queue=True):
        if cls._active:        
            cls._active=False
            TobiiTrackerBrowser._event_queue.put(None)
            TobiiTrackerBrowser._browser.stop()
            
            if cls._mainloop_referenced is False:
                TobiiTrackerBrowser._mainloop.stop()
                TobiiTrackerBrowser._mainloop = None
            
            if empty_queue is True:
                e=1
                while e!=None:
                    try:            
                        e=TobiiTrackerBrowser.getNextEvent()
                    except Queue.Empty:
                        pass
    
            TobiiTrackerBrowser._browser = None
            TobiiTrackerBrowser._detectedTrackers=OrderedDict()

    @classmethod
    def isActive(cls):
        return cls._active
        
    @classmethod
    def getMainLoop(cls):
        cls._mainloop_referenced=True
        return cls._mainloop
        
    @classmethod    
    def getNextEvent(cls,timeout=None):
        if timeout is None:
            e = TobiiTrackerBrowser._event_queue.get_nowait()
            TobiiTrackerBrowser._event_queue.task_done()
            return e
        e=TobiiTrackerBrowser._event_queue.get(block=True, timeout=timeout)
        TobiiTrackerBrowser._event_queue.task_done()
        return e

    @classmethod
    def on_eyetracker_browser_event(cls, event_type, event_name, eyetracker_info):
        if event_type == TobiiPyEyetrackerBrowser.FOUND:
            TobiiTrackerBrowser._detectedTrackers[eyetracker_info.product_id] = eyetracker_info
            TobiiTrackerBrowser._event_queue.put(TrackerFoundEvent(eyetracker_info))            
            return False

        if event_type == TobiiPyEyetrackerBrowser.UPDATED:
            TobiiTrackerBrowser._detectedTrackers[eyetracker_info.product_id] = eyetracker_info
            TobiiTrackerBrowser._event_queue.put(TrackerUpdatedEvent(eyetracker_info))            
            return False
        
        if TobiiPyEyetrackerBrowser.REMOVED:
            del TobiiTrackerBrowser._detectedTrackers[eyetracker_info.product_id]
            TobiiTrackerBrowser._event_queue.put(TrackerRemovedEvent(eyetracker_info))            
            return False

        raise ioDeviceError(device=cls,msg="TobiiTrackerBrowser.on_eyetracker_browser_event received unhandled event type {0} for Tobii device with info: {1}".format(event_type,eyetracker_info))
        
    @classmethod
    def getTrackerDetails(cls,tracker_product_id):
        tobiiInfoProperties=['product_id','given_name','model','generation','firmware_version','status']
        tprops=OrderedDict()
        eyetracker_info=TobiiTrackerBrowser._detectedTrackers[tracker_product_id]
        for tp in tobiiInfoProperties:
            ta=getattr(eyetracker_info,tp)
            if callable(ta):
                ta=ta()
            tprops[tp]=ta
        tprops['factory_info_string']=str(eyetracker_info.factory_info)
        return tprops
        
    @classmethod
    def getDetectedTrackerList(cls):
        return [t for t in TobiiTrackerBrowser._detectedTrackers.values()]


    @classmethod
    def _checkForMatch(cls,tracker_info,model,product_id):
        if product_id:
            if tracker_info.product_id!=product_id: 
                return False
        if model:
            if model != tracker_info.model:
                return False
        
        return True
       
    @classmethod
    def findDevice(cls, model=None, product_id=None, timeout=10.0):
        tracker_info=None
        
        # check existing detected devices
        matching_tracker_infos=[tracker_info for tracker_info in cls.getDetectedTrackerList() if cls._checkForMatch(tracker_info,model,product_id) is True]
        if matching_tracker_infos:
            return matching_tracker_infos[0]
            
        started_browsing_time=getTime()        
        while(getTime()-started_browsing_time < timeout):
            try:
                tb_event=TobiiTrackerBrowser.getNextEvent(timeout=0.05)
                if tb_event is None:
                    break
                if isinstance(tb_event, TrackerFoundEvent):
                    tracker_info=tb_event.tracker_info
                    if TobiiTrackerBrowser._checkForMatch(tracker_info,model,product_id) is True:
                        return tracker_info
            except Queue.Empty:
                pass



# Tobii Eye Tracker and Time Syncronization Services

class TobiiTracker(object):
    LEFT=0
    RIGHT=1
    eye_data=OrderedDict(tracker_time_usec=np.NaN,
                         pupil_diameter_mm=np.NaN,
                         gaze_norm=[np.NaN,np.NaN],
                         gaze_mm=[np.NaN,np.NaN,np.NaN],
                         eye_location_norm=[np.NaN,np.NaN,np.NaN],
                         eye_location_mm=[np.NaN,np.NaN,np.NaN],
                         validity_code=np.NaN,                           
                         status='UNKNOWN',
                         trigger_signal=None)    
    def __init__(self, eyetracker_info=None, product_id=None, model=None, mainloop=None, create_sync_manager=True):
        self._eyetracker_info=eyetracker_info
        self._requested_product_id=product_id
        self._requested_model=model
        self._mainloop=mainloop
        self._eyetracker=None
        self._queue=None
        self._tobiiClock = None
        self._getTobiiClockResolution=None
        self._getTobiiClockTime=None
        self._sync_manager = None
        self._syncTimeEventDeque=None
        self._isRecording=False

        if eyetracker_info is None:
            if not TobiiTrackerBrowser.isActive():
                TobiiTrackerBrowser.start()
                self._eyetracker_info=TobiiTrackerBrowser.findDevice(model,product_id)
                if self._eyetracker_info:
                    self._mainloop=TobiiTrackerBrowser.getMainLoop()
                TobiiTrackerBrowser.stop()
            else:
                self._eyetracker_info=TobiiTrackerBrowser.findDevice(model,product_id)
        
        if self._eyetracker_info is None:
            raise exceptions.BaseException("Could not find a Tobii Eye Tracker matching requirements.")
            
        if self._mainloop is None:
            if TobiiTrackerBrowser.isActive():                       
                self._mainloop=TobiiTrackerBrowser.getMainLoop()
            else:
                TobiiPy.init()
                self._mainloop = TobiiPyMainloopThread()
                self._mainloop.start()

        self._queue=Queue.Queue()
        
        TobiiPyEyeTracker.create_async(self._mainloop,self._eyetracker_info,self.on_eyetracker_created)
    
        stime=getTime()
        while getTime()-stime<10.0:
            try:            
                event=self._queue.get(block=True,timeout=.1)
                if isinstance(event,TobiiTrackerCreatedEvent):
                    self._eyetracker=event.tracker_object
                    self._eyetracker.events.OnFramerateChanged += self.on_external_framerate_change
                    if hasattr(self._eyetracker.events,'OnHeadMovementBoxChanged'):
                        self._eyetracker.events.OnHeadMovementBoxChanged += self.on_head_box_change
                    elif hasattr(self._eyetracker.events,'OnTrackBoxChanged'):
                        self._eyetracker.events.OnTrackBoxChanged += self.on_head_box_change
                    else:
                        print 'WARNING: TobiiClasses could not set callback hook for "self.on_head_box_change".'
                    self._eyetracker.events.OnXConfigurationChanged += self.on_x_series_physical_config_change
                    
                    break
                self._queue.task_done()
            except Queue.Empty:
                pass
                
        if self._eyetracker is None:
            raise exceptions.BaseException("Could not connect to Tobii. Timeout.")
            
        if create_sync_manager:
            self._eyetracker.events.OnError += self.on_eyetracker_error
            self._tobiiClock = TobiiPyClock()
            self._getTobiiClockResolution=self._tobiiClock.get_resolution
            self._getTobiiClockTime=self._tobiiClock.get_time
            self._syncTimeEventDeque=collections.deque(maxlen=32)
            self._sync_manager = TobiiPySyncManager(self._tobiiClock,
                                         self._eyetracker_info,
                                         self._mainloop,
                                         self.on_sync_error,
                                         self.on_sync_status)

    def on_eyetracker_created(self, *args, **kwargs):
        #print 'on_eyetracker_created: entered' 
        et=None
        if len(args) >=2:
            et=args[1]
        else:
            raise exceptions.BaseException("WARNING: on_eyetracker_created: Unhandled args count",len(args), args)
        
        error = kwargs.get('error',None)
        if error:
            raise exceptions.BaseException("Connection to Tobii failed because of an exception: %s" % (str(error),))

        self._queue.put(TobiiTrackerCreatedEvent(et))
        
        return False
        
    def on_eyetracker_error(self, *args, **kwargs):
        print2err("TobiiTracker.on_eyetracker_error: ",args, kwargs)
        return False

    def on_sync_error(self, *args, **kwargs):
        print2err("TobiiTracker.on_sync_error: ",args, kwargs)
        return False

    def on_sync_status(self, *args, **kwargs):
        sync_state=args[0]
        self._syncTimeEventDeque.append(sync_state)
        return False

    def on_eyetracker_data(self, *args,**kwargs):
        eye_data_event=args[1]
        LEFT=self.LEFT
        RIGHT=self.RIGHT
        
        eyes=(copy.deepcopy(self.eye_data),copy.deepcopy(self.eye_data))
                                    
        eyes[LEFT]['validity_code']=eye_data_event.LeftValidity
        eyes[RIGHT]['validity_code']=eye_data_event.RightValidity
        eyes[LEFT]['tracker_time_usec']=eye_data_event.Timestamp
        eyes[RIGHT]['tracker_time_usec']=eye_data_event.Timestamp
        if hasattr(eye_data_event,'TrigSignal'):
            eyes[LEFT]['trigger_signal']=eye_data_event.TrigSignal
            eyes[RIGHT]['trigger_signal']=eye_data_event.TrigSignal
            
       
        #print "*** lastEyeData.RightGazePoint2D: ",lastEyeData.RightGazePoint2D.__dict__
        if eye_data_event.LeftValidity >=2 and eye_data_event.RightValidity >=2:
            # no eye signal                            
            eyes[LEFT]['status']="Missing"
            eyes[RIGHT]['status']="Missing"
          
        elif eye_data_event.LeftValidity <2 and eye_data_event.RightValidity >=2:
            # left eye only available
            eyes[LEFT]['status']="Available"
            eyes[RIGHT]['status']="Missing"
            
            eyes[LEFT]['pupil_diameter_mm']=eye_data_event.LeftPupil
            eyes[LEFT]['gaze_norm'][0]=eye_data_event.LeftGazePoint2D.x
            eyes[LEFT]['gaze_norm'][1]=eye_data_event.LeftGazePoint2D.y
            eyes[LEFT]['gaze_mm'][0]=eye_data_event.LeftGazePoint3D.x
            eyes[LEFT]['gaze_mm'][1]=eye_data_event.LeftGazePoint3D.y
            eyes[LEFT]['gaze_mm'][2]=eye_data_event.LeftGazePoint3D.z
            eyes[LEFT]['eye_location_norm'][0]=eye_data_event.LeftEyePosition3DRelative.x
            eyes[LEFT]['eye_location_norm'][1]=eye_data_event.LeftEyePosition3DRelative.y
            eyes[LEFT]['eye_location_norm'][2]=eye_data_event.LeftEyePosition3DRelative.z
            eyes[LEFT]['eye_location_mm'][0]=eye_data_event.LeftEyePosition3D.x
            eyes[LEFT]['eye_location_mm'][1]=eye_data_event.LeftEyePosition3D.y
            eyes[LEFT]['eye_location_mm'][2]=eye_data_event.LeftEyePosition3D.z
                        
        elif eye_data_event.LeftValidity >=2 and eye_data_event.RightValidity <2:
            # right eye only available
            eyes[RIGHT]['status']="Available"
            eyes[LEFT]['status']="Missing"
            
            eyes[RIGHT]['pupil_diameter_mm']=eye_data_event.RightPupil
            eyes[RIGHT]['gaze_norm'][0]=eye_data_event.RightGazePoint2D.x
            eyes[RIGHT]['gaze_norm'][1]=eye_data_event.RightGazePoint2D.y
            eyes[RIGHT]['gaze_mm'][0]=eye_data_event.RightGazePoint3D.x
            eyes[RIGHT]['gaze_mm'][1]=eye_data_event.RightGazePoint3D.y
            eyes[RIGHT]['gaze_mm'][2]=eye_data_event.RightGazePoint3D.z
            eyes[RIGHT]['eye_location_norm'][0]=eye_data_event.RightEyePosition3DRelative.x
            eyes[RIGHT]['eye_location_norm'][1]=eye_data_event.RightEyePosition3DRelative.y
            eyes[RIGHT]['eye_location_norm'][2]=eye_data_event.RightEyePosition3DRelative.z
            eyes[RIGHT]['eye_location_mm'][0]=eye_data_event.RightEyePosition3D.x
            eyes[RIGHT]['eye_location_mm'][1]=eye_data_event.RightEyePosition3D.y
            eyes[RIGHT]['eye_location_mm'][2]=eye_data_event.RightEyePosition3D.z
        else:
            # binocular available
            eyes[RIGHT]['status']="Available"
            eyes[LEFT]['status']="Available"
            
            eyes[LEFT]['pupil_diameter_mm']=eye_data_event.LeftPupil
            eyes[LEFT]['gaze_norm'][0]=eye_data_event.LeftGazePoint2D.x
            eyes[LEFT]['gaze_norm'][1]=eye_data_event.LeftGazePoint2D.y
            eyes[LEFT]['gaze_mm'][0]=eye_data_event.LeftGazePoint3D.x
            eyes[LEFT]['gaze_mm'][1]=eye_data_event.LeftGazePoint3D.y
            eyes[LEFT]['gaze_mm'][2]=eye_data_event.LeftGazePoint3D.z
            eyes[LEFT]['eye_location_norm'][0]=eye_data_event.LeftEyePosition3DRelative.x
            eyes[LEFT]['eye_location_norm'][1]=eye_data_event.LeftEyePosition3DRelative.y
            eyes[LEFT]['eye_location_norm'][2]=eye_data_event.LeftEyePosition3DRelative.z
            eyes[LEFT]['eye_location_mm'][0]=eye_data_event.LeftEyePosition3D.x
            eyes[LEFT]['eye_location_mm'][1]=eye_data_event.LeftEyePosition3D.y
            eyes[LEFT]['eye_location_mm'][2]=eye_data_event.LeftEyePosition3D.z

            eyes[RIGHT]['pupil_diameter_mm']=eye_data_event.RightPupil
            eyes[RIGHT]['gaze_norm'][0]=eye_data_event.RightGazePoint2D.x
            eyes[RIGHT]['gaze_norm'][1]=eye_data_event.RightGazePoint2D.y
            eyes[RIGHT]['gaze_mm'][0]=eye_data_event.RightGazePoint3D.x
            eyes[RIGHT]['gaze_mm'][1]=eye_data_event.RightGazePoint3D.y
            eyes[RIGHT]['gaze_mm'][2]=eye_data_event.RightGazePoint3D.z
            eyes[RIGHT]['eye_location_norm'][0]=eye_data_event.RightEyePosition3DRelative.x
            eyes[RIGHT]['eye_location_norm'][1]=eye_data_event.RightEyePosition3DRelative.y
            eyes[RIGHT]['eye_location_norm'][2]=eye_data_event.RightEyePosition3DRelative.z
            eyes[RIGHT]['eye_location_mm'][0]=eye_data_event.RightEyePosition3D.x
            eyes[RIGHT]['eye_location_mm'][1]=eye_data_event.RightEyePosition3D.y
            eyes[RIGHT]['eye_location_mm'][2]=eye_data_event.RightEyePosition3D.z

        return False        

    def on_start_tracking(self, *args,**kwargs):
        return False        

    def on_stop_tracking(self, *args,**kwargs):
        return False   

    def on_external_framerate_change(self, *args,**kwargs):
        print2err("NOTE: Tobii System Sampling Rate Changed.")        
        return False   

    def on_head_box_change(self, *args,**kwargs):
        print2err("NOTE: Tobii Head Movement Box Changed.")        
        return False
    
    def on_x_series_physical_config_change(self, *args, **kwargs):
        print2err("NOTE: Tobii X Series Physical Settings Changed.")        
        return False
        
    def getTimeSyncManager(self):
        return self._sync_manager
        
    def getTimeSyncState(self):
        return self._sync_manager.sync_state()
    
    def getCurrentEyeTrackerTime(self):
        return self._sync_manager.convert_from_local_to_remote(self._getTobiiClockTime())
        
    def getCurrentLocalTobiiTime(self):
        return self._getTobiiClockTime()
        
    def getTobiiTimeResolution(self):
        return self._getTobiiClockResolution()

    def getMainLoop(self):
        return self._mainloop
        
    def getTrackerDetails(self):
        tobiiInfoProperties=['product_id','given_name','model','generation','firmware_version','status']
        tprops=OrderedDict()
        eyetracker_info=self._eyetracker_info
        for tp in tobiiInfoProperties:
            ta=getattr(eyetracker_info,tp)
            if callable(ta):
                ta=ta()
            tprops[tp]=ta
        tprops['factory_info_string']=str(eyetracker_info.factory_info)
        return tprops
    
    def getTrackerInfo(self):
        if hasattr(self._eyetracker,'GetUnitInfo'):
            return self._eyetracker.GetUnitInfo()
        return None
        
    def startTracking(self,et_data_rx_callback=None):
        if et_data_rx_callback:
            self.on_eyetracker_data=et_data_rx_callback
        self._eyetracker.events.OnGazeDataReceived += self.on_eyetracker_data
        self._eyetracker.StartTracking(self.on_start_tracking)
        self._isRecording=True
        return True

    def stopTracking(self): 
        self._eyetracker.events.OnGazeDataReceived -= self.on_eyetracker_data
        self._eyetracker.StopTracking(self.on_stop_tracking)
        self._isRecording=False
        
    def getName(self):
        return self._eyetracker.GetUnitName()

    def setName(self,name):
        self._eyetracker.SetUnitName(name)

    def getLowBlinkMode(self):
        try:
            return self._eyetracker.GetLowblinkMode()
        except Exception:
            pass
        return None

    def setLowBlinkMode(self,enable):
        if hasattr(self._eyetracker,'SetLowblinkMode'):
            try:
                if isinstance(enable,bool) or enable == 0 or enable == 1:
                    self._eyetracker.SetLowblinkMode(enable)
                return self._eyetracker.GetLowblinkMode()
            except Exception:
                pass
        return None
        
    def setSamplingRate(self,rate):
        if rate in self._eyetracker.EnumerateFramerates():
            self._eyetracker.SetFramerate(rate)
            return rate
        return self._eyetracker.GetFramerate()
        
    def getAvailableSamplingRates(self):
        return self._eyetracker.EnumerateFramerates()

    def getSamplingRate(self):
        return self._eyetracker.GetFramerate()
    
    def getIlluminationMode(self):
        try:
            return self._eyetracker.getIlluminationMode()
        except Exception:
            pass
        return None
        
    def getAvailableIlluminationModes(self):
        try:
            return self._eyetracker.EnumerateIlluminationModes()
        except Exception:
            return []

    def setIlluminationMode(self,imode):
        imodes=self.getAvailableIlluminationModes()
        if len(imodes)>0:
            if imode in imodes:
                self._eyetracker.SetIlluminationMode(imode)
                return imode
            return self._eyetracker.getIlluminationMode()
        else:
            print 'WARNING: setIlluminationMode is not supported by either your Tobii model, or the version of the Tobii SDK being used.'
            
    def getHeadBox(self):
        hb=None
        if hasattr(self._eyetracker,'GetTrackBox'): 
            hb=self._eyetracker.GetTrackBox()
        elif hasattr(self._eyetracker,'GetHeadMovementBox'):
            hb=self._eyetracker.GetHeadMovementBox()
        
        if hb:        
            return np.asarray([
                            (hb.Point1.x,hb.Point1.y,hb.Point1.z),
                            (hb.Point2.x,hb.Point2.y,hb.Point2.z),
                            (hb.Point3.x,hb.Point3.y,hb.Point3.z),
                            (hb.Point4.x,hb.Point4.y,hb.Point4.z),
                            (hb.Point5.x,hb.Point5.y,hb.Point5.z),
                            (hb.Point6.x,hb.Point6.y,hb.Point6.z),
                            (hb.Point7.x,hb.Point7.y,hb.Point7.z),
                            (hb.Point8.x,hb.Point8.y,hb.Point8.z)
                            ])
        return None
        
    def setXSeriesPhysicalPlacement(self, upperLeft, upperRight, lowerLeft):
        if self.getTrackerDetails()['generation'] == 'X':        
            self._eyetracker.SetXConfiguration(upperLeft, 
                                               upperRight, 
                                               lowerLeft)
            return True
        return False

    def getEyeTrackerPhysicalPlacement(self):
        etpc= self._eyetracker.GetXConfiguration()
        ll=etpc.LowerLeft
        ul=etpc.UpperLeft
        ur=etpc.UpperRight
        return dict(lowerLeft=(ll.x,ll.y,ll.z), 
                    upperLeft=(ul.x,ul.y,ul.z),
                    upperRight=(ur.x,ur.y,ur.z))
    
    def getAvailableExtensions(self):
        return [OrderedDict(name=e.Name,extensionId=e.ExtensionId,protocolVersion=e.ProtocolVersion,realm=e.Realm) for e in self._eyetracker.GetAvailableExtensions()]

    def getEnabledExtensions(self):
        return [OrderedDict(name=e.Name,extensionId=e.ExtensionId,protocolVersion=e.ProtocolVersion,realm=e.Realm) for e in self._eyetracker.GetEnabledExtensions()]
    
    def enableExtension(self,extension):
        extension_id=extension
        if isinstance(extension, OrderedDict):
            extension_id=extension['extensionId']
        self._eyetracker.EnableExtension(extension_id)
        
    def disconnect(self):
        if self._isRecording:
            self.stopTracking()
        self._mainloop.stop()
        self._mainloop=None
        self._eyetracker_info=None
        self._requested_product_id=None
        self._requested_model=None
        self._eyetracker=None
        
    def __del__(self):
        if self._mainloop:
            self.disconnect()

# test script
 
if __name__ == '__main__':
    #init global clock manually for test    
    from  psychopy.clock import MonotonicClock    
    Computer.global_clock=MonotonicClock()
    
    TobiiTrackerBrowser.start()
    
    print ">> Return first device detected and print details dict: "
    tracker_info=TobiiTrackerBrowser.findDevice()        
    if tracker_info:
        print "Success: ",tracker_info
        print '\tDetails:'
        for k,v in TobiiTrackerBrowser.getTrackerDetails(tracker_info.product_id).iteritems():
            print '\t',k,':',v
    else:
        print 'ERROR: No Tracker Found.'
    print ''
    
    print ">> Return first Tobii T120 detected: "
    tracker_info=TobiiTrackerBrowser.findDevice(model='Tobii T120')        
    if tracker_info:
        print "\tSuccess: ",tracker_info
    else:
        print '\tERROR: No Tracker Found.'
    print ''

    print ">> Return first Tobii T120 with id TT120-206-95100697 detected: "
    tracker_info=TobiiTrackerBrowser.findDevice(model='Tobii T120',product_id='TT120-206-95100697')        
    if tracker_info:
        print "\tSuccess: ",tracker_info
    else:
        print '\tERROR: No Tracker Found.'
    print ''

    print ">> Return Tobii with product id 12345678 detected (should always fail): "
    tracker_info=TobiiTrackerBrowser.findDevice(product_id='1234567')        
    if tracker_info:
        print "\tSuccess: ",tracker_info
    else:
        print 'ERROR: No Tracker Found.'

    TobiiTrackerBrowser.stop()
    
    print '###################################'
    print ''
    
    print "Test Creating a connected TobiiTracker class, using first available Tobii:"

    tobii_tracker=TobiiTracker()
    print "\tCreated a Connected Tobii Tracker OK."
    print "\tDetails:"
    for k,v in tobii_tracker.getTrackerDetails().iteritems():
        print "\t\t{0}  {1}".format(k,v)
    
    print ''
    print 'Tracker Name: ',tobii_tracker.getName()
    print 'Set Tracker Name (to "tracker [time]") ...'
    tobii_tracker.setName('tracker %.6f'%getTime())
    print 'Tracker Name now: ',tobii_tracker.getName()

    print ''
    print 'Tracker Low Blink Mode: ',tobii_tracker.getLowBlinkMode()

    print ''
    print 'Tracker Low Blink Mode: ',tobii_tracker.getAvailableIlluminationModes()

    print ''
    imodes=tobii_tracker.getAvailableIlluminationModes()
    print 'Valid Tracker Illumination Modes: ',imodes
    if imodes:
        cimode=tobii_tracker.getIlluminationMode()
        print 'Current Illumination Mode: ',cimode
        print 'Setting Illumination Mode to ',imodes[0]
        tobii_tracker.setIlluminationMode(imodes[0])
        print 'Current Illumination Mode Now: ',tobii_tracker.getIlluminationMode()
        print 'Setting Illumination Mode back to ',cimode
        tobii_tracker.setIlluminationMode(cimode)
        print 'Current Illumination Mode Now: ',tobii_tracker.getIlluminationMode()
    else:
        print "NOTE: Illumination Mode API features are not supported."
        
    print ''
    print 'Tracker Head Movement Box: ',tobii_tracker.getHeadBox()

    print ''
    print 'Tracker Physical Placement: ',tobii_tracker.getEyeTrackerPhysicalPlacement()

    print ''
    print 'Tracker Enabled Extensions: ',tobii_tracker.getEnabledExtensions()

    print ''
    print 'Tracker Available Extensions: ',tobii_tracker.getAvailableExtensions()

    print ''
    srates=tobii_tracker.getAvailableSamplingRates()
    print 'Valid Tracker Sampling Rates: ',srates
    crate=tobii_tracker.getSamplingRate()
    print 'Current Sampling Rate: ',crate
    print 'Setting Sampling Rate to ',srates[0]
    tobii_tracker.setSamplingRate(srates[0])
    print 'Current Sampling Rate Now: ',tobii_tracker.getSamplingRate()
    print 'Setting Sampling Rate back to ',crate
    tobii_tracker.setSamplingRate(crate)
    print 'Current Sampling Rate Now: ',tobii_tracker.getSamplingRate()
    
    print ''
    print 'Tobii Time Info (20 sec):'    
    # give some time for events
    
    last_times=None
    first_call_times=None
    stime=getTime()
    while getTime()-stime<20.0:
        print '\tgetTobiiTimeResolution: ',tobii_tracker.getTobiiTimeResolution()
        iohub_t=int(getTime()*1000000.0)
        tobii_local_t=tobii_tracker.getCurrentLocalTobiiTime()
        tobii_remote_t=tobii_tracker.getCurrentEyeTrackerTime()
        tlocal_iohub_dt=tobii_local_t-iohub_t
        tremote_iohub_dt=tobii_remote_t-iohub_t
        tlocal_tremote_dt=tobii_remote_t-tobii_local_t
        
        if last_times:
            print '\tioHub Time in usec (dt): ',iohub_t,iohub_t-last_times[0]
            print '\tgetCurrentLocalTobiiTime (dt): ',tobii_local_t, tobii_local_t-last_times[1]
            print '\tgetCurrentEyeTrackerTime (dt): ',tobii_remote_t, tobii_remote_t-last_times[2]
            print '\tioHub, tobii local, tobii remote Elapsed times:',iohub_t-first_call_times[0],tobii_local_t-first_call_times[1],tobii_remote_t-first_call_times[2]
            print '\t---'        
        else:
            first_call_times=(iohub_t,tobii_local_t,tobii_remote_t)
        last_times=(iohub_t,tobii_local_t,tobii_remote_t)
        time.sleep(0.2)
        
    print ''
    print 'Tobii Recording Data (20 sec):'

    tobii_tracker.startTracking()

    stime=getTime()
    while getTime()-stime<20.0:
        time.sleep(0.01)
        
    tobii_tracker.stopTracking()
    
    tobii_tracker.disconnect()
    
    print ""
    print "TESTS COMPLETE."

#
##########################################################        

