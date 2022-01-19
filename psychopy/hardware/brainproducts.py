"""
Python support for `Brain Products GMBH <https://www.brainproducts.com>`_ hardware.

Here we have implemented support for the Remote Control Server application,
which allows you to control recordings, send annotations etc. all from Python.
"""

import socket
import time
import threading
import weakref
from psychopy import logging

_appStates = {
    'AP:0': 'Closed',
    'AP:1': 'Open',
    'AP:-1': 'Errored',
}

_recordingStates = {
    'RS:0': 'Idle',
    'RS:1': 'Monitoring',
    'RS:2': 'Calibration',
    'RS:3': 'Impedance check',
    'RS:4': 'Recording',  # the manual calls this Saving (recording)"
    'RS:5': 'Saving calibration',  # the manual calls this "Saving calibration"
    'RS:6': 'Paused',
    'RS:7': 'Paused calibration',
    'RS:8': 'Paused impedance check',
}

_acquisitionStates = {
    'AQ:0': 'Stopped',
    'AQ:1': 'Running',
    'AQ:2': 'Warning',
    'AQ:3': 'Error',
}


class RemoteControlServer:
    """
    Provides a remote-control interface to BrainProducts Recorder.

    Example usage::

        import time
        from psychopy import logging
        from psychopy.hardware import brainproducts

        logging.console.setLevel(logging.DEBUG)
        rcs = brainproducts.RemoteControlServer()
        rcs.open('testExp',
                 workspace='C:/Vision/Workfiles/Standard Workspace.rwksp',
                 participant='S0021')
        rcs.openRecorder()
        time.sleep(2)
        rcs.mode = 'monitor' # or 'impedance', or 'default'
        rcs.startRecording()
        time.sleep(2)
        rcs.sendAnnotation('124', 'STIM')
        time.sleep(1)
        rcs.pauseRecording()
        time.sleep(1)
        rcs.resumeRecording()
        time.sleep(1)
        rcs.stopRecording()
        time.sleep(1)
        rcs.mode = 'default'  # stops monitoring mode

    """

    def __init__(self, host='127.0.0.1', port=6700, timeout=1.0,
                 testMode=False):
        """To initialize the remote control recorder.

        Parameters
        ----------
        host : string, optional
            The IP address or hostname of the computer running RCS.
            Defaults to ``127.0.0.1``.
        port : int, optional
            The port on which RCS is listening for a connection on the
            EEG computer. This should usually not need to be changed.
            Defaults to ``6700``.
        timeout : float, optional
            The timeout (in seconds) to wait for sending/receivign commands
        testMode : bool, optional
            If ``True``, the network connection to the RCS computer will
            not actually be initialized.
            Defaults to ``False``.
        """
        self._testMode = testMode

        self.applicationState = None
        self.recordingState = None
        self.acquisitionState = None

        self._host = host
        self._port = port
        self._recording = False
        self._timeout = timeout

        # various properties that are initially unknown
        self._mode = 'default'
        self._exp_name = None
        self._participant = None
        self._workspace = None
        self._amplifier = None
        self._overwriteProtection = None
        self._RCSversion = None

        self._bufferChars = ''  # unprocessed stream from RCS
        self._bufferList = []  # list of messages
        self._socket = socket.socket(socket.AF_INET,
                                     socket.SOCK_STREAM)
        self._socket.settimeout(self._timeout)

        try:
            self._socket.connect((self._host, self._port))
        except socket.error:
            if not self._testMode:
                msg = ('Could not connect to RCS at %s:%s. Make sure the '
                       'Remote Control Server software is running and set '
                       'to "Connect"' %
                       (self._host, self._port))
                raise RuntimeError(msg)
            else:
                pass

        self._listener = _ListenerThread(self)
        self._listener.start()

    def sendRaw(self, message, checkOutput='OK'):
        """A helper function to send raw messages (strings) to the RCS.

        This is normally only used for debugging purposes and is not
        needed by most users.

        Parameters
        ----------
            message : string
                The string that will be sent
            checkOutput : string (default='OK')
                If a value is provided then this will be checked for by
                this function. If no check is needed then set checkOutput=None
        """
        # Append \r if it's not already part of the message: RCS
        # uses this as command separators.
        if self._testMode:
            return

        # check for reply
        if not message.endswith('\r') or not message.endswith('\r\n'):
            message += '\r'
        if type(message) != bytes:
            message = message.encode('utf-8')
        self._socket.sendall(message)

        # did reply include OK message?
        if not checkOutput:
            return
        # wait for message with expected output (means OK)
        reply = self.waitForMessage(endswith=checkOutput)
        if not reply:
            logging.warning(
                "RCS Didn't receive expected response from RCS to "
                "the message {}. Current stack of recent responses:{}."
                .format(message, self._listener.messages))
            logging.flush()
        else:
            return True

    def waitForMessage(self, containing='', endswith=''):
        """Wait for a message, optionally one that meets certain criteria

        Parameters
        ----------
        containing : str
            A string the message must contain
        endswith : str
            A string the message must end with (ignoring newline characters)

        Returns
        -------
        The (complete) message string if one was received or None if not
        """
        # check output
        OK = False
        t0 = time.time()
        while time.time() - t0 < self._timeout and not OK:
            for reply in self._listener.messages:
                if reply.endswith(endswith) and containing in reply:
                    logging.debug("RCS received {}".format(repr(reply)))
                    self._listener.messages.remove(reply)
                    return reply

    def waitForState(self, stateName, permitted, timeout=10):
        """Helper function to wait for a particular state (or any attribute, for that matter)
         to have a particular value. Beware this will wait indefinitely, so only call
         if you are confident that the state will eventually arrive!

        Parameters
        ----------
        stateName : str
            Name of the state (e.g. "applicationState")
        permitted : list
            List of values that are permitted before returning

        """
        if type(permitted) is not list:
            raise TypeError("permitted must be a list of permitted values")
        t0 = time.time()
        while getattr(self, stateName) not in permitted:
            time.sleep(0.01)
            if time.time()-t0 > timeout:
                logging.warning(
                    f'RCS {stateName} not achieved: expected states {permitted} but state is {getattr(self, stateName)}'
                )
                return

    def open(self, expName, participant, workspace):
        """Opens a study/workspace on the RCS server

        Parameters
        ----------
        expName : str
            Name of the experiment. Will make up the first part of the
            EEG filename.
        participant : str
            Participant identifier. Will make up the second part of the
            EEG filename.
        workspace : str
            The full path to the workspace file (.rwksp), with forward slashes
            as path separators. e.g. "c:/myFolder/mySetup.rwksp"
        """
        self.workspace = workspace
        self.participant = participant
        self.expName = expName
        # all appears OK
        logging.info(
            'RCS connected: {} - {}'.format(self.expName, self.participant))

    def openRecorder(self):
        """Opens the Recorder application from the Remote Control.

        Neat, huh?!
        """
        msg = 'O'
        self.sendRaw(msg, checkOutput="O:OK")
        # after reporting OK it should also change the status
        self.waitForState("applicationState", ["Open"])
        self.waitForState("recordingState", ["Idle"])
        # check that the RCS is using the correct messaging version
        self.sendRaw("VM", checkOutput="VM:2")

    def _updateState(self, msg):
        # Update our state variables from a state message
        if msg[:2] == 'AP':
            self.applicationState = _appStates[msg]
            logging.info('RCS Recorder app is now {}'
                         .format(self.applicationState.upper()))
        elif msg[:2] == 'RS':
            self.recordingState = _recordingStates[msg]
            logging.info('RCS Recorder State is now {}'
                         .format(self.recordingState.upper()))
        elif msg[:2] == 'AQ':
            self.acquisitionState = _acquisitionStates[msg]
            logging.info('RCS Acq is now {}'
                         .format(self.acquisitionState.upper()))
        else:
            raise RuntimeError("RCS._updateState was sent unknown message"
                               "'{}'".format(msg))

    @property
    def workspace(self):
        """
        Get/set the path to the workspace file. An absolute path is required.

        Example Usage::

            rcs.workspace = 'C:/Vision/Worksfiles/testing.rwksp'

        """
        return self._workspace

    @workspace.setter
    def workspace(self, path):
        msg = '1:%s' % path
        self.sendRaw(msg, checkOutput=msg + ':OK')

        self._workspace = path

    @property
    def expName(self):
        """
        Get/set the name of the experiment or study (string)

        The name will make up the first part of the EEG filename.

        Example Usage::

            rcs.expName = 'MyTestStudy'

        """
        return self._exp_name

    @expName.setter
    def expName(self, name):
        msg = '2:%s' % name
        self.sendRaw(msg, checkOutput=msg + ':OK')

        self._exp_name = name

    @property
    def participant(self):
        """
        Get/set the participant identifier (a string or numeric).

        This identifier will make up the center part of the EEG filename.

        """
        return self._participant

    @participant.setter
    def participant(self, participant):
        msg = '3:{}'.format(participant)
        self.sendRaw(msg, checkOutput=msg + ':OK')
        # keep track of the change
        self._participant = participant

    @property
    def mode(self):
        """
        Get/set the current mode.

        Mode is a string that can be one of:

        - 'default' or 'def' or None will exit special modes
        - 'impedance' or 'imp' for impedance checking
        - 'monitoring' or 'mon'
        - 'test' or 'tes' to go into test view

        """
        return self._mode

    @mode.setter
    def mode(self, mode):
        if mode in ['impedance', 'imp']:
            if self.recordingState == "Recording":
                finalRecordingState = "Paused impedance check"
            else:
                finalRecordingState = "Impedance check"
            self._mode = 'impedance'
            msg = 'I'
        elif mode in ['monitor', 'mon']:
            self._mode = 'monitor'
            msg = 'M'
        elif mode in ['test', 'tes']:
            self._mode = 'test'
            msg = 'T'
        elif mode in ['default', 'def', None]:
            self._mode = 'default'
            msg = 'SV'
        else:
            msg = ('`mode` must be one of: impedance, imp, monitor, mon, test '
                   'def, or default.')
            raise ValueError(msg)

        replyOK = self.sendRaw(msg, checkOutput=msg + ':OK')
        if not replyOK:
            raise IOError(f"Failed to set RCS into mode {mode}. RCS did not reply 'OK'")

        # now wait for appropriate state changes to match our target mode
        if mode in ['impedance', 'imp']:
            self.waitForState("recordingState", [finalRecordingState])
            self.waitForState("acquisitionState", ["Running"])
        elif mode in ['monitor', 'mon']:
            self.waitForState("recordingState", ["Monitoring"])
            self.waitForState("acquisitionState", ["Running"])
        elif mode in ['test', 'tes']:
            self.waitForState("recordingState", ["Calibration"])
            self.waitForState("acquisitionState", ["Running"])
        elif mode in ['default', 'def', None]:
            self.waitForState("recordingState", ["Idle"])
            self.waitForState("acquisitionState", ["Stopped"])

    @property
    def timeout(self):
        """What is a reasonable timeout in seconds (initially set to 0.5)

        For some systems (e.g. when the RCS is the same machine) you might want
        to set this to a lower value. For an unpredictable or slow network
        connection you might want to set this to a higher value.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        self._socket.settimeout(timeout)
        self._timeout = timeout

    @property
    def amplifier(self):
        """Get/set the amplifier to use. Could be one of
        "  ['actiCHamp', 'BrainAmp Family',"
        " 'LiveAmp', 'QuickAmp USB', 'Simulated Amplifier',"
        " 'V-Amp / FirstAmp']

        For Liveamp you should also provide the serial number,
        comma separated from the amplifier type.

        Examples:
            rcs = RemoteControlServer()
            rcs.amplifier = 'LiveAmp', 'LA-05490-0200'
            # OR
            rcs.amplifier = 'actiCHamp'
        """
        return self._amplifier

    @amplifier.setter
    def amplifier(self, amplifier):
        # did we get a tuple/list of ampType, ampSN or just name?
        serialNumber = None
        if len(amplifier) == 2:  # e.g. ('LiveAmp', '34834727')
            amplifier, serialNumber = amplifier
        elif len(amplifier) == 1:  # e.g. ('actiCHamp')
            amplifier = amplifier[0]  # extract string from tuple/list
        else:
            assert type(amplifier) == str  # hopefully then we got the name raw
        # check for LiveAmp that we also have a SN
        if amplifier == 'LiveAmp' and not serialNumber:
            logging.warning("LiveAmp may need a serial number. Use\n"
                          "  rcs.amplifier = 'LiveAmp', 'LA-serialNumberHere'")
            logging.flush()
        if amplifier in ['actiCHamp', 'BrainAmp Family',
                         'LiveAmp', 'QuickAmp USB', 'Simulated Amplifier',
                         'V-Amp / FirstAmp']:
            msg = "SA:{}".format(amplifier)
            self.sendRaw(msg, checkOutput=msg + ':OK')
        else:
            errMsg = (f"Unknown amplifier '{amplifier}'. The `amplifier` value "
                      "should be a LiveAmp serial number or one of "
                      "['actiCHamp', 'BrainAmp Family',"
                      " 'LiveAmp', 'QuickAmp USB', 'Simulated Amplifier',"
                      " 'V-Amp / FirstAmp']")
            raise ValueError(errMsg)
        if serialNumber:
            # LiveAmp allows you to send the serial number
            msg = "SN:{}".format(serialNumber)
            self.sendRaw(msg, checkOutput=msg + ':OK')
        self._amplifier = amplifier
        self._amplifierSN = serialNumber

    @property
    def overwriteProtection(self):
        """An attribute to get/set whether the overwrite protection is turned on.

        When checking the attribute the state of `rcs.overwriteProtection` a call will be
        made to the RCS and the report is based on the response. There is also a
        variable `rcs._overwriteProtection` that is simply the stored state from the
        most recent call and does not make any further communication with the RCS itself.

        Usage example::

            rcs.overwriteProtection = True  # set it to be on
            print(rcs.overwriteProtection)  # print current state
        """
        reply = self.sendRaw("OW", checkOutput=None)  # we'll check this one manually
        # reply is OW:0:OK or OW:1:OK
        if reply == 'OW:0:OK':
            state = False
        elif reply == 'OW:1:OK':
            state = True
        else:
            raise IOError("Request for overwrite state received unknown"
                          "response '{}'".format(reply))
        self._overwriteProtection = state
        return self._overwriteProtection

    @overwriteProtection.setter
    def overwriteProtection(self, value):
        if value not in [True, False]:  # or 1, 0 not necess bool type
            raise ValueError("RCS.overwriteProtection should be set to "
                             "True or False, not '{}'".format(value))
        msg = "OW:{}".format(int(value))
        self.sendRaw(msg, checkOutput=msg + ':OK')
        self._overwriteProtection = bool(value)

    @property
    def version(self):
        """Reports the version of the RCS application

        Example usage::

            print(rcs.version)

        """
        if not self._RCSversion:
            # otherwise request info from RCS
            msg = 'VS'
            self.sendRaw(msg, checkOutput='')
            reply = self.waitForMessage(containing='VS:')
            if reply:
                self._RCSversion = reply.strip().replace("VS:")
            else:
                logging.warning("Failed to retrieve the version of the RCS software")
                logging.flush()
        return self._RCSversion

    def dcReset(self):
        """Use this to reset any DC offset that might have accumulated
        if you aren't using a high-pass filter"""
        msg = 'D'
        self.sendRaw(msg)

    def startRecording(self):
        """
        Start recording EEG.

        """
        recordingType = self.recordingState
        if recordingType not in ['Monitoring', 'Calibration', 'Impedance check']:
            msg = ('To start recording, the RCS must be in one of "Monitoring", '
                   f'"Calibration" or "Impedance check" states, not {recordingType}')
            raise RuntimeError(msg)
        if self._recording:
            msg = 'Recording is already in progress!'
            raise RuntimeError(msg)

        msg = 'S'
        self.sendRaw(msg)

        self.waitForState("recordingState", ["Recording", "Saving calibration"])
        self._recording = True

    def stopRecording(self):
        """
        Stop recording EEG.

        """
        if not self._recording:
            msg = 'Recording has not yet been started!'
            raise RuntimeError(msg)

        msg = 'Q'
        self.sendRaw(msg)
        self.waitForState("recordingState", ["Recording", "Calibration"])
        self._recording = False

    def pauseRecording(self):
        """
        Pause recording EEG without ending the session.

        """
        msg = 'P'
        self.sendRaw(msg)
        self.waitForState("recordingState", ["Paused", "Paused calibration"])

    def resumeRecording(self):
        """
        Resume a paused recording

        """
        msg = 'C'
        self.sendRaw(msg)
        self.waitForState("recordingState", ["Recording", "Saving calibration"])

    def sendAnnotation(self, annotation, annType):
        """Sends a message to be logged on the Recorder. 
        
        The timing of annotations may be imprecise and this
        should not be trusted as a method of sending sync triggers.

        Annotations can contain any ASCII characters except for ";"

        Parameters
        -----------------

        annotation : string
            The description text to be sent in the annotation.

        annType : string
            The category of the annotation which are user-defined
            strings (e.g. stimulus, response)

        Example usage::

            rcs.sendAnnotation("face003", "stimulus")
        
        """
        msg = "AN:{};{}".format(annotation, annType)
        self.sendRaw(msg)

    def close(self):
        """Closes the recording and deletes all associated workspace
        variables (e.g. when a participant has been completed)
        """
        msg = 'X'
        self.sendRaw(msg)
        self.waitForState("recordingState", ["Idle"])
        self.waitForState("acquisitionState", ["Stopped"])
        self.waitForState("applicationState", ["Closed"])


class _ListenerThread(threading.Thread):
    def __init__(self, parent):
        self._socket = parent._socket  # type: socket.socket
        self.messages = []
        self._buffer = ''
        threading.Thread.__init__(self, daemon=True)
        self._parentRef = weakref.ref(parent)
        self._is_running = None

    def run(self):
        """Gets run repeatedly until terminates
        """
        if self._is_running is None:
            self._is_running = True
        while self._is_running:
            try:
                if self._socket._closed:
                    break
                recvd = self._socket.recv(512).decode('utf-8')
                self._buffer += recvd
                self.processBuffer()
            except socket.timeout:
                time.sleep(0.1)
            except OSError:
                if self._socket._closed:
                    self._is_running = False

    def processBuffer(self):

        # check for whole messages:
        nMessages = self._buffer.count('\r')
        msgList = self._buffer.split('\r')
        for msgN in range(nMessages):
            thisMsg = msgList[msgN]
            # remove message from buffer so we don't reuse
            self._buffer = self._buffer.replace(thisMsg + '\r', '')
            # check if the message is a change of state
            if thisMsg[:2] in ['AP', 'RS', 'AQ']:
                self._parentRef()._updateState(thisMsg)
            else:
                self.messages.append(thisMsg)

    def clear(self):
        self.messages = []
        self._buffer = ''
        while True:
            try:
                self._socket.recv(1)
            except socket.timeout:  # no chars left to clear
                return


if __name__ == "__main__":
    logging.console.setLevel(logging.DEBUG)
    rcs = RemoteControlServer()
    rcs.open('testExp',
             workspace='C:/Vision/Workfiles/Standard Workspace.rwksp',
             participant='S0021')
    rcs.openRecorder()
    time.sleep(2)
    rcs.mode = 'monitor'  # or 'impedance', or 'default'
    rcs.startRecording()
    time.sleep(2)
    rcs.sendAnnotation('124', 'STIM')
    time.sleep(1)
    rcs.pauseRecording()
    time.sleep(1)
    rcs.resumeRecording()
    time.sleep(1)
    rcs.stopRecording()
    time.sleep(1)
    rcs.mode = 'default'  # stops monitoring mode
