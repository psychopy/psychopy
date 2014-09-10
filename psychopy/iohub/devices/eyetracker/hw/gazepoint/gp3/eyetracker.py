# -*- coding: utf-8 -*-
"""
ioHub
Common Eye Tracker Interface for the GazePoint GP3 system.
.. file: ioHub/devices/eyetracker/hw/gazepoint/gp3/eyetracker.py

Distributed under the terms of the GNU General Public License
(GPL version 3 or any later version).

.. moduleauthor:: ????
.. fileauthor:: ???
"""

import numpy as np 
from ...... import print2err,printExceptionDetailsToStdErr
from ......constants import EventConstants, EyeTrackerConstants
from ..... import Computer
from .... import EyeTrackerDevice
from ....eye_events import *
from gevent import socket, sleep
import errno
#from ...... import to_numeric

getTime=Computer.getTime

def to_numeric(lit):
    'Return value of numeric literal string or ValueError exception'
    # Handle '0'
    if lit == '0': return 0
    # Hex/Binary
    litneg = lit[1:] if lit[0] == '-' else lit
    if litneg[0] == '0':
        if litneg[1] in 'xX':
            return int(lit,16)
        elif litneg[1] in 'bB':
            return int(lit,2)
        else:
            try:
                return int(lit,8)
            except ValueError:
                pass

    # Int/Float/Complex
    try:
        return int(lit)
    except ValueError:
        pass
    try:
        return float(lit)
    except ValueError:
        pass
    try:
        return complex(lit)
    except ValueError:
        pass

    # return original str
    return lit

class EyeTracker(EyeTrackerDevice):
    """
    TheEyeTribe implementation of the Common Eye Tracker Interface can be used
    by providing the following EyeTracker path as the device class in 
    the iohub_config.yaml device settings file:
        
        eyetracker.hw.theeyetribe.EyeTracker
        
    """

    # GP3 tracker times are received as msec
    #
    DEVICE_TIMEBASE_TO_SEC =  1.0
    EVENT_CLASS_NAMES=['MonocularEyeSampleEvent','BinocularEyeSampleEvent','FixationStartEvent',
                         'FixationEndEvent', 'SaccadeStartEvent', 'SaccadeEndEvent',
                         'BlinkStartEvent', 'BlinkEndEvent']

    # Set in the __init__ to to be the instance of the pyTribe.TheEyeTribe
    # interface.

    _recording=False
    __slots__=['_gp3','_rx_buffer']
    #_hpb=None
    def __init__(self,*args,**kwargs):        
        EyeTrackerDevice.__init__(self,*args,**kwargs)

        # Holds the GP3 socket interface
        self._gp3 = None

        # Holds data received from GP3 tracker that has not yet been parsed
        # into messages
        self._rx_buffer=''

        # Used to hold the last sample processed by iohub.
        self._latest_sample=None

        # Used to hold the last valid gaze position processed by ioHub.
        # If the last sample received from the GP3 indicates missing eye
        # position, then this is set to None
        #
        self._latest_gaze_position=None

        # Connect to the eye tracker server by default.
        self.setConnectionState(True)
        
    def trackerTime(self):
        """
        Current eye tracker time in the eye tracker's native time base. 
        The TET system uses a usec timebase.
        
        Args: 
            None
            
        Returns:
            float: current native eye tracker time. (in usec for the TET)
        """
        if self._gp3:
             # TODO Replace with GP3  and custom code to get current device's time.
            return EyeTrackerConstants.EYETRACKER_ERROR#getTime()
            
        return EyeTrackerConstants.EYETRACKER_ERROR
        
    def trackerSec(self):
        """
        Current eye tracker time, normalized to sec.msec format.

        Args: 
            None
            
        Returns:
            float: current native eye tracker time in sec.msec-usec format.
        """
        if self._gp3:
            return self.trackerTime()*self.DEVICE_TIMEBASE_TO_SEC
        return EyeTrackerConstants.EYETRACKER_ERROR

    def _checkForNetData(self, timeout = 0):
        self._gp3.settimeout(timeout)
        while True:
            try:
                rxdat = self._gp3.recv(4096)
                if rxdat:
                    self._rx_buffer += bytes.decode(rxdat).replace('\r\n','')
                    return self._rx_buffer
                else:
                    print2err('***** GP3 Closed Connection *****')
                    # Connection closed
                    self.setRecordingState(False)
                    self.setConnectionState(False)
                    self._rx_buffer=''
                    return None

            except socket.error, e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK or err == 'timed out':
                    # non blocking socket found no data; it happens.
                    return self._rx_buffer
                else:
                    # a valid error occurred
                    print2err('***** _checkForNetData Error *****')
                    printExceptionDetailsToStdErr()
                    return self._rx_buffer

    def _parseRxBuffer(self):
        msgs = []
        while self._rx_buffer:
            msg_end_ix = self._rx_buffer.find('/>')
            if msg_end_ix >= 0:
                msgtxt = self._rx_buffer[:msg_end_ix]
                msg_start_ix = msgtxt.find('<')
                if len(msgtxt) > 1 and msg_start_ix >= 0:
                    msgtxt = msgtxt[msg_start_ix+1:]
                    msgtoks = msgtxt.split()
                    if msgtoks:
                        msg = dict(type=msgtoks[0])
                        for t in msgtoks[1:]:
                            tkey, tval = t.split("=")
                            msg[tkey]=to_numeric(tval.strip('"'))
                        msgs.append(msg)
                else:
                    print2err("Incomplete Message Found: [",msgtxt,']')
                self._rx_buffer = self._rx_buffer[msg_end_ix+2:]
            else:
                break
        return msgs

    def setConnectionState(self, enable):
        """
        setConnectionState is a no-op when using the TET system, as the
        connection is established when the TheEyeTribe EyeTracker class is created,
        and remains active until the program ends, or a error occurs resulting
        in the loss of the tracker connection.

        Args:
            enable (bool): True = enable the connection, False = disable the connection.

        Return:
            bool: indicates the current connection state to the eye tracking hardware.
        """
        if enable is True and self._gp3 is None:
            try:
                self._rx_buffer=''
                self._gp3 = socket.socket()
                address = ('127.0.0.1',4242)
                self._gp3.connect(address)

                init_connection_str='<SET ID="ENABLE_SEND_CURSOR" STATE="1" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_POG_LEFT" STATE="1" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_POG_RIGHT" STATE="1" />\r\n'
                #init_connection_str+='<SET ID="ENABLE_SEND_PUPIL_LEFT" STATE="1" />\r\n'
                #init_connection_str+='<SET ID="ENABLE_SEND_PUPIL_RIGHT" STATE="1" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_POG_FIX" STATE="1" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_DATA" STATE="0" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_COUNTER" STATE="1" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_TIME" STATE="1" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_TIME_TICK" STATE="1" />\r\n'
                self._gp3.sendall(str.encode(init_connection_str))
#               self._gp3.send(str.encode('<SET ID="ENABLE_SEND_POG_BEST" STATE="1" />\r\n'))
#               self._gp3.send(str.encode('<SET ID="ENABLE_SEND_USER_DATA" />\r\n'))
                # block for upp to 1 second to get reply txt.
                strStatus = self._checkForNetData(1.0)
                if strStatus:
                    self._rx_buffer = ''
                    return True
                else:
                    return False

            except socket.error as e:
                if e.args[0]==10061:
                    print2err('***** Socket Error: Check Gazepoint control software is running *****')
                print2err('Error connecting to GP3 ', e)
        elif enable is False and self._gp3:
            try:
                if self._gp3:
                    self.setRecordingState(False)
                self._gp3.close()
                self._gp3 = None
                self._rx_buffer=''
            except:
                print2err('Problem disconnecting from device - GP3')
                self._rx_buffer=''
        return self.isConnected()
        
        
    def isConnected(self):
        """
        isConnected returns whether the TheEyeTribe is connected to the experiment PC
        and if the tracker state is valid. Returns True if the tracker can be 
        put into Record mode, etc and False if there is an error with the tracker
        or tracker connection with the experiment PC.

        Args:
            None
            
        Return:
            bool:  True = the eye tracking hardware is connected. False otherwise.

        """
        return self._gp3 is not None

    def sendMessage(self,message_contents,time_offset=None):
        """
        The sendMessage method is not supported by the TheEyeTribe implementation
        of the Common Eye Tracker Interface, as the TheEyeTribe SDK does not support
        saving eye data to a native data file during recording.
        """
        # TODO TET Implementation, NOT part of common API methods ever used
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

    def sendCommand(self, key, value=None):
        """
        The sendCommand method is not supported by the TheEyeTribe Common Eye Tracker
        Interface.
        """
        
        # TODO TET Implementation, NOT part of common API methods ever used
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

#    def runSetupProcedure(self,starting_state=EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE):
#        """
#        runSetupProcedure performs a calibration routine for the TheEyeTribe
#        eye tracking system.
#        
#        Result:
#            bool: True if setup / calibration procedure passed, False otherwise. If false, should likely exit experiment.
#        """
#        try:
#            # TODO TET Implementation
#            calibration_properties=self.getConfiguration().get('calibration')
#            screenColor=calibration_properties.get('screen_background_color')
#            # [r,g,b] of screen
#
#            #genv=TETPsychopyCalibrationGraphics(self,screenColor=screenColor)
#
#            #calibrationOK=genv.runCalibration()
#            #genv.window.close()
#            
#            #genv._unregisterEventMonitors()
#            #genv.clearAllEventBuffers()
#            
#            return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
#            
#        except:
#            print2err("Error during runSetupProcedure")
#            printExceptionDetailsToStdErr()
#        return EyeTrackerConstants.EYETRACKER_ERROR

    def enableEventReporting(self,enabled=True):
        """
        enableEventReporting is functionally identical to the eye tracker
        device specific setRecordingState method.
        """
        
        try:        
            self.setRecordingState(enabled)
            enabled=EyeTrackerDevice.enableEventReporting(self,enabled)
            return enabled
        except Exception, e:
            print2err("Exception in EyeTracker.enableEventReporting: ", str(e))
            printExceptionDetailsToStdErr()

    def setRecordingState(self,recording):
        """
        setRecordingState is used to start or stop the recording of data from 
        the eye tracking device.
        
        args:
           recording (bool): if True, the eye tracker will start recordng available
              eye data and sending it to the experiment program if data streaming
              was enabled for the device. If recording == False, then the eye
              tracker stops recording eye data and streaming it to the experiment.
              
        If the eye tracker is already recording, and setRecordingState(True) is
        called, the eye tracker will simple continue recording and the method call
        is a no-op. Likewise if the system has already stopped recording and 
        setRecordingState(False) is called again.

        Args:
            recording (bool): if True, the eye tracker will start recordng data.; false = stop recording data.
           
        Return:trackerTime
            bool: the current recording state of the eye tracking device
        """
        current_state = self.isRecordingEnabled()
        if self._gp3 and recording is True and current_state is False:
            self._rx_buffer=''
            self._gp3.sendall(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))
            rxdat = self._checkForNetData(1.0)
            if rxdat is None:
                EyeTracker._recording=False
                return EyeTrackerDevice.enableEventReporting(self, False)
            EyeTracker._recording=True
        elif self._gp3 and recording is False and current_state is True:
            self._rx_buffer=''
            self._gp3.sendall(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="0" />\r\n'))
            rxdat = self._checkForNetData(1.0)
            EyeTracker._recording=False
            self._latest_sample=None
            self._latest_gaze_position=None
        return EyeTrackerDevice.enableEventReporting(self, recording)

    def isRecordingEnabled(self):
        """
        isRecordingEnabled returns the recording state from the eye tracking 
        device.

        Args:
           None
  
        Return:
            bool: True == the device is recording data; False == Recording is not occurring
        """
        if self._gp3:
            return self._recording
        return False

    def _poll(self):
        """
        This method is called by gp3 every n msec based on the polling  interval
        set in the eye tracker config. Default is 5 msec
        """
        try:
            if not self.isRecordingEnabled():
                return

            logged_time=Computer.getTime()

            #TODO: ??? How to implement trackerSec, using 0.0 constant 
            tracker_time = 0.0 #self.trackerSec()           

           
            # Check for any new rx data from gp3 socket.
            # If None is returned, that means the gp3 closed the socket
            # connection.
            if self._checkForNetData() is None:
                return

            # Parse any rx text received from the gp3 into msg dicts.
            msgs = self._parseRxBuffer()
            for m in msgs:
                if m.get('type') == 'REC':
                    # Always tracks binoc, so always use BINOCULAR_EYE_SAMPLE
                    #print2err("REC MSG: ",m)
                    event_type=EventConstants.BINOCULAR_EYE_SAMPLE

                    # <REC TIME="2.123" TIME_TICK="79876879598675" FPOGX="0.00000"
                    # FPOGY="0.00000" FPOGS="0.00000"
                    # FPOGD="0.44469" FPOGID="0" FPOGV="0" CX="0.53281"
                    # CY="0.59082" CS="0" />
                    #data = incomingData.split('"')

                    event_timestamp = m.get('TIME',EyeTrackerConstants.UNDEFINED) #in seconds, take from the REC TIME field

                    # TODO event_delay, how to calulate TBD.
                    event_delay = 0.0 # SHOULD BE something like
                                      # tracker_time - event_timestamp

                    iohub_time = logged_time - event_delay

                    # TODO: Determine how to calc CI for TET Samples
                    confidence_interval = logged_time - self._last_poll_time

                    self._last_poll_time = logged_time

                    # TODO: fill in eye sample specific data fields
                    # IMP: Use _eyeTrackerToDisplayCoords method to set values for array
                    left_gaze_x = m.get('LPOGX',EyeTrackerConstants.UNDEFINED)
                    left_gaze_y = m.get('LPOGY',EyeTrackerConstants.UNDEFINED)
                    left_gaze_x, left_gaze_y = self._eyeTrackerToDisplayCoords((left_gaze_x,left_gaze_y))
                    left_pupil_size = EyeTrackerConstants.UNDEFINED

                    # IMP: Use _eyeTrackerToDisplayCoords method to set values for array
                    right_gaze_x = m.get('RPOGX',EyeTrackerConstants.UNDEFINED)
                    right_gaze_y = m.get('RPOGY',EyeTrackerConstants.UNDEFINED)
                    right_gaze_x, right_gaze_y = self._eyeTrackerToDisplayCoords((right_gaze_x,right_gaze_y))
                    right_pupil_size = EyeTrackerConstants.UNDEFINED

                    #TODO: Set combined vars to the GP3 provided
                    # left / right eye pos avg. data
                    combined_gaze_x = m.get('FPOGX',EyeTrackerConstants.UNDEFINED)
                    combined_gaze_y = m.get('FPOGY',EyeTrackerConstants.UNDEFINED)
                    combined_gaze_x, combined_gaze_y = self._eyeTrackerToDisplayCoords((combined_gaze_x,combined_gaze_y))

                    # TODO: status field set to indicate missing data
                    # val 2 = left eye missing data, 20 = right eye missing data, 22 = both eyes missing
                    status = 0


                    binocSample=[
                             0, # experiment_id, iohub fills in automatically
                             0, # session_id, iohub fills in automatically
                             0, # device id, keep at 0
                             Computer._getNextEventID(), # iohub event unique ID
                             event_type, # BINOCULAR_EYE_SAMPLE
                             event_timestamp, # eye tracker device time stamp
                             logged_time, # time _poll is called
                             iohub_time,
                             confidence_interval,
                             event_delay,
                             0,
                             left_gaze_x,
                             left_gaze_y,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             left_pupil_size,
                             # TODO: Confirm what 'pupil size' actually is in GP3
                             EyeTrackerConstants.PUPIL_AREA,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             right_gaze_x,
                             right_gaze_y,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             right_pupil_size,
                             # TODO: Confirm what 'pupil size' actually is in GP3
                             EyeTrackerConstants.PUPIL_AREA,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             status
                                 ]

                    self._addNativeEventToBuffer((binocSample,(combined_gaze_x,combined_gaze_y)))

                else:
                    # Message type is not being handled.
                    print2err("UNHANDLED GP3 MESSAGE: ", m)
                
        except Exception:
            print2err("ERROR occurred during GP3 Sample Callback.")
            printExceptionDetailsToStdErr()
        finally:
            return 0
            
    def _getIOHubEventObject(self,native_event_data):
        """
        The _getIOHubEventObject method is called by the ioHub Process to convert 
        new native device event objects that have been received to the appropriate 
        ioHub Event type representation. 
        """        
        self._latest_sample,cgp=native_event_data

        if cgp[0] is not None and cgp[1] is not None:
            self._latest_gaze_position=cgp
        else:
            self._latest_gaze_position=None

        return self._latest_sample
        
    def _eyeTrackerToDisplayCoords(self,eyetracker_point):
        """
        Converts GP3 gaze positions to the Display device coordinate space.
        TODO: Check if thgis works for 0.0,0.0 being left,top to 1.0,1.0
        """

        gaze_x,gaze_y=eyetracker_point
        left,top,right,bottom=self._display_device.getCoordBounds()
        w,h=right-left,top-bottom            
        x,y=left+w*gaze_x,bottom+h*(1.0-gaze_y)        

        #print2err("GP3: ",(eyetracker_point),(left,top,right,bottom),(x,y))
        return x,y
        
    def _displayToEyeTrackerCoords(self,display_x,display_y):
        """
        Converts a Display device point to GP3 gaze position coordinate space.
        TODO: Check if thgis works for 0.0,0.0 being left,top to 1.0,1.0
        """
        left,top,right,bottom=self._display_device.getCoordBounds()
        w,h=right-left,top-bottom 
    
        return (left-display_x)/w,(top-display_y)/h

    def _close(self):
        if self._gp3:
            self.setRecordingState(False)
            self.setConnectionState(False)
        EyeTrackerDevice._close(self)