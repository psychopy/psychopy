"""
Name: u6.py
Desc: Defines the U6 class, which makes working with a U6 much easier. All of
      the low-level functions for the U6 are implemented as functions of the U6
      class. There are also a handful additional functions which improve upon
      the interface provided by the low-level functions.

To learn about the low-level functions, please see Section 5.2 of the U6 User's 
Guide:

http://labjack.com/support/u6/users-guide/5.2
"""
from LabJackPython import *

import struct, ConfigParser

def openAllU6():
    """
    A helpful function which will open all the connected U6s. Returns a 
    dictionary where the keys are the serialNumber, and the value is the device
    object.
    """
    returnDict = dict()
    
    for i in range(deviceCount(6)):
        d = U6(firstFound = False, devNumber = i+1)
        returnDict[str(d.serialNumber)] = d
        
    return returnDict

def dumpPacket(buffer):
    """
    Name: dumpPacket(buffer)
    Args: byte array
    Desc: Returns hex value of all bytes in the buffer
    """
    return repr([ hex(x) for x in buffer ])

def getBit(n, bit):
    """
    Name: getBit(n, bit)
    Args: n, the original integer you want the bit of
          bit, the index of the bit you want
    Desc: Returns the bit at position "bit" of integer "n"
    
    >>> n = 5
    >>> bit = 2
    >>> getBit(n, bit)
    1
    >>> bit = 0
    >>> getBit(n, bit)
    1

    """
    return int(bool((int(n) & (1 << bit)) >> bit))

def toBitList(inbyte):
    """
    Name: toBitList(inbyte)
    Args: a byte
    Desc: Converts a byte into list for access to individual bits
    
    >>> inbyte = 5
    >>> toBitList(inbyte)
    [1, 0, 1, 0, 0, 0, 0, 0]
    
    """
    return [ getBit(inbyte, b) for b in range(8) ]

def dictAsString(d):
    """Helper function that returns a string representation of a dictionary"""
    s = "{"
    for key, val in sorted(d.items()):
        s += "%s: %s, " % (key, val)
    s = s.rstrip(", ")  # Nuke the trailing comma
    s += "}"
    return s

class CalibrationInfo(object):
    """ A class to hold the calibration info for a U6 """
    def __init__(self):
        # A flag to tell difference between nominal and actual values.
        self.nominal = True
    
        # Positive Channel calibration
        self.ain10vSlope = 3.1580578 * (10 ** -4)
        self.ain10vOffset = -10.5869565220
        self.ain1vSlope = 3.1580578 * (10 ** -5)
        self.ain1vOffset = -1.05869565220
        self.ain100mvSlope = 3.1580578 * (10 ** -6)
        self.ain100mvOffset = -0.105869565220
        self.ain10mvSlope = 3.1580578 * (10 ** -7)
        self.ain10mvOffset = -0.0105869565220
        
        self.ainSlope = [self.ain10vSlope, self.ain1vSlope, self.ain100mvSlope, self.ain10mvSlope]
        self.ainOffset = [self.ain10vOffset, self.ain1vOffset, self.ain100mvOffset, self.ain10mvOffset]
        
        # Negative Channel calibration
        self.ain10vNegSlope = -3.15805800 * (10 ** -4)
        self.ain10vCenter = 33523.0
        self.ain1vNegSlope = -3.15805800 * (10 ** -5)
        self.ain1vCenter = 33523.0
        self.ain100mvNegSlope = -3.15805800 * (10 ** -6)
        self.ain100mvCenter = 33523.0
        self.ain10mvNegSlope = -3.15805800 * (10 ** -7)
        self.ain10mvCenter = 33523.0
        
        self.ainNegSlope = [self.ain10vNegSlope, self.ain1vNegSlope, self.ain100mvNegSlope, self.ain10mvNegSlope]
        self.ainCenter = [self.ain10vCenter, self.ain1vCenter, self.ain100mvCenter, self.ain10mvCenter]
        
        # Miscellaneous
        self.dac0Slope = 13200.0
        self.dac0Offset = 0
        self.dac1Slope = 13200.0
        self.dac1Offset = 0
        
        self.dacSlope = [self.dac0Slope, self.dac1Slope]
        self.dacOffset = [self.dac0Offset, self.dac1Offset]

        self.currentOutput0 = 0.0000100000
        self.currentOutput1 = 0.0002000000
        
        self.temperatureSlope = -92.379
        self.temperatureOffset = 465.129
        
        # Hi-Res ADC stuff
        # Positive Channel calibration
        self.proAin10vSlope = 3.1580578 * (10 ** -4)
        self.proAin10vOffset = -10.5869565220
        self.proAin1vSlope = 3.1580578 * (10 ** -5)
        self.proAin1vOffset = -1.05869565220
        self.proAin100mvSlope = 3.1580578 * (10 ** -6)
        self.proAin100mvOffset = -0.105869565220
        self.proAin10mvSlope = 3.1580578 * (10 ** -7)
        self.proAin10mvOffset = -0.0105869565220
        
        self.proAinSlope = [self.proAin10vSlope, self.proAin1vSlope, self.proAin100mvSlope, self.proAin10mvSlope]
        self.proAinOffset = [self.proAin10vOffset, self.proAin1vOffset, self.proAin100mvOffset, self.proAin10mvOffset]
        
        # Negative Channel calibration
        self.proAin10vNegSlope = -3.15805800 * (10 ** -4)
        self.proAin10vCenter = 33523.0
        self.proAin1vNegSlope = -3.15805800 * (10 ** -5)
        self.proAin1vCenter = 33523.0
        self.proAin100mvNegSlope = -3.15805800 * (10 ** -6)
        self.proAin100mvCenter = 33523.0
        self.proAin10mvNegSlope = -3.15805800 * (10 ** -7)
        self.proAin10mvCenter = 33523.0
        
        self.proAinNegSlope = [self.proAin10vNegSlope, self.proAin1vNegSlope, self.proAin100mvNegSlope, self.proAin10mvNegSlope]
        self.proAinCenter = [self.proAin10vCenter, self.proAin1vCenter, self.proAin100mvCenter, self.proAin10mvCenter]


    def __str__(self):
        return str(self.__dict__)

class U6(Device):
    """
    U6 Class for all U6 specific low-level commands.
    
    Example:
    >>> import u6
    >>> d = u6.U6()
    >>> print d.configU6()
    {'SerialNumber': 320032102, ... , 'FirmwareVersion': '1.26'}
    """
    def __init__(self, debug = False, autoOpen = True, **kargs):
        """
        Name: U6.__init__(self, debug = False, autoOpen = True, **kargs)
        Args: debug, Do you want debug information?
              autoOpen, If true, then the constructor will call open for you
              **kargs, The arguments to be passed to open.
        Desc: Your basic constructor.
        """
        
        Device.__init__(self, None, devType = 6)
        
        self.firmwareVersion = 0
        self.bootloaderVersion = 0
        self.hardwareVersion = 0
        self.productId = 0
        self.fioDirection = [None] * 8
        self.fioState = [None] * 8
        self.eioDirection = [None] * 8
        self.eioState = [None] * 8
        self.cioDirection = [None] * 8
        self.cioState = [None] * 8
        self.dac1Enable = 0
        self.dac0 = 0
        self.dac1 = 0
        self.calInfo = CalibrationInfo()
        self.deviceName = 'U6'
        self.debug = debug

        if autoOpen:
            self.open(**kargs)

    def open(self, localId = None, firstFound = True, serial = None, devNumber = None, handleOnly = False, LJSocket = None):
        """
        Name: U6.open(localId = None, firstFound = True, devNumber = None,
                      handleOnly = False, LJSocket = None)
        Args: firstFound, If True, use the first found U6
              serial, open a U6 with the given serial number
              localId, open a U6 with the given local id.
              devNumber, open a U6 with the given devNumber
              handleOnly, if True, LabJackPython will only open a handle
              LJSocket, set to "<ip>:<port>" to connect to LJSocket
        Desc: Opens a U6 for reading and writing.
        
        >>> myU6 = u6.U6(autoOpen = False)
        >>> myU6.open()
        """
        Device.open(self, 6, firstFound = firstFound, serial = serial, localId = localId, devNumber = devNumber, handleOnly = handleOnly, LJSocket = LJSocket )

    def configU6(self, LocalID = None):
        """
        Name: U6.configU6(LocalID = None)
        Args: LocalID, if set, will write the new value to U6
        Desc: Writes the Local ID, and reads some hardware information.
        
        >>> myU6 = u6.U6()
        >>> myU6.configU6()
        {'BootloaderVersion': '6.15',
         'FirmwareVersion': '0.88',
         'HardwareVersion': '2.0',
         'LocalID': 1,
         'ProductID': 6,
         'SerialNumber': 360005087,
         'VersionInfo': 4}
        """
        command = [ 0 ] * 26
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x0A
        command[3] = 0x08
        #command[4]  = Checksum16 (LSB)
        #command[5]  = Checksum16 (MSB)
        
        if LocalID != None:
            command[6] = (1 << 3)
            command[8] = LocalID
            
        #command[7] = Reserved
        
        #command[9-25] = Reserved 
        try:
            result = self._writeRead(command, 38, [0xF8, 0x10, 0x08])
        except LabJackException, e:
            if e.errorCode is 4:
                print "NOTE: ConfigU6 returned an error of 4. This probably means you are using U6 with a *really old* firmware. Please upgrade your U6's firmware as soon as possible."
                result = self._writeRead(command, 38, [0xF8, 0x10, 0x08], checkBytes = False)
            else:
                raise e
        
        self.firmwareVersion = "%s.%02d" % (result[10], result[9])
        self.bootloaderVersion = "%s.%02d" % (result[12], result[11]) 
        self.hardwareVersion = "%s.%02d" % (result[14], result[13])
        self.serialNumber = struct.unpack("<I", struct.pack(">BBBB", *result[15:19]))[0]
        self.productId = struct.unpack("<H", struct.pack(">BB", *result[19:21]))[0]
        self.localId = result[21]
        self.versionInfo = result[37]
        self.deviceName = 'U6'
        if self.versionInfo == 12:
            self.deviceName = 'U6-Pro'
        
        return { 'FirmwareVersion' : self.firmwareVersion, 'BootloaderVersion' : self.bootloaderVersion, 'HardwareVersion' : self.hardwareVersion, 'SerialNumber' : self.serialNumber, 'ProductID' : self.productId, 'LocalID' : self.localId, 'VersionInfo' : self.versionInfo, 'DeviceName' : self.deviceName }
        
    def configIO(self, NumberTimersEnabled = None, EnableCounter1 = None, EnableCounter0 = None, TimerCounterPinOffset = None, EnableUART = None):
        """
        Name: U6.configIO(NumberTimersEnabled = None, EnableCounter1 = None,
                          EnableCounter0 = None, TimerCounterPinOffset = None)
        Args: NumberTimersEnabled, Number of timers to enable
              EnableCounter1, Set to True to enable counter 1, F to disable
              EnableCounter0, Set to True to enable counter 0, F to disable
              TimerCounterPinOffset, where should the timers/counters start
              
              if all args are None, command just reads.
              
        Desc: Writes and reads the current IO configuration.
        
        >>> myU6 = u6.U6()
        >>> myU6.configIO()
        {'Counter0Enabled': False,
         'Counter1Enabled': False,
         'NumberTimersEnabled': 0,
         'TimerCounterPinOffset': 0}
        """
        command = [ 0 ] * 16
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x05
        command[3] = 0x0B
        #command[4]  = Checksum16 (LSB)
        #command[5]  = Checksum16 (MSB)
        
        if NumberTimersEnabled != None:
            command[6] = 1
            command[7] = NumberTimersEnabled
        
        if EnableCounter0 != None:
            command[6] = 1
            
            if EnableCounter0:
                command[8] = 1
        
        if EnableCounter1 != None:
            command[6] = 1
            
            if EnableCounter1:
                command[8] |= (1 << 1)
        
        if TimerCounterPinOffset != None:
            command[6] = 1
            command[9] = TimerCounterPinOffset
            
        if EnableUART is not None:
            command[6] |= 1
            command[6] |= (1 << 5)
        
        result = self._writeRead(command, 16, [0xf8, 0x05, 0x0B])
        
        return { 'NumberTimersEnabled' : result[8], 'Counter0Enabled' : bool(result[9] & 1), 'Counter1Enabled' : bool( (result[9] >> 1) & 1), 'TimerCounterPinOffset' : result[10] }

    def configTimerClock(self, TimerClockBase = None, TimerClockDivisor = None):
        """
        Name: U6.configTimerClock(TimerClockBase = None,
                                  TimerClockDivisor = None)
        Args: TimerClockBase, which timer base to use
              TimerClockDivisor, set the divisor
              
              if all args are None, command just reads.
              Also, if you cannot set the divisor without setting the base.
              
        Desc: Writes and read the timer clock configuration.
        
        >>> myU6 = u6.U6()
        >>> myU6.configTimerClock()
        {'TimerClockDivisor': 256, 'TimerClockBase': 2}
        """
        command = [ 0 ] * 10
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x02
        command[3] = 0x0A
        #command[4]  = Checksum16 (LSB)
        #command[5]  = Checksum16 (MSB)
        #command[6]  = Reserved
        #command[7]  = Reserved
        
        if TimerClockBase != None:
            command[8] = (1 << 7)
            command[8] |= TimerClockBase & 7
        
        if TimerClockDivisor != None:
            command[9] = TimerClockDivisor
            
        result = self._writeRead(command, 10, [0xF8, 0x2, 0x0A])
        
        divisor = result[9]
        if divisor == 0:
            divisor = 256
        return { 'TimerClockBase' : (result[8] & 7), 'TimerClockDivisor' : divisor }

    def _buildBuffer(self, sendBuffer, readLen, commandlist):
        for cmd in commandlist:
            if isinstance(cmd, FeedbackCommand):
                sendBuffer += cmd.cmdBytes
                readLen += cmd.readLen
            elif isinstance(cmd, list):
                sendBuffer, readLen = self._buildBuffer(sendBuffer, readLen, cmd)
        return (sendBuffer, readLen)
                
    def _buildFeedbackResults(self, rcvBuffer, commandlist, results, i):
        for cmd in commandlist:
            if isinstance(cmd, FeedbackCommand):
                results.append(cmd.handle(rcvBuffer[i:i+cmd.readLen]))
                i += cmd.readLen
            elif isinstance(cmd, list):
                self._buildFeedbackResults(rcvBuffer, cmd, results, i)
        return results

    def getFeedback(self, *commandlist):
        """
        Name: U6.getFeedback(commandlist)
        Args: the FeedbackCommands to run
        Desc: Forms the commandlist into a packet, sends it to the U6, and reads
              the response.
        
        >>> myU6 = U6()
        >>> ledCommand = u6.LED(False)
        >>> internalTempCommand = u6.AIN(30, 31, True)
        >>> myU6.getFeedback(ledCommand, internalTempCommand)
        [None, 23200]

        OR if you like the list version better:
        
        >>> myU6 = U6()
        >>> ledCommand = u6.LED(False)
        >>> internalTempCommand = u6.AIN(30, 31, True)
        >>> commandList = [ ledCommand, internalTempCommand ]
        >>> myU6.getFeedback(commandList)
        [None, 23200]
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
            
            raise LowlevelErrorException("\nThis Command\n    %s\nreturned an error:\n    %s" %  ( culprit, lowlevelErrorToString(rcvBuffer[6]) ) )
        
        results = []
        i = 9
        return self._buildFeedbackResults(rcvBuffer, commandlist, results, i)

    def readMem(self, BlockNum, ReadCal=False):
        """
        Name: U6.readMem(BlockNum, ReadCal=False)
        Args: BlockNum, which block to read
              ReadCal, set to True to read the calibration data
        Desc: Reads 1 block (32 bytes) from the non-volatile user or 
              calibration memory. Please read section 5.2.6 of the user's
              guide before you do something you may regret.
        
        >>> myU6 = U6()
        >>> myU6.readMem(0)
        [ < userdata stored in block 0 > ]
        
        NOTE: Do not call this function while streaming.
        """
        command = [ 0 ] * 8
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x01
        command[3] = 0x2A
        if ReadCal:
            command[3] = 0x2D
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = 0x00
        command[7] = BlockNum
        
        result = self._writeRead(command, 40, [ 0xF8, 0x11, command[3] ])
        
        return result[8:]
    
    def readCal(self, BlockNum):
        return self.readMem(BlockNum, ReadCal = True)
        
    def writeMem(self, BlockNum, Data, WriteCal=False):
        """
        Name: U6.writeMem(BlockNum, Data, WriteCal=False)
        Args: BlockNum, which block to write
              Data, a list of bytes to write
              WriteCal, set to True to write calibration.
        Desc: Writes 1 block (32 bytes) from the non-volatile user or 
              calibration memory. Please read section 5.2.7 of the user's
              guide before you do something you may regret.
        
        >>> myU6 = U6()
        >>> myU6.writeMem(0, [ < userdata to be stored in block 0 > ])
        
        NOTE: Do not call this function while streaming.
        """
        if not isinstance(Data, list):
            raise LabJackException("Data must be a list of bytes")
        
        command = [ 0 ] * 40
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x11
        command[3] = 0x28
        if WriteCal:
            command[3] = 0x2B
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = 0x00
        command[7] = BlockNum
        command[8:] = Data
        
        self._writeRead(command, 8, [0xF8, 0x11, command[3]])

    def writeCal(self, BlockNum, Data):
        return self.writeMem(BlockNum, Data, WriteCal = True)
        
    def eraseMem(self, EraseCal=False):
        """
        Name: U6.eraseMem(EraseCal=False)
        Args: EraseCal, set to True to erase the calibration memory.
        Desc: The U6 uses flash memory that must be erased before writing.
              Please read section 5.2.8 of the user's guide before you do
              something you may regret.
        
        >>> myU6 = U6()
        >>> myU6.eraseMem()
        
        NOTE: Do not call this function while streaming.
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
    
    def eraseCal(self):
        return self.eraseMem(EraseCal=True)
    
    def streamConfig(self, NumChannels = 1, ResolutionIndex = 0, SamplesPerPacket = 25, SettlingFactor = 0, InternalStreamClockFrequency = 0, DivideClockBy256 = False, ScanInterval = 1, ChannelNumbers = [0], ChannelOptions = [0], ScanFrequency = None, SampleFrequency = None):
        """
        Name: U6.streamConfig(NumChannels = 1, ResolutionIndex = 0,
                              SamplesPerPacket = 25, SettlingFactor = 0,
                              InternalStreamClockFrequency = 0, DivideClockBy256 = False,
                              ScanInterval = 1, ChannelNumbers = [0],
                              ChannelOptions = [0], ScanFrequency = None,
                              SampleFrequency = None )
        Args: NumChannels, the number of channels to stream
              ResolutionIndex, the resolution index of the samples (0-8)
              SettlingFactor, the settling factor to be used
              ChannelNumbers, a list of channel numbers to stream
              ChannelOptions, a list of channel options bytes.
                              ChannelOptions byte:  bit 7 = Differential,
                                                    bit 4-5 = GainIndex
                                Set bit 7 for differential reading.
                                GainIndex: 0(b00)=x1,  1(b01)=x10, 2(b10)=x100,
                                           3(b11)=x1000
              
              Set Either:
              
              ScanFrequency, the frequency in Hz to scan the channel list (ChannelNumbers).
                             sample rate (Hz) = ScanFrequency * NumChannels
              
              -- OR --
              
              SamplesPerPacket, how many samples make one packet
              InternalStreamClockFrequency, 0 = 4 MHz, 1 = 48 MHz
              DivideClockBy256, True = divide the clock by 256
              ScanInterval, clock/ScanInterval = frequency.
              
              See Section 5.2.12 of the User's Guide for more details.
              
              Deprecated:
              
              SampleFrequency, the frequency in Hz to sample.  Use ScanFrequency
                               since SampleFrequency has always set the scan
                               frequency and the name is confusing.
        
        Desc: Configures streaming on the U6. On a decent machine, you can
              expect to stream a range of 0.238 Hz to 15 Hz. Without the
              conversion, you can get up to 55 Hz.
        """
        if NumChannels != len(ChannelNumbers) or NumChannels != len(ChannelOptions):
            raise LabJackException("NumChannels must match length of ChannelNumbers and ChannelOptions")
        if len(ChannelNumbers) != len(ChannelOptions):
            raise LabJackException("len(ChannelNumbers) doesn't match len(ChannelOptions)")
        
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
        
        command = [ 0 ] * (14 + NumChannels*2)
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = NumChannels+4
        command[3] = 0x11
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = NumChannels
        command[7] = ResolutionIndex
        command[8] = SamplesPerPacket
        #command[9] = Reserved
        command[10] = SettlingFactor
        command[11] = (InternalStreamClockFrequency & 1) << 3
        if DivideClockBy256:
            command[11] |= 1 << 1
        t = struct.pack("<H", ScanInterval)
        command[12] = ord(t[0])
        command[13] = ord(t[1])
        for i in range(NumChannels):
            command[14+(i*2)] = ChannelNumbers[i]
            command[15+(i*2)] = ChannelOptions[i]
        
        
        self._writeRead(command, 8, [0xF8, 0x01, 0x11])
        
        # Set up the variables for future use.
        self.streamSamplesPerPacket = SamplesPerPacket
        self.streamChannelNumbers = ChannelNumbers
        self.streamChannelOptions = ChannelOptions
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
    
    def processStreamData(self, result, numBytes = None):
        """
        Name: U6.processStreamData(result, numPackets = None)
        Args: result, the string returned from streamData()
              numBytes, the number of bytes per packet
        Desc: Breaks stream data into individual channels and applies
              calibrations.
              
        >>> reading = d.streamData(convert = False)
        >>> print proccessStreamData(reading['result'])
        defaultDict(list, {'AIN0' : [3.123, 3.231, 3.232, ...]})
        """
        if numBytes is None:
            numBytes = 14 + (self.streamSamplesPerPacket * 2)
        
        returnDict = collections.defaultdict(list)
        
        j = self.streamPacketOffset
        for packet in self.breakupPackets(result, numBytes):
            for sample in self.samplesFromPacket(packet):
                if j >= len(self.streamChannelNumbers):
                    j = 0
                
                if self.streamChannelNumbers[j] in (193, 194):
                    value = struct.unpack('<BB', sample )
                elif self.streamChannelNumbers[j] >= 200:
                    value = struct.unpack('<H', sample )[0]
                else:
                    if (self.streamChannelOptions[j] >> 7) == 1:
                        # do signed
                        value = struct.unpack('<H', sample )[0]
                    else:
                        # do unsigned
                        value = struct.unpack('<H', sample )[0]
                    
                    gainIndex = (self.streamChannelOptions[j] >> 4) & 0x3
                    value = self.binaryToCalibratedAnalogVoltage(gainIndex, value, is16Bits = True, resolutionIndex = 0)
                
                returnDict["AIN%s" % self.streamChannelNumbers[j]].append(value)
                
                j += 1
            
            self.streamPacketOffset = j

        return returnDict
        
    def watchdog(self, Write = False, ResetOnTimeout = False, SetDIOStateOnTimeout = False, TimeoutPeriod = 60, DIOState = 0, DIONumber = 0):
        """
        Name: U6.watchdog(Write = False, ResetOnTimeout = False,
                          SetDIOStateOnTimeout = False, TimeoutPeriod = 60,
                          DIOState = 0, DIONumber = 0)
        Args: Write, Set to True to write new values to the watchdog.
              ResetOnTimeout, True means reset the device on timeout
              SetDIOStateOnTimeout, True means set the sate of a DIO on timeout
              TimeoutPeriod, Time, in seconds, to wait before timing out.
              DIOState, 1 = High, 0 = Low
              DIONumber, which DIO to set.
        Desc: Controls a firmware based watchdog timer.
        """
        command = [ 0 ] * 16
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x05
        command[3] = 0x09
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        if Write:
            command[6] = 1
        if ResetOnTimeout:
            command[7] = (1 << 5)
        if SetDIOStateOnTimeout:
            command[7] |= (1 << 4)
        
        t = struct.pack("<H", TimeoutPeriod)
        command[8] = ord(t[0])
        command[9] = ord(t[1])
        command[10] = ((DIOState & 1 ) << 7)
        command[10] |= (DIONumber & 0xf)
        
        result = self._writeRead(command, 16, [ 0xF8, 0x05, 0x09])
        
        watchdogStatus = {}
        
        if result[7] == 0:
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

    SPIModes = { 'A' : 0, 'B' : 1, 'C' : 2, 'D' : 3 }
    def spi(self, SPIBytes, AutoCS=True, DisableDirConfig = False, SPIMode = 'A', SPIClockFactor = 0, CSPINNum = 0, CLKPinNum = 1, MISOPinNum = 2, MOSIPinNum = 3):
        """
        Name: U6.spi(SPIBytes, AutoCS=True, DisableDirConfig = False,
                     SPIMode = 'A', SPIClockFactor = 0, CSPINNum = 0, 
                     CLKPinNum = 1, MISOPinNum = 2, MOSIPinNum = 3)
        Args: SPIBytes, A list of bytes to send.
              AutoCS, If True, the CS line is automatically driven low
                      during the SPI communication and brought back high
                      when done.
              DisableDirConfig, If True, function does not set the direction
                                of the line.
              SPIMode, 'A', 'B', 'C',  or 'D'. 
              SPIClockFactor, Sets the frequency of the SPI clock.
              CSPINNum, which pin is CS
              CLKPinNum, which pin is CLK
              MISOPinNum, which pin is MISO
              MOSIPinNum, which pin is MOSI
        Desc: Sends and receives serial data using SPI synchronous
              communication. See Section 5.2.17 of the user's guide.
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
        
        return { 'NumSPIBytesTransferred' : result[7], 'SPIBytes' : result[8:] }
    
    def asynchConfig(self, Update = True, UARTEnable = True, DesiredBaud = None, BaudFactor = 63036):
        """
        Name: U6.asynchConfig(Update = True, UARTEnable = True, 
                              DesiredBaud = None, BaudFactor = 63036)
        Args: Update, If True, new values are written.
              UARTEnable, If True, UART will be enabled.
              DesiredBaud, If set, will apply the formualt to 
                           calculate BaudFactor.
              BaudFactor, = 2^16 - 48000000/(2 * Desired Baud). Ignored
                        if DesiredBaud is set.
        Desc: Configures the U6 UART for asynchronous communication. See
              section 5.2.18 of the User's Guide.
        """
        
        if UARTEnable:
            self.configIO(EnableUART = True)
        
        command = [ 0 ] * 10
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x02
        command[3] = 0x14
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        #commmand[6] = 0x00
        if Update:
            command[7] = (1 << 7)
        if UARTEnable:
            command[7] |= (1 << 6)
        
        if DesiredBaud != None:
            BaudFactor = (2**16) - 48000000/(2 * DesiredBaud)   
        
        t = struct.pack("<H", BaudFactor)
        command[8] = ord(t[0])
        command[9] = ord(t[1])
        
        results = self._writeRead(command, 10, [0xF8, 0x02, 0x14])
            
        if command[8] != results[8] and command[9] != results[9]:
            raise LabJackException("BaudFactor didn't stick.")
        
    def asynchTX(self, AsynchBytes):
        """
        Name: U6.asynchTX(AsynchBytes)
        Args: AsynchBytes, List of bytes to send
        Desc: Sends bytes to the U6 UART which will be sent asynchronously
              on the transmit line. Section 5.2.19 of the User's Guide.
        """
        
        numBytes = len(AsynchBytes)
        
        oddPacket = False
        if numBytes%2 != 0:
            oddPacket = True
            AsynchBytes.append(0)
            numBytes = numBytes + 1
        
        command = [ 0 ] * (8+numBytes)
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 1 + (numBytes/2)
        command[3] = 0x15
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        #commmand[6] = 0x00
        command[7] = numBytes
        if oddPacket:
            command[7] = numBytes-1
        command[8:] = AsynchBytes
        
        result = self._writeRead(command, 10, [ 0xF8, 0x02, 0x15])
        
        return { 'NumAsynchBytesSent' : result[7], 'NumAsynchBytesInRXBuffer' : result[8] }
    
    def asynchRX(self, Flush = False):
        """
        Name: U6.asynchTX(AsynchBytes)
        Args: Flush, If True, empties the entire 256-byte RX buffer.
        Desc: Sends bytes to the U6 UART which will be sent asynchronously
              on the transmit line. Section 5.2.20 of the User's Guide.
        """
        command = [ 0, 0xF8, 0x01, 0x16, 0, 0, 0, int(Flush)]
        
        result = self._writeRead(command, 40, [ 0xF8, 0x11, 0x16 ])
        
        return { 'NumAsynchBytesInRXBuffer' : result[7], 'AsynchBytes' : result[8:] }
    
    def i2c(self, Address, I2CBytes, EnableClockStretching = False, NoStopWhenRestarting = False, ResetAtStart = False, SpeedAdjust = 0, SDAPinNum = 0, SCLPinNum = 1, NumI2CBytesToReceive = 0, AddressByte = None):
        """
        Name: U6.i2c(Address, I2CBytes,
                     EnableClockStretching = False, NoStopWhenRestarting = False,
                     ResetAtStart = False, SpeedAdjust = 0,
                     SDAPinNum = 0, SCLPinNum = 1, 
                     NumI2CBytesToReceive = 0, AddressByte = None)
        Args: Address, the address (Not shifted over)
              I2CBytes, a list of bytes to send
              EnableClockStretching, True enables clock stretching
              NoStopWhenRestarting, True means no stop sent when restarting
              ResetAtStart, if True, an I2C bus reset will be done
                            before communicating.
              SpeedAdjust, Allows the communication frequency to be reduced.
              SDAPinNum, Which pin will be data
              SCLPinNum, Which pin is clock
              NumI2CBytesToReceive, Number of I2C bytes to expect back.
              AddressByte, The address as you would put it in the lowlevel
                           packet. Overrides Address. Optional.
        Desc: Sends and receives serial data using I2C synchronous
              communication. Section 5.2.21 of the User's Guide.
        """
        numBytes = len(I2CBytes)
        
        oddPacket = False
        if numBytes%2 != 0:
            oddPacket = True
            I2CBytes.append(0)
            numBytes = numBytes+1
        
        command = [ 0 ] * (14+numBytes)
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 4 + (numBytes/2)
        command[3] = 0x3B
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        if EnableClockStretching:
            command[6] |= (1 << 3)
        if NoStopWhenRestarting:
            command[6] |= (1 << 2)
        if ResetAtStart:
            command[6] |= (1 << 1)
        
        command[7] = SpeedAdjust
        command[8] = SDAPinNum
        command[9] = SCLPinNum
        
        if AddressByte != None:
            command[10] = AddressByte
        else:
            command[10] = Address << 1
        #command[11] = Reserved
        command[12] = numBytes
        if oddPacket:
            command[12] = numBytes-1
        command[13] = NumI2CBytesToReceive
        command[14:] = I2CBytes
        
        oddResponse = False
        if NumI2CBytesToReceive%2 != 0:
            NumI2CBytesToReceive = NumI2CBytesToReceive+1
            oddResponse = True
        
        result = self._writeRead(command, (12+NumI2CBytesToReceive), [0xF8, (3+(NumI2CBytesToReceive/2)), 0x3B])
        
        if NumI2CBytesToReceive != 0:
            return { 'AckArray' : result[8:12], 'I2CBytes' : result[12:] }
        else:
            return { 'AckArray' : result[8:12] }
            
    def sht1x(self, DataPinNum = 0, ClockPinNum = 1, SHTOptions = 0xc0):
        """
        Name: U6.sht1x(DataPinNum = 0, ClockPinNum = 1, SHTOptions = 0xc0)
        Args: DataPinNum, Which pin is the Data line
              ClockPinNum, Which line is the Clock line
              SHTOptions (and proof people read documentation):
                bit 7 = Read Temperature
                bit 6 = Read Realtive Humidity
                bit 2 = Heater. 1 = on, 0 = off
                bit 1 = Reserved at 0
                bit 0 = Resolution. 1 = 8 bit RH, 12 bit T; 0 = 12 RH, 14 bit T
        Desc: Reads temperature and humidity from a Sensirion SHT1X sensor.
              Section 5.2.22 of the User's Guide.
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
        
        result = self._writeRead(command, 16, [ 0xF8, 0x05, 0x39])
        
        val = (result[11]*256) + result[10]
        temp = -39.60 + 0.01*val
        
        val = (result[14]*256) + result[13]
        humid = -4 + 0.0405*val + -.0000028*(val*val)
        humid = (temp - 25)*(0.01 + 0.00008*val) + humid
        
        return { 'StatusReg' : result[8], 'StatusCRC' : result[9], 'Temperature' : temp, 'TemperatureCRC' : result[12], 'Humidity' : humid, 'HumidityCRC' : result[15] }
        
    # --------------------------- Old U6 code -------------------------------

    def _readCalDataBlock(self, n):
        """
        Internal routine to read the specified calibration block (0-2)
        """
        sendBuffer = [0] * 8
        sendBuffer[1] = 0xF8  # command byte
        sendBuffer[2] = 0x01  #  number of data words
        sendBuffer[3] = 0x2D  #  extended command number
        sendBuffer[6] = 0x00
        sendBuffer[7] = n     # Blocknum = 0
        self.write(sendBuffer)
        buff = self.read(40)
        return buff[8:]

    def getCalibrationData(self):
        """
        Name: U6.getCalibrationData()
        Args: None
        Desc: Gets the slopes and offsets for AIN and DACs,
              as well as other calibration data
        
        >>> myU6 = U6()
        >>> myU6.getCalibrationData()
        >>> myU6.calInfo
        <ainDiffOffset: -2.46886488446,...>
        """
        if self.debug is True:
            print "Calibration data retrieval"
        
        self.calInfo.nominal = False
        
        #reading block 0 from memory
        rcvBuffer = self._readCalDataBlock(0)
        
        # Positive Channel calibration
        self.calInfo.ain10vSlope = toDouble(rcvBuffer[:8])
        self.calInfo.ain10vOffset = toDouble(rcvBuffer[8:16])
        self.calInfo.ain1vSlope = toDouble(rcvBuffer[16:24])
        self.calInfo.ain1vOffset = toDouble(rcvBuffer[24:])
        
        #reading block 1 from memory
        rcvBuffer = self._readCalDataBlock(1)
        
        self.calInfo.ain100mvSlope = toDouble(rcvBuffer[:8])
        self.calInfo.ain100mvOffset = toDouble(rcvBuffer[8:16])
        self.calInfo.ain10mvSlope = toDouble(rcvBuffer[16:24])
        self.calInfo.ain10mvOffset = toDouble(rcvBuffer[24:])
        
        self.calInfo.ainSlope = [self.calInfo.ain10vSlope, self.calInfo.ain1vSlope, self.calInfo.ain100mvSlope, self.calInfo.ain10mvSlope]
        self.calInfo.ainOffset = [self.calInfo.ain10vOffset, self.calInfo.ain1vOffset, self.calInfo.ain100mvOffset, self.calInfo.ain10mvOffset]
        
        #reading block 2 from memory
        rcvBuffer = self._readCalDataBlock(2)
        
        # Negative Channel calibration
        self.calInfo.ain10vNegSlope = toDouble(rcvBuffer[:8])
        self.calInfo.ain10vCenter = toDouble(rcvBuffer[8:16])
        self.calInfo.ain1vNegSlope = toDouble(rcvBuffer[16:24])
        self.calInfo.ain1vCenter = toDouble(rcvBuffer[24:])
        
        #reading block 3 from memory
        rcvBuffer = self._readCalDataBlock(3)
        
        self.calInfo.ain100mvNegSlope = toDouble(rcvBuffer[:8])
        self.calInfo.ain100mvCenter = toDouble(rcvBuffer[8:16])
        self.calInfo.ain10mvNegSlope = toDouble(rcvBuffer[16:24])
        self.calInfo.ain10mvCenter = toDouble(rcvBuffer[24:])
        
        self.calInfo.ainNegSlope = [self.calInfo.ain10vNegSlope, self.calInfo.ain1vNegSlope, self.calInfo.ain100mvNegSlope, self.calInfo.ain10mvNegSlope]
        self.calInfo.ainCenter = [self.calInfo.ain10vCenter, self.calInfo.ain1vCenter, self.calInfo.ain100mvCenter, self.calInfo.ain10mvCenter]
        
        #reading block 4 from memory
        rcvBuffer = self._readCalDataBlock(4)
        
        # Miscellaneous
        self.calInfo.dac0Slope = toDouble(rcvBuffer[:8])
        self.calInfo.dac0Offset = toDouble(rcvBuffer[8:16])
        self.calInfo.dac1Slope = toDouble(rcvBuffer[16:24])
        self.calInfo.dac1Offset = toDouble(rcvBuffer[24:])
        
        self.calInfo.dacSlope = [self.calInfo.dac0Slope, self.calInfo.dac1Slope]
        self.calInfo.dacOffset = [self.calInfo.dac0Offset, self.calInfo.dac1Offset]
        
        #reading block 5 from memory
        rcvBuffer = self._readCalDataBlock(5)
        
        self.calInfo.currentOutput0 = toDouble(rcvBuffer[:8])
        self.calInfo.currentOutput1 = toDouble(rcvBuffer[8:16])
        
        self.calInfo.temperatureSlope = toDouble(rcvBuffer[16:24])
        self.calInfo.temperatureOffset = toDouble(rcvBuffer[24:])
        
        if self.deviceName.endswith("Pro"):
            # Hi-Res ADC stuff
            
            #reading block 6 from memory
            rcvBuffer = self._readCalDataBlock(6)
            
            # Positive Channel calibration
            self.calInfo.proAin10vSlope = toDouble(rcvBuffer[:8])
            self.calInfo.proAin10vOffset = toDouble(rcvBuffer[8:16])
            self.calInfo.proAin1vSlope = toDouble(rcvBuffer[16:24])
            self.calInfo.proAin1vOffset = toDouble(rcvBuffer[24:])
            
            #reading block 7 from memory
            rcvBuffer = self._readCalDataBlock(7)
            
            self.calInfo.proAin100mvSlope = toDouble(rcvBuffer[:8])
            self.calInfo.proAin100mvOffset = toDouble(rcvBuffer[8:16])
            self.calInfo.proAin10mvSlope = toDouble(rcvBuffer[16:24])
            self.calInfo.proAin10mvOffset = toDouble(rcvBuffer[24:])
            
            self.calInfo.proAinSlope = [self.calInfo.proAin10vSlope, self.calInfo.proAin1vSlope, self.calInfo.proAin100mvSlope, self.calInfo.proAin10mvSlope]
            self.calInfo.proAinOffset = [self.calInfo.proAin10vOffset, self.calInfo.proAin1vOffset, self.calInfo.proAin100mvOffset, self.calInfo.proAin10mvOffset]
            
            #reading block 8 from memory
            rcvBuffer = self._readCalDataBlock(8)
            
            # Negative Channel calibration
            self.calInfo.proAin10vNegSlope = toDouble(rcvBuffer[:8])
            self.calInfo.proAin10vCenter = toDouble(rcvBuffer[8:16])
            self.calInfo.proAin1vNegSlope = toDouble(rcvBuffer[16:24])
            self.calInfo.proAin1vCenter = toDouble(rcvBuffer[24:])
            
            #reading block 9 from memory
            rcvBuffer = self._readCalDataBlock(9)
            
            self.calInfo.proAin100mvNegSlope = toDouble(rcvBuffer[:8])
            self.calInfo.proAin100mvCenter = toDouble(rcvBuffer[8:16])
            self.calInfo.proAin10mvNegSlope = toDouble(rcvBuffer[16:24])
            self.calInfo.proAin10mvCenter = toDouble(rcvBuffer[24:])
            
            self.calInfo.proAinNegSlope = [self.calInfo.proAin10vNegSlope, self.calInfo.proAin1vNegSlope, self.calInfo.proAin100mvNegSlope, self.calInfo.proAin10mvNegSlope]
            self.calInfo.proAinCenter = [self.calInfo.proAin10vCenter, self.calInfo.proAin1vCenter, self.calInfo.proAin100mvCenter, self.calInfo.proAin10mvCenter]

    def binaryToCalibratedAnalogVoltage(self, gainIndex, bytesVoltage, is16Bits=False, resolutionIndex=0):
        """
        Name: U6.binaryToCalibratedAnalogVoltage(gainIndex, bytesVoltage, 
                                                 is16Bits = False, resolutionIndex = 0)
        Args: gainIndex, which gain index did you use?
              bytesVoltage, bytes returned from the U6
              is16Bits, set to True if bytesVoltage is 16 bits (not 24)
              resolutionIndex, which resolution index did you use?  Set this for
                               U6-Pro devices to ensure proper hi-res conversion.
        Desc: Converts binary voltage to an analog value.
        """
        if not is16Bits:
            bits = float(bytesVoltage)/256
        else:
            bits = float(bytesVoltage)

        if self.deviceName.endswith("Pro") and (resolutionIndex > 8 or resolutionIndex == 0):
            #Use hi-res calibration constants
            center = self.calInfo.proAinCenter[gainIndex]
            negSlope = self.calInfo.proAinNegSlope[gainIndex]
            posSlope = self.calInfo.proAinSlope[gainIndex]
        else:
            #Use normal calibration constants
            center = self.calInfo.ainCenter[gainIndex]
            negSlope = self.calInfo.ainNegSlope[gainIndex]
            posSlope = self.calInfo.ainSlope[gainIndex]

        if bits < center:
            return (center - bits) * negSlope
        else:
            return (bits - center) * posSlope

    def binaryToCalibratedAnalogTemperature(self, bytesTemperature, is16Bits=False):
        """
        Name: U6.binaryToCalibratedAnalogTemperature(bytesTemperature, is16Bits = False)
        Args: bytesTemperature, bytes returned from the U6
              is16Bits, set to True if bytesTemperature is 16 bits (not 24)
        Desc: Converts binary temperature to Kelvin.
        """
        voltage = self.binaryToCalibratedAnalogVoltage(0, bytesTemperature, is16Bits, 1)
        return self.calInfo.temperatureSlope * float(voltage) + self.calInfo.temperatureOffset

    def voltageToDACBits(self, volts, dacNumber = 0, is16Bits = False):
        """
        Name: U6.voltageToDACBits(volts, dacNumber = 0, is16Bits = False)
        Args: volts, the voltage you would like to set the DAC to.
              dacNumber, 0 or 1, helps apply the correct calibration
              is16Bits, True if you are going to use the 16-bit DAC command
        Desc: Takes a voltage, and turns it into the bits needed for the DAC
              Feedback commands.
        """
        bits = ( volts * self.calInfo.dacSlope[dacNumber] ) + self.calInfo.dacOffset[dacNumber]
        if not is16Bits:
            bits = bits/256
        
        return int(bits)

    def softReset(self):
        """
        Name: U6.softReset()
        Args: none
        Desc: Send a soft reset.
        
        >>> myU6 = U6()
        >>> myU6.softReset()
        """
        command = [ 0x00, 0x99, 0x01, 0x00 ]
        command = setChecksum8(command, 4)
        
        self.write(command, False, False)
        results = self.read(4)
        
        if results[3] != 0:
            raise LowlevelErrorException(results[3], "The softReset command returned an error:\n    %s" % lowlevelErrorToString(results[3]))

    def hardReset(self):
        """
        Name: U6.hardReset()
        Args: none
        Desc: Send a hard reset.
        
        >>> myU6 = U6()
        >>> myU6.hardReset()
        """
        command = [ 0x00, 0x99, 0x02, 0x00 ]
        command = setChecksum8(command, 4)
        
        self.write(command, False, False)
        results = self.read(4)
        
        if results[3] != 0:
            raise LowlevelErrorException(results[3], "The softHard command returned an error:\n    %s" % lowlevelErrorToString(results[3]))
            
        self.close()

    def setLED(self, state):
        """
        Name: U6.setLED(state)
        Args: state: 1 = On, 0 = Off
        Desc: Sets the state of the LED. (5.2.5.4 of user's guide)
        
        >>> d = u6.U6()
        >>> d.setLED(0)
        ... (LED turns off) ...
        """
        self.getFeedback(LED(state))

    def setDOState(self, ioNum, state = 1):
        """
        Name: U6.setDOState(ioNum, state = 1)
        Args: ioNum, which digital I/O to change
                  0 - 7   = FIO0 - FIO7
                  8 - 15  = EIO0 - EIO7
                  16 - 19 = CIO0 - CIO3
                  20 - 22 = MIO0 - MIO2
              state, 1 = High, 0 = Low
        Desc: A convenience function to set the state of a digital I/O. Will
              also set the direction to output.
        
        Example:
        >>> import u6
        >>> d = u6.U6()
        >>> d.setDOState(0, state = 1)
        """
        self.getFeedback(BitDirWrite(ioNum, 1), BitStateWrite(ioNum, state))

    def getDIState(self, ioNum):
        """
        Name: U6.getDIState(ioNum)
        Args: ioNum, which digital I/O to read
                  0 - 7   = FIO0 - FIO7
                  8 - 15  = EIO0 - EIO7
                  16 - 19 = CIO0 - CIO3
                  20 - 22 = MIO0 - MIO2
        Desc: A convenience function to read the state of a digital I/O.  Will
              also set the direction to input.
        
        Example:
        >>> import u6
        >>> d = u6.U6()
        >>> print d.getDIState(0)
        1
        """
        return self.getFeedback(BitDirWrite(ioNum, 0), BitStateRead(ioNum))[1]

    def getDIOState(self, ioNum):
        """
        Name: U6.getDIOState(ioNum)
        Args: ioNum, which digital I/O to read
                  0 - 7   = FIO0 - FIO7
                  8 - 15  = EIO0 - EIO7
                  16 - 19 = CIO0 - CIO3
                  20 - 22 = MIO0 - MIO2
        Desc: A convenience function to read the state of a digital I/O.  Will
              not change the direction.
        
        Example:
        >>> import u6
        >>> d = u6.U6()
        >>> print d.getDIOState(0)
        1
        """
        return self.getFeedback(BitStateRead(ioNum))[0]

    def getTemperature(self):
        """
        Name: U6.getTemperature()
        Args: none
        Desc: Reads the U6's internal temperature sensor in Kelvin. 
              See Section 2.6.4 of the U6 User's Guide.
        
        >>> myU6.getTemperature()
        299.87723471224308
        """
        if self.calInfo.nominal:
            # Read the actual calibration constants if we haven't already.
            self.getCalibrationData()
        
        result = self.getFeedback(AIN24AR(14))
        return self.binaryToCalibratedAnalogTemperature(result[0]['AIN'])

    def getAIN(self, positiveChannel, resolutionIndex=0, gainIndex=0, settlingFactor=0, differential=False):
        """
        Name: U6.getAIN(positiveChannel, resolutionIndex = 0, gainIndex = 0,
                        settlingFactor = 0, differential = False)
        Args: positiveChannel, the positive channel to read from
              resolutionIndex, the resolution index.  0 = default, 1-8 = high-speed
                               ADC, 9-12 = high-res ADC (U6-Pro only).
              gainIndex, the gain index.  0=x1, 1=x10, 2=x100, 3=x1000,
                         15=autorange.
              settlingFactor, the settling factor.  0=Auto, 1=20us, 2=50us,
                              3=100us, 4=200us, 5=500us, 6=1ms, 7=2ms, 8=5ms, 
                              9=10ms.
              differential, set to True for differential reading.  Negative
                            channel is positiveChannel+1.
        Desc: Reads an AIN and applies the calibration constants to it.
        
        >>> myU6.getAIN(14)
        299.87723471224308
        """
        result = self.getFeedback(AIN24AR(positiveChannel, resolutionIndex, gainIndex, settlingFactor, differential))
        
        return self.binaryToCalibratedAnalogVoltage(result[0]['GainIndex'], result[0]['AIN'], resolutionIndex = resolutionIndex)

    def readDefaultsConfig(self):
        """
        Name: U6.readDefaultsConfig()
        Args: None
        Desc: Reads the power-up defaults stored in flash.
        """
        results = dict()
        defaults = self.readDefaults(0)
        
        results['FIODirection'] = defaults[4]
        results['FIOState'] = defaults[5]
        
        results['EIODirection'] = defaults[8]
        results['EIOState'] = defaults[9]
        
        results['CIODirection'] = defaults[12]
        results['CIOState'] = defaults[13]
        
        results['ConfigWriteMask'] = defaults[16]
        results['NumOfTimersEnable'] = defaults[17]
        results['CounterMask'] = defaults[18]
        results['PinOffset'] = defaults[19]
        
        defaults = self.readDefaults(1)
        results['ClockSource'] = defaults[0]
        results['Divisor'] = defaults[1]
        
        results['TMR0Mode'] = defaults[16]
        results['TMR0ValueL'] = defaults[17]
        results['TMR0ValueH'] = defaults[18]
        
        results['TMR1Mode'] = defaults[20]
        results['TMR1ValueL'] = defaults[21]
        results['TMR1ValueH'] = defaults[22]
        
        results['TMR2Mode'] = defaults[24]
        results['TMR2ValueL'] = defaults[25]
        results['TMR2ValueH'] = defaults[26]
        
        results['TMR3Mode'] = defaults[28]
        results['TMR3ValueL'] = defaults[29]
        results['TMR3ValueH'] = defaults[30]
        
        defaults = self.readDefaults(2)
        
        results['DAC0'] = struct.unpack( ">H", struct.pack("BB", *defaults[16:18]) )[0]
        
        results['DAC1'] = struct.unpack( ">H", struct.pack("BB", *defaults[20:22]) )[0]
        
        defaults = self.readDefaults(3)
        
        for i in range(14):
            results["AIN%sGainRes" % i] = defaults[i]
            results["AIN%sOptions" % i] = defaults[i+16]
        
        return results

    def exportConfig(self):
        """
        Name: U6.exportConfig()
        Args: None
        Desc: Takes a configuration and puts it into a ConfigParser object.
        """
        # Make a new configuration file
        parser = ConfigParser.SafeConfigParser()
        
        # Change optionxform so that options preserve their case.
        parser.optionxform = str
        
        # Local Id and name
        section = "Identifiers"
        parser.add_section(section)
        parser.set(section, "Local ID", str(self.localId))
        parser.set(section, "Name", str(self.getName()))
        parser.set(section, "Device Type", str(self.devType))
        
        # FIO Direction / State
        section = "FIOs"
        parser.add_section(section)
        
        dirs, states = self.getFeedback( PortDirRead(), PortStateRead() )
        
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
        
        ioconfig = self.configIO()
        for key, value in ioconfig.items():
            parser.set(section, key, str(value))
            
        
        for i in range(ioconfig['NumberTimersEnabled']):
            mode, value = self.readRegister(7100 + (2 * i), numReg = 2, format = ">HH")
            parser.set(section, "Timer%s Mode" % i, str(mode))
            parser.set(section, "Timer%s Value" % i, str(value))
        
        return parser

    def loadConfig(self, configParserObj):
        """
        Name: U6.loadConfig(configParserObj)
        Args: configParserObj, A Config Parser object to load in
        Desc: Takes a configuration and updates the U6 to match it.
        """
        parser = configParserObj
        
        # Set Identifiers:
        section = "Identifiers"
        if parser.has_section(section):
            if parser.has_option(section, "device type"):
                if parser.getint(section, "device type") != self.devType:
                    raise Exception("Not a U6 Config file.")
            
            if parser.has_option(section, "local id"):
                self.configU6( LocalID = parser.getint(section, "local id"))
                
            if parser.has_option(section, "name"):
                self.setName( parser.get(section, "name") )
            
        # Set FIOs:
        section = "FIOs"
        if parser.has_section(section):
            fiodirs = 0
            eiodirs = 0
            ciodirs = 0
            
            fiostates = 0
            eiostates = 0
            ciostates = 0
            
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
                
            self.configIO(NumberTimersEnabled = nte, EnableCounter1 = c1e, EnableCounter0 = c0e, TimerCounterPinOffset = cpo)
            
            
            mode = None
            value = None
            
            for i in range(4):
                if parser.has_option(section, "timer%i mode" % i):
                    mode = parser.getint(section, "timer%i mode" % i)
                    
                    if parser.has_option(section, "timer%i value" % i):
                        value = parser.getint(section, "timer%i value" % i)
                    
                    self.getFeedback( TimerConfig(i, mode, value) )

class FeedbackCommand(object):
    '''
    The base FeedbackCommand class
    
    Used to make Feedback easy. Make a list of these
    and call getFeedback.
    '''
    readLen = 0
    def handle(self, input):
        return None

validChannels = range(144)
class AIN(FeedbackCommand):
    '''
    Analog Input Feedback command

    AIN(PositiveChannel)
    
    PositiveChannel : the positive channel to use 

    NOTE: This function kept for compatibility. Please use
          the new AIN24 and AIN24AR.
    
    returns 16-bit unsigned int sample
    
    >>> d.getFeedback( u6.AIN( PositiveChannel ) )
    [ 19238 ]
    '''
    def __init__(self, PositiveChannel):
        if PositiveChannel not in validChannels:
            raise LabJackException("Invalid Positive Channel specified")
        
        self.positiveChannel = PositiveChannel
        self.cmdBytes = [ 0x01, PositiveChannel, 0 ]

    readLen =  2
    
    def __repr__(self):
        return "<u6.AIN( PositiveChannel = %s )>" % self.positiveChannel

    def handle(self, input):
        result = (input[1] << 8) + input[0]
        return result

class AIN24(FeedbackCommand):
    '''
    Analog Input 24-bit Feedback command

    ainCommand = AIN24(PositiveChannel, ResolutionIndex = 0, GainIndex = 0,
                       SettlingFactor = 0, Differential = False)
    
    See section 5.2.5.2 of the user's guide.
    
    NOTE: If you use a gain index of 15 (autorange), you should be using
          the AIN24AR command instead. 
    
    positiveChannel : The positive channel to use
    resolutionIndex : 0=default, 1-8 for high-speed ADC,
                      9-12 for high-res ADC on U6-Pro.
    gainIndex : 0=x1, 1=x10, 2=x100, 3=x1000, 15=autorange
    settlingFactor : 0=Auto, 1=20us, 2=50us, 3=100us, 4=200us, 5=500us, 6=1ms,
                     7=2ms, 8=5ms, 9=10ms.
    differential : If this bit is set, a differential reading is done where
                   the negative channel is positiveChannel+1
    
    returns 24-bit unsigned int sample
    
    >>> d.getFeedback( u6.AIN24(PositiveChannel, ResolutionIndex = 0,
                                GainIndex = 0, SettlingFactor = 0,
                                Differential = False ) )
    [ 193847 ]
    '''
    def __init__(self, PositiveChannel, ResolutionIndex = 0, GainIndex = 0, SettlingFactor = 0, Differential = False):
        if PositiveChannel not in validChannels:
            raise LabJackException("Invalid Positive Channel specified")

        self.positiveChannel = PositiveChannel
        self.resolutionIndex = ResolutionIndex
        self.gainIndex = GainIndex
        self.settlingFactor = SettlingFactor
        self.differential = Differential
        
        byte2 = ( ResolutionIndex & 0xf )
        byte2 = ( ( GainIndex & 0xf ) << 4 ) + byte2
        
        byte3 = (int(Differential) << 7) + SettlingFactor
        self.cmdBytes = [ 0x02, PositiveChannel, byte2, byte3 ]

    def __repr__(self):
        return "<u6.AIN24( PositiveChannel = %s, ResolutionIndex = %s, GainIndex = %s, SettlingFactor = %s, Differential = %s )>" % (self.positiveChannel, self.resolutionIndex, self.gainIndex, self.settlingFactor, self.differential)

    readLen =  3

    def handle(self, input):
        #Put it all into an integer.
        result = (input[2] << 16 ) + (input[1] << 8 ) + input[0]
        return result

class AIN24AR(FeedbackCommand):
    '''
    Autorange Analog Input 24-bit Feedback command

    ainARCommand = AIN24AR(0, ResolutionIndex = 0, GainIndex = 0, 
                           SettlingFactor = 0, Differential = False)
    
    See section 5.2.5.3 of the user's guide
    
    PositiveChannel : The positive channel to use
    ResolutionIndex : 0=default, 1-8 for high-speed ADC, 
                      9-13 for high-res ADC on U6-Pro.
    GainIndex : 0=x1, 1=x10, 2=x100, 3=x1000, 15=autorange
    SettlingFactor : 0=Auto, 1=20us, 2=50us, 3=100us, 4=200us, 5=500us, 6=1ms,
                     7=2ms, 8=5ms, 9=10ms.
    Differential : If this bit is set, a differential reading is done where
                   the negative channel is positiveChannel+1
    
    returns a dictionary:
        { 
        'AIN' : < 24-bit binary reading >, 
        'ResolutionIndex' : < actual resolution setting used for the reading >,
        'GainIndex' : < actual gain used for the reading >,
        'Status' : < reserved for future use >
        }
    
    >>> d.getFeedback( u6.AIN24AR( PositiveChannel, ResolutionIndex = 0,
                                   GainIndex = 0, SettlingFactor = 0,
                                   Differential = False ) )
    { 'AIN' : 193847, 'ResolutionIndex' : 0, 'GainIndex' : 0, 'Status' : 0 }
    '''
    def __init__(self, PositiveChannel, ResolutionIndex = 0, GainIndex = 0, SettlingFactor = 0, Differential = False):
        if PositiveChannel not in validChannels:
            raise LabJackException("Invalid Positive Channel specified")

        self.positiveChannel = PositiveChannel
        self.resolutionIndex = ResolutionIndex
        self.gainIndex = GainIndex
        self.settlingFactor = SettlingFactor
        self.differential = Differential

        byte2 = ( ResolutionIndex & 0xf )
        byte2 = ( ( GainIndex & 0xf ) << 4 ) + byte2
        
        byte3 = (int(Differential) << 7) + SettlingFactor
        self.cmdBytes = [ 0x03, PositiveChannel, byte2, byte3 ]

    def __repr__(self):
        return "<u6.AIN24AR( PositiveChannel = %s, ResolutionIndex = %s, GainIndex = %s, SettlingFactor = %s, Differential = %s )>" % (self.positiveChannel, self.resolutionIndex, self.gainIndex, self.settlingFactor, self.differential)

    readLen =  5

    def handle(self, input):
        #Put it all into an integer.
        result = (input[2] << 16 ) + (input[1] << 8 ) + input[0]
        resolutionIndex = input[3] & 0xf
        gainIndex = ( input[3] >> 4 ) & 0xf 
        status = input[4]
        
        return { 'AIN' : result, 'ResolutionIndex' : resolutionIndex, 'GainIndex' : gainIndex, 'Status' : status }   

class WaitShort(FeedbackCommand):
    '''
    WaitShort Feedback command

    specify the number of 128us time increments to wait
    
    >>> d.getFeedback( u6.WaitShort( Time ) )
    [ None ]
    '''
    def __init__(self, Time):
        self.time = Time % 256
        self.cmdBytes = [ 5, Time % 256 ]
        
    def __repr__(self):
        return "<u6.WaitShort( Time = %s )>" % self.time

class WaitLong(FeedbackCommand):
    '''
    WaitLong Feedback command
    
    specify the number of 32ms time increments to wait
    
    >>> d.getFeedback( u6.WaitLog( Time ) )
    [ None ]
    '''
    def __init__(self, Time):
        self.time = Time
        self.cmdBytes = [ 6, Time % 256 ]

    def __repr__(self):
        return "<u6.WaitLog( Time = %s )>" % self.time

class LED(FeedbackCommand):
    '''
    LED Toggle

    specify whether the LED should be on or off by truth value
    
    1 or True = On, 0 or False = Off
    
    >>> d.getFeedback( u6.LED( State ) )
    [ None ]
    '''
    def __init__(self, State):
        self.state = State
        self.cmdBytes = [ 9, int(bool(State)) ]
        
    def __repr__(self):
        return "<u6.LED( State = %s )>" % self.state

class BitStateRead(FeedbackCommand):
    '''
    BitStateRead Feedback command

    read the state of a single bit of digital I/O.  Only digital lines return
    valid readings.

    IONumber: 0-7=FIO, 8-15=EIO, 16-19=CIO
    return 0 or 1
    
    >>> d.getFeedback( u6.BitStateRead( IONumber ) )
    [ 1 ]
    '''
    def __init__(self, IONumber):
        self.ioNumber = IONumber
        self.cmdBytes = [ 10, IONumber % 20 ]

    def __repr__(self):
        return "<u6.BitStateRead( IONumber = %s )>" % self.ioNumber

    readLen = 1

    def handle(self, input):
        return int(bool(input[0]))

class BitStateWrite(FeedbackCommand):
    '''
    BitStateWrite Feedback command

    write a single bit of digital I/O.  The direction of the specified line is
    forced to output.

    IONumber: 0-7=FIO, 8-15=EIO, 16-19=CIO
    State: 0 or 1
    
    >>> d.getFeedback( u6.BitStateWrite( IONumber, State ) )
    [ None ]
    '''
    def __init__(self, IONumber, State):
        self.ioNumber = IONumber
        self.state = State
        self.cmdBytes = [ 11, (IONumber % 20) + (int(bool(State)) << 7) ]
    
    def __repr__(self):
        return "<u6.BitStateWrite( IONumber = %s, State = %s )>" % self.ioNumber

class BitDirRead(FeedbackCommand):
    '''
    Read the digital direction of one I/O

    IONumber: 0-7=FIO, 8-15=EIO, 16-19=CIO
    returns 1 = Output, 0 = Input
    
    >>> d.getFeedback( u6.BitDirRead( IONumber ) )
    [ 1 ]
    '''
    def __init__(self, IONumber):
        self.ioNumber = IONumber
        self.cmdBytes = [ 12, IONumber % 20 ]

    def __repr__(self):
        return "<u6.BitDirRead( IONumber = %s )>" % self.ioNumber

    readLen = 1

    def handle(self, input):
        return int(bool(input[0]))

class BitDirWrite(FeedbackCommand):
    '''
    BitDirWrite Feedback command

    Set the digital direction of one I/O

    IONumber: 0-7=FIO, 8-15=EIO, 16-19=CIO
    Direction: 1 = Output, 0 = Input
    
    >>> d.getFeedback( u6.BitDirWrite( IONumber, Direction ) )
    [ None ] 
    '''
    def __init__(self, IONumber, Direction):
        self.ioNumber = IONumber
        self.direction = Direction
        self.cmdBytes = [ 13, (IONumber % 20) + (int(bool(Direction)) << 7) ]
        
    def __repr__(self):
        return "<u6.BitDirWrite( IONumber = %s, Direction = %s )>" % (self.ioNumber, self.direction)

class PortStateRead(FeedbackCommand):
    """
    PortStateRead Feedback command

    Reads the state of all digital I/O.
    
    >>> d.getFeedback( u6.PortStateRead() )
    [ { 'FIO' : 10, 'EIO' : 0, 'CIO' : 0 } ]
    """
    def __init__(self):
        self.cmdBytes = [ 26 ]
        
    def __repr__(self):
        return "<u6.PortStateRead()>"
        
    readLen = 3
    
    def handle(self, input):
        return {'FIO' : input[0], 'EIO' : input[1], 'CIO' : input[2] }

class PortStateWrite(FeedbackCommand):
    """
    PortStateWrite Feedback command
    
    State: A list of 3 bytes representing FIO, EIO, CIO
    WriteMask: A list of 3 bytes, representing which to update.
               The Default is all ones.
    
    >>> d.getFeedback( u6.PortStateWrite( State,
                                          WriteMask = [ 0xff, 0xff, 0xff] ) )
    [ None ]
    """
    def __init__(self, State, WriteMask = [ 0xff, 0xff, 0xff]):
        self.state = State
        self.writeMask = WriteMask
        self.cmdBytes = [ 27 ] + WriteMask + State
        
    def __repr__(self):
        return "<u6.PortStateWrite( State = %s, WriteMask = %s )>" % (self.state, self.writeMask)
        
class PortDirRead(FeedbackCommand):
    """
    PortDirRead Feedback command
    Reads the direction of all digital I/O.
    
    >>> d.getFeedback( u6.PortDirRead() )
    [ { 'FIO' : 10, 'EIO' : 0, 'CIO' : 0 } ]
    """
    def __init__(self):
        self.cmdBytes = [ 28 ]
    
    def __repr__(self):
        return "<u6.PortDirRead()>"
    
    readLen = 3
    
    def handle(self, input):
        return {'FIO' : input[0], 'EIO' : input[1], 'CIO' : input[2] }

class PortDirWrite(FeedbackCommand):
    """
    PortDirWrite Feedback command
    
    Direction: A list of 3 bytes representing FIO, EIO, CIO
    WriteMask: A list of 3 bytes, representing which to update. Default is all ones.
    
    >>> d.getFeedback( u6.PortDirWrite( Direction, 
                                        WriteMask = [ 0xff, 0xff, 0xff] ) )
    [ None ]
    """
    def __init__(self, Direction, WriteMask = [ 0xff, 0xff, 0xff]):
        self.direction = Direction
        self.writeMask = WriteMask
        self.cmdBytes = [ 29 ] + WriteMask + Direction
        
    def __repr__(self):
        return "<u6.PortDirWrite( Direction = %s, WriteMask = %s )>" % (self.direction, self.writeMask)
    
class DAC8(FeedbackCommand):
    '''
    8-bit DAC Feedback command
    
    Controls a single analog output

    Dac: 0 or 1
    Value: 0-255
    
    >>> d.getFeedback( u6.DAC8( Dac, Value ) )
    [ None ]
    '''
    def __init__(self, Dac, Value):
        self.dac = Dac
        self.value = Value % 256
        self.cmdBytes = [ 34 + (Dac % 2), Value % 256 ]
    
    def __repr__(self):
        return "<u6.DAC8( Dac = %s, Value = %s )>" % (self.dac, self.value)
        
class DAC0_8(DAC8):
    """
    8-bit DAC Feedback command for DAC0
    
    Controls DAC0 in 8-bit mode.

    Value: 0-255
    
    >>> d.getFeedback( u6.DAC0_8( Value ) )
    [ None ]
    """
    def __init__(self, Value):
        DAC8.__init__(self, 0, Value)

    def __repr__(self):
        return "<u6.DAC0_8( Value = %s )>" % self.value

class DAC1_8(DAC8):
    """
    8-bit DAC Feedback command for DAC1
    
    Controls DAC1 in 8-bit mode.

    Value: 0-255
    
    >>> d.getFeedback( u6.DAC1_8( Value ) )
    [ None ]
    """
    def __init__(self, Value):
        DAC8.__init__(self, 1, Value)
    
    def __repr__(self):
        return "<u6.DAC1_8( Value = %s )>" % self.value

class DAC16(FeedbackCommand):
    '''
    16-bit DAC Feedback command

    Controls a single analog output

    Dac: 0 or 1
    Value: 0-65535
    
    >>> d.getFeedback( u6.DAC16( Dac, Value ) )
    [ None ]
    '''
    def __init__(self, Dac, Value):
        self.dac = Dac
        self.value = Value
        self.cmdBytes = [ 38 + (Dac % 2), Value % 256, Value >> 8 ]
    
    def __repr__(self):
        return "<u6.DAC8( Dac = %s, Value = %s )>" % (self.dac, self.value)

class DAC0_16(DAC16):
    """
    16-bit DAC Feedback command for DAC0
    
    Controls DAC0 in 16-bit mode.

    Value: 0-65535
    
    >>> d.getFeedback( u6.DAC0_16( Value ) )
    [ None ]
    """
    def __init__(self, Value):
        DAC16.__init__(self, 0, Value)
    
    def __repr__(self):
        return "<u6.DAC0_16( Value = %s )>" % self.value

class DAC1_16(DAC16):
    """
    16-bit DAC Feedback command for DAC1
    
    Controls DAC1 in 16-bit mode.

    Value: 0-65535
    
    >>> d.getFeedback( u6.DAC1_16( Value ) )
    [ None ]
    """
    def __init__(self, Value):
        DAC16.__init__(self, 1, Value)
        
    def __repr__(self):
        return "<u6.DAC1_16( Value = %s )>" % self.value
        
class Timer(FeedbackCommand):
    """
    For reading the value of the Timer. It provides the ability to update/reset
    a given timer, and read the timer value.
    ( Section 5.2.5.17 of the User's Guide)
    
    timer: 0 to 3 for timer0 to timer3
    
    UpdateReset: Set True if you want to update the value
    
    Value: Only updated if the UpdateReset bit is 1.  The meaning of this
           parameter varies with the timer mode.

    Mode: Set to the timer mode to handle any special processing. See classes
          QuadratureInputTimer and TimerStopInput1.

    Returns an unsigned integer of the timer value, unless Mode has been
    specified and there are special return values. See Section 2.9.1 for
    expected return values. 

    >>> d.getFeedback( u6.Timer( timer, UpdateReset = False, Value = 0 \
    ... , Mode = None ) )
    [ 12314 ]
    """
    def __init__(self, timer, UpdateReset = False, Value=0, Mode = None):
        if timer not in range(4):
            raise LabJackException("Timer should be 0-3.")
        if UpdateReset and Value == None:
            raise LabJackException("UpdateReset set but no value.")
        
        self.timer = timer
        self.updateReset = UpdateReset
        self.value = Value
        self.mode = Mode
        
        self.cmdBytes = [ (42 + (2*timer)), UpdateReset, Value % 256, Value >> 8 ]
    
    readLen = 4
    
    def __repr__(self):
        return "<u6.Timer( timer = %s, UpdateReset = %s, Value = %s, Mode = %s )>" % (self.timer, self.updateReset, self.value, self.mode)
    
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
    For reading the value of Timer0. It provides the ability to update/reset
    Timer0, and read the timer value.
    (Section 5.2.5.17 of the User's Guide)
    
    UpdateReset: Set True if you want to update the value
    
    Value: Only updated if the UpdateReset bit is 1.  The meaning of this
           parameter varies with the timer mode.

    Mode: Set to the timer mode to handle any special processing. See classes
          QuadratureInputTimer and TimerStopInput1.

    >>> d.getFeedback( u6.Timer0( UpdateReset = False, Value = 0, \
    ... Mode = None ) )
    [ 12314 ]
    """
    def __init__(self, UpdateReset = False, Value = 0, Mode = None):
        Timer.__init__(self, 0, UpdateReset, Value, Mode)
        
    def __repr__(self):
        return "<u6.Timer0( UpdateReset = %s, Value = %s, Mode = %s )>" % (self.updateReset, self.value, self.mode)

class Timer1(Timer):
    """
    For reading the value of Timer1. It provides the ability to update/reset
    Timer1, and read the timer value.
    (Section 5.2.5.17 of the User's Guide)
    
    UpdateReset: Set True if you want to update the value
    
    Value: Only updated if the UpdateReset bit is 1.  The meaning of this
           parameter varies with the timer mode.

    Mode: Set to the timer mode to handle any special processing. See classes
          QuadratureInputTimer and TimerStopInput1.

    >>> d.getFeedback( u6.Timer1( UpdateReset = False, Value = 0, \
    ... Mode = None ) )
    [ 12314 ]
    """
    def __init__(self, UpdateReset = False, Value = 0, Mode = None):
        Timer.__init__(self, 1, UpdateReset, Value, Mode)
    
    def __repr__(self):
        return "<u6.Timer1( UpdateReset = %s, Value = %s, Mode = %s )>" % (self.updateReset, self.value, self.mode)

class Timer2(Timer):
    """
    For reading the value of Timer2. It provides the ability to update/reset
    Timer2, and read the timer value.
    (Section 5.2.5.17 of the User's Guide)
    
    UpdateReset: Set True if you want to update the value
    
    Value: Only updated if the UpdateReset bit is 1.  The meaning of this
           parameter varies with the timer mode.

    Mode: Set to the timer mode to handle any special processing. See classes
          QuadratureInputTimer and TimerStopInput1.

    >>> d.getFeedback( u6.Timer2( UpdateReset = False, Value = 0, \
    ... Mode = None ) )
    [ 12314 ]
    """
    def __init__(self, UpdateReset = False, Value = 0, Mode = None):
        Timer.__init__(self, 2, UpdateReset, Value, Mode)
    
    def __repr__(self):
        return "<u6.Timer2( UpdateReset = %s, Value = %s, Mode = %s )>" % (self.updateReset, self.value, self.mode)

class Timer3(Timer):
    """
    For reading the value of Timer3. It provides the ability to update/reset
    Timer3, and read the timer value.
    (Section 5.2.5.17 of the User's Guide)
    
    UpdateReset: Set True if you want to update the value
    
    Value: Only updated if the UpdateReset bit is 1.  The meaning of this
           parameter varies with the timer mode.

    Mode: Set to the timer mode to handle any special processing. See classes
          QuadratureInputTimer and TimerStopInput1.

    >>> d.getFeedback( u6.Timer3( UpdateReset = False, Value = 0, \
    ... Mode = None ) )
    [ 12314 ]
    """
    def __init__(self, UpdateReset = False, Value = 0, Mode = None):
        Timer.__init__(self, 3, UpdateReset, Value, Mode)
    
    def __repr__(self):
        return "<u6.Timer3( UpdateReset = %s, Value = %s, Mode = %s )>" % (self.updateReset, self.value, self.mode)

class QuadratureInputTimer(Timer):
    """
    For reading Quadrature input timers. They are special because their values
    are signed.
    
    ( Section 2.9.1.8 of the User's Guide)
    
    Args:
       UpdateReset: Set True if you want to reset the counter.
       Value: Set to 0, and UpdateReset to True to reset the counter.
    
    Returns a signed integer.
    
    >>> # Setup the two timers to be quadrature
    >>> d.getFeedback( u6.Timer0Config( 8 ), u6.Timer1Config( 8 ) )
    [None, None]
    >>> # Read the value
    >>> d.getFeedback( u6.QuadratureInputTimer() )
    [-21]
    """
    def __init__(self, UpdateReset = False, Value = 0):
        Timer.__init__(self, 0, UpdateReset, Value, Mode = 8)
        
    def __repr__(self):
        return "<u6.QuadratureInputTimer( UpdateReset = %s, Value = %s )>" % (self.updateReset, self.value)

class TimerStopInput1(Timer1):
    """
    For reading a stop input timer. They are special because the value returns
    the current edge count and the stop value.
    
    ( Section 2.9.1.9 of the User's Guide)
    
    Args:
        UpdateReset: Set True if you want to update the value.
        Value: The stop value. Only updated if the UpdateReset bit is 1.
    
    Returns a tuple where the first value is current edge count, and the second
    value is the stop value.
    
    >>> # Setup the timer to be Stop Input
    >>> d.getFeedback( u6.Timer0Config( 9, Value = 30 ) )
    [None]
    >>> # Read the timer
    >>> d.getFeedback( u6.TimerStopInput1() )
    [(0, 30)]
    """
    def __init__(self, UpdateReset = False, Value = 0):
        Timer.__init__(self, 1, UpdateReset, Value, Mode = 9)
    
    def __repr__(self):
        return "<u6.TimerStopInput1( UpdateReset = %s, Value = %s )>" % (self.updateReset, self.value)

class TimerConfig(FeedbackCommand):
    """
    This IOType configures a particular timer.
    
    timer: # of the timer to configure
    
    TimerMode: See Section 2.9 for more information about the available modes.
    
    Value: The meaning of this parameter varies with the timer mode.
    
    >>> d.getFeedback( u6.TimerConfig( timer, TimerMode, Value = 0 ) )
    [ None ]
    """
    def __init__(self, timer, TimerMode, Value=0):
        '''Creates command bytes for configuring a Timer'''
        if timer not in range(4):
            raise LabJackException("Timer should be 0-3.")
        
        if TimerMode > 14 or TimerMode < 0:
            raise LabJackException("Invalid Timer Mode.")
        
        self.timer = timer
        self.timerMode = TimerMode
        self.value = Value
        
        self.cmdBytes = [43 + (timer * 2), TimerMode, Value % 256, Value >> 8]
    
    def __repr__(self):
        return "<u6.TimerConfig( timer = %s, TimerMode = %s, Value = %s )>" % (self.timer, self.timerMode, self.value)

class Timer0Config(TimerConfig):
    """
    This IOType configures Timer0.
    
    TimerMode: See Section 2.9 for more information about the available modes.
    
    Value: The meaning of this parameter varies with the timer mode.
    
    >>> d.getFeedback( u6.Timer0Config( TimerMode, Value = 0 ) )
    [ None ]
    """
    def __init__(self, TimerMode, Value = 0):
        TimerConfig.__init__(self, 0, TimerMode, Value)
    
    def __repr__(self):
        return "<u6.Timer0Config( TimerMode = %s, Value = %s )>" % (self.timerMode, self.value)

class Timer1Config(TimerConfig):
    """
    This IOType configures Timer1.
    
    TimerMode: See Section 2.9 for more information about the available modes.
    
    Value: The meaning of this parameter varies with the timer mode.
    
    >>> d.getFeedback( u6.Timer1Config( TimerMode, Value = 0 ) )
    [ None ]
    """
    def __init__(self, TimerMode, Value = 0):
        TimerConfig.__init__(self, 1, TimerMode, Value)
    
    def __repr__(self):
        return "<u6.Timer1Config( TimerMode = %s, Value = %s )>" % (self.timerMode, self.value)

class Timer2Config(TimerConfig):
    """
    This IOType configures Timer2.
    
    TimerMode: See Section 2.9 for more information about the available modes.
    
    Value: The meaning of this parameter varies with the timer mode.
    
    >>> d.getFeedback( u6.Timer2Config( TimerMode, Value = 0 ) )
    [ None ]
    """
    def __init__(self, TimerMode, Value = 0):
        TimerConfig.__init__(self, 2, TimerMode, Value)
    
    def __repr__(self):
        return "<u6.Timer2Config( TimerMode = %s, Value = %s )>" % (self.timerMode, self.value)

class Timer3Config(TimerConfig):
    """
    This IOType configures Timer3.
    
    TimerMode: See Section 2.9 for more information about the available modes.
    
    Value: The meaning of this parameter varies with the timer mode.
    
    >>> d.getFeedback( u6.Timer3Config( TimerMode, Value = 0 ) )
    [ None ]
    """
    def __init__(self, TimerMode, Value = 0):
        TimerConfig.__init__(self, 3, TimerMode, Value)
    
    def __repr__(self):
        return "<u6.Timer3Config( TimerMode = %s, Value = %s )>" % (self.timerMode, self.value)

class Counter(FeedbackCommand):
    '''
    Counter Feedback command

    Reads a hardware counter, optionally resetting it

    counter: 0 or 1
    Reset: True ( or 1 ) = Reset, False ( or 0 ) = Don't Reset

    Returns the current count from the counter if enabled.  If reset,
    this is the value before the reset.
    
    >>> d.getFeedback( u6.Counter( counter, Reset = False ) )
    [ 2183 ]
    '''
    def __init__(self, counter, Reset):
        self.counter = counter
        self.reset = Reset
        self.cmdBytes = [ 54 + (counter % 2), int(bool(Reset))]

    def __repr__(self):
        return "<u6.Counter( counter = %s, Reset = %s )>" % (self.counter, self.reset)

    readLen = 4

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
    
    >>> d.getFeedback( u6.Counter0( Reset = False ) )
    [ 2183 ]
    '''
    def __init__(self, Reset = False):
        Counter.__init__(self, 0, Reset)
    
    def __repr__(self):
        return "<u6.Counter0( Reset = %s )>" % self.reset

class Counter1(Counter):
    '''
    Counter1 Feedback command

    Reads hardware counter1, optionally resetting it

    Reset: True ( or 1 ) = Reset, False ( or 0 ) = Don't Reset

    Returns the current count from the counter if enabled.  If reset,
    this is the value before the reset.
    
    >>> d.getFeedback( u6.Counter1( Reset = False ) )
    [ 2183 ]
    '''
    def __init__(self, Reset = False):
        Counter.__init__(self, 1, Reset)
    
    def __repr__(self):
        return "<u6.Counter1( Reset = %s )>" % self.reset

class DSP(FeedbackCommand):
    '''
    DSP Feedback command

    Acquires 1000 samples from the specified AIN at 50us intervals and performs
    the specified analysis on the acquired data.

    AcquireNewData: True, acquire new data; False, operate on existing data
    DSPAnalysis: 1, True RMS; 2, DC Offset; 3, Peak To Peak; 4, Period (ms)
    PLine: Positive Channel
    Gain: The gain you would like to use
    Resolution: The resolution index to use
    SettlingFactor: The SettlingFactor to use
    Differential: True, do differential readings; False, single-ended readings

    See section 5.2.5.20 of the U3 User's Guide 
    (http://labjack.com/support/u6/users-guide/5.2.5.20)
    
    >>> d.getFeedback( u6.DSP( PLine, Resolution = 0, Gain = 0,
                               SettlingFactor = 0,  Differential = False,
                               DSPAnalysis = 1, AcquireNewData = True) )
    [ 2183 ]
    '''
    def __init__(self, PLine, Resolution = 0, Gain = 0, SettlingFactor = 0,  Differential = False, DSPAnalysis = 1, AcquireNewData = True):
        self.pline = PLine
        self.resolution = Resolution
        self.gain = Gain
        self.settlingFactor = SettlingFactor
        self.differential = Differential
        
        self.dspAnalysis = DSPAnalysis
        self.acquireNewData = AcquireNewData
        
        byte1 = DSPAnalysis + ( int(AcquireNewData) << 7 )
        byte4 = ( Gain << 4 ) + Resolution
        byte5 = ( int(Differential) << 7 ) + SettlingFactor
        
        self.cmdBytes = [ 62, byte1, PLine, 0, byte4, byte5, 0, 0 ]

    def __repr__(self):
        return "<u6.DSP( PLine = %s, Resolution = %s, Gain = %s, SettlingFactor = %s, Differential = %s, DSPAnalysis = %s, AcquireNewData = %s )>" % (self.pline, self.resolution, self.gain, self.settlingFactor, self.differential, self.dspAnalysis, self.acquireNewData)

    readLen = 4

    def handle(self, input):
        inStr = ''.join([chr(x) for x in input])
        return struct.unpack('<I', inStr )[0]
