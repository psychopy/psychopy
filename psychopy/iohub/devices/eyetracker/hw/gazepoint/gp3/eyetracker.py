# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import errno
import sys

from gevent import socket

from ....eye_events import *
from ..... import Computer, Device
from ......constants import EyeTrackerConstants
from ......errors import print2err, printExceptionDetailsToStdErr
from ......util import updateSettings

ET_UNDEFINED = EyeTrackerConstants.UNDEFINED
getTime = Computer.getTime

if sys.platform == 'win32':
    from ctypes import byref, c_int64, windll
    _fcounter_ = c_int64()
    _qpfreq_ = c_int64()
    windll.Kernel32.QueryPerformanceFrequency(byref(_qpfreq_))
    _qpfreq_ = float(_qpfreq_.value)
    _winQPC_ = windll.Kernel32.QueryPerformanceCounter

    def getLocalhostGP3Time():
        _winQPC_(byref(_fcounter_))
        return _fcounter_.value / _qpfreq_


def to_numeric(lit):
    """Return value of a numeric literal string. If the string can not be
    converted then the original string is returned.

    :param lit:
    :return:

    """
    # Handle '0'
    if lit == '0':
        return 0
    # Hex/Binary
    litneg = lit[1:] if lit[0] == '-' else lit
    if litneg[0] == '0':
        if litneg[1] in 'xX':
            return int(lit, 16)
        elif litneg[1] in 'bB':
            return int(lit, 2)
        else:
            try:
                return int(lit, 8)
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
    To start iohub with a Gazepoint GP3 eye tracker device, add a GP3
    device to the device dictionary passed to launchHubServer or the 
    experiment's iohub_config.yaml::

        eyetracker.hw.gazepoint.gp3.EyeTracker

    .. note:: The Gazepoint control application **must** be running
              while using this interface.
              
    Examples:
        A. Start ioHub with Gazepoint GP3 device and run tracker calibration::
    
            from psychopy.iohub import launchHubServer
            from psychopy.core import getTime, wait

            iohub_config = {'eyetracker.hw.gazepoint.gp3.EyeTracker':
                {'name': 'tracker', 'device_timer': {'interval': 0.005}}}
                
            io = launchHubServer(**iohub_config)
            
            # Get the eye tracker device.
            tracker = io.devices.tracker
                            
            # run eyetracker calibration
            r = tracker.runSetupProcedure()
            
        B. Print all eye tracker events received for 2 seconds::
                        
            # Check for and print any eye tracker events received...
            tracker.setRecordingState(True)
            
            stime = getTime()
            while getTime()-stime < 2.0:
                for e in tracker.getEvents():
                    print(e)
            
        C. Print current eye position for 5 seconds::
                        
            # Check for and print current eye position every 100 msec.
            stime = getTime()
            while getTime()-stime < 5.0:
                print(tracker.getPosition())
                wait(0.1)
            
            tracker.setRecordingState(False)
            
            # Stop the ioHub Server
            io.quit()
    """

    # GP3 tracker times are received as msec
    #
    DEVICE_TIMEBASE_TO_SEC = 1.0
    EVENT_CLASS_NAMES = [
        'GazepointSampleEvent',
        'BinocularEyeSampleEvent',
        'FixationStartEvent',
        'FixationEndEvent',
        'SaccadeStartEvent',
        'SaccadeEndEvent',
        'BlinkStartEvent',
        'BlinkEndEvent']
    _recording = False
    __slots__ = ['_gp3', '_rx_buffer', '_ttfreq', '_last_fix_evt', '_serverIsLocalhost']

    def __init__(self, *args, **kwargs):
        EyeTrackerDevice.__init__(self, *args, **kwargs)

        # Holds the GP3 socket interface
        self._gp3 = None

        # Holds data received from GP3 tracker that has not yet been parsed
        # into messages
        self._rx_buffer = ''

        # Used to hold the last sample processed by iohub.
        self._latest_sample = None

        # Used to hold the last valid gaze position processed by ioHub.
        # If the last sample received from the GP3 indicates missing eye
        # position, then this is set to None
        #
        self._latest_gaze_position = None

        # Connect to the eye tracker server by default.
        self.setConnectionState(True)
        self._serverIsLocalhost = self.getConfiguration().get('network_settings').get('ip_address') in ['localhost',
                                                                                                        '127.0.0.1']
        self._gp3get("TIME_TICK_FREQUENCY")
        self._ttfreq = self._waitForAck('TIME_TICK_FREQUENCY').get("FREQ")

        self._last_fix_evt = None

    def trackerTime(self):
        """
        Current eye tracker time in the eye tracker's native time base.
        The GP3 system uses a sec.usec timebase based on the Windows QPC,
        so when running on a single computer setup, iohub can directly read
        the current gazepoint time. When running with a two computer setup,
        current gazepoint time is assumed to equal current local time.

        Returns:
            float: current native eye tracker time in sec.msec format.
        """
        if sys.platform == 'win32' and self._serverIsLocalhost:
            return getLocalhostGP3Time()
        return getTime()

    def trackerSec(self):
        """
        Same as the GP3 implementation of trackerTime().
        """
        return self.trackerTime() * self.DEVICE_TIMEBASE_TO_SEC

    def _sendRequest(self, rtype, ID, **kwargs):
        params = ''
        for k, v in kwargs.items():
            params += ' {}="{}"'.format(k, v)
        rqstr = '<{} ID="{}" {} />\r\n'.format(rtype, ID, params)
        # print2err("Sending: {}\n".format(rqstr))
        self._gp3.sendall(str.encode(rqstr))

    def _gp3set(self, ID, **kwargs):
        self._sendRequest("SET", ID, **kwargs)

    def _gp3get(self, ID, **kwargs):
        self._sendRequest("GET", ID, **kwargs)

    def _waitForAck(self, type_id, timeout=5.0):
        stime = getTime()
        while getTime() - stime < timeout:
            self._checkForNetData(0.25)
            msgs = self._parseRxBuffer()
            for m in msgs:
                if m.get('ID') == type_id:
                    return m
        return None

    def _checkForNetData(self, timeout=0.0):
        self._gp3.settimeout(timeout)
        while True:
            try:
                rxdat = self._gp3.recv(4096)
                if rxdat:
                    self._rx_buffer += bytes.decode(rxdat).replace('\r\n', '')
                    return self._rx_buffer
                else:
                    print2err('***** GP3 Closed Connection *****')
                    # Connection closed
                    self.setRecordingState(False)
                    self.setConnectionState(False)
                    self._rx_buffer = ''
                    return None

            except socket.error as e:
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
                    msgtxt = msgtxt[msg_start_ix + 1:]
                    msgtoks = msgtxt.split()
                    if msgtoks:
                        msg = dict(type=msgtoks[0])
                        for t in msgtoks[1:]:
                            tkey, tval = t.split('=')
                            try:
                                msg[tkey] = to_numeric(tval.strip('"'))
                            except Exception:
                                msg[tkey] = tval
                        msgs.append(msg)
                else:
                    print2err('Incomplete Message Found: [', msgtxt, ']')
                self._rx_buffer = self._rx_buffer[msg_end_ix + 2:]
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
                self._rx_buffer = ''
                self._gp3 = socket.socket()
                haddress = self.getConfiguration().get('network_settings').get('ip_address')
                hport = int(self.getConfiguration().get('network_settings').get('port'))
                address = (haddress, hport)
                self._gp3.connect(address)
                init_connection_str = ''
                init_connection_str += '<SET ID="ENABLE_SEND_POG_LEFT" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_POG_RIGHT" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_PUPIL_LEFT" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_PUPIL_RIGHT" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_POG_FIX" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_POG_BEST" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_EYE_LEFT" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_EYE_RIGHT" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_COUNTER" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_DIAL" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_GSR" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_HR" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_HR_PULSE" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_TIME" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_TIME_TICK" STATE="1" />\r\n'
                init_connection_str += '<SET ID="ENABLE_SEND_DATA" STATE="0" />\r\n'
                self._gp3.sendall(str.encode(init_connection_str))

                if self._waitForAck('ENABLE_SEND_TIME_TICK'):
                    self._rx_buffer = ''
                    return True
                else:
                    return False

            except socket.error as e:
                if e.args[0] == 10061:
                    print2err('***** Socket Error: Check Gazepoint control software is running *****')
                print2err('Error connecting to GP3 ', e)

        elif enable is False and self._gp3:
            try:
                if self._gp3:
                    self.setRecordingState(False)
                self._gp3.close()
                self._gp3 = None
                self._rx_buffer = ''
            except Exception:
                print2err('Problem disconnecting from device - GP3')
                self._rx_buffer = ''
        return self.isConnected()

    def isConnected(self):
        """
        isConnected returns whether the GP3 is connected to the experiment
        PC and if the tracker state is valid. Returns True if the tracker can
        be put into Record mode, etc and False if there is an error with the
        tracker or tracker connection with the experiment PC.

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
                print2err('Warning: GP3 EyeTracker.sendMessage time_offset argument is ignored.')
            if self._gp3 and self.isRecordingEnabled() is True:
                strMessage = '<SET ID="USER_DATA" VALUE="{0}"/>\r\n'.format(message_contents)
                self._gp3.sendall(strMessage)
        except Exception:
            print2err('Problems sending message: {0}'.format(message_contents))
            printExceptionDetailsToStdErr()
        return EyeTrackerConstants.EYETRACKER_OK

    def enableEventReporting(self, enabled=True):
        """
        enableEventReporting is functionally identical to the eye tracker
        device specific setRecordingState method.
        """

        try:
            self.setRecordingState(enabled)
            enabled = EyeTrackerDevice.enableEventReporting(self, enabled)
            return enabled
        except Exception as e:
            print2err('Exception in EyeTracker.enableEventReporting: ', str(e))
            printExceptionDetailsToStdErr()

    def setRecordingState(self, recording):
        """
        setRecordingState is used to start or stop the recording of data from the eye tracking device.

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
            self._rx_buffer = ''
            self._gp3.sendall(
                str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))
            rxdat = self._checkForNetData(1.0)
            if rxdat is None:
                EyeTracker._recording = False
                return EyeTrackerDevice.enableEventReporting(self, False)
            EyeTracker._recording = True
        elif self._gp3 and recording is False and current_state is True:
            self._rx_buffer = ''
            self._gp3.sendall(
                str.encode('<SET ID="ENABLE_SEND_DATA" STATE="0" />\r\n'))
            self._checkForNetData(1.0)
            EyeTracker._recording = False
            self._latest_sample = None
            self._latest_gaze_position = None
        return EyeTrackerDevice.enableEventReporting(self, recording)

    def isRecordingEnabled(self):
        """
        isRecordingEnabled returns the recording state from the eye tracking device.

        Return:
            bool: True == the device is recording data; False == Recording is not occurring
        """
        if self._gp3:
            return self._recording
        return False

    def runSetupProcedure(self, calibration_args={}):
        """
        Start the eye tracker calibration procedure.
        """
        cal_config = updateSettings(self.getConfiguration().get('calibration'), calibration_args)
        #print2err("gp3 cal_config:", cal_config)

        use_builtin = cal_config.get('use_builtin')
        targ_timeout = cal_config.get('target_duration')
        targ_delay = cal_config.get('target_delay')

        self._gp3set('CALIBRATE_TIMEOUT', VALUE=targ_timeout)
        self._gp3set('CALIBRATE_DELAY', VALUE=targ_delay)
        self._waitForAck('CALIBRATE_DELAY', timeout=2.0)

        if use_builtin is True:
            self._gp3set('CALIBRATE_RESET')
            self._gp3set('CALIBRATE_SHOW', STATE=1)
            self._gp3set('CALIBRATE_START', STATE=1)

        else:
            from .calibration import GazepointCalibrationProcedure
            calibration = GazepointCalibrationProcedure(self, calibration_args)

            calibration.runCalibration()

            calibration.window.close()

            calibration._unregisterEventMonitors()
            calibration.clearAllEventBuffers()

        # Get calibration result and return to experiment process.
        cal_result = self._waitForAck('CALIB_RESULT', timeout=30.0)
        if cal_result:
            self._gp3set('CALIBRATE_SHOW', STATE=0)
            self._gp3set('CALIBRATE_START', STATE=0)
            self._gp3get('CALIBRATE_RESULT_SUMMARY')
            del cal_result['type']
            del cal_result['ID']

            cal_summary = self._waitForAck('CALIBRATE_RESULT_SUMMARY')
            del cal_summary['type']
            del cal_summary['ID']
            cal_result['SUMMARY'] = cal_summary

        self._gp3set('CALIBRATE_SHOW', STATE=0)
        self._gp3set('CALIBRATE_START', STATE=0)

        return cal_result

    def _poll(self):
        """
        This method is called by iohub every n msec based on the polling interval set in the eye tracker config.
        """
        try:
            if not self.isRecordingEnabled():
                return

            logged_time = Computer.getTime()
            tracker_time = self.trackerTime()

            # Check for any new rx data from gp3 socket.
            # If None is returned, that means the gp3 closed the socket
            # connection.
            if self._checkForNetData() is None:
                return

            # Parse any rx text received from the gp3 into msg dicts.
            msgs = self._parseRxBuffer()
            for m in msgs:
                if m.get('type') == 'REC':
                    binocSample = self._parseSampleFromMsg(m, logged_time, tracker_time)
                    self._addNativeEventToBuffer(binocSample)

                    # left / right eye pos avg. data
                    combined_gaze_x = m.get('FPOGX', ET_UNDEFINED)
                    combined_gaze_y = m.get('FPOGY', ET_UNDEFINED)
                    combined_gaze_x, combined_gaze_y = self._eyeTrackerToDisplayCoords(
                        (combined_gaze_x, combined_gaze_y))

                    if combined_gaze_x is not None and combined_gaze_y is not None:
                        self._latest_gaze_position = (combined_gaze_x, combined_gaze_y)
                    else:
                        self._latest_gaze_position = None

                    for fix_evt in self._parseFixationFromMsg(m, logged_time, tracker_time):
                        self._addNativeEventToBuffer(fix_evt)

                elif m.get('type') == 'ACK':
                    pass  # print2err('ACK Received: ', m)
                else:
                    # Message type is not being handled.
                    print2err('UNHANDLED GP3 MESSAGE: ', m)

            self._last_poll_time = logged_time

        except Exception:
            print2err('ERROR occurred during GP3 Sample Callback.')
            printExceptionDetailsToStdErr()
        finally:
            return 0

    def _parseFixationFromMsg(self, m, logged_time, tracker_time):
        fix_evts = []
        fix_valid = m.get('FPOGV', ET_UNDEFINED)
        if fix_valid == 1:
            fix_x, fix_y = self._eyeTrackerToDisplayCoords((m.get('FPOGX', ET_UNDEFINED), m.get('FPOGY', ET_UNDEFINED)))
            fix_stime = m.get('FPOGS', ET_UNDEFINED)
            fix_duration = m.get('FPOGD', ET_UNDEFINED)
            fix_id = m.get('FPOGID', ET_UNDEFINED)
            m = dict(FPOGID=fix_id, FPOGV=fix_valid, FPOGX=fix_x, FPOGY=fix_y, FPOGS=fix_stime, FPOGD=fix_duration,
                     TIME=int(m.get('TIME')), TIME_TICK=int(m.get('TIME_TICK')))

            if self._last_fix_evt is None:
                # Create start fixation evt based on m
                fix_evts = self._createStartFixEvt(m, logged_time, tracker_time)
            elif fix_id != self._last_fix_evt.get('FPOGID'):
                # Create Fixation end evt based on self._last_fix_evt
                fix_evts = self._createEndFixEvt(self._last_fix_evt, logged_time, tracker_time)
                # Create start fixation evt based on m
                fstart = self._createStartFixEvt(m, logged_time, tracker_time)
                fix_evts.extend(fstart)

            self._last_fix_evt = m

        return fix_evts

    def _createStartFixEvt(self, m, logged_time, tracker_time):
        # Create start fixation evt based on m
        # GP3 does not create separate left and right eye fix evts, so we
        # create a left and right fix evt each time.
        gaze = m.get('FPOGX', ET_UNDEFINED), m.get('FPOGY', ET_UNDEFINED)

        fix_dur = m.get('FPOGD', ET_UNDEFINED)
        if self._serverIsLocalhost:
            evt_tick_time = int(m.get('TIME_TICK', ET_UNDEFINED))
            evt_tick_sec = evt_tick_time / self._ttfreq
            sample_delay = tracker_time - evt_tick_sec
            iohub_time = logged_time - sample_delay - fix_dur
        else:
            sample_delay = 0
            iohub_time = logged_time - sample_delay - fix_dur

        device_time = m.get('FPOGS', ET_UNDEFINED)
        confidence_interval = logged_time - self._last_poll_time
        etype = EventConstants.FIXATION_START
        estatus = 0

        sel = [
            0,  # exp ID
            0,  # sess ID
            0,  # device id (not currently used)
            Device._getNextEventID(),  # event ID
            etype,  # event type
            device_time,
            logged_time,
            iohub_time,
            confidence_interval,
            sample_delay,
            0,
            EyeTrackerConstants.LEFT_EYE,  # eye
            gaze[0],  # gaze x
            gaze[1],  # gaze y
            ET_UNDEFINED,  # gaze z
            ET_UNDEFINED,  # angle x
            ET_UNDEFINED,  # angle y
            ET_UNDEFINED,  # raw x
            ET_UNDEFINED,  # raw y
            ET_UNDEFINED,  # pupil measure 1
            ET_UNDEFINED,  # pupil measure type 1
            ET_UNDEFINED,  # pupil measure 2
            ET_UNDEFINED,  # pupil measure 2 type
            ET_UNDEFINED,  # ppd x
            ET_UNDEFINED,  # ppd y
            ET_UNDEFINED,  # velocity x
            ET_UNDEFINED,  # velocity y
            ET_UNDEFINED,  # velocity xy
            estatus  # status
        ]

        ser = list(sel)
        ser[3] = Device._getNextEventID()
        ser[11] = EyeTrackerConstants.RIGHT_EYE

        return [sel, ser]

    def _createEndFixEvt(self, m, logged_time, tracker_time):
        # Create end fixation evt based on m
        etype = EventConstants.FIXATION_END
        estatus = 0

        gaze = m.get('FPOGX', ET_UNDEFINED), m.get('FPOGY', ET_UNDEFINED)
        fix_dur = m.get('FPOGD', ET_UNDEFINED)
        device_time = m.get('FPOGS', ET_UNDEFINED) + fix_dur

        if self._serverIsLocalhost:
            evt_tick_time = int(m.get('TIME_TICK', ET_UNDEFINED))
            evt_tick_sec = evt_tick_time / self._ttfreq
            sample_delay = tracker_time - evt_tick_sec
        else:
            sample_delay = 0

        confidence_interval = logged_time - self._last_poll_time
        iohub_time = logged_time - sample_delay

        eel = [0,
               0,
               0,  # device id (not currently used)
               Device._getNextEventID(),
               etype,
               device_time,
               logged_time,
               iohub_time,
               confidence_interval,
               sample_delay,
               0,
               EyeTrackerConstants.LEFT_EYE,
               fix_dur,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               gaze[0],
               gaze[1],
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               ET_UNDEFINED,
               estatus
               ]

        eer = list(eel)
        eer[3] = Device._getNextEventID()
        eer[11] = EyeTrackerConstants.RIGHT_EYE

        return [eel, eer]

    def _parseSampleFromMsg(self, m, logged_time, tracker_time):
        # Always use GAZEPOINT_SAMPLE
        event_type = EventConstants.GAZEPOINT_SAMPLE

        # in seconds, take from the REC TIME field
        event_timestamp = m.get('TIME', ET_UNDEFINED)

        if self._serverIsLocalhost:
            evt_tick_time = int(m.get('TIME_TICK', ET_UNDEFINED))
            evt_tick_sec = evt_tick_time / self._ttfreq
            sample_delay = tracker_time - evt_tick_sec
        else:
            sample_delay = 0

        iohub_time = logged_time - sample_delay

        confidence_interval = logged_time - self._last_poll_time

        left_gaze_x = m.get('LPOGX', ET_UNDEFINED)
        left_gaze_y = m.get('LPOGY', ET_UNDEFINED)
        left_gaze_x, left_gaze_y = self._eyeTrackerToDisplayCoords(
            (left_gaze_x, left_gaze_y))
        left_pupil_size = m.get(
            'LPD', ET_UNDEFINED)  # diameter of pupil in pixels
        left_pupil_size_2 = m.get("LPUPILD", ET_UNDEFINED)  # diameter of pupil in meters (sic!)

        right_gaze_x = m.get('RPOGX', ET_UNDEFINED)
        right_gaze_y = m.get('RPOGY', ET_UNDEFINED)
        right_gaze_x, right_gaze_y = self._eyeTrackerToDisplayCoords(
            (right_gaze_x, right_gaze_y))
        right_pupil_size = m.get(
            'RPD', ET_UNDEFINED)  # diameter of pupil in pixels
        right_pupil_size_2 = m.get("RPUPILD", ET_UNDEFINED)  # diameter of pupil in meters (sic!)

        #
        # The X and Y-coordinates of the left and right eye pupil
        # in the camera image, as a fraction of the
        # camera image size.
        left_raw_x = m.get('LPCX', ET_UNDEFINED)
        left_raw_y = m.get('LPCY', ET_UNDEFINED)
        right_raw_x = m.get('RPCX', ET_UNDEFINED)
        right_raw_y = m.get('RPCY', ET_UNDEFINED)

        left_eye_status = m.get('LPOGV', ET_UNDEFINED)
        right_eye_status = m.get('RPOGV', ET_UNDEFINED)

        dial = m.get('DIAL', ET_UNDEFINED)
        dialv = m.get('DIALV', ET_UNDEFINED)
        gsr = m.get('GSR', ET_UNDEFINED)
        gsrv = m.get('GSRV', ET_UNDEFINED)
        hr = m.get('HR', ET_UNDEFINED)
        hrv = m.get('HRV', ET_UNDEFINED)
        hrp = m.get('HRP', ET_UNDEFINED)

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

        return [
            0,  # experiment_id, iohub fills in automatically
            0,  # session_id, iohub fills in automatically
            0,  # device id, keep at 0
            Device._getNextEventID(),  # iohub event unique ID
            event_type,  # BINOCULAR_EYE_SAMPLE
            event_timestamp,  # eye tracker device time stamp
            logged_time,  # time _poll is called
            iohub_time,
            confidence_interval,
            sample_delay,
            0,
            left_gaze_x,
            left_gaze_y,
            left_raw_x,
            left_raw_y,
            left_pupil_size,
            EyeTrackerConstants.PUPIL_DIAMETER,
            left_pupil_size_2 * 1000,  # converting to MM
            EyeTrackerConstants.PUPIL_DIAMETER_MM,
            right_gaze_x,
            right_gaze_y,
            right_raw_x,
            right_raw_y,
            right_pupil_size,
            EyeTrackerConstants.PUPIL_DIAMETER,
            right_pupil_size_2 * 1000,  # converting to MM
            EyeTrackerConstants.PUPIL_DIAMETER_MM,
            dial,
            dialv,
            gsr,
            gsrv,
            hr,
            hrv,
            hrp,
            status
        ]

    def _getIOHubEventObject(self, native_event_data):
        """
        The _getIOHubEventObject method is called by the ioHub Process to
        convert new native device event objects that have been received to the
        appropriate ioHub Event type representation.
        """
        self._latest_sample = native_event_data
        return self._latest_sample

    def _eyeTrackerToDisplayCoords(self, eyetracker_point):
        """
        Converts GP3 gaze positions to the Display device coordinate space.
        """
        gaze_x, gaze_y = eyetracker_point
        left, top, right, bottom = self._display_device.getCoordBounds()
        w, h = right - left, top - bottom
        x, y = left + w * gaze_x, bottom + h * (1.0 - gaze_y)
        return x, y

    def _displayToEyeTrackerCoords(self, display_x, display_y):
        """
        Converts a Display device point to GP3 gaze position coordinate space.
        """
        left, top, right, bottom = self._display_device.getCoordBounds()
        w, h = right - left, top - bottom

        return (left - display_x) / w, (top - display_y) / h

    def _close(self):
        if self._gp3:
            self.setRecordingState(False)
            self.setConnectionState(False)
        EyeTrackerDevice._close(self)
