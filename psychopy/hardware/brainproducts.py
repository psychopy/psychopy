from __future__ import division, unicode_literals

import numpy as np
import socket
import time


def pauseToSend(pause=0.1):
    """Simple helper to provide a default pause duration
    
    In the future this might also abort early if return
    signal detected?"""
    time.sleep(pause)


class RemoteControlServer(object):
    """
    Provides a remote-control interface to BrainProducts Recorder.
    """
    def __init__(self, host='127.0.0.1', port=6700, timeout=1.0,
                 testMode=False):
        """
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

        self._host = host
        self._port = port
        self._recording = False
        self._timeout = 0.5

        # various properties that are initially unknown
        self._mode = None
        self._exp_name = None
        self._participant = None
        self._workspace = None
        self._amplifier = None
        self._overwriteProtection = None

        self._socket = socket.socket(socket.AF_INET,
                                     socket.SOCK_STREAM)
        self._socket.settimeout(self._timeout)

        try:
            self._socket.connect((self._host, self._port))
        except socket.error:
            if not self._testMode:
                msg = ('Could not connect to RCS at %s:%s!' %
                       (self._host, self._port))
                raise RuntimeError(msg)
            else:
                pass

        self.mode = 'default'
        
    def __del__(self):
        self._socket.close()

    def sendRaw(self, message, checkOK='OK'):
        """A helper function to send raw messages (strings) to the RCS.

        This is normally only used for debugging purposes and is not
        needed by most users.

        Parameters
        ----------
            message : string
                The string that will be sent
            checkOK : string (default='OK')
                If a value is provided then this will be checked for by
                this function. If no check is needed then set checkOK=None
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
        reply = ''
        while not reply.endswith('\r'):
            reply += self._socket.recv(1).decode('utf-8')
        reply = reply.strip('\r')

        # did reply include OK message?
        if checkOK and not reply.endswith(checkOK):
            raise IOError("Sending command '{}' to RCS returned an unexpected "
                          "reply '{}'".format(message.decode('utf-8'), reply))
        
        return reply

    def _clearInputBuffer(self):
        """Clears the input buffer so that any new messages.
        Not needed by most users.
        Will incurr one timeout because will keep clearing chars
        until a timeout occurs.
        """
        while True:
            try:
                self._socket.recv(1)
            except socket.timeout:  # no chars left to clear
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

    @property
    def workspace(self):
        """
        Get/set the path to the workspace file. An absolute path is required.

        Example Usage
        --------------

            rcs.workspace = 'C:/Users/EEG/Desktop/testing.rwksp'

        """
        return self._workspace

    @workspace.setter
    def workspace(self, path):
        msg = '1:{}'.format(path)
        self.sendRaw(msg)
        pauseToSend()

        msg = '4'
        self.sendRaw(msg)
        pauseToSend()

        self._workspace = path

    @property
    def expName(self):
        """
        Get/set the name of the experiment or study (string)

        The name will make up the first part of the EEG filename.

        Example Usage
        --------------

            rcs.expName = 'MyTestStudy'

        """
        return self._exp_name

    @expName.setter
    def expName(self, name):
        msg = '2:{}'.format(name)
        self.sendRaw(msg)
        pauseToSend()

        self._exp_name = name

    @property
    def participant(self):
        """
        Get/set the participant identifier.

        This identifier will make up the center part of the EEG filename.

        Parameters
        ----------
        participant : int or string
            The participant identifier, e.g., `123`.

        """
        return self._participant

    @participant.setter
    def participant(self, participant):
        msg = '3:%s' % (participant)
        self.sendRaw(msg)
        pauseToSend()
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
        - 'viewtest' or 'view' to go into test view

        """
        return self._mode

    @mode.setter
    def mode(self, mode):
        if (mode == 'impedance') or (mode == 'imp'):
            self._mode = 'impedance'
            msg = 'I'
        elif (mode == 'monitor') or (mode == 'mon'):
            self._mode = 'monitor'
            msg = 'M'
        elif mode in ['default', 'def', None]:
            self._mode = 'default'
            msg = 'X'
        else:
            msg = ('`mode` must be one of: impedance, imp, monitor, mon, '
                   'def, or default.')
            raise ValueError(msg)
        
        self.sendRaw(msg)

    @property
    def timeout(self):
        """What is a reasonable timeout in seconds (initially set to 0.5)

        For some systems (e.g. when the RCS is the same machine) you might want to set 
        this to a lower value. For an unpredictable or slow network connection you 
        might want to set this to a higher value.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        self._socket.settimeout(timeout)
        self._timeout = timeout

    @property
    def amplifier(self):
        """Get/set the amplifier to use
        """
        return self._amplifier
    
    @amplifier.setter
    def amplifier(self, amplifier):
        if amplifier in ['actiCHamp', 'BrainAmp Family',
                         'LiveAmp', 'QuickAmp USB', 'Simulated Amplifier', 
                         'V-Amp / FirstAmp']:
            msg = "SA:{}".format(amplifier)
        elif amplifier.startswith("LA-"):
            # LiveAmp allows you to send the serial number
            msg = "SN:{}".format(amplifier)
        else:
            errMsg = ("Unknown amplifier '{amp}'. The `amplifier` value "
                      "should be a LiveAmp serial number or one of "
                      "['actiCHamp', 'BrainAmp Family',"
                      " 'LiveAmp', 'QuickAmp USB', 'Simulated Amplifier',"
                      " 'V-Amp / FirstAmp']")
            raise ValueError(errMsg)
        self.sendRaw(msg)
        self._amplifier = amplifier

    @property
    def overwriteProtection(self):
        """Get/set whether the 
        """
        if self._overwriteProtection is None:
            reply = self.sendRaw("OW")
        return self._overwriteProtection

    @overwriteProtection.setter
    def overwriteProtection(self, value):
        if value not in [True, False]:  # or 1, 0 not necess bool type
            raise ValueError("RCS.overwriteProtection should be set to "
                             "True or False, not '{}'".format(value))
        msg = "OW:{}".format(int(value))
        self.sendRaw(msg)
        self._overwriteProtection = bool(value)

    def dcReset(self):
        """Use this to reset any DC offset that might have accumulated
        if you aren't using a high-pass filter"""
        msg = 'D'
        self.sendRaw(msg)

    def startRecording(self):
        """
        Start recording EEG.

        """
        if self._recording:
            msg = 'Recording is still in progress!'
            raise RuntimeError(msg)

        msg = 'S'
        self.sendRaw(msg)
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
        self._recording = False

    def pauseRecording(self):
        """
        Pause recording EEG without ending the session.

        """
        msg = 'P'
        self.sendRaw(msg)

    def resumeRecording(self):
        """
        Resume a paused recording

        """
        msg = 'C'
        self.sendRaw(msg)

    def sendAnnotation(self, annotation, annType):
        """Sends a message to be logged on the Recorder. 
        
        The timing of annotations may be imprecise and this
        should not be trusted as a method of sending sync triggers.

        Annotations can contain any ASCII characters except for ";"

        Parameters
        -----------------
        annotation : string
            The desription text to be sent in the annotation.

        annType : string
            The category of the annotation which are user-defined
            strings (e.g. stimulus, response)

        Example usage
        --------------

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


if __name__=="__main__":
    rcs = RemoteControlServer()
    rcs.open('testExp', workspace='BrainCap_64_wksp/BC-64.rwksp', 
             participant='S0021')
