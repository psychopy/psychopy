# -*- coding: utf-8 -*-
# ioHub Python Module
# .. file: psychopy/iohub/devices/eyetracker/hw/gazepoint/gp3/eyetracker.py
#
# .. fileauthor:: Martin Guest Sol Simpson
#
# Distributed under the terms of the GNU General Public License
# (GPL version 3 or any later version).
#
#

from ...... import print2err, printExceptionDetailsToStdErr, to_numeric
from ......constants import EyeTrackerConstants
from ..... import Computer
from .... import EyeTrackerDevice
from ....eye_events import *
from gevent import socket
import errno

ET_UNDEFINED = EyeTrackerConstants.UNDEFINED
getTime = Computer.getTime

class EyeTracker(EyeTrackerDevice):
    """
    The Gazepoint GP3 implementation of the Common Eye Tracker Interface can be
    used by providing the following EyeTracker class path as the eye tracker
    device name in the iohub_config.yaml device settings file::
        
        eyetracker.hw.gazepoint.gp3.EyeTracker

    .. note:: The Gazepoint control application **must** be running
              while using this interface.

    The Gazepoint GP3 interface supports:
    * connection / disconnection to the GP3 device.
    * Starting / stopping when eye position data is collected.
    * Sending text messages to the GP3 system.
    * current gaze position information, using the FPOGX, FPOGY fields from
      the most receint REC message received from the GP3
    * Generation of the BinocularEyeSampleEvent type based on the GP3 REC
      message type. The following fields of an eye sample event are populated
      populated:
        * device_time: uses TIME field of the REC message
        * logged_time: the time the REC message was received / read.
        * time: currently set to equal the time the REC message was received.
        * left_gaze_x: uses LFOGX
        * left_gaze_y: uses LFOGY
        * right_gaze_x: uses RFOGX
        * right_gaze_y: uses RFOGY
        * combined_gaze_x: uses FPOGX
        * combined_gaze_Y: uses FPOGY
        * left_pupil_size: uses LPD and is diameter in pixels
        * right_pupil_size: uses RPD and is diamter in pixels

    The Gazepoint GP3 interface uses a polling method to check for new eye
    tracker data. The default polling interval is 5 msec. This can be changed
    in the device's configuration settings for the experiment if needed.

    The following functionality has not yet been implemented in the ioHub GP3
    interface:
    * Built-in calibration graphics
    * Calculation of the REC event delay in ioHub. Therefore the event time
      stamps should not be considered msec accurate.
    """

    # GP3 tracker times are received as msec
    #
    DEVICE_TIMEBASE_TO_SEC =  1.0
    EVENT_CLASS_NAMES=['MonocularEyeSampleEvent','BinocularEyeSampleEvent','FixationStartEvent',
                         'FixationEndEvent', 'SaccadeStartEvent', 'SaccadeEndEvent',
                         'BlinkStartEvent', 'BlinkEndEvent']
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
        TO DO: Method not implemented in GP3 interface.

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
        TO DO: Method not implemented in GP3 interface.

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
                            try:
                                msg[tkey]=to_numeric(tval.strip('"'))
                            except Exception:
                                msg[tkey] = tval
                        msgs.append(msg)
                else:
                    print2err("Incomplete Message Found: [",msgtxt,']')
                self._rx_buffer = self._rx_buffer[msg_end_ix+2:]
            else:
                break
        return msgs

    def setConnectionState(self, enable):
        """
        Connects or disconnects from the GP3 eye tracking hardware.

        By default, when ioHub is started, a connection is automatically made,
        and when the experiment completes and ioHub is closed, so is the GP3
        connection.
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
                init_connection_str+='<SET ID="ENABLE_SEND_USER_DATA" STATE="1"/>\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_PUPIL_LEFT" STATE="1" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_PUPIL_RIGHT" STATE="1" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_POG_FIX" STATE="1" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_POG_BEST" STATE="1" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_DATA" STATE="0" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_COUNTER" STATE="1" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_TIME" STATE="1" />\r\n'
                init_connection_str+='<SET ID="ENABLE_SEND_TIME_TICK" STATE="1" />\r\n'
                self._gp3.sendall(str.encode(init_connection_str))
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
            except Exception:
                print2err('Problem disconnecting from device - GP3')
                self._rx_buffer=''
        return self.isConnected()
        
        
    def isConnected(self):
        """
        isConnected returns whether the GP3 is connected to the experiment PC
        and if the tracker state is valid. Returns True if the tracker can be 
        put into Record mode, etc and False if there is an error with the tracker
        or tracker connection with the experiment PC.

        Args:
            None
            
        Return:
            bool:  True = the eye tracking hardware is connected. False otherwise.

        """
        return self._gp3 is not None

    def sendMessage(self, message_contents, time_offset=None):
        """
        The sendMessage method sends the message_contents str to the GP3.
        """
        try:
            if time_offset is not None:
                print2err("Warning: GP3 EyeTracker.sendMessage time_offset arguement is ignored by this eye tracker interface.")
            if self._gp3 and self.isRecordingEnabled() is True:
                strMessage='<SET ID="USER_DATA" VALUE="{0}"/>\r\n'.format(message_contents)
                self._gp3.sendall(strMessage)
        except Exception:
            print2err('Problems sending message: {0}'.FORMAT(message_contents))
            printExceptionDetailsToStdErr()
        return EyeTrackerConstants.EYETRACKER_OK

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
        This method is called by gp3 every n msec based on the polling interval
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
                    event_type=EventConstants.BINOCULAR_EYE_SAMPLE

                    event_timestamp = m.get('TIME',ET_UNDEFINED) #in seconds, take from the REC TIME field

                    # TODO event_delay, how to calulate TBD.
                    event_delay = 0.0 # SHOULD BE something like
                                      # tracker_time - event_timestamp

                    iohub_time = logged_time - event_delay

                    # TODO: Determine how to calc CI for TET Samples
                    confidence_interval = logged_time - self._last_poll_time

                    self._last_poll_time = logged_time

                    left_gaze_x = m.get('LPOGX',ET_UNDEFINED)
                    left_gaze_y = m.get('LPOGY',ET_UNDEFINED)
                    left_gaze_x, left_gaze_y = self._eyeTrackerToDisplayCoords((left_gaze_x,left_gaze_y))
                    left_pupil_size = m.get('LPD',ET_UNDEFINED) #diameter of pupil in pixels

                    right_gaze_x = m.get('RPOGX',ET_UNDEFINED)
                    right_gaze_y = m.get('RPOGY',ET_UNDEFINED)
                    right_gaze_x, right_gaze_y = self._eyeTrackerToDisplayCoords((right_gaze_x,right_gaze_y))
                    right_pupil_size = m.get('RPD',ET_UNDEFINED) #diameter of pupil in pixels

                    # left / right eye pos avg. data
                    combined_gaze_x = m.get('FPOGX',ET_UNDEFINED)
                    combined_gaze_y = m.get('FPOGY',ET_UNDEFINED)
                    combined_gaze_x, combined_gaze_y = self._eyeTrackerToDisplayCoords((combined_gaze_x,combined_gaze_y))

                    #
                    # The X and Y-coordinates of the left and right eye pupil
                    # in the camera image, as a fraction of the
                    # camera image size.
                    left_raw_x = m.get('LPCX',ET_UNDEFINED)
                    left_raw_y = m.get('LPCY',ET_UNDEFINED)
                    right_raw_x = m.get('RPCX',ET_UNDEFINED)
                    right_raw_y = m.get('RPCY',ET_UNDEFINED)


                    left_eye_status = m.get('LPOGV',ET_UNDEFINED)
                    right_eye_status = m.get('RPOGV',ET_UNDEFINED)

                    # 0 = both eyes OK
                    status = 0
                    if left_eye_status == right_eye_status and right_eye_status == 0:
                        # both eyes are missing
                        status = 22
                    elif left_eye_status == 0:
                        # Just left eye missing
                        status = 20
                    elif right_eye_status == 0:
                        # Just right eye missing
                        status = 2


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
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             left_raw_x,
                             left_raw_y,
                             left_pupil_size,
                             EyeTrackerConstants.PUPIL_DIAMETER,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             right_gaze_x,
                             right_gaze_y,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             right_raw_x,
                             right_raw_y,
                             right_pupil_size,
                             EyeTrackerConstants.PUPIL_DIAMETER,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             ET_UNDEFINED,
                             status
                                 ]

                    self._addNativeEventToBuffer((binocSample,(combined_gaze_x,combined_gaze_y)))

                elif m.get('type') == 'ACK':
                    print2err("ACK Received: ", m)
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