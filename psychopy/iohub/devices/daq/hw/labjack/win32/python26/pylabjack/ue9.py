"""
Name: ue9.py
Desc: Defines the UE9 class, which makes working with a UE9 much easier. All of
      the low-level functions for the UE9 are implemented as functions of the
      UE9 class. There are also a handful additional functions which improve
      upon the interface provided by the low-level functions.

To learn about the low-level functions, please see Section 5.2 of the UE9 User's Guide:

http://labjack.com/support/ue9/users-guide/5.2 
"""
from LabJackPython import *

import struct, socket, select, ConfigParser
from datetime import datetime

def openAllUE9():
    """
    A helpful function which will open all the connected UE9s. Returns a 
    dictionary where the keys are the serialNumber, and the value is the device
    object.
    """
    returnDict = dict()
    
    for i in range(deviceCount(9)):
        d = UE9(firstFound = False, devNumber = i+1)
        returnDict[str(d.serialNumber)] = d
        
    return returnDict

def parseIpAddress(bytes):
    return "%s.%s.%s.%s" % (bytes[3], bytes[2], bytes[1], bytes[0] )
    
def unpackInt(bytes):
    return struct.unpack("<I", struct.pack("BBBB", *bytes))[0]

def unpackShort(bytes):
    return struct.unpack("<H", struct.pack("BB", *bytes))[0]

DEFAULT_CAL_CONSTANTS = { "AINSlopes" : { '0' : 0.000077503, '1' : 0.000038736, '2' : 0.000019353, '3' : 0.0000096764, '8' : 0.00015629  }, "AINOffsets" : { '0' : -0.012000, '1' : -0.012000, '2' : -0.012000, '3' : -0.012000, '8' : -5.1760 }, "TempSlope" : 0.012968, "DACSlopes" : { '0' : 842.59, '1' : 842.59}, "DACOffsets" : { '0' : 0.0, '1': 0.0} }

class UE9(Device):
    """
    UE9 Class for all UE9 specific low-level commands.
    
    Example:
    >>> import ue9
    >>> d = ue9.UE9()
    >>> print d.commConfig()
    {'CommFWVersion': '1.47', ..., 'IPAddress': '192.168.1.114'}
    """
    def __init__(self, debug = False, autoOpen = True, **kargs):
        """
        Name: UE9.__init__(self)
        Args: debug, True for debug information
        Desc: Your basic constructor.
        
        >>> myUe9 = ue9.UE9()
        """
        Device.__init__(self, None, devType = 9)
        
        self.debug = debug
        self.calData = None
        self.controlFWVersion = self.commFWVersion = None
        self.ethernet = False

        if autoOpen:
            self.open(**kargs)
    
    def open(self, firstFound = True, serial = None, ipAddress = None, localId = None, devNumber = None, ethernet=False, handleOnly = False, LJSocket = None):
        """
        Name: UE9.open(firstFound = True, ipAddress = None, localId = None, devNumber = None, ethernet=False)
        Args: firstFound, Open the first found UE9
              serial, open a UE9 with the given serial number.
              ipAddress, Specify the IP Address of the UE9 you want to open
              localId, Specify the localId of the UE9 you want to open
              devNumber, Specify the USB dev number of the UE9
              ethernet, set to true to connect over ethernet.
              handleOnly, if True, LabJackPython will only open a handle
              LJSocket, set to "<ip>:<port>" to connect to LJSocket
        Desc: Opens the UE9.
        
        >>> myUe9 = ue9.UE9(autoOpen = False)
        >>> myUe9.open()
        """
        self.ethernet = ethernet
        Device.open(self, 9, Ethernet = ethernet, firstFound = firstFound, serial = serial, localId = localId, devNumber = devNumber, ipAddress = ipAddress, handleOnly = handleOnly, LJSocket = LJSocket)
        
    def commConfig(self, LocalID = None, IPAddress = None, Gateway = None, Subnet = None, PortA = None, PortB = None, DHCPEnabled = None):
        """
        Name: UE9.commConfig(LocalID = None, IPAddress = None, Gateway = None,
                Subnet = None, PortA = None, PortB = None, DHCPEnabled = None)
        Args: LocalID, Set the LocalID
              IPAddress, Set the IPAdress 
              Gateway, Set the Gateway
              Subnet, Set the Subnet
              PortA, Set Port A
              PortB, Set Port B
              DHCPEnabled, True = Enabled, False = Disabled
        Desc: Writes and reads various configuration settings associated
              with the Comm processor. Section 5.2.1 of the User's Guide.
        
        >>> myUe9 = ue9.UE9()
        >>> myUe9.commConfig()
        {'CommFWVersion': '1.47',
         'DHCPEnabled': False,
         'Gateway': '192.168.1.1',
         'HWVersion': '1.10',
         'IPAddress': '192.168.1.114',
         'LocalID': 1,
         'MACAddress': 'XX:XX:XX:XX:XX:XX',
         'PortA': 52360,
         'PortB': 52361,
         'PowerLevel': 0,
         'ProductID': 9,
         'SerialNumber': 27121XXXX,
         'Subnet': '255.255.255.0'}
        """
        command = [ 0 ] * 38
        
        #command[0] = Checksum8
        command[1] = 0x78
        command[2] = 0x10
        command[3] = 0x01
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        #command[6] = Writemask. Set it along the way.
        #command[7] = Reserved
        if LocalID != None:
            command[6] |= 1
            command[8] = LocalID
        
        if IPAddress != None:
            command[6] |= (1 << 2)
            ipbytes = IPAddress.split('.')
            ipbytes = [ int(x) for x in ipbytes ]
            ipbytes.reverse()
            command[10:14] = ipbytes
        
        if Gateway != None:
            command[6] |= (1 << 3)
            gwbytes = Gateway.split('.')
            gwbytes = [ int(x) for x in gwbytes ]
            gwbytes.reverse()
            command[14:18] = gwbytes
            
        if Subnet != None:
            command[6] |= (1 << 4)
            snbytes = Subnet.split('.')
            snbytes = [ int(x) for x in snbytes ]
            snbytes.reverse()
            command[18:21] = snbytes
            
        if PortA != None:
            command[6] |= (1 << 5)
            t = struct.pack("<H", PortA)
            command[22] = ord(t[0])
            command[23] = ord(t[1])
        
        if PortB != None:
            command[6] |= (1 << 5)
            t = struct.pack("<H", PortB)
            command[24] = ord(t[0])
            command[25] = ord(t[1])

        if DHCPEnabled != None:
            command[6] |= (1 << 6)
            if DHCPEnabled:
                command[26] = 1
        
        result = self._writeRead(command, 38, [], checkBytes = False)
        
        if result[0] == 0xB8 and result[1] == 0xB8:
            raise LabJackException("Device detected a bad checksum.")
        elif result[1:4] != [ 0x78, 0x10, 0x01 ]:
            raise LabJackException("Got incorrect command bytes.")
        elif not verifyChecksum(result):
            raise LabJackException("Checksum was incorrect.")
        
        self.localId = result[8]
        self.powerLevel = result[9]
        self.ipAddress = parseIpAddress(result[10:14])
        self.gateway = parseIpAddress(result[14:18])
        self.subnet = parseIpAddress(result[18:22])
        self.portA = struct.unpack("<H", struct.pack("BB", *result[22:24]))[0]
        self.portB = struct.unpack("<H", struct.pack("BB", *result[24:26]))[0]
        self.DHCPEnabled = bool(result[26])
        self.productId = result[27]
        macBytes = result[28:34]
        self.macAddress = "%02X:%02X:%02X:%02X:%02X:%02X" % (result[33], result[32], result[31], result[30], result[29], result[28])
        
        self.serialNumber = struct.unpack("<I", struct.pack("BBBB", result[28], result[29], result[30], 0x10))[0]
        
        self.hwVersion = "%s.%02d" % (result[35], result[34])
        self.commFWVersion = "%s.%02d" % (result[37], result[36])
        self.firmwareVersion = [self.controlFWVersion, self.commFWVersion]

        return { 'LocalID' : self.localId, 'PowerLevel' : self.powerLevel, 'IPAddress' : self.ipAddress, 'Gateway' : self.gateway, 'Subnet' : self.subnet, 'PortA' : self.portA, 'PortB' : self.portB, 'DHCPEnabled' : self.DHCPEnabled, 'ProductID' : self.productId, 'MACAddress' : self.macAddress, 'HWVersion' : self.hwVersion, 'CommFWVersion' : self.commFWVersion, 'SerialNumber' : self.serialNumber}
    
    def flushBuffer(self):
        """
        Name: UE9.flushBuffer()
        Args: None
        Desc: Resets the pointers to the stream buffer to make it empty.
        
        >>> myUe9 = ue9.UE9()
        >>> myUe9.flushBuffer()
        """
        command = [ 0x08, 0x08 ]
        self._writeRead(command, 2, [], False, False, False)
    
    def discoveryUDP(self):
        """
        Name: UE9.discoveryUDP()
        Args: None
        Desc: Sends a UDP Broadcast packet and returns a dictionary of the
              result. The dictionary contains all the things that are in the
              commConfig dictionary.
        
        >>> myUe9 = ue9.UE9()
        >>> myUe9.discoveryUDP()
        {'192.168.1.114': {'CommFWVersion': '1.47', ... },
         '192.168.1.209': {'CommFWVersion': '1.47', ... }}
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        host = '255.255.255.255'
        port = 52362
        addr = (host,port)
        
        sndBuffer = [0] * 6
        sndBuffer[0] = 0x22
        sndBuffer[1] = 0x78
        sndBuffer[2] = 0x00
        sndBuffer[3] = 0xA9
        sndBuffer[4] = 0x00
        sndBuffer[5] = 0x00
    
        packFormat = "B" * len(sndBuffer)
        tempString = struct.pack(packFormat, *sndBuffer)
        
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
        s.sendto(tempString, addr)
        
        inputs = [s]
        
        ue9s = {}
        
        listen = True
        while listen:
            #We will wait 2 seconds for a response from a Ue9
            rs,ws,es = select.select(inputs, [], [], 1)
            listen = False
            for r in rs:
                if r is s:
                    data,addr = s.recvfrom(38)
                    ue9s[addr[0]] = data
                    listen = True
        s.close()
        
        for ip, data in ue9s.items():
            data = list(struct.unpack("B"*38, data))
            ue9 = { 'LocalID' : data[8], 'PowerLevel' : data[9] , 'IPAddress' : parseIpAddress(data[10:14]), 'Gateway' : parseIpAddress(data[14:18]), 'Subnet' : parseIpAddress(data[18:23]), 'PortA' : struct.unpack("<H", struct.pack("BB", *data[22:24]))[0], 'PortB' : struct.unpack("<H", struct.pack("BB", *data[24:26]))[0], 'DHCPEnabled' : bool(data[26]), 'ProductID' : data[27], 'MACAddress' : "%02X:%02X:%02X:%02X:%02X:%02X" % (data[33], data[32], data[31], data[30], data[29], data[28]), 'SerialNumber' : struct.unpack("<I", struct.pack("BBBB", data[28], data[29], data[30], 0x10))[0], 'HWVersion' : "%s.%02d" % (data[35], data[34]), 'CommFWVersion' : "%s.%02d" % (data[37], data[36])}
            ue9s[ip] = ue9
        
        return ue9s

    def controlConfig(self, PowerLevel = None, FIODir = None, FIOState = None, EIODir = None, EIOState = None, CIODirection = None, CIOState = None, MIODirection = None, MIOState = None, DoNotLoadDigitalIODefaults = None, DAC0Enable = None, DAC0 = None, DAC1Enable = None, DAC1 = None):
        """
        Name: UE9.controlConfig(PowerLevel = None, FIODir = None, 
              FIOState = None, EIODir = None,
              EIOState = None, CIODirection = None, CIOState = None,
              MIODirection = None, MIOState = None, 
              DoNotLoadDigitalIODefaults = None, DAC0Enable = None, 
              DAC0 = None, DAC1Enable = None, DAC1 = None)
        Args: PowerLevel, 0 = Fixed High, 48 MHz, 1 = Fixed low, 6 MHz
              FIODir, Direction of FIOs
              FIOState, State of FIOs
              EIODir, Direction of EIOs
              EIOState, State of EIOs
              CIODirection, Direction of CIOs (max of 4)
              CIOState, State of CIOs (max of 4)
              MIODirection, Direction of MIOs (max of 3)
              MIOState, Direction of MIOs (max of 3)
              DoNotLoadDigitalIODefaults, Set True, to not load the defaults
              DAC0Enable, True = DAC0 Enabled, False = DAC0 Disabled
              DAC0, The default value for DAC0
              DAC1Enable, True = DAC1 Enabled, False = DAC1 Disabled
              DAC1, The default value for DAC1
        Desc: Configures various parameters associated with the Control
              processor. Affects only the power-up values, not current 
              state. See section 5.3.2 of the User's Guide.
        
        >>> myUe9 = ue9.UE9()
        >>> myUe9.controlConfig()
        {'CIODirection': 0,
         'CIOState': 0,
         'ControlBLVersion': '1.12',
         'ControlFWVersion': '1.97',
         'DAC0': 0,
         'DAC0 Enabled': False,
         'DAC1': 0,
         'DAC1 Enabled': False,
         'EIODir': 0,
         'EIOState': 0,
         'FIODir': 0,
         'FIOState': 0,
         'HiRes Flag': False,
         'MIODirection': 0,
         'MIOState': 0,
         'PowerLevel': 0,
         'ResetSource': 119}
        """
        command = [ 0 ] * 18
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x06
        command[3] = 0x08
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        #command[6] = Writemask. Set it along the way.
        
        if PowerLevel != None:
            command[6] |= 1
            command[7] = PowerLevel
        
        if FIODir != None:
            command[6] |= (1 << 1)
            command[8] = FIODir
        
        if FIOState != None:
            command[6] |= (1 << 1)
            command[9] = FIOState
        
        if EIODir != None:
            command[6] |= (1 << 1)
            command[10] = EIODir
        
        if EIOState != None:
            command[6] |= (1 << 1)
            command[11] = EIOState
        
        if CIODirection != None:
            command[6] |= (1 << 1)
            command[12] = ( CIODirection & 0xf) << 4
        
        if CIOState != None:
            command[6] |= (1 << 1)
            command[12] |= ( CIOState & 0xf )
        
        if DoNotLoadDigitalIODefaults != None:
            command[6] |= (1 << 1)
            if DoNotLoadDigitalIODefaults:
                command[13] |= (1 << 7)
        
        if MIODirection != None:
            command[6] |= (1 << 1)
            command[13] |= ( MIODirection & 7 ) << 4
        
        if MIOState != None:
            command[6] |= (1 << 1)
            command[13] |= ( MIOState & 7 )
        
        if DAC0Enable != None:
            command[6] |= (1 << 2)
            if DAC0Enable:
                command[15] = (1 << 7)
        
        if DAC0 != None:
            command[6] |= (1 << 2)
            command[14] = DAC0 & 0xff
            command[15] |= (DAC0 >> 8 ) & 0xf
        
        if DAC1Enable != None:
            command[6] |= (1 << 2)
            if DAC1Enable:
                command[17] = (1 << 7)
        
        if DAC1 != None:
            command[6] |= (1 << 2)
            command[16] = DAC1 & 0xff
            command[17] |= (DAC1 >> 8 ) & 0xf
        
        result = self._writeRead(command, 24, [ 0xF8, 0x09, 0x08 ])
        
        self.powerLevel = result[7]
        self.controlFWVersion = "%s.%02d" % (result[10], result[9])
        self.firmwareVersion = [self.controlFWVersion, self.commFWVersion]
        self.controlBLVersion = "%s.%02d" % (result[12], result[11])
        self.hiRes = bool(result[13] & 1)
        
        self.deviceName = 'UE9'
        if self.hiRes:
            self.deviceName = 'UE9-Pro'
        
        return { 'PowerLevel' : self.powerLevel, 'ResetSource' : result[8], 'ControlFWVersion' : self.controlFWVersion, 'ControlBLVersion' : self.controlBLVersion, 'HiRes Flag' : self.hiRes, 'FIODir' : result[14], 'FIOState' : result[15], 'EIODir' : result[16], 'EIOState' : result[17], 'CIODirection' : (result[18] >> 4) & 0xf, 'CIOState' : result[18] & 0xf, 'MIODirection' : (result[19] >> 4) & 7, 'MIOState' : result[19] & 7, 'DAC0 Enabled' : bool(result[21] >> 7 & 1), 'DAC0' : (result[21] & 0xf) + result[20], 'DAC1 Enabled' : bool(result[23] >> 7 & 1), 'DAC1' : (result[23] & 0xf) + result[22], 'DeviceName' : self.deviceName }
        
    def feedback(self, FIOMask = 0, FIODir = 0, FIOState = 0, EIOMask = 0, EIODir = 0, EIOState = 0, CIOMask = 0, CIODirection = 0, CIOState = 0, MIOMask = 0, MIODirection = 0, MIOState = 0, DAC0Update = False, DAC0Enabled = False, DAC0 = 0, DAC1Update = False, DAC1Enabled = False, DAC1 = 0, AINMask = 0, AIN14ChannelNumber = 0, AIN15ChannelNumber = 0, Resolution = 0, SettlingTime = 0, AIN1_0_BipGain = 0, AIN3_2_BipGain = 0, AIN5_4_BipGain  = 0, AIN7_6_BipGain = 0, AIN9_8_BipGain = 0, AIN11_10_BipGain = 0, AIN13_12_BipGain = 0, AIN15_14_BipGain = 0):
        """
        Name: UE9.feedback(FIOMask = 0, FIODir = 0, FIOState = 0,
              EIOMask = 0, EIODir = 0, EIOState = 0, CIOMask = 0,
              CIODirection = 0, CIOState = 0, MIOMask = 0, MIODirection = 0,
              MIOState = 0, DAC0Update = False, DAC0Enabled = None,
              DAC0 = None, DAC1Update = False, DAC1Enabled = None, DAC1 = None,
              AINMask = 0, AIN14ChannelNumber = 0, AIN15ChannelNumber = 0,
              Resolution = 0, SettlingTime = 0, AIN1_0_BipGain = 0,
              AIN3_2_BipGain = 0, AIN5_4_BipGain  = 0, AIN7_6_BipGain = 0,
              AIN9_8_BipGain = 0, AIN11_10_BipGain = 0, AIN13_12_BipGain = 0,
              AIN15_14_BipGain = 0)
        Args: See section 5.3.3 of the User's Guide
        Desc: A very useful function that writes/reads almost every I/O on the
              LabJack UE9. See section 5.3.3 of the User's Guide.

        >>> myUe9 = ue9.UE9()
        >>> myUe9.feedback()
        {'AIN0': 0, ...
         'TimerB': 0,
         'TimerC': 0}
        """
        command = [ 0 ] * 34
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x0E
        command[3] = 0x00
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = FIOMask
        command[7] = FIODir
        command[8] = FIOState
        command[9] = EIOMask
        command[10] = EIODir
        command[11] = EIOState
        command[12] = CIOMask
        command[13] = (CIODirection & 0xf) << 4
        command[13] |= (CIOState & 0xf)
        command[14] = MIOMask
        command[15] = (MIODirection & 7) << 4
        command[15] |= (MIOState & 7 )
        
        if DAC0Update:
            if DAC0Enabled:
                command[17] = 1 << 7
            command[17] |= 1 << 6
            
            command[16] = DAC0 & 0xff
            command[17] |= (DAC0 >> 8) & 0xf
        
        if DAC1Update:
            if DAC1Enabled:
                command[19] = 1 << 7
            command[19] |= 1 << 6
            
            command[18] = DAC1 & 0xff
            command[19] |= (DAC1 >> 8) & 0xf
        
        command[20] = AINMask & 0xff
        command[21] = (AINMask >> 8) & 0xff
        command[22] = AIN14ChannelNumber
        command[23] = AIN15ChannelNumber
        command[24] = Resolution
        command[25] = SettlingTime
        command[26] = AIN1_0_BipGain
        command[27] = AIN3_2_BipGain
        command[28] = AIN5_4_BipGain
        command[29] = AIN7_6_BipGain
        command[30] = AIN9_8_BipGain
        command[31] = AIN11_10_BipGain
        command[32] = AIN13_12_BipGain
        command[33] = AIN15_14_BipGain
        
        result = self._writeRead(command, 64, [ 0xF8, 0x1D, 0x00], checkBytes = False)
        
        returnDict = { 'FIODir' : result[6], 'FIOState' : result[7], 'EIODir' : result[8], 'EIOState' : result[9], 'CIODir' : (result[10] >> 4) & 0xf, 'CIOState' : result[10] & 0xf, 'MIODir' : (result[11] >> 4) & 7, 'MIOState' : result[11] & 7, 'Counter0' : unpackInt(result[44:48]), 'Counter1' : unpackInt(result[48:52]), 'TimerA' : unpackInt(result[52:56]), 'TimerB' : unpackInt(result[56:60]), 'TimerC' : unpackInt(result[60:]) }
        
        """
'AIN0' : b2c(unpackShort(result[12:14])), 'AIN1' : unpackShort(result[14:16]), 'AIN2' : unpackShort(result[16:18]), 'AIN3' : unpackShort(result[18:20]), 'AIN4' : unpackShort(result[20:22]), 'AIN5' : unpackShort(result[22:24]), 'AIN6' : unpackShort(result[24:26]), 'AIN7' : unpackShort(result[26:28]), 'AIN8' : unpackShort(result[28:30]), 'AIN9' : unpackShort(result[30:32]), 'AIN10' : unpackShort(result[32:34]), 'AIN11' : unpackShort(result[34:36]), 'AIN12' : unpackShort(result[36:38]), 'AIN13' : unpackShort(result[38:40]), 'AIN14' : unpackShort(result[40:42]), 'AIN15' : unpackShort(result[42:44]), 
        """
        
        b2c = self.binaryToCalibratedAnalogVoltage
        g = 0
        for i in range(16):
            bits = unpackShort(result[(12+(2*i)):(14+(2*i))])
            if i%2 == 0:
                gain = command[26 + g] & 0xf
            else:
                gain = (command[26 + g] >> 4) & 0xf
                g += 1
            returnDict["AIN%s" % i] = b2c(bits, gain)
        
        return returnDict

    digitalPorts = [ 'FIO', 'EIO', 'CIO', 'MIO' ]
    def singleIO(self, IOType, Channel, Dir = None, BipGain = None, State = None, Resolution = None, DAC = 0, SettlingTime = 0):
        """
        Name: UE9.singleIO(IOType, Channel, Dir = None, BipGain = None, State = None, Resolution = None, DAC = 0, SettlingTime = 0)
        Args: See section 5.3.4 of the User's Guide
        Desc: An alternative to Feedback, is this function which writes or
              reads a single output or input. See section 5.3.4 of the User's
              Guide.
              
        >>> myUe9 = ue9.UE9()
        >>> myUe9.singleIO(1, 0, Dir = 1, State = 0)
        {'FIO0 Direction': 1, 'FIO0 State': 0}
        """
        command = [ 0 ] * 8
        
        #command[0] = Checksum8
        command[1] = 0xA3
        command[2] = IOType
        command[3] = Channel
        
        if IOType == 0:
            #Digital Bit Read
            pass
        elif IOType == 1:
            #Digital Bit Write
            if Dir == None or State == None:
                raise LabJackException("Need to specify a direction and state")
            command[4] = Dir
            command[5] = State
        elif IOType == 2:
            #Digital Port Read
            pass
        elif IOType == 3:
            #Digital Port Write
            if Dir == None or State == None:
                raise LabJackException("Need to specify a direction and state")
            command[4] = Dir
            command[5] = State
        elif IOType == 4:
            #Analog In
            if BipGain == None or Resolution == None or SettlingTime == None:
                raise LabJackException("Need to specify a BipGain, Resolution, and SettlingTime")
            command[4] = BipGain
            command[5] = Resolution
            command[6] = SettlingTime
        elif IOType == 5:
            #Analog Out
            if DAC == None:
                raise LabJackException("Need to specify a DAC Value")
            command[4] = DAC & 0xff
            command[5] = (DAC >> 8) & 0xf
        
        result = self._writeRead(command, 8, [ 0xA3 ], checkBytes = False)
        
        if result[2] == 0:
            #Digital Bit Read
            return { "FIO%s State" % result[3] : result[5], "FIO%s Direction" % result[3] : result[4] }
        elif result[2] == 1:
            #Digital Bit Write
            return { "FIO%s State" % result[3] : result[5], "FIO%s Direction" % result[3] : result[4] }
        elif result[2] == 2:
            #Digital Port Read
            return { "%s Direction" % self.digitalPorts[result[3]] : result[4], "%s State" % self.digitalPorts[result[3]] : result [5] }
        elif result[2] == 3:
            #Digital Port Write
            return { "%s Direction" % self.digitalPorts[result[3]] : result[4], "%s State" % self.digitalPorts[result[3]] : result [5] }
        elif result[2] == 4:
            #Analog In
            ain = float((result[6] << 16) + (result[5] << 8) + result[4]) / 256
            return { "AIN%s" % result[3] : ain }
        elif result[2] == 5:
            #Analog Out
            dac = (result[6] << 16) + (result[5] << 8) + result[4]
            return { "DAC%s" % result[3] : dac }
    
    def timerCounter(self, TimerClockDivisor=0, UpdateConfig=False, NumTimersEnabled=0, Counter0Enabled=False, Counter1Enabled=False, TimerClockBase=LJ_tcSYS, ResetTimer0=False, ResetTimer1=False, ResetTimer2=False, ResetTimer3=False, ResetTimer4=False, ResetTimer5=False, ResetCounter0=False, ResetCounter1=False, Timer0Mode=None, Timer0Value=None, Timer1Mode=None, Timer1Value=None, Timer2Mode=None, Timer2Value=None, Timer3Mode=None, Timer3Value=None, Timer4Mode=None, Timer4Value=None, Timer5Mode=None, Timer5Value=None):
        """
        Name: UE9.timerCounter(TimerClockDivisor=0, UpdateConfig=False,
                               NumTimersEnabled=0, Counter0Enabled=False,
                               Counter1Enabled=True, TimerClockBase=LJ_tcSYS,
                               ResetTimer0=False, ResetTimer1=False,
                               ResetTimer2=False, ResetTimer3=False,
                               ResetTimer4=False, ResetTimer5=False,
                               ResetCounter0=False, ResetCounter1=False,
                               Timer0Mode=None, Timer0Value=None,
                               Timer1Mode=None, Timer1Value=None,
                               Timer2Mode=None, Timer2Value=None,
                               Timer3Mode=None, Timer3Value=None,
                               Timer4Mode=None, Timer4Value=None,
                               Timer5Mode=None, Timer5Value=None)
        
        Args: TimerClockDivisor, The timer clock is divided by this value, or
                                 divided by 256 if this value is 0. The
                                 UpdateConfig bit must be set to change this
                                 parameter.
              UpdateConfig, If true, counters and timers are re-configured by
                            this call. If false, the timer/counter configuration
                            will remain the same.
              NumTimersEnabled, The number of timers enabled
              TimerClockBase, The determines the timer base clock which is used
                              by all output mode timers. The choices are a fixed
                              750 kHz clock source, or the system clock. The UE9
                              is by default in high power mode which means the
                              system clock is fixed at 48 MHz. The UpdateConfig
                              bit must be set to change this parameter.
              ResetTimer#, Resets the specified timer
              ResetCounter#, Resets the specified counter
              Timer#Mode, These values are only updated if the UpdateConfig
                           parameter is True. See section 5.3.5 in the User's
                           Guide for values to pass to configure a timer.
              Timer#Value, Only updates if UpdateReset is True. The meaning of
                           this parameter varies with the timer mode. See
                           Section 2.10 for further information.
        
        Desc: Enables, configures, and reads the counters and timers. See
              section 5.3.5 of the User's Guide for more information.
        >>> dev = UE9()
        >>> dev.timerCounter()
        {'Counter0Enabled': False, 'Timer5Enabled': False, 'Timer0Enabled': False, 'Timer1': 0, 'Timer4': 0, 'Timer3Enabled': False, 'Timer4Enabled': False, 'Timer5': 0, 'Counter1Enabled': False, 'Timer3': 0, 'Timer2': 0, 'Timer1Enabled': False, 'Timer0': 0, 'Timer2Enabled': False}
        """
        command = [ 0 ] * 30

        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x0C
        command[3] = 0x18
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = TimerClockDivisor

        # Create EnableMask
        if UpdateConfig:
            command[7] = 128 | NumTimersEnabled
            if Counter0Enabled: command[7] = command[7] | 8
            if Counter1Enabled: command[7] = command[7] | 16
        else: UpdateConfig = 0

        # Configure clock base
        command[8] = TimerClockBase

        # Configure UpdateReset
        if ResetTimer0: command[9] = 1
        if ResetTimer1: command[9] = command[9] | 2
        if ResetTimer2: command[9] = command[9] | 4
        if ResetTimer3: command[9] = command[9] | 8
        if ResetTimer4: command[9] = command[9] | 16
        if ResetTimer5: command[9] = command[9] | 32
        if ResetCounter0: command[9] = command[9] | 64
        if ResetCounter1: command[9] = command[9] | 128

        # Configure timers and counters if we are updating the configuration
        if UpdateConfig:
            if NumTimersEnabled >= 1:
                if Timer0Mode == None: raise LabJackException("Need to specify a mode for Timer0")
                if Timer0Value == None: raise LabJackException("Need to specify a value for Timer0")
                command[10] = Timer0Mode
                command[11] = Timer0Value & 0xff
                command[12] = (Timer0Value >> 8) & 0xff
            if NumTimersEnabled >= 2:
                if Timer1Mode == None: raise LabJackException("Need to specify a mode for Timer1")
                if Timer1Value == None: raise LabJackException("Need to specify a value for Timer1")
                command[13] = Timer1Mode
                command[14] = Timer1Value & 0xff
                command[15] = (Timer1Value >> 8) & 0xff
            if NumTimersEnabled >= 3:
                if Timer2Mode == None: raise LabJackException("Need to specify a mode for Timer2")
                if Timer2Value == None: raise LabJackException("Need to specify a value for Timer2")
                command[16] = Timer2Mode
                command[17] = Timer2Value & 0xff
                command[18] = (Timer2Value >> 8) & 0xff
            if NumTimersEnabled >= 4:
                if Timer3Mode == None: raise LabJackException("Need to specify a mode for Timer3")
                if Timer3Value == None: raise LabJackException("Need to specify a value for Timer3")
                command[19] = Timer3Mode
                command[20] = Timer3Value & 0xff
                command[21] = (Timer3Value >> 8) & 0xff
            if NumTimersEnabled >= 5:
                if Timer4Mode == None: raise LabJackException("Need to specify a mode for Timer4")
                if Timer4Value == None: raise LabJackException("Need to specify a value for Timer4")
                command[22] = Timer4Mode
                command[23] = Timer4Value & 0xff
                command[24] = (Timer4Value >> 8) & 0xff
            if NumTimersEnabled == 6:
                if Timer5Mode == None: raise LabJackException("Need to specify a mode for Timer5")
                if Timer5Value == None: raise LabJackException("Need to specify a value for Timer5")
                command[25] = Timer5Mode
                command[26] = Timer5Value & 0xff
                command[27] = (Timer5Value >> 8) & 0xff
            if NumTimersEnabled > 7: raise LabJackException("Only a maximum of 5 timers can be enabled")
            command[28] = 0#command[28] = Counter0Mode
            command[29] = 0#command[29] = Counter1Mode

        result = self._writeRead(command, 40, [ 0xF8, 0x11, 0x18 ])

        # Parse the results
        returnValue = {}
        for i in range(0,6):
            returnValue["Timer" + str(i) + "Enabled"] = result[7] >> i & 1 == 1
        for i in range(0,2):
            returnValue["Counter" + str(i) + "Enabled"] = result[7] >> i + 6 & 1 == 1
        for i in range(0, 6):
            returnValue["Timer" + str(i)] = unpackInt(result[8+i*4:12+i*4])
        for i in range(0,2):
            counterValue = [0]
            counterValue.extend(result[32+i*4:35+i*4])
            returnValue["Counter" + str(i)] = unpackInt(counterValue)

        return returnValue

    def readMem(self, BlockNum):
        """
        Name: UE9.readMem(BlockNum)
        Args: BlockNum, which block to read
              ReadCal, set to True to read the calibration data
        Desc: Reads 1 block (128 bytes) from the non-volatile user or 
              calibration memory. Please read section 5.3.10 of the user's
              guide before you do something you may regret.
        
        >>> myUE9 = UE9()
        >>> myUE9.readMem(0)
        [ < userdata stored in block 0 > ]
        
        NOTE: Do not call this function while streaming.
        """
        command = [ 0 ] * 8
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x01
        command[3] = 0x2A
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = 0x00
        command[7] = BlockNum
        
        result = self._writeRead(command, 136, [ 0xF8, 0x41, 0x2A ])
        
        return result[8:]

    def writeMem(self, BlockNum, Data):
        """
        Name: UE9.writeMem(BlockNum, Data, WriteCal=False)
        Args: BlockNum, which block to write
              Data, a list of bytes to write
        Desc: Writes 1 block (128 bytes) from the non-volatile user or 
              calibration memory. Please read section 5.3.11 of the user's
              guide before you do something you may regret.
        
        >>> myUE9 = UE9()
        >>> myUE9.writeMem(0, [ < userdata to be stored in block 0 > ])
        
        NOTE: Do not call this function while streaming.
        """
        if not isinstance(Data, list):
            raise LabJackException("Data must be a list of bytes")
        
        command = [ 0 ] * 136
        
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x41
        command[3] = 0x28
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)
        command[6] = 0x00
        command[7] = BlockNum
        command[8:] = Data

        self._writeRead(command, 8, [0xF8, 0x01, command[3]])

    def eraseMem(self, EraseCal=False):
        """
        Name: UE9.eraseMem(EraseCal=False)
        Args: EraseCal, set to True to erase the calibration memory.
        Desc: The UE9 uses flash memory that must be erased before writing.
              Please read section 5.2.12 of the user's guide before you do
              something you may regret.
        
        >>> myUE9 = UE9()
        >>> myUE9.eraseMem()
        
        NOTE: Do not call this function while streaming.
        """
        command = [ 0 ] * 8
            
        #command[0] = Checksum8
        command[1] = 0xF8
        command[2] = 0x01
        command[3] = 0x29
        #command[4] = Checksum16 (LSB)
        #command[5] = Checksum16 (MSB)

        if EraseCal:
            command[6] = 0x4C
            command[7] = 0x4A
        else:
            command[6] = 0x00
            command[7] = 0x00
        
        self._writeRead(command, 8, [0xF8, 0x01, command[3]])

    def streamClearData(self):
        """
        Name: UE9.streamClearData()
        Args: None
        Desc: Clears the streaming data on the stream USB endpoint or TCP socket
              that was left over from a previous stream.
        Note: Use before and/or after streaming.  Timeout delay can occur occur.
        """
        try:
            for i in range(0, 10):
                res = self.read(192, stream = True)
                if len(res) == 192:
                    if all([ ord(b) == 0 for b in res ]):
                        #stream data cleared (Windows)
                        break
                else:
                    if isinstance(self.handle, UE9TCPHandle):
                        if len(res):
                            #Probably only got 46.  Continue reading.
                            continue
                    #stream data cleared
                    break
        except:
            #probably a timeout, but expected
            pass

    def streamConfig(self, NumChannels = 1, Resolution = 12, SettlingTime = 0, InternalStreamClockFrequency = 0, DivideClockBy256 = False, EnableExternalScanTrigger = False, EnableScanPulseOutput = False, ScanInterval = 1, ChannelNumbers = [0], ChannelOptions = [0], SampleFrequency = None, ScanFrequency = None):
        """
        Name: UE9.streamConfig(NumChannels = 1, Resolution = 12,
                               SettlingTime = 0, InternalStreamClockFrequency = 0,
                               DivideClockBy256 = False, ScanInterval = 1, 
                               EnableExternalScanTrigger = False, EnableScanPulseOutput = False,
                               ChannelNumbers = [0], ChannelOptions = [0],
                               SampleFrequency = None, ScanFrequency = None )
        Args: NumChannels, the number of channels to stream
              Resolution, the resolution of the samples (12 - 16)
              SettlingTime, the settling time to be used 
                            (SettlingTime * 5 microseconds)
              ChannelNumbers, a list of channel numbers to stream
              ChannelOptions, a list of channel options bytes.
                              Option byte values (BipGain):
                                  0 = Unipolar Gain 1, 1 = Unipolar Gain 2,
                                  2 = Unipolar Gain 4, 3 = Unipolar Gain 8,
                                  8 = Bipolar Gain 1
              EnableExternalScanTrigger, enable external scan trigger.  The UE9 
                                         scans the table each time it detects a
                                         falling edge on Counter 1 (slave mode).
              EnableScanPulseOutput, enable scan pulse output.  Counter 1 will
                                     pulse low just before every scan (master 
                                     mode).
              
              Set:
              
              ScanFrequency, the frequency in Hz to scan the channel list (ChannelNumbers).
                             sample rate (Hz) = ScanFrequency * NumChannels
              
              -- OR --
              
              InternalStreamClockFrequency, 0 = 4 MHz, 1 = 48 MHz, 2 = 750 kHz,
                                            3 = 24 MHz
              DivideClockBy256, True = divide the clock by 256
              ScanInterval, clock/ScanInterval = scan frequency.
              
              See Section 5.3.6 of the User's Guide for more details.
              
              Deprecated:
              
              SampleFrequency, the frequency in Hz to sample.  Setting
                               ScanFrequency instead is recommended.
        
        Desc: Configures streaming on the UE9.
        """
        if NumChannels != len(ChannelNumbers) or NumChannels != len(ChannelOptions):
            raise LabJackException("NumChannels must match length of ChannelNumbers and ChannelOptions")
        if len(ChannelNumbers) != len(ChannelOptions):
            raise LabJackException("len(ChannelNumbers) doesn't match len(ChannelOptions)")

        if ScanFrequency != None or SampleFrequency != None:
            if ScanFrequency == None:
                ScanFrequency = SampleFrequency/NumChannels
            
            if ScanFrequency >= 11.5:
                DivideClockBy256 = False
                if ScanFrequency >= 733:
                    InternalStreamClockFrequency = 1
                    ScanInterval = 48000000/ScanFrequency
                elif ScanFrequency >= 367:
                    InternalStreamClockFrequency = 3
                    ScanInterval = 24000000/ScanFrequency
                elif ScanFrequency >= 61.1:
                    InternalStreamClockFrequency = 0
                    ScanInterval = 4000000/ScanFrequency
                else:
                    InternalStreamClockFrequency = 2
                    ScanInterval = 750000/ScanFrequency
            else:
                DivideClockBy256 = True
                if ScanFrequency >= 2.87:
                    InternalStreamClockFrequency = 1
                    ScanInterval = (48000000/256)/ScanFrequency
                elif ScanFrequency >= 1.44:
                    InternalStreamClockFrequency = 3
                    ScanInterval = (24000000/256)/ScanFrequency
                elif ScanFrequency >= 0.239:
                    InternalStreamClockFrequency = 0
                    ScanInterval = (4000000/256)/ScanFrequency
                else:
                    InternalStreamClockFrequency = 2
                    ScanInterval = (750000/256)/ScanFrequency
        
        SamplesPerPacket = 16

        # Force Scan Interval into correct range
        ScanInterval = min( ScanInterval, 65535 )
        ScanInterval = int( ScanInterval )
        ScanInterval = max( ScanInterval, 1 )
        
        # Only want the first 2 bit of data
        InternalStreamClockFrequency = InternalStreamClockFrequency & 3

        command = [ 0 ] * (12 + NumChannels*2)
        command[1] = 0xF8
        command[2] = NumChannels+3
        command[3] = 0x11
        command[6] = NumChannels
        command[7] = Resolution
        command[8] = SettlingTime
        command[9] = InternalStreamClockFrequency << 3
        if DivideClockBy256:
            command[9] |= 0x02
        if EnableExternalScanTrigger:
            command[9] |= 0x40
        if EnableScanPulseOutput:
            command[9] |= 0x80
        t = struct.pack("<H", ScanInterval)
        command[10] = ord(t[0])
        command[11] = ord(t[1])
        for i in range(NumChannels):
            command[12+(i*2)] = ChannelNumbers[i]
            command[13+(i*2)] = ChannelOptions[i]
        
        self._writeRead(command, 8, [0xF8, 0x01, 0x11])
        
        # Set up the variables for future use.
        self.streamSamplesPerPacket = SamplesPerPacket
        self.streamChannelNumbers = ChannelNumbers
        self.streamChannelOptions = ChannelOptions
        self.streamConfiged = True
        
        if InternalStreamClockFrequency == 1:
            freq = float(48000000)
        elif InternalStreamClockFrequency == 2:
            freq = float(750000)
        elif InternalStreamClockFrequency == 3:
            freq = float(24000000)
        else:
            freq = float(4000000)
        
        if DivideClockBy256:
            freq /= 256
        
        freq = freq/ScanInterval
        
        #packetsPerRequest needs to be a multiple of 4 for Linux/Mac OS X USB.
        #For Windows it needs to be under 11.
        if freq < 200:
            self.packetsPerRequest = 4
        else:
            self.packetsPerRequest = 8
        
        if self.ethernet:
            self.streamPacketSize = 46
        else:
            #USB stream packets have an additonal 2 bytes [0, 0] appended to the end
            self.streamPacketSize = 48

    def streamStart(self, clearData=False):
        """
        Name: UE9.streamStart(clearData=False)
        Args: clearData, clears left over stream data over USB or TCP
        Desc: Starts streaming on the UE9.
        Note: You must call streamConfig() before calling this function.
        """
        self.flushBuffer()
        if self.streamStarted == False and clearData == True:
            self.streamClearData()
        Device.streamStart(self)

    def streamData(self, convert=True):
        """
        Name: UE9.streamData(convert=True)
        Args: convert, should the packets be converted as they are read.
                       set to False to get much faster speeds, but you will 
                       have to process the results later.
        Desc: Reads stream data from a UE9. See our stream example to get an
              idea of how this function should be called. The return value of
              streamData is a dictionary with the following keys:
              * errors: The number of errors in this block.
              * numPackets: The number of USB packets collected to return this
                            block.
              * missed: The number of readings that were missed because of
                        buffer overflow on the LabJack.  Not supported on UE9.
              * firstPacket: The PacketCounter value in the first USB packet.
              * result: The raw bytes returned from read(). The only way to get
                        data if called with convert = False.
              * AINi, where i is an entry in the passed in PChannels. If called
                        with convert = True, this is a list of all the readings
                        in this block.
        Note: You must start the stream by calling streamStart() before calling
              this function.
        """
        if not self.streamStarted:
            raise LabJackException("Please start streaming before reading.")
        
        missed = 0 #Not available on UE9
        errors = 0
        newTimeLoop = True #Ethernet only
        resultBuffer = "" #Ethernet only
        numBytes = self.streamPacketSize
        
        while True:
            if self.ethernet and newTimeLoop == True:
                newTimeLoop = False
                startTime = datetime.now()
            
            result = self.read(numBytes * self.packetsPerRequest, stream = True)
            numPackets = len(result) // numBytes
            
            i = 0
            while i < numPackets:
                offset = (i*numBytes)
                #Check for empty data
                if ord(result[1+offset]) == 0:
                    if all([ ord(b) == 0 for b in result[offset:(offset+numBytes)]]):
                        if i+1 >= numPackets:
                            result = result[0:offset]
                        else:
                            result = result[0:offset] + result[offset+numBytes:]
                        numPackets = numPackets - 1
                        continue
                
                e = ord(result[11+offset])
                if e != 0:
                    errors += 1
                    if self.debug: print e
                i+=1
            
            if len(result) == 0  and self.ethernet == False:
                #No data over USB:
                yield None
                continue
            
            if self.ethernet:
                #Buffer new data
                resultBuffer += result
                packetsInBuffer = len(resultBuffer) // numBytes
                
                if packetsInBuffer >= self.packetsPerRequest:
                    #We're done reading data
                    newTimeLoop = True
                    numPackets = self.packetsPerRequest
                    result = resultBuffer[:(numBytes * self.packetsPerRequest)]
                    
                    #Adjust buffered data
                    resultBuffer = resultBuffer[(numBytes * self.packetsPerRequest):]
                else:
                    curTime = datetime.now()
                    timeElapsed = (curTime-startTime).seconds + float((curTime-startTime).microseconds)/1000000
                    if timeElapsed > 1.10:
                        newTimeLoop = True
                        if packetsInBuffer < 4:
                            #Group(s) of 4 packets not available
                            yield None
                            continue
                        else:
                            #Return packets in multiples of 4 like over USB
                            numPackets = (packetsInBuffer // 4) * 4
                            result = retResult[:(numBytes * numPackets)]
                            firstPacket = ord(result[10])
                            
                            #Adjust buffered data
                            resultBuffer = resultBuffer[(numBytes * numPackets):]
                    else:
                        continue
            
            firstPacket = ord(result[10])
            
            returnDict = dict(numPackets = numPackets, result = result, errors = errors, missed = missed, firstPacket = firstPacket)
            if convert:
                returnDict.update(self.processStreamData(result, numBytes = numBytes))
            
            errors = 0  #reset error count
            
            yield returnDict

    def streamStop(self, clearData=True):
        """
        Name: UE9.streamStop(clearData = True)
        Args: clearData, clears left over stream data over USB or TCP
        Desc: Stops streaming on the UE9.
        """
        Device.streamStop(self)
        self.flushBuffer()
        if self.streamStarted == False and clearData == True:
            self.streamClearData()

    def processStreamData(self, result, numBytes=None):
        """
        Name: UE9.processStreamData(result, numBytes = None)
        Args: result, the string returned from streamData()
              numBytes, the number of bytes per packet
        Desc: Breaks stream data into individual channels and applies
              calibrations.
              
        >>> reading = d.streamData(convert = False)
        >>> print proccessStreamData(reading['result'])
        defaultDict(list, {'AIN0' : [3.123, 3.231, 3.232, ...]})
        """
        if numBytes is None:
            numBytes = self.streamPacketSize

        returnDict = collections.defaultdict(list)

        j = self.streamPacketOffset
        for packet in self.breakupPackets(result, numBytes):
            if self.ethernet == False:
                packet = packet[:-2] #remove the extra bytes
            for sample in self.samplesFromPacket(packet):
                if j >= len(self.streamChannelNumbers):
                    j = 0

                if self.streamChannelNumbers[j] in (193, 194):
                    value = struct.unpack('<BB', sample )
                elif self.streamChannelNumbers[j] >= 200:
                    value = struct.unpack('<H', sample )[0]
                else:
                    value = struct.unpack('<H', sample )[0]
                    gain = self.streamChannelOptions[j] & 0x0F
                    value = self.binaryToCalibratedAnalogVoltage(value, gain)

                returnDict["AIN%s" % self.streamChannelNumbers[j]].append(value)
                j += 1

            self.streamPacketOffset = j
        return returnDict

    def watchdogConfig(self, ResetCommonTimeout = False, ResetControlonTimeout = False, UpdateDigitalIOB = False, UpdateDigitalIOA = False, UpdateDAC1onTimeout = False, UpdateDAC0onTimeout = False, TimeoutPeriod = 60, DIOConfigA = 0, DIOConfigB = 0, DAC0Enabled = False, DAC0 = 0, DAC1Enabled = False, DAC1 = 0):
        """
        Name: UE9.watchdogConfig(ResetCommonTimeout = False, ResetControlonTimeout = False,
                                 UpdateDigitalIOB = False, UpdateDigitalIOA = False,
                                 UpdateDAC1onTimeout = False, UpdateDAC0onTimeout = False,
                                 TimeoutPeriod = 60, DIOConfigA = 0,
                                 DIOConfigB = 0, DAC0Enabled = False,
                                 DAC0 = 0, DAC1Enabled = False,
                                 DAC1 = 0):
        Args: See section 5.3.13.1 of the user's guide.
        Desc: Writes the configuration of the watchdog.
        """
        command = [ 0 ] * 16
        
        command[1] = 0xF8
        command[2] = 0x05
        command[3] = 0x09
        
        if ResetCommonTimeout:
            command[7] |= (1 << 6)
        
        if ResetControlonTimeout:
            command[7] |= (1 << 5)
        
        if UpdateDigitalIOB:
            command[7] |= (1 << 4)
        
        if UpdateDigitalIOA:
            command[7] |= (1 << 3)
        
        if UpdateDAC1onTimeout:
            command[7] |= (1 << 1)
        
        if UpdateDAC0onTimeout:
            command[7] |= (1 << 0)
        
        t = struct.pack("<H", TimeoutPeriod)
        command[8] = ord(t[0])
        command[9] = ord(t[1])
        
        command[10] = DIOConfigA
        command[11] = DIOConfigB
        
        command[12] = DAC0 & 0xff
        command[13] = (int(DAC0Enabled) << 7) + ((DAC0 >> 8) & 0xf)
        
        command[14] = DAC1 & 0xff
        command[15] = (int(DAC1Enabled) << 7) + ((DAC1 >> 8) & 0xf)
        
        result = self._writeRead(command, 8, [0xF8, 0x01, 0x09])
        
        return { 'UpdateDAC0onTimeout' : bool(result[7]& 1), 'UpdateDAC1onTimeout' : bool((result[7] >> 1) & 1), 'UpdateDigitalIOAonTimeout' : bool((result[7] >> 3) & 1), 'UpdateDigitalIOBonTimeout' : bool((result[7] >> 4) & 1), 'ResetControlOnTimeout' : bool((result[7] >> 5) & 1), 'ResetCommOnTimeout' : bool((result[7] >> 6) & 1) }

    def watchdogRead(self):
        """
        Name: UE9.watchdogRead()
        Args: None
        Desc: Reads the current watchdog settings.
        """
        command = [ 0 ] * 6
        command[1] = 0xF8
        command[2] = 0x00
        command[3] = 0x09
        
        command = setChecksum8(command, 6)
        
        result = self._writeRead(command, 16, [0xF8, 0x05, 0x09], checksum = False)
        return { 'UpdateDAC0onTimeout' : bool(result[7]& 1), 'UpdateDAC1onTimeout' : bool((result[7] >> 1) & 1), 'UpdateDigitalIOAonTimeout' : bool((result[7] >> 3) & 1), 'UpdateDigitalIOBonTimeout' : bool((result[7] >> 4) & 1), 'ResetControlOnTimeout' : bool((result[7] >> 5) & 1), 'ResetCommOnTimeout' : bool((result[7] >> 6) & 1), 'TimeoutPeriod' : struct.unpack('<H', struct.pack("BB", *result[8:10]))[0], 'DIOConfigA' : result[10], 'DIOConfigB' : result[11], 'DAC0' : struct.unpack('<H', struct.pack("BB", *result[12:14]))[0], 'DAC1' : struct.unpack('<H', struct.pack("BB", *result[14:16]))[0] }

    SPIModes = { 'A' : 0, 'B' : 1, 'C' : 2, 'D' : 3 }
    def spi(self, SPIBytes, AutoCS=True, DisableDirConfig = False, SPIMode = 'A', SPIClockFactor = 0, CSPINNum = 1, CLKPinNum = 0, MISOPinNum = 3, MOSIPinNum = 2):
        """
        Name: UE9.spi(SPIBytes, AutoCS=True, DisableDirConfig = False,
                     SPIMode = 'A', SPIClockFactor = 0, CSPINNum = 1,
                     CLKPinNum = 0, MISOPinNum = 3, MOSIPinNum = 2)
        Args: SPIBytes, a list of bytes to be transferred.
              See Section 5.3.16 of the user's guide.
        Desc: Sends and receives serial data using SPI synchronous
              communication.
        """
        #print SPIBytes
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

    def asynchConfig(self, Update = True, UARTEnable = True, DesiredBaud  = 9600):
        """
        Name: UE9.asynchConfig(Update = True, UARTEnable = True, 
                              DesiredBaud = 9600)
        Args: See section 5.3.17 of the User's Guide.

        Desc: Configures the U3 UART for asynchronous communication. 
        
        returns a dictionary:
        {
            'Update' : True means new parameters were written
            'UARTEnable' : True means the UART is enabled
            'BaudFactor' : The baud factor being used
        }
        """
        
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
        
        BaudFactor = (2**16) - 48000000/(2 * DesiredBaud)
        t = struct.pack("<H", BaudFactor)
        command[8] = ord(t[0])
        command[9] = ord(t[1])
        
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
            
        returnDict['BaudFactor'] = struct.unpack("<H", struct.pack("BB", *result[8:]))[0]

        return returnDict

    def asynchTX(self, AsynchBytes):
        """
        Name: UE9.asynchTX(AsynchBytes)
        Args: AsynchBytes, must be a list of bytes to transfer.
        Desc: Sends bytes to the U3 UART which will be sent asynchronously on
              the transmit line. See section 5.3.18 of the user's guide.
        
        returns a dictionary:
        {
            'NumAsynchBytesSent' : Number of Asynch Bytes Sent
            'NumAsynchBytesInRXBuffer' : How many bytes are currently in the
                                         RX buffer.
        }
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

    def asynchRX(self, Flush = False):
        """
        Name: UE9.asynchRX(Flush = False)
        Args: Flush, Set to True to flush
        Desc: Reads the oldest 32 bytes from the U3 UART RX buffer
              (received on receive terminal). The buffer holds 256 bytes. See
              section 5.3.19 of the User's Guide.

        returns a dictonary:
        {
            'AsynchBytes' : List of received bytes
            'NumAsynchBytesInRXBuffer' : Number of AsynchBytes are in the RX
                                         Buffer.
        }
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

    def i2c(self, Address, I2CBytes, EnableClockStretching = False, NoStopWhenRestarting = False, ResetAtStart = False, SpeedAdjust = 0, SDAPinNum = 1, SCLPinNum = 0, NumI2CBytesToReceive = 0, AddressByte = None):
        """
        Name: UE9.i2c(Address, I2CBytes, ResetAtStart = False, EnableClockStretching = False, SpeedAdjust = 0, SDAPinNum = 0, SCLPinNum = 1, NumI2CBytesToReceive = 0, AddressByte = None)
        Args: Address, the address (not shifted over)
              I2CBytes, must be a list of bytes to send.
              See section 5.3.20 of the user's guide.
              AddressByte, The address as you would put it in the lowlevel
                           packet. Overrides Address. Optional
        Desc: Sends and receives serial data using I2C synchronous
              communication.
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
    
    def sht1x(self, DataPinNum = 0, ClockPinNum = 1, SHTOptions = 0xc0):
        """
        Name: UE9.sht1x(DataPinNum = 0, ClockPinNum = 1, SHTOptions = 0xc0)
        Args: DataPinNum, Which pin is the Data line
              ClockPinNum, Which line is the Clock line
        SHTOptions (and proof people read documentation):
            bit 7 = Read Temperature
            bit 6 = Read Realtive Humidity
            bit 2 = Heater. 1 = on, 0 = off
            bit 1 = Reserved at 0
            bit 0 = Resolution. 1 = 8 bit RH, 12 bit T; 0 = 12 RH, 14 bit T
        Desc: Reads temperature and humidity from a Sensirion SHT1X sensor.
              Section 5.3.21 of the User's Guide.
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

    def getAIN(self, channel, BipGain = 0x00, Resolution = 12, SettlingTime = 0):
        """
        Name: UE9.getAIN(channel, BipGain = 0x00, Resolution = 12,
                         SettlingTime = 0)
        """
        bits = self.singleIO(4, channel, BipGain = BipGain, Resolution = Resolution, SettlingTime = SettlingTime )
        return self.binaryToCalibratedAnalogVoltage(bits["AIN%s"%channel], BipGain, Resolution)

    def getTemperature(self):
        """
        Name: UE9.getTemperature()
        """
        if self.calData is None:
            self.getCalibrationData()
        
        bits = self.singleIO(4, 133, BipGain = 0x00, Resolution = 12, SettlingTime = 0 )
        return self.binaryToCalibratedAnalogTemperature(bits["AIN133"])

    def binaryToCalibratedAnalogVoltage(self, bits, gain, resolution = 0):
        """
        Name: UE9.binaryToCalibratedAnalogVoltage(bits, gain, resolution = 0)
        Args: bits, the binary value to be converted
              gain, the gain used. Please use the values from 5.3.3 of the
                    UE9's user's guide.
              resolution, which resolution did you use?  Set this for UE9-Pro
                          devices to ensure proper conversion.
        Desc: Converts the binary value returned from Feedback and SingleIO
              to a calibrated, analog voltage.
        
        >>> print d.singleIO(4, 1, BipGain = 0x01, Resolution = 12)
        {'AIN1': 65520.0}
        >>> print d.binaryToCalibratedAnalogVoltage(65520.0, 0x01, 12)
        2.52598272
        """
        if self.calData is not None:
            if self.deviceName.endswith("Pro") and resolution > 17:
                slope = self.calData['ProAINSlopes'][str(gain)]
                offset = self.calData['ProAINOffsets'][str(gain)]
            else:
                slope = self.calData['AINSlopes'][str(gain)]
                offset = self.calData['AINOffsets'][str(gain)]
        else:
            #Nornal and hi-res nominal calibration values are the same.
            slope = DEFAULT_CAL_CONSTANTS['AINSlopes'][str(gain)]
            offset = DEFAULT_CAL_CONSTANTS['AINOffsets'][str(gain)]
        
        return (bits * slope) + offset

    def binaryToCalibratedAnalogTemperature(self, bits):
        if self.calData is not None:
            return bits * self.calData['TempSlope']
        else:
            return bits * DEFAULT_CAL_CONSTANTS['TempSlope']

    def voltageToDACBits(self, volts, dacNumber = 0):
        """
        Name: UE9.voltageToDACBits(volts, dacNumber = 0)
        Args: volts, the voltage you would like to set the DAC to.
              dacNumber, 0 or 1, helps apply the correct calibration
        Desc: Takes a voltage, and turns it into the bits needed for setting
              the DAC in commands.
        """
        if self.calData is not None:
            slope = self.calData['DACSlopes'][str(dacNumber)]
            offset = self.calData['DACOffsets'][str(dacNumber)]
        else:
            slope = DEFAULT_CAL_CONSTANTS['DACSlopes'][str(dacNumber)]
            offset = DEFAULT_CAL_CONSTANTS['DACOffsets'][str(dacNumber)]
        
        return int((volts * slope) + offset)

    def getCalibrationData(self):
        """
        Name: UE9.getCalibrationData()
        Args: None
        Desc: Reads the calibration constants off the UE9, and stores them
              for use with binaryToCalibratedAnalogVoltage.
        
        Note: Please note that this function calls controlConfig to check
              if the device is a UE9 or not. It also makes calls to
              readMem, so please don't call this while streaming.
        """
        # Insure that we know if we are dealing with a Pro or not.
        self.controlConfig()
        
        results = dict()
        
        ainslopes = { '0' : None, '1' : None, '2' : None, '3' : None, '8' : None }
        ainoffsets = { '0' : None, '1' : None, '2' : None, '3' : None, '8' : None }
        proainslopes = { '0' : None, '8' : None }
        proainoffsets = { '0' : None, '8' : None }
        dacslopes = { '0' : None, '1' : None }
        dacoffsets = { '0' : None, '1' : None }
        
        tempslope = None
        
        memBlock = self.readMem(0)
        ainslopes['0'] = toDouble(memBlock[:8])
        ainoffsets['0'] = toDouble(memBlock[8:16])
        
        ainslopes['1'] = toDouble(memBlock[16:24])
        ainoffsets['1'] = toDouble(memBlock[24:32])
        
        ainslopes['2'] = toDouble(memBlock[32:40])
        ainoffsets['2'] = toDouble(memBlock[40:48])
        
        ainslopes['3'] = toDouble(memBlock[48:56])
        ainoffsets['3'] = toDouble(memBlock[56:])
        
        memBlock = self.readMem(1)
        ainslopes['8'] = toDouble(memBlock[:8])
        ainoffsets['8'] = toDouble(memBlock[8:16])
        
        # Read DAC and Temperature slopes
        memBlock = self.readMem(2)
        dacslopes['0'] = toDouble(memBlock[:8])
        dacoffsets['0'] = toDouble(memBlock[8:16])
        
        dacslopes['1'] = toDouble(memBlock[16:24])
        dacoffsets['1'] = toDouble(memBlock[24:32])
        
        tempslope = toDouble(memBlock[32:40])
        
        if self.deviceName.endswith("Pro"):
            memBlock = self.readMem(3)
            proainslopes['0'] = toDouble(memBlock[:8])
            proainoffsets['0'] = toDouble(memBlock[8:16])
            
            memBlock = self.readMem(4)
            proainslopes['8'] = toDouble(memBlock[:8])
            proainoffsets['8'] = toDouble(memBlock[8:16])
        
        self.calData = { "AINSlopes" : ainslopes, "AINOffsets" : ainoffsets, "ProAINSlopes" : proainslopes, "ProAINOffsets" : proainoffsets, 'TempSlope' : tempslope, "DACSlopes" : dacslopes, "DACOffsets" : dacoffsets }
        
        return self.calData
    
    def readDefaultsConfig(self):
        """
        Name: UE9.readDefaultsConfig( ) 
        Args: None
        Desc: Reads the power-up defaults stored in flash.
        """
        results = dict()
        defaults = self.readDefaults(0)
        
        results['FIODirection'] = defaults[4]
        results['FIOState'] = defaults[5]
        results['EIODirection'] = defaults[6]
        results['EIOState'] = defaults[7]
        results['CIODirection'] = defaults[8]
        results['CIOState'] = defaults[9]
        results['MIODirection'] = defaults[10]
        results['MIOState'] = defaults[11]
        
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
        
        results['TMR4Mode'] = defaults[0]
        results['TMR4ValueL'] = defaults[1]
        results['TMR4ValueH'] = defaults[2]
        
        results['TMR5Mode'] = defaults[4]
        results['TMR5ValueL'] = defaults[5]
        results['TMR5ValueH'] = defaults[6]
        
        results['DAC0'] = struct.unpack( ">H", struct.pack("BB", *defaults[16:18]) )[0]
        
        results['DAC1'] = struct.unpack( ">H", struct.pack("BB", *defaults[20:22]) )[0]
        
        defaults = self.readDefaults(3)
        
        for i in range(14):
            results["AIN%sRes" % i] = defaults[i]
            results["AIN%sBPGain" % i] = defaults[i+16]
        
        defaults = self.readDefaults(4)
        for i in range(14):
            results["AIN%sSettling" % i] = defaults[i]
        
        return results

    def exportConfig(self):
        """
        Name: UE9.exportConfig( ) 
        Args: None
        Desc: Takes the current configuration and puts it into a ConfigParser
              object. Useful for saving the setup of your UE9.
        """
        # Make a new configuration file
        parser = ConfigParser.SafeConfigParser()
        
        # Change optionxform so that options preserve their case.
        parser.optionxform = str
        
        # Local Id and name
        self.commConfig()
        self.controlConfig()
        
        section = "Identifiers"
        parser.add_section(section)
        parser.set(section, "Local ID", str(self.localId))
        parser.set(section, "Name", str(self.getName()))
        parser.set(section, "Device Type", str(self.devType))
        parser.set(section, "MAC Address", str(self.macAddress))
        
        # Comm Config settings
        section = "Communication"
        parser.add_section(section)
        
        parser.set(section, "DHCPEnabled", str(self.DHCPEnabled))
        parser.set(section, "IP Address", str(self.ipAddress))
        parser.set(section, "Subnet", str(self.subnet))
        parser.set(section, "Gateway", str(self.gateway))
        parser.set(section, "PortA", str(self.portA))
        parser.set(section, "PortB", str(self.portB))
        
        
        # FIO Direction / State
        section = "FIOs"
        parser.add_section(section)
        
        parser.set(section, "FIO Directions", str( self.readRegister(6750) ))
        parser.set(section, "FIO States", str( self.readRegister(6700) ))
        parser.set(section, "EIO Directions", str( self.readRegister(6751) ))
        parser.set(section, "EIO States", str( self.readRegister(6701) ))
        parser.set(section, "CIO Directions", str( self.readRegister(6752) ))
        parser.set(section, "CIO States", str( self.readRegister(6702) ))
        #parser.set(section, "MIOs Directions", str( self.readRegister(50591) ))
        #parser.set(section, "MIOs States", str( self.readRegister(50591) ))
            
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
        
        parser.set(section, "TimerClockBase", str(self.readRegister(7000)))
        parser.set(section, "TimerClockDivisor", str(self.readRegister(7002)))
        
        # Timers / Counters
        section = "Timers And Counters"
        parser.add_section(section)
        
        nte = self.readRegister(50501)
        cm = self.readRegister(50502)
        ec0 = bool( cm & 1 )
        ec1 = bool( (cm >> 1) & 1 )
        
        parser.set(section, "NumberTimersEnabled", str(nte) )
        parser.set(section, "Counter0Enabled", str(ec0) )
        parser.set(section, "Counter1Enabled", str(ec1) )
        
        for i in range(nte):
            mode, value = self.readRegister(7100 + (i*2), numReg = 2, format = ">HH")
            parser.set(section, "Timer%s Mode" % i, str(mode))
            parser.set(section, "Timer%s Value" % i, str(value))
            
        
        
        return parser

    def loadConfig(self, configParserObj):
        """
        Name: UE9.loadConfig( configParserObj ) 
        Args: configParserObj, A Config Parser object to load in
        Desc: Takes a configuration and updates the UE9 to match it.
        """
        parser = configParserObj
        
        # Set Identifiers:
        section = "Identifiers"
        if parser.has_section(section):
            if parser.has_option(section, "device type"):
                if parser.getint(section, "device type") != self.devType:
                    raise Exception("Not a UE9 Config file.")
            
            if parser.has_option(section, "local id"):
                self.commConfig( LocalID = parser.getint(section, "local id"))
                
            if parser.has_option(section, "name"):
                self.setName( parser.get(section, "name") )
        
        # Comm Config settings
        section = "Communication"
        if parser.has_section(section):
            DHCPEnabled = None
            ipAddress = None
            subnet = None
            gateway = None
            portA = None
            portB = None
            
            if parser.has_option(section, "DHCPEnabled"):
                DHCPEnabled = parser.getboolean(section, "DHCPEnabled")
                
            if parser.has_option(section, "ipAddress"):
                ipAddress = parser.get(section, "ipAddress")
                
            if parser.has_option(section, "subnet"):
                subnet = parser.get(section, "subnet")
            
            if parser.has_option(section, "gateway"):
                gateway = parser.get(section, "gateway")
            
            if parser.has_option(section, "portA"):
                portA = parser.getint(section, "portA")
                
            if parser.has_option(section, "portB"):
                portB = parser.getint(section, "portB")
                
            self.commConfig( DHCPEnabled = DHCPEnabled, IPAddress = ipAddress, Subnet = subnet, Gateway = gateway, PortA = portA, PortB = portB )
        
        
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
            
            bitmask = 0xff00
            
            # FIO State/Dir
            self.writeRegister(6700, bitmask + fiostates )
            self.writeRegister(6750, bitmask + fiodirs )
            
            # EIO State/Dir
            self.writeRegister(6701, bitmask + eiostates )
            self.writeRegister(6751, bitmask + eiodirs )
            
            # CIO State/Dir
            self.writeRegister(6702, bitmask + ciostates )
            self.writeRegister(6752, bitmask + ciodirs )
            
                
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
            if parser.has_option(section, "timerclockbase"):
                self.writeRegister(7000, parser.getint(section, "timerclockbase"))
            
            if parser.has_option(section, "timerclockdivisor"):
                self.writeRegister(7002, parser.getint(section, "timerclockbase"))
        
        # Set Timers / Counters
        section = "Timers And Counters"
        if parser.has_section(section):
            nte = 0
            
            if parser.has_option(section, "NumberTimersEnabled"):
                nte = parser.getint(section, "NumberTimersEnabled")
                self.writeRegister(50501, nte)
            
            if parser.has_option(section, "Counter0Enabled"):
                cm = (self.readRegister(50502) & 2) # 0b10
                c0e = parser.getboolean(section, "Counter0Enabled")
                self.writeRegister(50502, cm + int(c0e))
            
            if parser.has_option(section, "Counter1Enabled"):
                cm = (self.readRegister(50502) & 1) # 0b01
                c1e = parser.getboolean(section, "Counter1Enabled")
                self.writeRegister(50502, (int(c1e) << 1) + 1)
            
            
            
            mode = None
            value = None
            
            for i in range(nte):
                if parser.has_option(section, "timer%s mode"):
                    mode = parser.getint(section, "timer%s mode")
                    
                    if parser.has_option(section, "timer%s value"):
                        value = parser.getint(section, "timer%s mode")
                    
                    self.writeRegister(7100 + (i*2), [mode, value])
