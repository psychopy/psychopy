"""
Name: u3.py
Desc: Defines the U3 class, which makes working with a U3 much easier. All of
      the low-level functions for the U3 are implemented as functions of the U3
      class. There are also a handful additional functions which improve upon
      the interface provided by the low-level functions.

To learn about the low-level functions, please see Section 5.2 of the U3 User's Guide:

http://labjack.com/support/u3/users-guide/5.2 

Section Number Mapping:
1 = Object Functions
2 = User's Guide Functions
3 = Convenience Functions
4 = Private Helper Functions

"""
from LabJackPython import *
import struct, ConfigParser

FIO0, FIO1, FIO2, FIO3, FIO4, FIO5, FIO6, FIO7, \
EIO0, EIO1, EIO2, EIO3, EIO4, EIO5, EIO6, EIO7, \
CIO0, CIO1, CIO2, CIO3 = range(20)

def openAllU3():
    """
    A helpful function which will open all the connected U3s. Returns a 
    dictionary where the keys are the serialNumber, and the value is the device
    object.
    """
    returnDict = dict()
    
    for i in range(deviceCount(3)):
        d = U3(firstFound = False, devNumber = i+1)
        returnDict[str(d.serialNumber)] = d
        
    return returnDict
        

class U3(Device):
    """
    U3 Class for all U3 specific low-level commands.
    
    Example:
    >>> import u3
    >>> d = u3.U3()
    >>> print d.configU3()
    {'SerialNumber': 320032102, ... , 'FirmwareVersion': '1.26'}
    """
    def __init__(self, debug = False, autoOpen = True, **kargs):
        """
        Name: U3.__init__(debug = False, autoOpen = True, **openArgs)
        
        Args: debug, enables debug output
              autoOpen, if true, the class will try to open a U3 using openArgs
              **openArgs, the arguments to pass to the open call. See U3.open()
        
        Desc: Instantiates a new U3 object. If autoOpen == True, then it will
              also open a U3.
              
        Examples:
        Simplest:
        >>> import u3
        >>> d = u3.U3()
        
        For debug output:
        >>> import u3
        >>> d = u3.U3(debug = True)
        
        To open a U3 with Local ID = 2:
        >>> import u3
        >>> d = u3.U3(localId = 2)
        """
        Device.__init__(self, None, devType = 3)
        self.debug = debug
        self.calData = None
        self.ledState = True
        
        if autoOpen:
            self.open(**kargs)
    __init__.section = 1 
        
    def open(self, firstFound = True, serial = None, localId = None, devNumber = None, handleOnly = False, LJSocket = None):
        """
        Name: U3.open(firstFound = True, localId = None, devNumber = None,
                      handleOnly = False, LJSocket = None)
        
        Args: firstFound, If True, use the first found U3
              serial, open a U3 with the given serial number
              localId, open a U3 with the given local id.
              devNumber, open a U3 with the given devNumber
              handleOnly, if True, LabJackPython will only open a handle
              LJSocket, set to "<ip>:<port>" to connect to LJSocket
        
        Desc: Use to open a U3. If handleOnly is false, it will call configU3
              and save the resulting information to the object. This allows the
              use of d.serialNumber, d.firmwareVersion, etc.
        
        Examples:
        Simplest:
        >>> import u3
        >>> d = u3.U3(autoOpen = False)
        >>> d.open()
        
        Handle-only, with a serial number = 320095789:
        >>> import u3
        >>> d = u3.U3(autoOpen = False)
        >>> d.open(handleOnly = True, serial = 320095789)
        
        Using LJSocket:
        >>> import u3
        >>> d = u3.U3(autoOpen = False)
        >>> d.open(LJSocket = "localhost:6000")
        """
        Device.open(self, 3, firstFound = firstFound, serial = serial, localId = localId, devNumber = devNumber, handleOnly = handleOnly, LJSocket = LJSocket )
    open.section = 1
    
    def configU3(self, LocalID = None, TimerCounterConfig = None, FIOAnalog = None, FIODirection = None, FIOState = None, EIOAnalog = None, EIODirection = None, EIOState = None, CIODirection = None, CIOState = None, DAC1Enable = None, DAC0 = None, DAC1 = None, TimerClockConfig = None, TimerClockDivisor = None, CompatibilityOptions = None ):
        """
        Name: U3.configU3(LocalID = None, TimerCounterConfig = None, FIOAnalog = None, FIODirection = None, FIOState = None, EIOAnalog = None, EIODirection = None, EIOState = None, CIODirection = None, CIOState = None, DAC1Enable = None, DAC0 = None, DAC1 = None, TimerClockConfig = None, TimerClockDivisor = None, CompatibilityOptions = None)
        
        Args: See section 5.2.2 of the users guide.
        
        Desc: Sends the low-level configU3 command. Also saves relevant 
              information to the U3 object for later use.
              
        Example:
        Simplest:
        >>> import u3
        >>> d = u3.U3()
        >>> print d.configU3()
        {
         'LocalID': 1, 
         'SerialNumber': 320035782, 
         'DeviceName': 'U3-LV', 
         'FIODirection': 0, 
         'FirmwareVersion': '1.24', 
         ... , 
         'ProductID': 3
        }

        Configure all FIOs and EI0s to analog on boot:
        >>> import u3
        >>> d = u3.U3()
        >>> print d.configU3( FIOAnalog = 255, EIOAnalog = 255)
        {
         'FIOAnalog': 255,
         'EIOAnalog': 255,
         ... , 
         'ProductID': 3
        }
        """
        
        writeMask = 0
        
        if FIOAnalog is not None or FIODirection is not None or FIOState is not None or EIOAnalog is not None or EIODirection is not None or EIOState is not None or CIODirection is not None or CIOState is not None:
            writeMask |= 2
        
        if DAC1Enable is not None or DAC0 is not None or DAC1 is not None:
            writeMask |= 4
        
        if LocalID is not None:
            writeMask |= 8
        
        if TimerClockConfig is not None or TimerClockDivisor is not None:
            writeMask |= 16
        
        if CompatibilityOptions is not None:
            writeMask |= 32
        
        command = [ 0 ] * 26
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x0A
        command[3] = 0x08
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = writeMask
        #command[7] = WriteMask1
        
        if LocalID is not None:
            command[8] = LocalID
        
        if TimerCounterConfig is not None:
            command[9] = TimerCounterConfig
        
        if FIOAnalog is not None:
            command[10] = FIOAnalog
        
        if FIODirection is not None:
            command[11] = FIODirection
        
        if FIOState is not None:
            command[12] = FIOState
        
        if EIOAnalog is not None:
            command[13] = EIOAnalog
        
        if EIODirection is not None:
            command[14] = EIODirection
        
        if EIOState is not None:
            command[15] = EIOState
        
        if CIODirection is not None:
            command[16] = CIODirection
        
        if CIOState is not None:
            command[17] = CIOState
        
        if DAC1Enable is not None:
            command[18] = DAC1Enable
        
        if DAC0 is not None:
            command[19] = DAC0
        
        if DAC1 is not None:
            command[20] = DAC1
        
        if TimerClockConfig is not None:
            command[21] = TimerClockConfig
        
        if TimerClockDivisor is not None:
            command[22] = TimerClockDivisor
        
        if CompatibilityOptions is not None:
            command[23] = CompatibilityOptions
        
        result = self._writeRead(command, 38, [0xF8, 0x10, 0x08])
        
        # Error-free, time to parse the response
        self.firmwareVersion = "%d.%02d" % (result[10], result[9])
        self.bootloaderVersion = "%d.%02d" % (result[12], result[11])
        self.hardwareVersion = "%d.%02d" % (result[14], result[13])
        self.serialNumber = struct.unpack("<I", struct.pack(">BBBB", *result[15:19]))[0]
        self.productId = struct.unpack("<H", struct.pack(">BB", *result[19:21]))[0]
        self.localId = result[21]
        self.timerCounterMask = result[22]
        self.fioAnalog = result[23]
        self.fioDirection = result[24]
        self.fioState = result[25]
        self.eioAnalog = result[26]
        self.eioDirection = result[27]
        self.eioState = result[28]
        self.cioDirection = result[29]
        self.cioState = result[30]
        self.dac1Enable = result[31]
        self.dac0 = result[32]
        self.dac1 = result[33]
        self.timerClockConfig = result[34]
        self.timerClockDivisor = result[35]
        if result[35] == 0:
            self.timerClockDivisor = 256
        
        self.compatibilityOptions = result[36]
        self.versionInfo = result[37]
        self.deviceName = 'U3'
        if self.versionInfo == 1:
            self.deviceName += 'B'
        elif self.versionInfo == 2:
            self.deviceName += '-LV'
        elif self.versionInfo == 18:
            self.deviceName += '-HV'
        
        return { 'FirmwareVersion' : self.firmwareVersion, 'BootloaderVersion' : self.bootloaderVersion, 'HardwareVersion' : self.hardwareVersion, 'SerialNumber' : self.serialNumber, 'ProductID' : self.productId, 'LocalID' : self.localId, 'TimerCounterMask' : self.timerCounterMask, 'FIOAnalog' : self.fioAnalog, 'FIODirection' : self.fioDirection, 'FIOState' : self.fioState, 'EIOAnalog' : self.eioAnalog, 'EIODirection' : self.eioDirection, 'EIOState' : self.eioState, 'CIODirection' : self.cioDirection, 'CIOState' : self.cioState, 'DAC1Enable' : self.dac1Enable, 'DAC0' : self.dac0, 'DAC1' : self.dac1, 'TimerClockConfig' : self.timerClockConfig, 'TimerClockDivisor' : self.timerClockDivisor, 'CompatibilityOptions' : self.compatibilityOptions, 'VersionInfo' : self.versionInfo, 'DeviceName' : self.deviceName }
    configU3.section = 2
    
    def configIO(self, TimerCounterPinOffset = None, EnableCounter1 = None, EnableCounter0 = None, NumberOfTimersEnabled = None, FIOAnalog = None, EIOAnalog = None, EnableUART = None):
        """
        Name: U3.configIO(TimerCounterPinOffset = 4, EnableCounter1 = None, EnableCounter0 = None, NumberOfTimersEnabled = None, FIOAnalog = None, EIOAnalog = None, EnableUART = None)
        
        Args: See section 5.2.3 of the user's guide.
        
        Desc: The configIO command.
        
        Examples:
        Simplest:
        >>> import u3
        >>> d = u3.U3()
        >>> print d.configIO()
        {
         'NumberOfTimersEnabled': 0,
         'TimerCounterPinOffset': 4,
         'DAC1Enable': 0,
         'FIOAnalog': 239,
         'EIOAnalog': 0,
         'TimerCounterConfig': 64,
         'EnableCounter1': False,
         'EnableCounter0': False
        }
        
        Set all FIOs and EIOs to digital (until power cycle):
        >>> import u3
        >>> d = u3.U3()
        >>> print d.configIO(FIOAnalog = 0, EIOAnalog = 0)
        {
         'NumberOfTimersEnabled': 0,
         'TimerCounterPinOffset': 4,
         'DAC1Enable': 0,
         'FIOAnalog': 0,
         'EIOAnalog': 0,
         'TimerCounterConfig': 64,
         'EnableCounter1': False,
         'EnableCounter0': False
        }

        """
        
        writeMask = 0
        
        if EIOAnalog is not None:
            writeMask |= 1
            writeMask |= 8
        
        if FIOAnalog is not None:
            writeMask |= 1
            writeMask |= 4
            
        if EnableUART is not None:
            writeMask |= 1
            writeMask |= (1 << 5)
            
        if TimerCounterPinOffset is not None or EnableCounter1 is not None or EnableCounter0 is not None or NumberOfTimersEnabled is not None :
            writeMask |= 1
        
        command = [ 0 ] * 12
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x03
        command[3] = 0x0B
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = writeMask
        #command[7] = Reserved
        command[8] = 0
        
        if EnableUART is not None:
            command[9] = int(EnableUART) << 2
        
        if TimerCounterPinOffset is None:
            command[8] |= ( 4 & 15 ) << 4
        else:
            command[8] |= ( TimerCounterPinOffset & 15 ) << 4
            
        if EnableCounter1 is not None:
            command[8] |= 1 << 3
        if EnableCounter0 is not None:
            command[8] |= 1 << 2
        if NumberOfTimersEnabled is not None:
            command[8] |= ( NumberOfTimersEnabled & 3 )
            
        if FIOAnalog is not None:
            command[10] = FIOAnalog
        
        if EIOAnalog is not None:
            command[11] = EIOAnalog
        
        result = self._writeRead(command, 12, [0xF8, 0x03, 0x0B])
        
        self.timerCounterConfig = result[8]
        
        self.numberTimersEnabled = self.timerCounterConfig & 3
        self.counter0Enabled = bool( (self.timerCounterConfig >> 2) & 1 )
        self.counter1Enabled = bool( (self.timerCounterConfig >> 3) & 1 )
        self.timerCounterPinOffset = ( self.timerCounterConfig >> 4 )
        
        
        self.dac1Enable = result[9]
        self.fioAnalog = result[10]
        self.eioAnalog = result[11]
        
        return { 'TimerCounterConfig' : self.timerCounterConfig, 'DAC1Enable' : self.dac1Enable, 'FIOAnalog' : self.fioAnalog, 'EIOAnalog' : self.eioAnalog, 'NumberOfTimersEnabled' : self.numberTimersEnabled, 'EnableCounter0' : self.counter0Enabled, 'EnableCounter1' : self.counter1Enabled, 'TimerCounterPinOffset' : self.timerCounterPinOffset }
    configIO.section = 2
    
    def configTimerClock(self, TimerClockBase = None, TimerClockDivisor = None):
        """
        Name: U3.configTimerClock(TimerClockBase = None, TimerClockDivisor = None)
        Args: TimeClockBase, the base for the timer clock.
              TimerClockDivisor, the divisor for the clock.
        
        Desc: Writes and reads the time clock configuration. See section 5.2.4
              of the user's guide.
        
        Note: TimerClockBase and TimerClockDivisor must be set at the same time.
        """
        command = [ 0 ] * 10
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x02
        command[3] = 0x0A
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        #command[6] = Reserved
        #command[7] = Reserved
        if TimerClockBase is not None:
            command[8] = ( 1 << 7 ) + ( TimerClockBase & 7 )
            if TimerClockDivisor is not None:
                command[9] =  TimerClockDivisor
        elif TimerClockDivisor is not None:
            raise LabJackException("You can't set just the divisor, must set both.")
        
        result = self._writeRead(command, 10, [0xf8, 0x02, 0x0A])
        
        self.timerClockBase = ( result[8] & 7 )
        self.timerClockDivisor = result[9]
        
        return { 'TimerClockBase' : self.timerClockBase, 'TimerClockDivisor' : self.timerClockDivisor }
    configTimerClock.section = 2

    def toggleLED(self):
        """
        Name: U3.toggleLED()
        
        Args: None
        
        Desc: Toggles the state LED on and off.
        
        Example:
        >>> import u3
        >>> d = u3.U3()
        >>> d.toggleLED()
        """
        self.getFeedback( LED( not self.ledState ) )
        self.ledState = not self.ledState
    toggleLED.section = 3
    
    def setFIOState(self, fioNum, state = 1):
        """
        Name: U3.setFIOState(fioNum, state = 1)
        Args: fioNum, which FIO to change
              state, 1 = High, 0 = Low
        Desc: A convenience function to set the state of an FIO. Will also
              set the direction to output.  Note that this function can set
              all digital I/O lines (FIO0 - CIO3), and is equivalent to using
              the setDOState method.
        
        Example:
        >>> import u3
        >>> d = u3.U3()
        >>> d.setFIOState(4, state = 1)
        """
        self.getFeedback(BitDirWrite(fioNum, 1), BitStateWrite(fioNum, state))
    setFIOState.section = 3
    
    def getFIOState(self, fioNum):
        """
        Name: U3.getFIOState(fioNum)
        
        Args: fioNum, which FIO to read
        
        Desc: A convenience function to read the state of an FIO.  Note that
              this function can read all digital I/O lines (FIO0 - CIO3), and
              is equivalent to using the getDIOState method.
        
        Example:
        >>> import u3
        >>> d = u3.U3()
        >>> print d.getFIOState(4)
        1
        """
        return self.getFeedback(BitStateRead(fioNum))[0]
    getFIOState.section = 3

    def setDOState(self, ioNum, state = 1):
        """
        Name: U3.setDOState(ioNum, state = 1)
        Args: ioNum, which digital I/O to change
                  0 - 7   = FIO0 - FIO7
                  8 - 15  = EIO0 - EIO7
                  16 - 19 = CIO0 - CIO3
              state, 1 = High, 0 = Low
        Desc: A convenience function to set the state of a digital I/O. Will
              also set the direction to output.
        
        Example:
        >>> import u3
        >>> d = u3.U3()
        >>> d.setDOState(4, state = 1)
        """
        self.getFeedback(BitDirWrite(ioNum, 1), BitStateWrite(ioNum, state))
    setDOState.section = 3

    def getDIState(self, ioNum):
        """
        Name: U3.getDIState(ioNum)
        Args: ioNum, which digital I/O to read
                  0 - 7   = FIO0 - FIO7
                  8 - 15  = EIO0 - EIO7
                  16 - 19 = CIO0 - CIO3
        Desc: A convenience function to read the state of a digital I/O.  Will
              also set the direction to input.
        
        Example:
        >>> import u3
        >>> d = u3.U3()
        >>> print d.getDIState(4)
        1
        """
        return self.getFeedback(BitDirWrite(ioNum, 0), BitStateRead(ioNum))[1]
    getDIState.section = 3

    def getDIOState(self, ioNum):
        """
        Name: U3.getDIOState(ioNum)
        Args: ioNum, which digital I/O to read
                  0 - 7   = FIO0 - FIO7
                  8 - 15  = EIO0 - EIO7
                  16 - 19 = CIO0 - CIO3
        Desc: A convenience function to read the state of a digital I/O.  Will
              not change the direction.
        
        Example:
        >>> import u3
        >>> d = u3.U3()
        >>> print d.getDIOState(4)
        1
        """
        return self.getFeedback(BitStateRead(ioNum))[0]
    getDIOState.section = 3

    def getTemperature(self):
        """
        Name: U3.getTemperature()
        
        Args: None
        
        Desc: Reads the internal temperature sensor on the U3. Returns the
              temperature in Kelvin.
        """
        
        # Get the calibration data first, otherwise the conversion is way off (10 degC on my U3)
        if self.calData is None:
            self.getCalibrationData()

        bits, = self.getFeedback( AIN(30, 31) )
        
        return self.binaryToCalibratedAnalogTemperature(bits)

    def getAIN(self, posChannel, negChannel = 31, longSettle=False, quickSample=False):
        """
        Name: U3.getAIN(posChannel, negChannel = 31, longSettle=False,
                                                     quickSample=False)
        
        Args: posChannel, the positive channel to read from.
              negChannel, the negitive channel to read from.
              longSettle, set to True for longSettle
              quickSample, set to True for quickSample
        
        Desc: A convenience function to read an AIN.
        
        Example:
        >>> import u3
        >>> d = u3.U3()
        >>> print d.getAIN( 0 )
        0.0501680038869
        """
        isSpecial = False
        
        if negChannel == 32:
            isSpecial = True
            negChannel = 30
        
        bits = self.getFeedback(AIN(posChannel, negChannel, longSettle, quickSample))[0]
        
        singleEnded = True
        if negChannel != 31:
            singleEnded = False
        
        lvChannel = True
        
        try:
            if self.deviceName.endswith("-HV") and posChannel < 4:
                lvChannel = False
        except AttributeError:
            pass
        
        if isSpecial:
            negChannel = 32
        
        return self.binaryToCalibratedAnalogVoltage(bits, isLowVoltage = lvChannel, isSingleEnded = singleEnded, isSpecialSetting = isSpecial, channelNumber = posChannel)
    getAIN.section = 3

    def configAnalog(self, *args):
        """
        Convenience method to configIO() that adds the given input numbers
        in the range FIO0-EIO7 (0-15) to the analog team. That is, it adds
        the given bit positions to those already set in the FIOAnalog
        and EIOAnalog bitfields.

        >>> import u3
        >>> d = u3.U3()
        >>> d.debug = True
        >>> d.configIO()
        Sent:  [0x47, 0xf8, 0x3, 0xb, 0x40, 0x0, 0x0, 0x0, 0x40, 0x0, 0x0, 0x0]
        Result:  [0x56, 0xf8, 0x3, 0xb, 0x4f, 0x0, 0x0, 0x0, 0x40, 0x0, 0xf, 0x0]
        {'NumberOfTimersEnabled': 0, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 64, 'EnableCounter1': False, 'EnableCounter0': False}
        >>> d.configAnalog(u3.FIO4, u3.FIO5)
        Sent:  [0x47, 0xf8, 0x3, 0xb, 0x40, 0x0, 0x0, 0x0, 0x40, 0x0, 0x0, 0x0]
        Result:  [0x56, 0xf8, 0x3, 0xb, 0x4f, 0x0, 0x0, 0x0, 0x40, 0x0, 0xf, 0x0]
        Sent:  [0x93, 0xf8, 0x3, 0xb, 0x8c, 0x0, 0xd, 0x0, 0x40, 0x0, 0x3f, 0x0]
        Result:  [0x86, 0xf8, 0x3, 0xb, 0x7f, 0x0, 0x0, 0x0, 0x40, 0x0, 0x3f, 0x0]
        {'NumberOfTimersEnabled': 0, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 63, 'EIOAnalog': 0, 'TimerCounterConfig': 64, 'EnableCounter1': False, 'EnableCounter0': False}
        """
        configIODict = self.configIO()
        # Without args, return the same as configIO()
        if len(args) == 0:
            return configIODict

        FIOAnalog, EIOAnalog = configIODict['FIOAnalog'], configIODict['EIOAnalog']
        #
        for i in args:
            if i > EIO7:
                pass    # Invalid. Must be in the range FIO0-EIO7.
            elif i < EIO0:
                FIOAnalog |= 2**i
            else:
                EIOAnalog |= 2**(i-EIO0)   # Start the EIO counting at 0, not 8
        return self.configIO(FIOAnalog = FIOAnalog, EIOAnalog = EIOAnalog)

    def configDigital(self, *args):
        """
        The converse of configAnalog(). The convenience method to configIO,
        adds the given input numbers in the range FIO0-EIO7 (0-15) to the
        digital team. That is, it removes the given bit positions from those
        already set in the FIOAnalog and EIOAnalog bitfields.

        >>> import u3
        >>> d = u3.U3()
        >>> d.debug = True
        >>> d.configIO()
        Sent:  [0x47, 0xf8, 0x3, 0xb, 0x40, 0x0, 0x0, 0x0, 0x40, 0x0, 0x0, 0x0]
        Result:  [0x56, 0xf8, 0x3, 0xb, 0x4f, 0x0, 0x0, 0x0, 0x40, 0x0, 0xf, 0x0]
        {'NumberOfTimersEnabled': 0, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 64, 'EnableCounter1': False, 'EnableCounter0': False}
        >>> d.configAnalog(u3.FIO4, u3.FIO5, u3.EIO0)
        Sent:  [0x47, 0xf8, 0x3, 0xb, 0x40, 0x0, 0x0, 0x0, 0x40, 0x0, 0x0, 0x0]
        Result:  [0x56, 0xf8, 0x3, 0xb, 0x4f, 0x0, 0x0, 0x0, 0x40, 0x0, 0xf, 0x0]
        Sent:  [0x94, 0xf8, 0x3, 0xb, 0x8d, 0x0, 0xd, 0x0, 0x40, 0x0, 0x3f, 0x1]
        Result:  [0x87, 0xf8, 0x3, 0xb, 0x80, 0x0, 0x0, 0x0, 0x40, 0x0, 0x3f, 0x1]
        {'NumberOfTimersEnabled': 0, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 63, 'EIOAnalog': 1, 'TimerCounterConfig': 64, 'EnableCounter1': False, 'EnableCounter0': False}
        >>> d.configDigital(u3.FIO4, u3.FIO5, u3.EIO0)
        Sent:  [0x47, 0xf8, 0x3, 0xb, 0x40, 0x0, 0x0, 0x0, 0x40, 0x0, 0x0, 0x0]
        Result:  [0x87, 0xf8, 0x3, 0xb, 0x80, 0x0, 0x0, 0x0, 0x40, 0x0, 0x3f, 0x1]
        Sent:  [0x63, 0xf8, 0x3, 0xb, 0x5c, 0x0, 0xd, 0x0, 0x40, 0x0, 0xf, 0x0]
        Result:  [0x56, 0xf8, 0x3, 0xb, 0x4f, 0x0, 0x0, 0x0, 0x40, 0x0, 0xf, 0x0]
        {'NumberOfTimersEnabled': 0, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 64, 'EnableCounter1': False, 'EnableCounter0': False}

        """
        configIODict = self.configIO()
        # Without args, return the same as configIO()
        if len(args) == 0:
            return configIODict

        FIOAnalog, EIOAnalog = configIODict['FIOAnalog'], configIODict['EIOAnalog']
        #
        for i in args:
            if i > EIO7:
                pass    # Invalid. Must be in the range FIO0-EIO7.
            elif i < EIO0:
                if FIOAnalog & 2**i:    # If it is set
                    FIOAnalog ^= 2**i   # Remove it
            else:
                if EIOAnalog & 2**(i-EIO0):   # Start the EIO counting at 0, not 8
                    EIOAnalog ^= 2**(i-EIO0)
        return self.configIO(FIOAnalog = FIOAnalog, EIOAnalog = EIOAnalog)

    def _buildBuffer(self, sendBuffer, readLen, commandlist):
        """
        Builds up the buffer to be written for getFeedback
        """
        for cmd in commandlist:
            if isinstance(cmd, FeedbackCommand):
                sendBuffer += cmd.cmdBytes
                readLen += cmd.readLen
            elif isinstance(cmd, list):
                sendBuffer, readLen = self._buildBuffer(sendBuffer, readLen, cmd)
        return (sendBuffer, readLen)
    _buildBuffer.section = 4
                
    def _buildFeedbackResults(self, rcvBuffer, commandlist, results, i):
        """
        Builds the result list from the results of getFeedback
        """
        for cmd in commandlist:
            if isinstance(cmd, FeedbackCommand):
                results.append(cmd.handle(rcvBuffer[i:i+cmd.readLen]))
                i += cmd.readLen
            elif isinstance(cmd, list):
                self._buildFeedbackResults(rcvBuffer, cmd, results, i)
        return results
    _buildFeedbackResults.section = 4

    def getFeedback(self, *commandlist):
        """
        Name: U3.getFeedback(commandlist)
        
        Args: the FeedbackCommands to run
        
        Desc: Forms the commandlist into a packet, sends it to the U3, and reads the response.
        
        Examples:
        >>> myU3 = u3.U3()
        >>> ledCommand = u3.LED(False)
        >>> ain0Command = u3.AIN(0, 31, True)
        >>> myU3.getFeedback(ledCommand, ain0Command)
        [None, 9376]

        OR if you like the list version better:
        
        >>> myU3 = U3()
        >>> ledCommand = u3.LED(False)
        >>> ain0Command = u3.AIN(30, 31, True)
        >>> commandList = [ ledCommand, ain0Command ]
        >>> myU3.getFeedback(commandList)
        [None, 9376]
        
        """
        
        sendBuffer = [0] * 7
        sendBuffer[1] = 0xF8
        readLen = 9
        sendBuffer, readLen = self._buildBuffer(sendBuffer, readLen, commandlist)
        if len(sendBuffer) % 2:
            sendBuffer += [0]
        sendBuffer[2] = len(sendBuffer) / 2 - 3
        
        if readLen % 2:
            readLen += 1
            
        
        if len(sendBuffer) > MAX_USB_PACKET_LENGTH:
            raise LabJackException("ERROR: The feedback command you are attempting to send is bigger than 64 bytes ( %s bytes ). Break your commands up into separate calls to getFeedback()." % len(sendBuffer))
        
        if readLen > MAX_USB_PACKET_LENGTH:
            raise LabJackException("ERROR: The feedback command you are attempting to send would yield a response that is greater than 64 bytes ( %s bytes ). Break your commands up into separate calls to getFeedback()." % readLen)
        
        rcvBuffer = self._writeRead(sendBuffer, readLen, [], checkBytes = False, stream = False, checksum = True)
        
        # Check the response for errors
        try:
            self._checkCommandBytes(rcvBuffer, [0xF8])
        
            if rcvBuffer[3] != 0x00:
                raise LabJackException("Got incorrect command bytes")
        except LowlevelErrorException, e:
            if isinstance(commandlist[0], list):
                culprit = commandlist[0][ (rcvBuffer[7] -1) ]
            else:
                culprit = commandlist[ (rcvBuffer[7] -1) ]
            
            raise LowlevelErrorException("\nThis Command\n    %s\nreturned an error:\n    %s" %  (culprit , lowlevelErrorToString(rcvBuffer[6])))
            
        
        results = []
        i = 9
        return self._buildFeedbackResults(rcvBuffer, commandlist, results, i)
    getFeedback.section = 2    
    
    def readMem(self, blockNum, readCal=False):
        """
        Name: U3.readMem(blockNum, readCal=False)
        
        Args: blockNum, which block to read from
              readCal, set to True to read from calibration instead.
        
        Desc: Reads 1 block (32 bytes) from the non-volatile user or
              calibration memory. Please read section 5.2.6 of the user's guide
              before you do something you may regret.
        
        NOTE: Do not call this function while streaming.
        """
        command = [ 0 ] * 8
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x01
        command[3] = 0x2A
        if readCal:
            command[3] = 0x2D
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = 0x00
        command[7] = blockNum
        
        result = self._writeRead(command, 40, [0xF8, 0x11, command[3]])
        
        return result[8:]
    readMem.section = 2
     
    def readCal(self, blockNum):
        """
        Name: U3.readCal(blockNum)
        
        Args: blockNum, which block to read
        
        Desc: See the description of readMem and section 5.2.6 of the user's
              guide.
        
        Note: Do not call this function while streaming.
        """
        return self.readMem(blockNum, readCal = True)
    readCal.section = 2
        
    def writeMem(self, blockNum, data, writeCal=False):
        """
        Name: U3.writeMem(blockNum, data, writeCal=False)
        
        Args: blockNum, which block to write
              data, a list of bytes to write.
              writeCal, set to True to write to calibration instead
        
        Desc: Writes 1 block (32 bytes) from the non-volatile user or
              calibration memory. Please read section 5.2.7 of the user's guide
              before you do something you may regret. Memory must be erased
              before writing.
        
        Note: Do not call this function while streaming.
        """
        if not isinstance(data, list):
            raise LabJackException("Data must be a list of bytes")
        
        command = [ 0 ] * 40
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x11
        command[3] = 0x28
        if writeCal:
            command[3] = 0x2B
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = 0x00
        command[7] = blockNum
        command[8:] = data
        
        
        self._writeRead(command, 8, [0xF8, 0x01, command[3]])
    writeMem.section = 2
    
    def writeCal(self, blockNum):
        """
        Name: U3.writeCal(blockNum, data)
        
        Args: blockNum, which block to write
              data, a list of bytes
        
        Desc: See the description of writeMem and section 5.2.7 of the user's
              guide.
        
        Note: Do not call this function while streaming.
        """
        return self.writeMem(blockNum, data, writeCal = True)
    writeCal.section = 2
        
    def eraseMem(self, eraseCal=False):
        """
        Name: U3.eraseMem(eraseCal=False)
        
        Args: eraseCal, set to True to erase the calibration memory instead
        
        Desc: The U3 uses flash memory that must be erased before writing.
              Please read section 5.2.8 of the user's guide before you do
              something you may regret.
        
        Note: Do not call this function while streaming.
        """
        if eraseCal:
            command = [ 0 ] * 8
            
            #command[0] = Checksum8
            command[1] = 0xF8
            command[2] = 0x01
            command[3] = 0x2C
            #command[4] = Checksum16 (LSB)
            #command[5] = Checksum16 (MSB)
            command[6] = 0x4C
            command[7] = 0x6C
        else:
            command = [ 0 ] * 6
            
            #command[0] = Checksum8
            command[1] = 0xF8
            command[2] = 0x00
            command[3] = 0x29
            #command[4] = Checksum16 (LSB)
            #command[5] = Checksum16 (MSB)
        
        self._writeRead(command, 8, [0xF8, 0x01, command[3]])
    eraseMem.section = 2
    
    def eraseCal(self):
        """
        Name: U3.eraseCal()
        
        Args: None
        
        Desc: See the description of writeMem and section 5.2.8 of the user's
              guide.
        
        Note: Do not call this function while streaming.
        """
        return self.eraseMem(eraseCal = True)
    eraseCal.section = 2
    
    def reset(self, hardReset = False):
        """
        Name: U3.reset(hardReset = False)
        
        Args: hardReset, set to True for a hard reset.
        
        Desc: Causes a soft or hard reset.  A soft reset consists of 
              re-initializing most variables without re-enumeration. A hard
              reset is a reboot of the processor and does cause re-enumeration.
              See section 5.2.9 of the User's guide.
        """
        command = [ 0 ] * 4
        
        #command[0] = Checksum8
        command[1] = 0x99
        command[2] = 1
        if hardReset:
            command[2] = 2
        command[3] = 0x00
        
        command = setChecksum8(command, 4)
        
        self._writeRead(command, 4, [], False, False, False)
    reset.section = 2

    def streamConfig(self, NumChannels = 1, SamplesPerPacket = 25, InternalStreamClockFrequency = 0, DivideClockBy256 = False, Resolution = 3, ScanInterval = 1, PChannels = [30], NChannels = [31], ScanFrequency = None, SampleFrequency = None):
        """
        Name: U3.streamConfig(NumChannels = 1, SamplesPerPacket = 25,
                              InternalStreamClockFrequency = 0, DivideClockBy256 = False,
                              Resolution = 3, ScanInterval = 1,
                              PChannels = [30], NChannels = [31],
                              ScanFrequency = None, SampleFrequency = None)
        Args: NumChannels, the number of channels to stream
              Resolution, the resolution of the samples (0 - 3)
              PChannels, a list of channel numbers to stream
              NChannels, a list of channel options bytes
              
              Set Either:
              
              ScanFrequency, the frequency in Hz to scan the channel list (PChannels).
                             sample rate (Hz) = ScanFrequency * NumChannels
              
              -- OR --
              
              SamplesPerPacket, how many samples make one packet
              InternalStreamClockFrequency, 0 = 4 MHz, 1 = 48 MHz
              DivideClockBy256, True = divide the clock by 256
              ScanInterval, clock/ScanInterval = frequency.
              
              See Section 5.2.10 of the User's Guide for more details.
              
              Deprecated:
              
              SampleFrequency, the frequency in Hz to sample.  Use ScanFrequency
                               since SampleFrequency has always set the scan
                               frequency and the name is confusing.
        
        Desc: Stream mode operates on a table of channels that are scanned
              at the specified scan rate. Before starting a stream, you need 
              to call this function to configure the table and scan clock.
        
        Note: Requires U3 hardware version 1.21 or greater.
        """
        if len(PChannels) != NumChannels:
            raise LabJackException("Length of PChannels didn't match NumChannels")
        if len(NChannels) != NumChannels:
            raise LabJackException("Length of NChannels didn't match NumChannels")
        if len(PChannels) != len(NChannels):
            raise LabJackException("Length of PChannels didn't match the length of NChannels")
        
        if ScanFrequency != None or SampleFrequency != None:
            if ScanFrequency == None:
                ScanFrequency = SampleFrequency
            if ScanFrequency < 1000:
                if ScanFrequency < 25:
                    SamplesPerPacket = ScanFrequency
                DivideClockBy256 = True
                ScanInterval = 15625/ScanFrequency
            else:
                DivideClockBy256 = False
                ScanInterval = 4000000/ScanFrequency
        
        # Force Scan Interval into correct range
        ScanInterval = min( ScanInterval, 65535 )
        ScanInterval = int( ScanInterval )
        ScanInterval = max( ScanInterval, 1 )
        
        # Same with Samples per packet
        SamplesPerPacket = max( SamplesPerPacket, 1)
        SamplesPerPacket = int( SamplesPerPacket )
        SamplesPerPacket = min ( SamplesPerPacket, 25)
        
        command = [ 0 ] * ( 12 + (NumChannels * 2) )
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = NumChannels+3
        command[3] = 0x11
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = NumChannels
        command[7] = SamplesPerPacket
        #command[8] = Reserved
        
        command[9] |= ( InternalStreamClockFrequency & 0x01 ) << 3
        if DivideClockBy256:
            command[9] |= 1 << 2
        command[9] |= ( Resolution & 3 )
        
        t = struct.pack("<H", ScanInterval)
        command[10] = ord(t[0])
        command[11] = ord(t[1])
        
        for i in range(NumChannels):
            command[12+(i*2)] = PChannels[i]
            if NChannels[i] == 32:
                command[13+(i*2)] = 30
            else:
                command[13+(i*2)] = NChannels[i]
        
        self._writeRead(command, 8, [0xF8, 0x01, 0x11])
        
        self.streamSamplesPerPacket = SamplesPerPacket
        self.streamChannelNumbers = PChannels
        self.streamNegChannels = NChannels
        
        self.streamConfiged = True
        if InternalStreamClockFrequency == 1:
            freq = float(48000000)
        else:
            freq = float(4000000)
        
        if DivideClockBy256:
            freq /= 256
        
        freq = freq/ScanInterval
        
        if SamplesPerPacket < 25:
            #limit to one packet
            self.packetsPerRequest = 1
        else:
            self.packetsPerRequest = max(1, int(freq/SamplesPerPacket))
            self.packetsPerRequest = min(self.packetsPerRequest, 48)
    streamConfig.section = 2
    
    def processStreamData(self, result, numBytes = None):
        """
        Name: U3.processStreamData(result, numBytes = None)
        Args: result, the string returned from streamData()
              numBytes, the number of bytes per packet.
        Desc: Breaks stream data into individual channels and applies
              calibrations.
              
        >>> reading = d.streamData(convert = False)
        >>> print proccessStreamData(reading['result'])
        defaultDict(list, {'AIN0' : [3.123, 3.231, 3.232, ...]})
        """
        if numBytes is None:
            numBytes = 14 + (self.streamSamplesPerPacket * 2)
        
        returnDict = collections.defaultdict(list)
        
        for packet in self.breakupPackets(result, numBytes):
            for sample in self.samplesFromPacket(packet):
                if self.streamPacketOffset >= len(self.streamChannelNumbers):
                    self.streamPacketOffset = 0
                
                if self.streamChannelNumbers[self.streamPacketOffset] in (193, 194):
                    value = struct.unpack('<BB', sample )
                elif self.streamChannelNumbers[self.streamPacketOffset] >= 200:
                    value = struct.unpack('<H', sample )[0]
                else:  
                    if self.streamNegChannels[self.streamPacketOffset] == 31:
                        # do unsigned
                        value = struct.unpack('<H', sample )[0]
                        singleEnded = True
                    else:
                        # do signed
                        value = struct.unpack('<H', sample )[0]
                        singleEnded = False
                    
                    lvChannel = True
                    if self.deviceName.lower().endswith('hv') and self.streamChannelNumbers[self.streamPacketOffset] < 4:
                        lvChannel = False
                    
                    isSpecial = False
                    if self.streamNegChannels[self.streamPacketOffset] == 32:
                        isSpecial = True

                    value = self.binaryToCalibratedAnalogVoltage(value, isLowVoltage = lvChannel, isSingleEnded = singleEnded, channelNumber = self.streamChannelNumbers[self.streamPacketOffset], isSpecialSetting = isSpecial)
                
                returnDict["AIN%s" % self.streamChannelNumbers[self.streamPacketOffset]].append(value)
            
                self.streamPacketOffset += 1

        return returnDict
    processStreamData.section = 3
    
    def watchdog(self, ResetOnTimeout = False, SetDIOStateOnTimeout = False, TimeoutPeriod = 60, DIOState = 0, DIONumber = 0, onlyRead=False):
        """
        Name: U3.watchdog(ResetOnTimeout = False, SetDIOStateOnTimeout = False,
                          TimeoutPeriod = 60, DIOState = 0, DIONumber = 0,
                          onlyRead = False)
        
        Args: Check out section 5.2.14 of the user's guide.
              Set onlyRead to True to perform only a read
        
        Desc: This function will write the configuration of the watchdog,
              unless onlyRead is set to True.
        
        Returns a dictionary:
        {
            'WatchDogEnabled' : True if the watchdog is enabled, otherwise False
            'ResetOnTimeout' : If True, the device will reset on timeout.
            'SetDIOStateOnTimeout' : If True, the state of a DIO will be set
            'TimeoutPeriod' : Timeout Period in seconds
            'DIOState' : The state the DIO will be set to on timeout
            'DIONumber' : Which DIO will be set on timeout
        }
        
        NOTE: Requires U3 hardware version 1.21 or greater.
        """
        command = [ 0 ] * 16
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x05
        command[3] = 0x09
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        if not onlyRead:
            command[6] = 1
        
        if ResetOnTimeout:
            command[7] |= 1 << 5
        if SetDIOStateOnTimeout:
            command[7] |= 1 << 4
        
        t = struct.pack("<H", TimeoutPeriod)
        command[8] = ord(t[0])
        command[9] = ord(t[1])
        
        command[10] = (( DIOState & 1 ) << 7) + ( DIONumber & 15)
        
        
        result = self._writeRead(command, 16, [0xF8, 0x05, 0x09])
        
        watchdogStatus = {}
        
        if result[7] == 0 or result[7] == 255:
            watchdogStatus['WatchDogEnabled'] = False
            watchdogStatus['ResetOnTimeout'] = False
            watchdogStatus['SetDIOStateOnTimeout'] = False
        else:
            watchdogStatus['WatchDogEnabled'] = True
            
            if (( result[7] >> 5 ) & 1):
                watchdogStatus['ResetOnTimeout'] = True
            else:
                watchdogStatus['ResetOnTimeout'] = False
                
            if (( result[7] >> 4 ) & 1):
                watchdogStatus['SetDIOStateOnTimeout'] = True
            else:
                watchdogStatus['SetDIOStateOnTimeout'] = False
        
        watchdogStatus['TimeoutPeriod'] = struct.unpack('<H', struct.pack("BB", *result[8:10]))
        
        if (( result[10] >> 7 ) & 1):
            watchdogStatus['DIOState'] = 1
        else:
            watchdogStatus['DIOState'] = 0 
        
        watchdogStatus['DIONumber'] = ( result[10] & 15 )
        
        return watchdogStatus
    watchdog.section = 2

    SPIModes = { 'A' : 0, 'B' : 1, 'C' : 2, 'D' : 3 }
    def spi(self, SPIBytes, AutoCS=True, DisableDirConfig = False, SPIMode = 'A', SPIClockFactor = 0, CSPINNum = 4, CLKPinNum = 5, MISOPinNum = 6, MOSIPinNum = 7):
        """
        Name: U3.spi(SPIBytes, AutoCS=True, DisableDirConfig = False,
                     SPIMode = 'A', SPIClockFactor = 0, CSPINNum = 4,
                     CLKPinNum = 5, MISOPinNum = 6, MOSIPinNum = 7)
        
        Args: SPIBytes, a list of bytes to be transferred.
              See Section 5.2.15 of the user's guide.
        
        Desc: Sends and receives serial data using SPI synchronous
              communication.
        
        NOTE: Requires U3 hardware version 1.21 or greater.
        """
        if not isinstance(SPIBytes, list):
            raise LabJackException("SPIBytes MUST be a list of bytes")
        
        numSPIBytes = len(SPIBytes)
        
        oddPacket = False
        if numSPIBytes%2 != 0:
            SPIBytes.append(0)
            numSPIBytes = numSPIBytes + 1
            oddPacket = True
        
        command = [ 0 ] * (13 + numSPIBytes)
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 4 + (numSPIBytes/2)
        command[3] = 0x3A
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        
        if AutoCS:
            command[6] |= (1 << 7)
        if DisableDirConfig:
            command[6] |= (1 << 6)
        
        command[6] |= ( self.SPIModes[SPIMode] & 3 )
        
        command[7] = SPIClockFactor
        #command[8] = Reserved
        command[9] = CSPINNum
        command[10] = CLKPinNum
        command[11] = MISOPinNum
        command[12] = MOSIPinNum
        command[13] = numSPIBytes
        if oddPacket:
            command[13] = numSPIBytes - 1
        
        command[14:] = SPIBytes
        
        result = self._writeRead(command, 8+numSPIBytes, [ 0xF8, 1+(numSPIBytes/2), 0x3A ])
                
        return result[8:]
    spi.section = 2
        
    def asynchConfig(self, Update = True, UARTEnable = True, DesiredBaud  = 9600, olderHardware = False, configurePins = True ):
        """
        Name: U3.asynchConfig(Update = True, UARTEnable = True, 
                              DesiredBaud = 9600, olderHardware = False,
                              configurePins = True)
        Args: See section 5.2.16 of the User's Guide.
              olderHardware, If using hardware 1.21, please set olderHardware 
                             to True and read the timer configuration first.
              configurePins, Will call the configIO to set up pins for you.
        
        Desc: Configures the U3 UART for asynchronous communication. 
        
        returns a dictionary:
        {
            'Update' : True means new parameters were written
            'UARTEnable' : True means the UART is enabled
            'BaudFactor' : The baud factor being used
        }
        
        Note: Requires U3 hardware version 1.21+.
        """
        if configurePins:
            self.configIO(EnableUART=True)
        
        command = [ 0 ] * 10
            
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x02
        command[3] = 0x14
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        #command[6] = 0x00
        
        if Update:
            command[7] |= ( 1 << 7 )
        if UARTEnable:
            command[7] |= ( 1 << 6 )
        
        #command[8] = Reserved
        if olderHardware:
            command[9] = (2**8) - self.timerClockBase/DesiredBaud
        else:
            BaudFactor = (2**16) - 48000000/(2 * DesiredBaud)
            t = struct.pack("<H", BaudFactor)
            command[8] = ord(t[0])
            command[9] = ord(t[1])
        
        if olderHardware:
            result = self._writeRead(command, 10, [0xF8, 0x02, 0x14])
        else:
            result = self._writeRead(command, 10, [0xF8, 0x02, 0x14])
        
        returnDict = {}
        
        if ( ( result[7] >> 7 ) & 1 ):
            returnDict['Update'] = True
        else:
            returnDict['Update'] = False
        
        if ( ( result[7] >> 6 ) & 1):
            returnDict['UARTEnable'] = True
        else:
            returnDict['UARTEnable'] = False
            
        if olderHardware:
            returnDict['BaudFactor'] = result[9]
        else:
            returnDict['BaudFactor'] = struct.unpack("<H", struct.pack("BB", *result[8:]))[0]

        return returnDict
    asynchConfig.section = 2
    
    def asynchTX(self, AsynchBytes):
        """
        Name: U3.asynchTX(AsynchBytes)
        
        Args: AsynchBytes, must be a list of bytes to transfer.
        
        Desc: Sends bytes to the U3 UART which will be sent asynchronously on
              the transmit line. See section 5.2.17 of the user's guide.
        
        returns a dictionary:
        {
            'NumAsynchBytesSent' : Number of Asynch Bytes Sent
            'NumAsynchBytesInRXBuffer' : How many bytes are currently in the
                                         RX buffer.
        }
        
        Note: Requres U3 hardware version 1.21 or greater.
        """
        if not isinstance(AsynchBytes, list):
            raise LabJackException("AsynchBytes must be a list")
        
        numBytes = len(AsynchBytes)
        
        oddPacket = False
        if numBytes%2 != 0:
            AsynchBytes.append(0)
            numBytes = numBytes+1
            oddPacket = True
        
        command = [ 0 ] * ( 8 + numBytes)
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 1 + ( numBytes/2 )
        command[3] = 0x15
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        #command[6] = 0x00
        command[7] = numBytes
        if oddPacket:
            command[7] = numBytes - 1
        
        command[8:] = AsynchBytes
        
        result = self._writeRead(command, 10, [0xF8, 0x02, 0x15])
        
        return { 'NumAsynchBytesSent' : result[7], 'NumAsynchBytesInRXBuffer' : result[8] }
    asynchTX.section = 2
    
    def asynchRX(self, Flush = False):
        """
        Name: U3.asynchRX(Flush = False)
        
        Args: Flush, Set to True to flush
        
        Desc: Reads the oldest 32 bytes from the U3 UART RX buffer
              (received on receive terminal). The buffer holds 256 bytes. See
              section 5.2.18 of the User's Guide.

        returns a dictonary:
        {
            'AsynchBytes' : List of received bytes
            'NumAsynchBytesInRXBuffer' : Number of AsynchBytes are in the RX
                                         Buffer.
        }

        Note: Requres U3 hardware version 1.21 or greater.
        """
        command = [ 0 ] * 8
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x01
        command[3] = 0x16
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        #command[6] = 0x00
        if Flush:
            command[7] = 1
        
        
        result = self._writeRead(command, 40, [0xF8, 0x11, 0x16])
        
        return { 'AsynchBytes' : result[8:], 'NumAsynchBytesInRXBuffer' : result[7] }
    asynchRX.section = 2
    
    def i2c(self, Address, I2CBytes, EnableClockStretching = False, NoStopWhenRestarting = False, ResetAtStart = False, SpeedAdjust = 0, SDAPinNum = 6, SCLPinNum = 7, NumI2CBytesToReceive = 0, AddressByte = None):
        """
        Name: U3.i2c(Address, I2CBytes, ResetAtStart = False, 
                     EnableClockStretching = False, SpeedAdjust = 0,
                     SDAPinNum = 6, SCLPinNum = 7, NumI2CBytesToReceive = 0,
                     AddressByte = None)
        
        Args: Address, the address (not shifted over)
              I2CBytes, must be a list of bytes to send.
              See section 5.2.19 of the user's guide.
              AddressByte, use this if you don't want a shift applied.
                           This address will be put it in the low-level 
                           packet directly and overrides Address. Optional.
        
        Desc: Sends and receives serial data using I2C synchronous
              communication.
        
        Note: Requires hardware version 1.21 or greater.
        """
        if not isinstance(I2CBytes, list):
            raise LabJackException("I2CBytes must be a list")
        
        numBytes = len(I2CBytes)
        
        oddPacket = False
        if numBytes%2 != 0:
            I2CBytes.append(0)
            numBytes = numBytes + 1
            oddPacket = True
        
        command = [ 0 ] * (14 + numBytes)
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 4 + (numBytes/2)
        command[3] = 0x3B
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        if ResetAtStart:
            command[6] |= (1 << 1)
        if NoStopWhenRestarting:
            command[6] |= (1 << 2)
        if EnableClockStretching:
            command[6] |= (1 << 3)
        
        command[7] = SpeedAdjust
        command[8] = SDAPinNum
        command[9] = SCLPinNum
        if AddressByte != None:
            command[10] = AddressByte
        else:
            command[10] = Address << 1
        command[12] = numBytes
        if oddPacket:
            command[12] = numBytes-1
        command[13] = NumI2CBytesToReceive
        command[14:] = I2CBytes
        
        oddResponse = False
        if NumI2CBytesToReceive%2 != 0:
            NumI2CBytesToReceive = NumI2CBytesToReceive+1
            oddResponse = True
        
        result = self._writeRead(command, 12+NumI2CBytesToReceive, [0xF8, (3+(NumI2CBytesToReceive/2)), 0x3B])
                
        if len(result) > 12:
            if oddResponse:
                return { 'AckArray' : result[8:12], 'I2CBytes' : result[12:-1] }
            else:
                return { 'AckArray' : result[8:12], 'I2CBytes' : result[12:] }
        else:
            return { 'AckArray' : result[8:], 'I2CBytes' : [] }
    i2c.section = 2
    
    def sht1x(self, DataPinNum = 4, ClockPinNum = 5, SHTOptions = 0xc0):
        """
        Name: U3.sht1x(DataPinNum = 4, ClockPinNum = 5, SHTOptions = 0xc0)
        
        Args: See section 5.2.20 of the user's guide.
              SHTOptions, see below.
        
        Desc: Reads temperature and humidity from a Sensirion SHT1X sensor
              (which is used by the EI-1050).

        Returns a dictonary:
        {
            'StatusReg' : SHT1X status register
            'StatusRegCRC' : SHT1X status register CRC value
            'Temperature' : The temperature in C
            'TemperatureCRC' : The CRC value for the temperature
            'Humidity' : The humidity
            'HumidityCRC' : The CRC value for the humidity
        }

        Note: Requires hardware version 1.21 or greater.
        
        SHTOptions (and proof people read documentation):
            bit 7 = Read Temperature
            bit 6 = Read Realtive Humidity
            bit 2 = Heater. 1 = on, 0 = off
            bit 1 = Reserved at 0
            bit 0 = Resolution. 1 = 8 bit RH, 12 bit T; 0 = 12 RH, 14 bit T
        """
        command = [ 0 ] * 10
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x02
        command[3] = 0x39
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = DataPinNum
        command[7] = ClockPinNum
        #command[8] = Reserved
        command[9] = SHTOptions
        
        result = self._writeRead(command, 16, [0xF8, 0x05, 0x39])
        
        val = (result[11]*256) + result[10]
        temp = -39.60 + 0.01*val
        
        val = (result[14]*256) + result[13]
        humid = -4 + 0.0405*val + -.0000028*(val*val)
        humid = (temp - 25)*(0.01 + 0.00008*val) + humid
        
        return { 'StatusReg' : result[8], 'StatusRegCRC' : result[9], 'Temperature' : temp, 'TemperatureCRC' : result[12] , 'Humidity' : humid, 'HumidityCRC' : result[15] }
    sht1x.section = 2
    
    def binaryToCalibratedAnalogVoltage(self, bits, isLowVoltage = True, isSingleEnded = True, isSpecialSetting = False, channelNumber = 0):
        """
        Name: U3.binaryToCalibratedAnalogVoltage(bits, isLowVoltage = True,
                                                 isSingleEnded = True,
                                                 isSpecialSetting = False,
                                                 channelNumber = 0)
        
        Args: bits, the binary value of the reading.
              isLowVoltage, True if the reading came from a low-voltage channel
              isSingleEnded, True if the reading is not differential
              isSpecialSetting, True if the reading came from special range
              channelNumber, used to apply the correct calibration for HV
        
        Desc: Converts the bits returned from AIN functions into a calibrated
              voltage.
              
        Example:
        >>> import u3
        >>> d = u3.U3()
        >>> bits = d.getFeedback( u3.AIN(0, 31))[0]
        >>> print bits
        1248
        >>> print d.binaryToCalibratedAnalogVoltage(bits)
        0.046464288000000006
        """
        hasCal = self.calData is not None
        if isLowVoltage:
            if isSingleEnded and not isSpecialSetting:
                if hasCal:
                    return ( bits * self.calData['lvSESlope'] ) + self.calData['lvSEOffset']
                else:
                    return ( bits * 0.000037231 ) + 0
            elif isSpecialSetting:
                if hasCal:
                    return ( bits * self.calData['lvDiffSlope'] ) + self.calData['lvDiffOffset'] + self.calData['vRefAtCAl']
                else:
                    return (bits * 0.000074463)
            else:
                if hasCal:
                    return ( bits * self.calData['lvDiffSlope'] ) + self.calData['lvDiffOffset']
                else:
                    return (bits * 0.000074463) - 2.44
        else:
            if isSingleEnded and not isSpecialSetting:
                if hasCal:
                    return ( bits * self.calData['hvAIN%sSlope' % channelNumber] ) + self.calData['hvAIN%sOffset' % channelNumber]
                else:
                    return ( bits * 0.000314 ) + -10.3
            elif isSpecialSetting:
                if hasCal:
                    hvSlope = self.calData['hvAIN%sSlope' % channelNumber]
                    hvOffset = self.calData['hvAIN%sOffset' % channelNumber]
                    
                    diffR = ( bits * self.calData['lvDiffSlope'] ) + self.calData['lvDiffOffset'] + self.calData['vRefAtCAl']
                    reading = diffR * hvSlope / self.calData['lvSESlope'] + hvOffset
                    return reading
                else:
                    return (bits * 0.000074463) * (0.000314 / 0.000037231) + -10.3
            else:
                raise Exception, "Can't do differential on high voltage channels"
    binaryToCalibratedAnalogVoltage.section = 3
    
    def binaryToCalibratedAnalogTemperature(self, bytesTemperature):
        hasCal = self.calData is not None
        
        if hasCal:
            return self.calData['tempSlope'] * float(bytesTemperature)
        else:
            return float(bytesTemperature) * 0.013021
    
    def voltageToDACBits(self, volts, dacNumber = 0, is16Bits = False):
        """
        Name: U3.voltageToDACBits(volts, dacNumber = 0, is16Bits = False)
        
        Args: volts, the voltage you would like to set the DAC to.
              dacNumber, 0 or 1, helps apply the correct calibration
              is16Bits, True if you are going to use the 16-bit DAC command
        
        Desc: Takes a voltage, and turns it into the bits needed for the DAC 
              Feedback commands.
        """
        if self.calData is not None:
            bits = ( volts * self.calData['dac%sSlope' % dacNumber] ) + self.calData['dac%sOffset' % dacNumber]
        else:
            bits = volts * 51.717
        
        if is16Bits:
            bits *= 256
        
        return int(bits)
    voltageToDACBits.section = 3
    
    def getCalibrationData(self):
        """
        Name: U3.getCalibrationData()
        
        Args: None
        
        Desc: Reads in the U3's calibrations, so they can be applied to
              readings. Section 2.6.2 of the User's Guide is helpful. Sets up
              an internal calData dict for any future calls that need 
              calibration.
        """
        self.calData = dict()
        
        calData = self.readCal(0)
        
        self.calData['lvSESlope'] = toDouble(calData[0:8])
        self.calData['lvSEOffset'] = toDouble(calData[8:16])
        self.calData['lvDiffSlope'] = toDouble(calData[16:24])
        self.calData['lvDiffOffset'] = toDouble(calData[24:32])
        
        calData = self.readCal(1)
        
        self.calData['dac0Slope'] = toDouble(calData[0:8])
        self.calData['dac0Offset'] = toDouble(calData[8:16])
        self.calData['dac1Slope'] = toDouble(calData[16:24])
        self.calData['dac1Offset'] = toDouble(calData[24:32])
        
        calData = self.readCal(2)
        
        self.calData['tempSlope'] = toDouble(calData[0:8])
        self.calData['vRefAtCAl'] = toDouble(calData[8:16])
        self.calData['vRef1.5AtCal'] = toDouble(calData[16:24])
        self.calData['vRegAtCal'] = toDouble(calData[24:32])
        
        try:
            #these blocks do not exist on hardware revisions < 1.30
            calData = self.readCal(3)
        
            self.calData['hvAIN0Slope'] = toDouble(calData[0:8])
            self.calData['hvAIN1Slope'] = toDouble(calData[8:16])
            self.calData['hvAIN2Slope'] = toDouble(calData[16:24])
            self.calData['hvAIN3Slope'] = toDouble(calData[24:32])
            
            calData = self.readCal(4)
            
            self.calData['hvAIN0Offset'] = toDouble(calData[0:8])
            self.calData['hvAIN1Offset'] = toDouble(calData[8:16])
            self.calData['hvAIN2Offset'] = toDouble(calData[16:24])
            self.calData['hvAIN3Offset'] = toDouble(calData[24:32])
        except LowlevelErrorException, ex:
            if ex.errorCode != 26:
                #not an invalid block error, so do not disregard
                raise ex

        return self.calData
    getCalibrationData.section = 3
    
    def readDefaultsConfig(self):
        """
        Name: U3.readDefaultsConfig( ) 
        Args: None
        Desc: Reads the power-up defaults stored in flash.
        """
        results = dict()
        defaults = self.readDefaults(0)
        
        results['FIODirection'] = defaults[4]
        results['FIOState'] = defaults[5]
        results['FIOAnalog'] = defaults[6]
        
        results['EIODirection'] = defaults[8]
        results['EIOState'] = defaults[9]
        results['EIOAnalog'] = defaults[10]
        
        results['CIODirection'] = defaults[12]
        results['CIOState'] = defaults[13]
        
        results['NumOfTimersEnable'] = defaults[17]
        results['CounterMask'] = defaults[18]
        results['PinOffset'] = defaults[19]
        results['Options'] = defaults[20]
        
        defaults = self.readDefaults(1)
        results['ClockSource'] = defaults[0]
        results['Divisor'] = defaults[1]
        
        results['TMR0Mode'] = defaults[16]
        results['TMR0ValueL'] = defaults[17]
        results['TMR0ValueH'] = defaults[18]
        
        results['TMR1Mode'] = defaults[20]
        results['TMR1ValueL'] = defaults[21]
        results['TMR1ValueH'] = defaults[22]
        
        defaults = self.readDefaults(2)
        
        results['DAC0'] = struct.unpack( ">H", struct.pack("BB", *defaults[16:18]) )[0]
        
        results['DAC1'] = struct.unpack( ">H", struct.pack("BB", *defaults[20:22]) )[0]
        
        defaults = self.readDefaults(3)
        
        for i in range(16):
            results["AIN%sNegChannel" % i] = defaults[i]
        
        return results 
    readDefaultsConfig.section = 3
    
    def exportConfig(self):
        """
        Name: U3.exportConfig( ) 
        Args: None
        Desc: Takes the current configuration and puts it into a ConfigParser
              object. Useful for saving the setup of your U3.
        """
        # Make a new configuration file
        parser = ConfigParser.SafeConfigParser()
        
        # Change optionxform so that options preserve their case.
        parser.optionxform = str
        
        # Local Id and name
        self.configU3()
        
        section = "Identifiers"
        parser.add_section(section)
        parser.set(section, "Local ID", str(self.localId))
        parser.set(section, "Name", str(self.getName()))
        parser.set(section, "Device Type", str(self.devType))
        
        # FIO Direction / State
        section = "FIOs"
        parser.add_section(section)
        
        dirs, states = self.getFeedback( PortDirRead(), PortStateRead() )
        
        parser.set(section, "FIOs Analog", str( self.readRegister(50590) ))
        parser.set(section, "EIOs Analog", str( self.readRegister(50591) ))
        
        for key, value in dirs.items():
            parser.set(section, "%s Directions" % key, str(value))
            
        for key, value in states.items():
            parser.set(section, "%s States" % key, str(value))
            
        # DACs
        section = "DACs"
        parser.add_section(section)
        
        dac0 = self.readRegister(5000)
        dac0 = max(dac0, 0)
        dac0 = min(dac0, 5)
        parser.set(section, "DAC0", "%0.2f" % dac0)
        
        dac1 = self.readRegister(5002)
        dac1 = max(dac1, 0)
        dac1 = min(dac1, 5)
        parser.set(section, "DAC1", "%0.2f" % dac1)
        
        # Timer Clock Configuration
        section = "Timer Clock Speed Configuration"
        parser.add_section(section)
        
        timerclockconfig = self.configTimerClock()
        for key, value in timerclockconfig.items():
            parser.set(section, key, str(value))
        
        # Timers / Counters
        section = "Timers And Counters"
        parser.add_section(section)
        
        timerCounterConfig = self.configIO()
        
        nte = timerCounterConfig['NumberOfTimersEnabled']
        ec0 = timerCounterConfig['EnableCounter0']
        ec1 = timerCounterConfig['EnableCounter1']
        cpo = timerCounterConfig['TimerCounterPinOffset']
        
        parser.set(section, "NumberTimersEnabled", str(nte) )
        parser.set(section, "Counter0Enabled", str(ec0) )
        parser.set(section, "Counter1Enabled", str(ec1) )
        parser.set(section, "TimerCounterPinOffset", str(cpo) )
        
        for i in range(nte):
            mode, value = self.readRegister(7100 + (2*i), numReg = 2, format = ">HH")
            parser.set(section, "Timer%i Mode" % i, str(mode))
            parser.set(section, "Timer%i Value" % i, str(value))
        
        
        return parser
    exportConfig.section = 3

    def loadConfig(self, configParserObj):
        """
        Name: U3.loadConfig( configParserObj ) 
        Args: configParserObj, A Config Parser object to load in
        Desc: Takes a configuration and updates the U3 to match it.
        """
        parser = configParserObj
        
        # Set Identifiers:
        section = "Identifiers"
        if parser.has_section(section):
            if parser.has_option(section, "device type"):
                if parser.getint(section, "device type") != self.devType:
                    raise Exception("Not a U3 Config file.")
            
            if parser.has_option(section, "local id"):
                self.configU3( LocalID = parser.getint(section, "local id"))
                
            if parser.has_option(section, "name"):
                self.setName( parser.get(section, "name") )
            
        # Set FIOs:
        section = "FIOs"
        if parser.has_section(section):
            fioanalog = 0
            eioanalog = 0
        
            fiodirs = 0
            eiodirs = 0
            ciodirs = 0
            
            fiostates = 0
            eiostates = 0
            ciostates = 0
            
            if parser.has_option(section, "fios analog"):
                fioanalog = parser.getint(section, "fios analog")
            if parser.has_option(section, "eios analog"):
                eioanalog = parser.getint(section, "eios analog")
            
            if parser.has_option(section, "fios directions"):
                fiodirs = parser.getint(section, "fios directions")
            if parser.has_option(section, "eios directions"):
                eiodirs = parser.getint(section, "eios directions")
            if parser.has_option(section, "cios directions"):
                ciodirs = parser.getint(section, "cios directions")
            
            if parser.has_option(section, "fios states"):
                fiostates = parser.getint(section, "fios states")
            if parser.has_option(section, "eios states"):
                eiostates = parser.getint(section, "eios states")
            if parser.has_option(section, "cios states"):
                ciostates = parser.getint(section, "cios states")
            
            self.configIO(FIOAnalog = fioanalog, EIOAnalog = eioanalog)
            
            self.getFeedback( PortStateWrite([fiostates, eiostates, ciostates]), PortDirWrite([fiodirs, eiodirs, ciodirs]) )
                
        # Set DACs:
        section = "DACs"
        if parser.has_section(section):
            if parser.has_option(section, "dac0"):
                self.writeRegister(5000, parser.getfloat(section, "dac0"))
            
            if parser.has_option(section, "dac1"):
                self.writeRegister(5002, parser.getfloat(section, "dac1"))
                
        # Set Timer Clock Configuration
        section = "Timer Clock Speed Configuration"
        if parser.has_section(section):
            if parser.has_option(section, "timerclockbase") and parser.has_option(section, "timerclockdivisor"):
                self.configTimerClock(TimerClockBase = parser.getint(section, "timerclockbase"), TimerClockDivisor = parser.getint(section, "timerclockdivisor"))
        
        # Set Timers / Counters
        section = "Timers And Counters"
        if parser.has_section(section):
            nte = None
            c0e = None
            c1e = None
            cpo = None
            
            if parser.has_option(section, "NumberTimersEnabled"):
                nte = parser.getint(section, "NumberTimersEnabled")
            
            if parser.has_option(section, "TimerCounterPinOffset"):
                cpo = parser.getint(section, "TimerCounterPinOffset")
            
            if parser.has_option(section, "Counter0Enabled"):
                c0e = parser.getboolean(section, "Counter0Enabled")
            
            if parser.has_option(section, "Counter1Enabled"):
                c1e = parser.getboolean(section, "Counter1Enabled")
                
            self.configIO(NumberOfTimersEnabled = nte, EnableCounter1 = c1e, EnableCounter0 = c0e, TimerCounterPinOffset = cpo)
            
            
            mode = None
            value = None
            
            if parser.has_option(section, "timer0 mode"):
                mode = parser.getint(section, "timer0 mode")
                
                if parser.has_option(section, "timer0 value"):
                    value = parser.getint(section, "timer0 value")
                
                self.getFeedback( Timer0Config(mode, value) )
            
            if parser.has_option(section, "timer1 mode"):
                mode = parser.getint(section, "timer1 mode")
                
                if parser.has_option(section, "timer1 value"):
                    value = parser.getint(section, "timer1 value")
                
                self.getFeedback( Timer1Config(mode, value) )
    loadConfig.section = 3      

class FeedbackCommand(object):
    """
    The FeedbackCommand class is the base for all the Feedback commands.
    """
    readLen = 0
    def handle(self, input):
        return None

class AIN(FeedbackCommand):
    '''
    Analog Input Feedback command

    specify the positive and negative channels to use 
    (0-16, 30 and 31 are possible)
    also specify whether to turn on longSettle or quick Sample

    returns 16-bit signed int sample

    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.AIN(PositiveChannel = 0, NegativeChannel=31, LongSettling=False, QuickSample=False))
    Sent:  [0x1b, 0xf8, 0x2, 0x0, 0x20, 0x0, 0x0, 0x1, 0x0, 0x1f]
    Response:  [0xab, 0xf8, 0x3, 0x0, 0xaf, 0x0, 0x0, 0x0, 0x0, 0x20, 0x8f, 0x0]
    [36640]
    '''
    def __init__(self, PositiveChannel, NegativeChannel=31, 
            LongSettling=False, QuickSample=False):
        self.positiveChannel = PositiveChannel
        self.negativeChannel = NegativeChannel
        self.longSettling = LongSettling
        self.quickSample = QuickSample
        
        validChannels = range(16) + [30, 31]
        if PositiveChannel not in validChannels:
            raise Exception("Invalid Positive Channel specified")
        if NegativeChannel not in validChannels:
            raise Exception("Invalid Negative Channel specified")
        b = PositiveChannel 
        b |= (int(bool(LongSettling)) << 6)
        b |= (int(bool(QuickSample)) << 7)
        self.cmdBytes = [ 0x01, b, NegativeChannel ]

    readLen =  2
    
    def __repr__(self):
        return "<u3.AIN( PositiveChannel = %s, NegativeChannel = %s, LongSettling = %s, QuickSample = %s )>" % ( self.positiveChannel, self.negativeChannel, self.longSettling, self.quickSample )

    def handle(self, input):
        result = (input[1] << 8) + input[0]
        return result

class WaitShort(FeedbackCommand):
    '''
    WaitShort Feedback command

    specify the number of 128us time increments to wait

    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.WaitShort(Time = 9))
    Sent:  [0x9, 0xf8, 0x2, 0x0, 0xe, 0x0, 0x0, 0x5, 0x9, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    '''
    def __init__(self, Time):
        self.time = Time % 256
        self.cmdBytes = [ 5, Time % 256 ]

    def __repr__(self):
        return "<u3.WaitShort( Time = %s )>" % self.time

class WaitLong(FeedbackCommand):
    '''
    WaitLong Feedback command
    
    specify the number of 32ms time increments to wait
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.WaitLong(Time = 70))
    Sent:  [0x47, 0xf8, 0x2, 0x0, 0x4c, 0x0, 0x0, 0x6, 0x46, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    '''
    def __init__(self, Time):
        self.time = Time % 256
        self.cmdBytes = [ 6, Time % 256 ]
        
    def __repr__(self):
        return "<u3.WaitLong( Time = %s )>" % self.time

class LED(FeedbackCommand):
    '''
    LED Toggle

    specify whether the LED should be on or off by truth value
    
    1 or True = On, 0 or False = Off

    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.LED(State = False))
    Sent:  [0x4, 0xf8, 0x2, 0x0, 0x9, 0x0, 0x0, 0x9, 0x0, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    >>> d.getFeedback(u3.LED(State = True))
    Sent:  [0x5, 0xf8, 0x2, 0x0, 0xa, 0x0, 0x0, 0x9, 0x1, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    '''
    def __init__(self, State):
        self.state = State
        self.cmdBytes = [ 9, int(bool(State)) ]
        
    def __repr__(self):
        return "<u3.LED( State = %s )>" % self.state

class BitStateRead(FeedbackCommand):
    '''
    BitStateRead Feedback command

    read the state of a single bit of digital I/O.  Only digital
    lines return valid readings.

    IONumber: 0-7=FIO, 8-15=EIO, 16-19=CIO
    return 0 or 1
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.BitStateRead(IONumber = 5))
    Sent:  [0xa, 0xf8, 0x2, 0x0, 0xf, 0x0, 0x0, 0xa, 0x5, 0x0]
    Response:  [0xfb, 0xf8, 0x2, 0x0, 0x1, 0x0, 0x0, 0x0, 0x0, 0x1]
    [1]
    '''
    def __init__(self, IONumber):
        self.ioNumber = IONumber
        self.cmdBytes = [ 10, IONumber % 20 ]

    readLen = 1

    def __repr__(self):
        return "<u3.BitStateRead( IONumber = %s )>" % self.ioNumber

    def handle(self, input):
        return int(bool(input[0]))

class BitStateWrite(FeedbackCommand):
    '''
    BitStateWrite Feedback command

    write a single bit of digital I/O.  The direction of the 
    specified line is forced to output.

    IONumber: 0-7=FIO, 8-15=EIO, 16-19=CIO
    State: 0 or 1

    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.BitStateWrite(IONumber = 5, State = 0))
    Sent:  [0xb, 0xf8, 0x2, 0x0, 0x10, 0x0, 0x0, 0xb, 0x5, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    '''
    def __init__(self, IONumber, State):
        self.ioNumber = IONumber
        self.state = State
        self.cmdBytes = [ 11, (IONumber % 20) + (int(bool(State)) << 7) ]
        
    def __repr__(self):
        return "<u3.BitStateWrite( IONumber = %s, State = %s )>" % (self.ioNumber, self.state)

class BitDirRead(FeedbackCommand):
    '''
    Read the digital direction of one I/O

    IONumber: 0-7=FIO, 8-15=EIO, 16-19=CIO
    returns 1 = Output, 0 = Input

    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.BitDirRead(IONumber = 5))
    Sent:  [0xc, 0xf8, 0x2, 0x0, 0x11, 0x0, 0x0, 0xc, 0x5, 0x0]
    Response:  [0xfb, 0xf8, 0x2, 0x0, 0x1, 0x0, 0x0, 0x0, 0x0, 0x1]
    [1]
    '''
    def __init__(self, IONumber):
        self.ioNumber = IONumber
        self.cmdBytes = [ 12, IONumber % 20 ]

    readLen = 1

    def __repr__(self):
        return "<u3.BitDirRead( IONumber = %s )>" % self.ioNumber

    def handle(self, input):
        return int(bool(input[0]))

class BitDirWrite(FeedbackCommand):
    '''
    BitDirWrite Feedback command

    Set the digital direction of one I/O

    IONumber: 0-7=FIO, 8-15=EIO, 16-19=CIO
    Direction: 1 = Output, 0 = Input
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.BitDirWrite(IONumber = 5, Direction = 0))
    Sent:  [0xd, 0xf8, 0x2, 0x0, 0x12, 0x0, 0x0, 0xd, 0x5, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    '''
    def __init__(self, IONumber, Direction):
        self.ioNumber = IONumber
        self.direction = Direction
        self.cmdBytes = [ 13, (IONumber % 20) + (int(bool(Direction)) << 7) ]
        
    def __repr__(self):
        return "<u3.BitDirWrite( IONumber = %s, Direction = %s )>" % (self.ioNumber, self.direction)
    
class PortStateRead(FeedbackCommand):
    """
    PortStateRead Feedback command
    Reads the state of all digital I/O.

    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.PortStateRead())
    Sent:  [0x14, 0xf8, 0x1, 0x0, 0x1a, 0x0, 0x0, 0x1a]
    Response:  [0xeb, 0xf8, 0x3, 0x0, 0xee, 0x1, 0x0, 0x0, 0x0, 0xe0, 0xff, 0xf]
    [{'CIO': 15, 'FIO': 224, 'EIO': 255}]
    """
    def __init__(self):
        self.cmdBytes = [ 26 ]
        
    readLen = 3
    
    def handle(self, input):
        return {'FIO' : input[0], 'EIO' : input[1], 'CIO' : input[2] }
    
    def __repr__(self):
        return "<u3.PortStateRead()>"

class PortStateWrite(FeedbackCommand):
    """
    PortStateWrite Feedback command
    
    State: A list of 3 bytes representing FIO, EIO, CIO
    WriteMask: A list of 3 bytes, representing which to update.
               The Default is all ones.

    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.PortStateWrite(State = [0xab, 0xcd, 0xef], WriteMask = [0xff, 0xff, 0xff]))
    Sent:  [0x81, 0xf8, 0x4, 0x0, 0x7f, 0x5, 0x0, 0x1b, 0xff, 0xff, 0xff, 0xab, 0xcd, 0xef]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    """
    def __init__(self, State, WriteMask = [0xff, 0xff, 0xff]):
        self.state = State
        self.writeMask = WriteMask 
        self.cmdBytes = [ 27 ] + WriteMask + State
        
    def __repr__(self):
        return "<u3.PortStateWrite( State = %s, WriteMask = %s )>" % (self.state, self.writeMask)
        
class PortDirRead(FeedbackCommand):
    """
    PortDirRead Feedback command
    Reads the direction of all digital I/O.
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.PortDirRead())
    Sent:  [0x16, 0xf8, 0x1, 0x0, 0x1c, 0x0, 0x0, 0x1c]
    Response:  [0xfb, 0xf8, 0x3, 0x0, 0xfe, 0x1, 0x0, 0x0, 0x0, 0xf0, 0xff, 0xf]
    [{'CIO': 15, 'FIO': 240, 'EIO': 255}]
    """
    def __init__(self):
        self.cmdBytes = [ 28 ]
        
    readLen = 3
    
    def __repr__(self):
        return "<u3.PortDirRead()>"
    
    def handle(self, input):
        return {'FIO' : input[0], 'EIO' : input[1], 'CIO' : input[2] }

class PortDirWrite(FeedbackCommand):
    """
    PortDirWrite Feedback command
    
    Direction: A list of 3 bytes representing FIO, EIO, CIO
    WriteMask: A list of 3 bytes, representing which to update. Default is all ones.


    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.PortDirWrite(Direction = [0xaa, 0xcc, 0xff], WriteMask = [0xff, 0xff, 0xff]))
    Sent:  [0x91, 0xf8, 0x4, 0x0, 0x8f, 0x5, 0x0, 0x1d, 0xff, 0xff, 0xff, 0xaa, 0xcc, 0xff]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    """
    def __init__(self, Direction, WriteMask = [ 0xff, 0xff, 0xff]):
        self.direction = Direction
        self.writeMask = WriteMask
        self.cmdBytes = [ 29 ] + WriteMask + Direction

    def __repr__(self):
        return "<u3.PortDirWrite( Direction = %s, WriteMask = %s )>" % (self.direction, self.writeMask)

class DAC8(FeedbackCommand):
    '''
    8-bit DAC Feedback command
    
    Controls a single analog output

    Dac: 0 or 1
    Value: 0-255
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.DAC8(Dac = 0, Value = 0x55))
    Sent:  [0x72, 0xf8, 0x2, 0x0, 0x77, 0x0, 0x0, 0x22, 0x55, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    '''
    def __init__(self, Dac, Value):
        self.dac = Dac
        self.value = Value % 256 
        self.cmdBytes = [ 34 + (Dac % 2), Value % 256 ]
    
    def __repr__(self):
        return "<u3.DAC8( Dac = %s, Value = %s )>" % (self.dac, self.value)
        
class DAC0_8(DAC8):
    """
    8-bit DAC Feedback command for DAC0
    
    Controls DAC0 in 8-bit mode.

    Value: 0-255
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.DAC0_8(Value = 0x33))
    Sent:  [0x50, 0xf8, 0x2, 0x0, 0x55, 0x0, 0x0, 0x22, 0x33, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    """
    def __init__(self, Value):
        DAC8.__init__(self, 0, Value)
        
    def __repr__(self):
        return "<u3.DAC0_8( Value = %s )>" % self.value

class DAC1_8(DAC8):
    """
    8-bit DAC Feedback command for DAC1
    
    Controls DAC1 in 8-bit mode.

    Value: 0-255
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.DAC1_8(Value = 0x22))
    Sent:  [0x40, 0xf8, 0x2, 0x0, 0x45, 0x0, 0x0, 0x23, 0x22, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    """
    def __init__(self, Value):
        DAC8.__init__(self, 1, Value)
        
    def __repr__(self):
        return "<u3.DAC1_8( Value = %s )>" % self.value

class DAC16(FeedbackCommand):
    '''
    16-bit DAC Feedback command

    Controls a single analog output

    Dac: 0 or 1
    Value: 0-65535
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.DAC16(Dac = 0, Value = 0x5566))
    Sent:  [0xdc, 0xf8, 0x2, 0x0, 0xe1, 0x0, 0x0, 0x26, 0x66, 0x55]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    '''
    def __init__(self, Dac, Value):
        self.dac = Dac
        self.value = Value
        self.cmdBytes = [ 38 + (Dac % 2), Value % 256, Value >> 8 ]
        
    def __repr__(self):
        return "<u3.DAC16( Dac = %s, Value = %s )>" % (self.dac, self.value)

class DAC0_16(DAC16):
    """
    16-bit DAC Feedback command for DAC0
    
    Controls DAC0 in 16-bit mode.

    Value: 0-65535
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.DAC0_16(Value = 0x1122))
    Sent:  [0x54, 0xf8, 0x2, 0x0, 0x59, 0x0, 0x0, 0x26, 0x22, 0x11]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    """
    def __init__(self, Value):
        DAC16.__init__(self, 0, Value)
        
    def __repr__(self):
        return "<u3.DAC0_16( Value = %s )>" % self.value

class DAC1_16(DAC16):
    """
    16-bit DAC Feedback command for DAC1
    
    Controls DAC1 in 16-bit mode.

    Value: 0-65535
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.getFeedback(u3.DAC1_16(Value = 0x2233))
    Sent:  [0x77, 0xf8, 0x2, 0x0, 0x7c, 0x0, 0x0, 0x27, 0x33, 0x22]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    """
    def __init__(self, Value):
        DAC16.__init__(self, 1, Value)
    
    def __repr__(self):
        return "<u3.DAC1_16( Value = %s )>" % self.value

class Timer(FeedbackCommand):
    """
    For reading the value of the Timer. It provides the ability to update/reset
    a given timer, and read the timer value.
    (Section 5.2.5.14 of the User's Guide)
    
    timer: Either 0 or 1 for timer 0 or timer 1
     
    UpdateReset: Set True if you want to update the value
    
    Value: Only updated if the UpdateReset bit is 1.  The meaning of this
           parameter varies with the timer mode.
           
    Mode: Set to the timer mode to handle any special processing. See classes
          QuadratureInputTimer and TimerStopInput1.

    Returns an unsigned integer of the timer value, unless Mode has been
    specified and there are special return values. See Section 2.9.1 for
    expected return values. 

    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.configIO(NumberOfTimersEnabled = 1)
    Sent:  [0x49, 0xf8, 0x3, 0xb, 0x42, 0x0, 0x1, 0x0, 0x41, 0x0, 0x0, 0x0]
    Response:  [0x57, 0xf8, 0x3, 0xb, 0x50, 0x0, 0x0, 0x0, 0x41, 0x0, 0xf, 0x0]
    {'NumberOfTimersEnabled': 1, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 65, 'EnableCounter1': False, 'EnableCounter0': False}
    >>> d.getFeedback(u3.Timer(timer = 0, UpdateReset = False, Value = 0, Mode = None))
    Sent:  [0x26, 0xf8, 0x3, 0x0, 0x2a, 0x0, 0x0, 0x2a, 0x0, 0x0, 0x0, 0x0]
    Response:  [0xfc, 0xf8, 0x4, 0x0, 0xfe, 0x1, 0x0, 0x0, 0x0, 0x63, 0xdd, 0x4c, 0x72, 0x0]
    [1917640035]
    """
    def __init__(self, timer, UpdateReset = False, Value=0, Mode = None):
        self.timer = timer
        self.updateReset = UpdateReset
        self.value = Value
        self.mode = Mode
        if timer != 0 and timer != 1:
            raise LabJackException("Timer should be either 0 or 1.")
        if UpdateReset and Value == None:
            raise LabJackException("UpdateReset set but no value.")
            
        
        self.cmdBytes = [ (42 + (2*timer)), UpdateReset, Value % 256, Value >> 8 ]
    
    readLen = 4
    
    def __repr__(self):
        return "<u3.Timer( timer = %s, UpdateReset = %s, Value = %s, Mode = %s )>" % (self.timer, self.updateReset, self.value, self.mode)
    
    def handle(self, input):
        inStr = struct.pack('B' * len(input), *input)
        if self.mode == 8:
            return struct.unpack('<i', inStr )[0]
        elif self.mode == 9:
            maxCount, current = struct.unpack('<HH', inStr )
            return current, maxCount
        else:
            return struct.unpack('<I', inStr )[0]

class Timer0(Timer):
    """
    For reading the value of the Timer0. It provides the ability to
    update/reset Timer0, and read the timer value.
    (Section 5.2.5.14 of the User's Guide)
     
    UpdateReset: Set True if you want to update the value
    
    Value: Only updated if the UpdateReset bit is 1.  The meaning of this
           parameter varies with the timer mode.
           
    Mode: Set to the timer mode to handle any special processing. See classes
          QuadratureInputTimer and TimerStopInput1.

    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.configIO(NumberOfTimersEnabled = 1)
    Sent:  [0x49, 0xf8, 0x3, 0xb, 0x42, 0x0, 0x1, 0x0, 0x41, 0x0, 0x0, 0x0]
    Response:  [0x57, 0xf8, 0x3, 0xb, 0x50, 0x0, 0x0, 0x0, 0x41, 0x0, 0xf, 0x0]
    {'NumberOfTimersEnabled': 1, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 65, 'EnableCounter1': False, 'EnableCounter0': False}
    >>> d.getFeedback(u3.Timer0(UpdateReset = False, Value = 0, Mode = None))
    Sent:  [0x26, 0xf8, 0x3, 0x0, 0x2a, 0x0, 0x0, 0x2a, 0x0, 0x0, 0x0, 0x0]
    Response:  [0x51, 0xf8, 0x4, 0x0, 0x52, 0x2, 0x0, 0x0, 0x0, 0xf6, 0x90, 0x46, 0x86, 0x0]
    [2252771574]
    """
    def __init__(self, UpdateReset = False, Value = 0, Mode = None):
        Timer.__init__(self, 0, UpdateReset, Value, Mode)
        
    def __repr__(self):
        return "<u3.Timer0( UpdateReset = %s, Value = %s, Mode = %s )>" % (self.updateReset, self.value, self.mode)

class Timer1(Timer):
    """
    For reading the value of the Timer1. It provides the ability to
    update/reset Timer1, and read the timer value.
    (Section 5.2.5.14 of the User's Guide)
     
    UpdateReset: Set True if you want to update the value
    
    Value: Only updated if the UpdateReset bit is 1.  The meaning of this
           parameter varies with the timer mode.

    Mode: Set to the timer mode to handle any special processing. See classes
          QuadratureInputTimer and TimerStopInput1.

    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.configIO(NumberOfTimersEnabled = 2)
    Sent:  [0x4a, 0xf8, 0x3, 0xb, 0x43, 0x0, 0x1, 0x0, 0x42, 0x0, 0x0, 0x0]
    Response:  [0x58, 0xf8, 0x3, 0xb, 0x51, 0x0, 0x0, 0x0, 0x42, 0x0, 0xf, 0x0]
    {'NumberOfTimersEnabled': 2, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 66, 'EnableCounter1': False, 'EnableCounter0': False}
    >>> d.getFeedback(u3.Timer1(UpdateReset = False, Value = 0, Mode = None))
    Sent:  [0x28, 0xf8, 0x3, 0x0, 0x2c, 0x0, 0x0, 0x2c, 0x0, 0x0, 0x0, 0x0]
    Response:  [0x8d, 0xf8, 0x4, 0x0, 0x8e, 0x2, 0x0, 0x0, 0x0, 0xf3, 0x31, 0xd0, 0x9a, 0x0]
    [2597335539]
    """
    def __init__(self, UpdateReset = False, Value = 0, Mode = None):
        Timer.__init__(self, 1, UpdateReset, Value, Mode)
        
    def __repr__(self):
        return "<u3.Timer1( UpdateReset = %s, Value = %s, Mode = %s )>" % (self.updateReset, self.value, self.mode)

class QuadratureInputTimer(Timer):
    """
    For reading Quadrature input timers. They are special because their values
    are signed.
    
    (Section 2.9.1.8 of the User's Guide)
    
    Args:
       UpdateReset: Set True if you want to reset the counter.
       Value: Set to 0, and UpdateReset to True to reset the counter.
    
    Returns a signed integer.
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.configIO(NumberOfTimersEnabled = 2)
    Sent:  [0x4a, 0xf8, 0x3, 0xb, 0x43, 0x0, 0x1, 0x0, 0x42, 0x0, 0x0, 0x0]
    Response:  [0x58, 0xf8, 0x3, 0xb, 0x51, 0x0, 0x0, 0x0, 0x42, 0x0, 0xf, 0x0]
    {'NumberOfTimersEnabled': 2, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 66, 'EnableCounter1': False, 'EnableCounter0': False}
    >>> # Setup the two timers to be quadrature
    >>> d.getFeedback(u3.Timer0Config(8), u3.Timer1Config(8))
    Sent:  [0x66, 0xf8, 0x5, 0x0, 0x68, 0x0, 0x0, 0x2b, 0x8, 0x0, 0x0, 0x2d, 0x8, 0x0, 0x0, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None, None]
    >>> # Read the value
    [0]
    >>> d.getFeedback(u3.QuadratureInputTimer())
    Sent:  [0x26, 0xf8, 0x3, 0x0, 0x2a, 0x0, 0x0, 0x2a, 0x0, 0x0, 0x0, 0x0]
    Response:  [0xf5, 0xf8, 0x4, 0x0, 0xf5, 0x3, 0x0, 0x0, 0x0, 0xf8, 0xff, 0xff, 0xff, 0x0]
    [-8]
    >>> d.getFeedback(u3.QuadratureInputTimer())
    Sent:  [0x26, 0xf8, 0x3, 0x0, 0x2a, 0x0, 0x0, 0x2a, 0x0, 0x0, 0x0, 0x0]
    Response:  [0x9, 0xf8, 0x4, 0x0, 0xc, 0x0, 0x0, 0x0, 0x0, 0xc, 0x0, 0x0, 0x0, 0x0]
    [12]
    """
    def __init__(self, UpdateReset = False, Value = 0):
        Timer.__init__(self, 0, UpdateReset, Value, Mode = 8)
        
    def __repr__(self):
        return "<u3.QuadratureInputTimer( UpdateReset = %s, Value = %s )>" % (self.updateReset, self.value)

class TimerStopInput1(Timer1):
    """
    For reading a stop input timer. They are special because the value returns
    the current edge count and the stop value.
    
    (Section 2.9.1.9 of the User's Guide)
    
    Args:
        UpdateReset: Set True if you want to update the value.
        Value: The stop value. Only updated if the UpdateReset bit is 1.
    
    Returns a tuple where the first value is current edge count, and the second
    value is the stop value.
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.configIO(NumberOfTimersEnabled = 2)
    Sent:  [0x4a, 0xf8, 0x3, 0xb, 0x43, 0x0, 0x1, 0x0, 0x42, 0x0, 0x0, 0x0]
    Response:  [0x58, 0xf8, 0x3, 0xb, 0x51, 0x0, 0x0, 0x0, 0x42, 0x0, 0xf, 0x0]
    {'NumberOfTimersEnabled': 2, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 66, 'EnableCounter1': False, 'EnableCounter0': False}
    >>> # Setup the timer to be Stop Input
    >>> d.getFeedback(u3.Timer1Config(9, Value = 30))
    Sent:  [0x50, 0xf8, 0x3, 0x0, 0x54, 0x0, 0x0, 0x2d, 0x9, 0x1e, 0x0, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    >>> d.getFeedback(u3.TimerStopInput1())
    Sent:  [0x28, 0xf8, 0x3, 0x0, 0x2c, 0x0, 0x0, 0x2c, 0x0, 0x0, 0x0, 0x0]
    Response:  [0x1b, 0xf8, 0x4, 0x0, 0x1e, 0x0, 0x0, 0x0, 0x0, 0x1e, 0x0, 0x0, 0x0, 0x0]
    [(0, 0)]
    """
    def __init__(self, UpdateReset = False, Value = 0):
        Timer.__init__(self, 1, UpdateReset, Value, Mode = 9)

    def __repr__(self):
        return "<u3.TimerStopInput1( UpdateReset = %s, Value = %s )>" % (self.updateReset, self.value)

class TimerConfig(FeedbackCommand):
    """
    This IOType configures a particular timer.
    
    timer = # of the timer to configure
    
    TimerMode = See Section 2.9 for more information about the available modes.
    
    Value = The meaning of this parameter varies with the timer mode.

    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.configIO(NumberOfTimersEnabled = 1)
    Sent:  [0x49, 0xf8, 0x3, 0xb, 0x42, 0x0, 0x1, 0x0, 0x41, 0x0, 0x0, 0x0]
    Response:  [0x57, 0xf8, 0x3, 0xb, 0x50, 0x0, 0x0, 0x0, 0x41, 0x0, 0xf, 0x0]
    {'NumberOfTimersEnabled': 1, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 65, 'EnableCounter1': False, 'EnableCounter0': False}
    >>> d.getFeedback(u3.TimerConfig(timer = 0, TimerMode = 0, Value = 0))
    Sent:  [0x27, 0xf8, 0x3, 0x0, 0x2b, 0x0, 0x0, 0x2b, 0x0, 0x0, 0x0, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    >>> d.getFeedback(u3.TimerConfig(timer = 0, TimerMode = 0, Value = 65535))
    Sent:  [0x27, 0xf8, 0x3, 0x0, 0x29, 0x2, 0x0, 0x2b, 0x0, 0xff, 0xff, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    """
    def __init__(self, timer, TimerMode, Value=0):
        '''Creates command bytes for configureing a Timer'''
        #Conditions come from pages 33-34 of user's guide
        if timer != 0 and timer != 1:
            raise LabJackException("Timer should be either 0 or 1.")
        
        if TimerMode > 14 or TimerMode < 0:
            raise LabJackException("Invalid Timer Mode.")
        
        self.timer = timer
        self.timerMode = TimerMode
        self.value = Value
        
        self.cmdBytes = [43 + (timer * 2), TimerMode, Value % 256, Value >> 8]
        
    def __repr__(self):
        return "<u3.TimerConfig( timer = %s, TimerMode = %s, Value = %s )>" % (self.timer, self.timerMode, self.value)

class Timer0Config(TimerConfig):
    """
    This IOType configures Timer0.
    
    TimerMode = See Section 2.9 for more information about the available modes.
    
    Value = The meaning of this parameter varies with the timer mode.
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.configIO(NumberOfTimersEnabled = 1)
    Sent:  [0x49, 0xf8, 0x3, 0xb, 0x42, 0x0, 0x1, 0x0, 0x41, 0x0, 0x0, 0x0]
    Response:  [0x57, 0xf8, 0x3, 0xb, 0x50, 0x0, 0x0, 0x0, 0x41, 0x0, 0xf, 0x0]
    {'NumberOfTimersEnabled': 1, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 65, 'EnableCounter1': False, 'EnableCounter0': False}
    >>> d.getFeedback(u3.Timer0Config(TimerMode = 1, Value = 0))
    Sent:  [0x28, 0xf8, 0x3, 0x0, 0x2c, 0x0, 0x0, 0x2b, 0x1, 0x0, 0x0, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    >>> d.getFeedback(u3.Timer0Config(TimerMode = 1, Value = 65535))
    Sent:  [0x28, 0xf8, 0x3, 0x0, 0x2a, 0x2, 0x0, 0x2b, 0x1, 0xff, 0xff, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    """
    def __init__(self, TimerMode, Value = 0):
        TimerConfig.__init__(self, 0, TimerMode, Value)
        
    def __repr__(self):
        return "<u3.Timer0Config( TimerMode = %s, Value = %s )>" % (self.timerMode, self.value)

class Timer1Config(TimerConfig):
    """
    This IOType configures Timer1.
    
    TimerMode = See Section 2.9 for more information about the available modes.
    
    Value = The meaning of this parameter varies with the timer mode.

    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.configIO(NumberOfTimersEnabled = 2)
    Sent:  [0x4a, 0xf8, 0x3, 0xb, 0x43, 0x0, 0x1, 0x0, 0x42, 0x0, 0x0, 0x0]
    Response:  [0x58, 0xf8, 0x3, 0xb, 0x51, 0x0, 0x0, 0x0, 0x42, 0x0, 0xf, 0x0]
    {'NumberOfTimersEnabled': 2, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 66, 'EnableCounter1': False, 'EnableCounter0': False}
    >>> d.getFeedback(u3.Timer1Config(TimerMode = 6, Value = 1))
    Sent:  [0x30, 0xf8, 0x3, 0x0, 0x34, 0x0, 0x0, 0x2d, 0x6, 0x1, 0x0, 0x0]
    Response:  [0xfa, 0xf8, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [None]
    """
    def __init__(self, TimerMode, Value = 0):
        TimerConfig.__init__(self, 1, TimerMode, Value)
    
    def __repr__(self):
        return "<u3.Timer1Config( TimerMode = %s, Value = %s )>" % (self.timerMode, self.value)

class Counter(FeedbackCommand):
    '''
    Counter Feedback command

    Reads a hardware counter, optionally resetting it

    counter: 0 or 1
    Reset: True ( or 1 ) = Reset, False ( or 0 ) = Don't Reset

    Returns the current count from the counter if enabled.  If reset,
    this is the value before the reset.
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.configIO(EnableCounter0 = True, FIOAnalog = 15)
    Sent:  [0x5f, 0xf8, 0x3, 0xb, 0x58, 0x0, 0x5, 0x0, 0x44, 0x0, 0xf, 0x0]
    Response:  [0x5a, 0xf8, 0x3, 0xb, 0x53, 0x0, 0x0, 0x0, 0x44, 0x0, 0xf, 0x0]
    {'NumberOfTimersEnabled': 0, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 68, 'EnableCounter1': False, 'EnableCounter0': True}
    >>> d.getFeedback(u3.Counter(counter = 0, Reset = False))
    Sent:  [0x31, 0xf8, 0x2, 0x0, 0x36, 0x0, 0x0, 0x36, 0x0, 0x0]
    Response:  [0xfc, 0xf8, 0x4, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [0]
    >>> # Tap a ground wire to counter 0
    >>> d.getFeedback(u3.Counter(counter = 0, Reset = False))
    Sent:  [0x31, 0xf8, 0x2, 0x0, 0x36, 0x0, 0x0, 0x36, 0x0, 0x0]
    Response:  [0xe9, 0xf8, 0x4, 0x0, 0xec, 0x0, 0x0, 0x0, 0x0, 0xe8, 0x4, 0x0, 0x0, 0x0]
    [1256]
    '''
    def __init__(self, counter, Reset = False):
        self.counter = counter
        self.reset = Reset
        self.cmdBytes = [ 54 + (counter % 2), int(bool(Reset))]

    readLen = 4

    def __repr__(self):
        return "<u3.Counter( counter = %s, Reset = %s )>" % (self.counter, self.reset)

    def handle(self, input):
        inStr = ''.join([chr(x) for x in input])
        return struct.unpack('<I', inStr )[0]
    
class Counter0(Counter):
    '''
    Counter0 Feedback command

    Reads hardware counter0, optionally resetting it

    Reset: True ( or 1 ) = Reset, False ( or 0 ) = Don't Reset

    Returns the current count from the counter if enabled.  If reset,
    this is the value before the reset.
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.configIO(EnableCounter0 = True, FIOAnalog = 15)
    Sent:  [0x5f, 0xf8, 0x3, 0xb, 0x58, 0x0, 0x5, 0x0, 0x44, 0x0, 0xf, 0x0]
    Response:  [0x5a, 0xf8, 0x3, 0xb, 0x53, 0x0, 0x0, 0x0, 0x44, 0x0, 0xf, 0x0]
    {'NumberOfTimersEnabled': 0, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 68, 'EnableCounter1': False, 'EnableCounter0': True}
    >>> d.getFeedback(u3.Counter0( Reset = False ) )
    Sent:  [0x31, 0xf8, 0x2, 0x0, 0x36, 0x0, 0x0, 0x36, 0x0, 0x0]
    Response:  [0xfc, 0xf8, 0x4, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [0]
    >>> # Tap a ground wire to counter 0
    >>> d.getFeedback(u3.Counter0(Reset = False))
    Sent:  [0x31, 0xf8, 0x2, 0x0, 0x36, 0x0, 0x0, 0x36, 0x0, 0x0]
    Response:  [0xe, 0xf8, 0x4, 0x0, 0x11, 0x0, 0x0, 0x0, 0x0, 0x11, 0x0, 0x0, 0x0, 0x0]
    [17]
    >>> # Tap a ground wire to counter 0
    >>> d.getFeedback(u3.Counter0(Reset = False))
    Sent:  [0x31, 0xf8, 0x2, 0x0, 0x36, 0x0, 0x0, 0x36, 0x0, 0x0]
    Response:  [0x19, 0xf8, 0x4, 0x0, 0x1c, 0x0, 0x0, 0x0, 0x0, 0xb, 0x11, 0x0, 0x0, 0x0]
    [4363]

    '''
    def __init__(self, Reset = False):
        Counter.__init__(self, 0, Reset)
        
    def __repr__(self):
        return "<u3.Counter0( Reset = %s )>" % self.reset

class Counter1(Counter):
    '''
    Counter1 Feedback command

    Reads hardware counter1, optionally resetting it

    Reset: True ( or 1 ) = Reset, False ( or 0 ) = Don't Reset

    Returns the current count from the counter if enabled.  If reset,
    this is the value before the reset.
    
    >>> import u3
    >>> d = u3.U3()
    >>> d.debug = True
    >>> d.configIO(EnableCounter1 = True, FIOAnalog = 15)
    Sent:  [0x63, 0xf8, 0x3, 0xb, 0x5c, 0x0, 0x5, 0x0, 0x48, 0x0, 0xf, 0x0]
    Response:  [0x5e, 0xf8, 0x3, 0xb, 0x57, 0x0, 0x0, 0x0, 0x48, 0x0, 0xf, 0x0]
    {'NumberOfTimersEnabled': 0, 'TimerCounterPinOffset': 4, 'DAC1Enable': 0, 'FIOAnalog': 15, 'EIOAnalog': 0, 'TimerCounterConfig': 72, 'EnableCounter1': True, 'EnableCounter0': False}
    >>> d.getFeedback(u3.Counter1(Reset = False))
    Sent:  [0x32, 0xf8, 0x2, 0x0, 0x37, 0x0, 0x0, 0x37, 0x0, 0x0]
    Response:  [0xfc, 0xf8, 0x4, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    [0]
    >>> # Tap a ground wire to counter 1
    >>> d.getFeedback(u3.Counter1(Reset = False))
    Sent:  [0x32, 0xf8, 0x2, 0x0, 0x37, 0x0, 0x0, 0x37, 0x0, 0x0]
    Response:  [0xfd, 0xf8, 0x4, 0x0, 0x1, 0x0, 0x0, 0x0, 0x0, 0x1, 0x0, 0x0, 0x0, 0x0]
    [1]
    >>> # Tap a ground wire to counter 1
    >>> d.getFeedback(u3.Counter1(Reset = False))
    Sent:  [0x32, 0xf8, 0x2, 0x0, 0x37, 0x0, 0x0, 0x37, 0x0, 0x0]
    Response:  [0xb4, 0xf8, 0x4, 0x0, 0xb7, 0x0, 0x0, 0x0, 0x0, 0x6b, 0x2b, 0x21, 0x0, 0x0]
    [2173803]
    '''
    def __init__(self, Reset = False):
        Counter.__init__(self, 1, Reset)
        
    def __repr__(self):
        return "<u3.Counter0( Reset = %s )>" % self.reset
