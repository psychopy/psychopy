"""
Name: u12.py
Desc: Defines the U12 class, which makes working with a U12 much easier. The 
      functions of the U12 class are divided into two categories: UW and 
      low-level.
      
      Most of the UW functions are exposed as functions of the U12 class. With
      the exception of the "e" functions, UW functions are Windows only. The "e"
      functions will work with both the UW and the Exodriver. Therefore, people
      wishing to write cross-platform code should restrict themselves to using
      only the "e" functions. The UW functions are described in Section 4 of the
      U12 User's Guide:
      
      http://labjack.com/support/u12/users-guide/4
      
      All low-level functions of the U12 class begin with the word
      raw. For example, the low-level function Counter can be called with 
      U12.rawCounter(). Currently, low-level functions are limited to the 
      Exodriver (Linux and Mac OS X). You can find descriptions of the low-level
      functions in Section 5 of the U12 User's Guide:
      
      http://labjack.com/support/u12/users-guide/5
      
"""

import platform
import ctypes
import os, atexit
import math
from time import time
import struct

WINDOWS = "Windows"
ON_WINDOWS = (os.name == 'nt')

class U12Exception(Exception):
    """Custom Exception meant for dealing specifically with U12 Exceptions.

    Error codes are either going to be a LabJackUD error code or a -1.  The -1 implies
    a python wrapper specific error.
    def __init__(self, ec = 0, errorString = ''):
        self.errorCode = ec
        self.errorString = errorString

        if not self.errorString:
            #try:
            self.errorString = getErrorString(ec)
            #except Exception:
            #    self.errorString = str(self.errorCode)
    
    def __str__(self):
          return self.errorString
    
    """
    pass

class BitField(object):
    """
    Provides a method for working with bit fields.
    
    >>> bf = BitField()
    >>> print bf
    [ bit7 = 0, bit6 = 0, bit5 = 0, bit4 = 0, bit3 = 0, bit2 = 0, bit1 = 0, bit0 = 0 ]
    
    You can use attribute accessing for easy bit flipping:
    >>> bf.bit4 = 1
    >>> bf.bit7 = 1
    >>> print bf
    [ bit7 = 1, bit6 = 0, bit5 = 0, bit4 = 1, bit3 = 0, bit2 = 0, bit1 = 0, bit0 = 0 ]
    
    You can also use list-style accessing. Counting starts on the left:
    >>> print bf[0] # List index 0 is bit7
    1
    >>> print bf[3] # List index 3 is bit4
    1
    
    List-style slicing:
    >>> print bf[3:]
    [1, 0, 0, 0, 0]
    
    List-style setting bits works as you would expect:
    >>> bf[1] = 1
    >>> print bf
    [ bit7 = 1, bit6 = 1, bit5 = 0, bit4 = 1, bit3 = 0, bit2 = 0, bit1 = 0, bit0 = 0 ]
    
    It provides methods for going to and from bytes:
    
    >>> bf = BitField(123)
    >>> print bf
    [ bit7 = 0, bit6 = 1, bit5 = 1, bit4 = 1, bit3 = 1, bit2 = 0, bit1 = 1, bit0 = 1 ]
    
    >>> bf = BitField()
    >>> bf.fromByte(123) # Modifies bf in place
    >>> print bf
    [ bit7 = 0, bit6 = 1, bit5 = 1, bit4 = 1, bit3 = 1, bit2 = 0, bit1 = 1, bit0 = 1 ]
    
    >>> bf.bit4 = 0
    >>> print bf.asByte()
    107
    
    You can iterate of the raw bits ( 1 and 0 Vs. '1' and '0') easily:
    >>> for i in bf:
    ...     print i
    0
    1
    1
    0
    1
    0
    1
    1
    
    You can also iterate over the labels and their data values using items():
    >>> for label, data in bf.items():
    ...     print label, data
    bit7 0
    bit6 1
    bit5 1
    bit4 0
    bit3 1
    bit2 0
    bit1 1
    bit0 1
    
    As an added bonus, it can also be cast as an int or hex:
    >>> int(bf)
    107
    
    >>> hex(bf)
    '0x6b'
    
    See the description of the __init__ method for setting the label parameters.    """
    def __init__(self, rawByte = None, labelPrefix = "bit", labelList = None, zeroLabel = "0", oneLabel = "1"):
        """
        Name: BitField.__init__(rawByte = None, labelPrefix = "bit", 
                                labelList = None, zeroLabel = "0",
                                oneLabel = "1")
        Args: rawByte, a value to set the bit field values to.
              labelPrefix, what should go before the labels in labelList
              labelList, a list of labels to apply to each bit. If None, it
                            gets set to range(7,-1,-1).
              zeroLabel, bits with a value of 0 will have this label
              oneLabel, bits with a value of 1 will have this label
        Desc: Creates a new bitfield and sets up the labels.
        
        With out any arguments, you get a bit field that looks like this:
        >>> bf = BitField()
        >>> print bf
        [ bit7 = 0, bit6 = 0, bit5 = 0, bit4 = 0, bit3 = 0, bit2 = 0, bit1 = 0,
        bit0 = 0 ]
        
        To make the labels, it iterates over all the labelList and adds the 
        labelPrefix to them. If you have less than 8 labels, then your bit field
        will only work up to that many bits.
        
        To make a BitField with labels for FIO0-7 you can do the following:
        >>> bf = BitField(labelPrefix = "FIO")
        >>> print bf
        [ FIO7 = 0, FIO6 = 0, FIO5 = 0, FIO4 = 0, FIO3 = 0, FIO2 = 0, FIO1 = 0,
          FIO0 = 0 ]
        
        
        The labels don't have to be numbers, for example:
        >>> names = [ "Goodreau", "Jerri", "Selena", "Allan", "Tania",
                      "Kathrine", "Jessie", "Zelma" ]
        >>> bf = BitField( labelPrefix = "", labelList = names)
        >>> print bf
        [ Goodreau = 0, Jerri = 0, Selena = 0, Allan = 0, Tania = 0,
          Kathrine = 0, Jessie = 0, Zelma = 0 ]
          
        You can change the display value of zero and one to be whatever you 
        want. For example, if you have a BitField that represents FIO0-7 
        directions:
        >>> dirs = BitField(rawByte = 5, labelPrefix = "FIO", 
                              zeroLabel = "Output", oneLabel = "Input")
        >>> print dirs
        [ FIO7 = Output, FIO6 = Output, FIO5 = Output, FIO4 = Output, 
          FIO3 = Output, FIO2 = Input, FIO1 = Output, FIO0 = Input ]
        
        Note, that when you access the value, you will get 1 or 0, not "Input"
        or "Output. For example:
        >>> print dirs.FIO3
        0
        """
        # Do labels first, so that self.something = something works.
        self.__dict__['labels'] = []
        
        self.labelPrefix = labelPrefix
        
        if labelList is None:
            self.labelList = range(8)
        else:
            self.labelList = list(reversed(labelList))
        
        self.zeroLabel = zeroLabel
        self.oneLabel = oneLabel
        
        self.rawValue = 0
        self.rawBits = [ 0 ] * 8
        self.data = [ self.zeroLabel ] * 8
        
        items = min(8, len(self.labelList))
        for i in reversed(range(items)):
            self.labels.append("%s%s" % (self.labelPrefix, self.labelList[i]))
        
        if rawByte is not None:
            self.fromByte(rawByte)
    
    def fromByte(self, raw):
        """
        Name: BitField.fromByte(raw)
        Args: raw, the raw byte to make the BitField.
        Desc: Takes a byte, and modifies self to match.
        
        >>> bf = BitField()
        >>> bf.fromByte(123) # Modifies bf in place
        >>> print bf
        [ bit7 = 0, bit6 = 1, bit5 = 1, bit4 = 1, bit3 = 1, bit2 = 0, bit1 = 1,
          bit0 = 1 ]
        """
        self.rawValue = raw
        self.rawBits = []
        self.data = []
        
        items = min(8, len(self.labelList))
        for i in reversed(range(items)):
            self.rawBits.append( ((raw >> (i)) & 1) )
            self.data.append(self.oneLabel if bool(((raw >> (i)) & 1)) else self.zeroLabel)
    
    def asByte(self):
        """
        Name: BitField.asByte()
        Args: None
        Desc: Returns the value of the bitfield as a byte.
        
        >>> bf = BitField()
        >>> bf.fromByte(123) # Modifies bf in place
        >>> bf.bit4 = 0
        >>> print bf.asByte()
        107
        """
        byteVal = 0
        for i, v in enumerate(reversed(self.rawBits)):
            byteVal += ( 1 << i ) * v
        
        return byteVal
        
    def asBin(self):
        result = "0b"
        for i in self.rawBits:
            result += "%s" % i
        
        return result
    
    def __len__(self):
        return len(self.data)
    
    def __repr__(self):
        result = "["
        for i in range(len(self.data)):
            result += " %s = %s (%s)," % (self.labels[i], self.data[i], self.rawBits[i])
        result = result.rstrip(',')
        result += " ]"
        return "<BitField object: %s >" % result
    
    def __str__(self):
        result = "["
        for i in range(len(self.data)):
            result += " %s = %s," % (self.labels[i], self.data[i])
        result = result.rstrip(',')
        result += " ]"
        return result
        
    def __getattr__(self, label):
        try:
            i = self.labels.index(label)
            return self.rawBits[i]
        except ValueError:
            raise AttributeError(label)
            
    def __setattr__(self, label, value):
        try:
            i = self.labels.index(label)
            self.rawBits[i] = int(bool(value))
            self.data[i] = self.oneLabel if bool(value) else self.zeroLabel
        except ValueError:
            self.__dict__[label] = value
            
    def __getitem__(self, key):
        return self.rawBits[key]
        
    def __setitem__(self, key, value):
        self.rawBits[key] = int(bool(value))
        self.data[key] = self.oneLabel if bool(value) else self.zeroLabel
        
    def __iter__(self):
        return iter(self.rawBits)
        
    def items(self):
        """
        Name: BitField.items()
        Args: None
        Desc: Returns a list of tuples where the first item is the label and the
              second is the string value, like "High" or "Input"
              
        >>> dirs = BitField(rawByte = 5, labelPrefix = "FIO", 
                              zeroLabel = "Output", oneLabel = "Input")
        >>> print dirs
        [ FIO7 = Output, FIO6 = Output, FIO5 = Output, FIO4 = Output, 
          FIO3 = Output, FIO2 = Input, FIO1 = Output, FIO0 = Input ]
        >>> for label, data in dirs.items():
        ...   print label, data
        ... 
        FIO7 Output
        FIO6 Output
        FIO5 Output
        FIO4 Output
        FIO3 Output
        FIO2 Input
        FIO1 Output
        FIO0 Input
        """
        return zip(self.labels, self.data)
    
    def __int__(self):
        return self.asByte()
        
    def __hex__(self):
        return hex(self.asByte())
    
    def __add__(self, other):
        """
        A helper to prevent having to test if a variable is a bitfield or int.
        """
        return other + self.asByte()

def errcheck(ret, func, args):
    if ret == -1:
        try:
            ec = ctypes.get_errno()
            raise U12Exception("Exodriver returned error number %s" % ec)
        except AttributeError:
            raise U12Exception("Exodriver returned an error, but LabJackPython is unable to read the error code. Upgrade to Python 2.6 for this functionality.")
    else:
        return ret

def _loadLinuxSo():
    try:
        l = ctypes.CDLL("liblabjackusb.so", use_errno=True)
    except TypeError:
        l = ctypes.CDLL("liblabjackusb.so")
    l.LJUSB_Stream.errcheck = errcheck
    l.LJUSB_Read.errcheck = errcheck
    return l 

def _loadMacDylib():
    try:
        l = ctypes.CDLL("liblabjackusb.dylib", use_errno=True)
    except TypeError:
        l = ctypes.CDLL("liblabjackusb.dylib")
    l.LJUSB_Stream.errcheck = errcheck
    l.LJUSB_Read.errcheck = errcheck
    return l

staticLib = None
if os.name == 'posix':
        try:
            staticLib = _loadLinuxSo()
        except OSError, e:
            pass # We may be on Mac.
        except Exception, e:
            raise U12Exception("Could not load the Linux SO for some reason other than it not being installed. Ethernet connectivity only.\n\n    The error was: %s" % e)
        
        try:
            if staticLib is None:
                staticLib = _loadMacDylib()
        except OSError, e:
            raise U12Exception("Could not load the Exodriver driver. Ethernet connectivity only.\n\nCheck that the Exodriver is installed, and the permissions are set correctly.\nThe error message was: %s" % e)
        except Exception, e:
            raise U12Exception("Could not load the Mac Dylib for some reason other than it not being installed. Ethernet connectivity only.\n\n    The error was: %s" % e)   
else:
    try:
        staticLib = ctypes.windll.LoadLibrary("ljackuw")
    except Exception:
        raise Exception, "Could not load LabJack UW driver."
    
class U12(object):
    """
    U12 Class for all U12 specific commands.
    
    u12 = U12()
    
    """
    def __init__(self, id = -1, serialNumber = None, debug = False):
        self.id = id
        self.serialNumber = serialNumber
        self.deviceName = "U12"
        self.streaming = False
        self.handle = None
        self.debug = debug
        self._autoCloseSetup = False
        
        if not ON_WINDOWS:
            # Save some variables to save state.
            self.pwmAVoltage = 0
            self.pwmBVoltage = 0
            
            self.open(id, serialNumber)

    def open(self, id = -1, serialNumber = None):
        """
        Opens the U12.
        
        The Windows UW driver opens the device every time a function is called.
        The Exodriver, however, works like the UD family of devices and returns
        a handle. On Windows, this method does nothing. On Mac OS X and Linux,
        this method acquires a device handle and saves it to the U12 object.
        """
        if ON_WINDOWS:
            pass
        else:
            if self.debug: print "open called"
            devType = ctypes.c_ulong(1)
            openDev = staticLib.LJUSB_OpenDevice
            openDev.restype = ctypes.c_void_p
            
            
            if serialNumber is not None:
                numDevices = staticLib.LJUSB_GetDevCount(devType)
                
                for i in range(numDevices):
                    handle = openDev(i+1, 0, devType)
                    
                    if handle != 0 and handle is not None:
                        self.handle = ctypes.c_void_p(handle)
                        
                        try:
                            serial = self.rawReadSerial()
                        except Exception:
                            serial = self.rawReadSerial()
                        
                        if serial == int(serialNumber):
                            break
                        else:
                            self.close()
                    
                if self.handle is None:
                    raise U12Exception("Couldn't find a U12 with a serial number matching %s" % serialNumber)
                
            elif id != -1:
                numDevices = staticLib.LJUSB_GetDevCount(devType)
                
                for i in range(numDevices):
                    handle = openDev(i+1, 0, devType)
                    
                    if handle != 0 and handle is not None:
                        self.handle = ctypes.c_void_p(handle)
                        
                        try:
                            unitId = self.rawReadLocalId()
                        except Exception:
                            unitId = self.rawReadLocalId()
                        
                        if unitId == int(id):
                            break
                        else:
                            self.close()
                            
                if self.handle is None:
                    raise U12Exception("Couldn't find a U12 with a local ID matching %s" % id)
            elif id == -1:
                handle = openDev(1, 0, devType)
                
                if handle == 0 or handle is None:
                    raise Exception("Couldn't open a U12. Check that one is connected and try again.")
                else:
                    self.handle = ctypes.c_void_p(handle)
                    
                    # U12 ignores first command, so let's write a command.
                    command = [ 0 ] * 8
                    command[5] = 0x57 # 0b01010111
                    
                    try:
                        self.write(command)
                        self.read()
                    except Exception:
                        pass

                    self.id = self.rawReadLocalId()
                
            else:
                raise Exception("Invalid combination of parameters.")
            
            
            if not self._autoCloseSetup:
                # Only need to register auto-close once per device.
                atexit.register(self.close)
                self._autoCloseSetup = True
    
    def close(self):
        if ON_WINDOWS:
            pass
        else:
            staticLib.LJUSB_CloseDevice(self.handle)
            self.handle = None

    def write(self, writeBuffer):
        if ON_WINDOWS:
            pass
        else:
            if self.handle is None:
                raise U12Exception("The U12's handle is None. Please open a U12 with open()")
            
            if self.debug: print "Writing:", hexWithoutQuotes(writeBuffer)
            newA = (ctypes.c_byte*len(writeBuffer))(0) 
            for i in range(len(writeBuffer)):
                newA[i] = ctypes.c_byte(writeBuffer[i])
            
            writeBytes = staticLib.LJUSB_Write(self.handle, ctypes.byref(newA), len(writeBuffer))
            
            if(writeBytes != len(writeBuffer)):
                raise U12Exception( "Could only write %s of %s bytes." % (writeBytes, len(writeBuffer) ) )
                
            return writeBuffer
            
    def read(self, numBytes = 8):
        if ON_WINDOWS:
            pass
        else:
            if self.handle is None:
                raise U12Exception("The U12's handle is None. Please open a U12 with open()")
            newA = (ctypes.c_byte*numBytes)()
            readBytes = staticLib.LJUSB_Read(self.handle, ctypes.byref(newA), numBytes)
            # return a list of integers in command/response mode
            result = [(newA[i] & 0xff) for i in range(readBytes)]
            if self.debug: print "Received:", hexWithoutQuotes(result)
            return result


    # Low-level helpers
    def rawReadSerial(self):
        """
        Name: U12.rawReadSerial()
        
        Args: None
        
        Desc: Reads the serial number from internal memory.
        
        Returns: The U12's serial number as an integer.
        
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> print d.rawReadSerial()
        10004XXXX
        """
        results = self.rawReadRAM()
        return struct.unpack(">I", struct.pack("BBBB", results['DataByte3'], results['DataByte2'], results['DataByte1'], results['DataByte0']))[0]
        
    def rawReadLocalId(self):
        """
        Name: U12.rawReadLocalId()
        
        Args: None
        
        Desc: Reads the Local ID from internal memory.
        
        Returns: The U12's Local ID as an integer.
        
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> print d.rawReadLocalId()
        0
        """
        results = self.rawReadRAM(0x08)
        return results['DataByte0']
        

    # Begin Section 5 Functions
    
    def rawAISample(self, channel0PGAMUX = 8, channel1PGAMUX = 9, channel2PGAMUX = 10, channel3PGAMUX = 11, UpdateIO = False, LEDState = True, IO3toIO0States = 0, EchoValue = 0):
        """
        Name: U12.rawAISample(channel0PGAMUX = 8, channel1PGAMUX = 9,
                              channel2PGAMUX = 10, channel3PGAMUX = 11,
                              UpdateIO = False, LEDState = True,
                              IO3toIO0States = 0, EchoValue = 0)
        
        Args: channel0PGAMUX, A byte that contains channel0 information
              channel1PGAMUX, A byte that contains channel1 information
              channel2PGAMUX, A byte that contains channel2 information
              channel3PGAMUX, A byte that contains channel3 information
              IO3toIO0States, A byte that represents the states of IO0 to IO3
              UpdateIO, If true, set IO0 to IO 3 to match IO3toIO0States
              LEDState, Turns the status LED on or off.
              EchoValue, Sometimes, you want what you put in.
        
        Desc: Collects readings from 4 analog inputs. It can also toggle the
              status LED and update the state of the IOs. See Section 5.1 of
              the User's Guide.
              
              By default it will read AI0-3 (single-ended).
              
        Returns: A dictionary with the following keys:
            PGAOvervoltage, A bool representing if the U12 detected overvoltage
            IO3toIO0States, a BitField representing the state of IO0 to IO3
            Channel0-3, the analog voltage for the channel
            EchoValue, a repeat of the value passed in.
            
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> d.rawAISample()
        {
          'IO3toIO0States':
            <BitField object: [ IO3 = Low (0), IO2 = Low (0),
                                IO1 = Low (0), IO0 = Low (0) ] >,
          'Channel0': 1.46484375,
          'Channel1': 1.4501953125,
          'Channel2': 1.4599609375,
          'Channel3': 1.4306640625,
          'PGAOvervoltage': False,
          'EchoValue': 0
        }

        """
        command = [ 0 ] * 8
        
        # Bits 6-4: PGA for 1st Channel
        # Bits 3-0: MUX command for 1st Channel
        command[0] = int(channel0PGAMUX)
        
        tempNum = command[0] & 7 # 7 = 0b111
        channel0Number = tempNum if (command[0] & 0xf) > 7 else tempNum+8
        channel0Gain = (command[0] >> 4) & 7 # 7 = 0b111
        
        command[1] = int(channel1PGAMUX)
        
        tempNum = command[1] & 7 # 7 = 0b111
        channel1Number = tempNum if (command[1] & 0xf) > 7 else tempNum+8
        channel1Gain = (command[1] >> 4) & 7 # 7 = 0b111
        
        command[2] = int(channel2PGAMUX)
        
        tempNum = command[2] & 7 # 7 = 0b111
        channel2Number = tempNum if (command[2] & 0xf) > 7 else tempNum+8
        channel2Gain = (command[2] >> 4) & 7 # 7 = 0b111
        
        command[3] = int(channel3PGAMUX)
        
        tempNum = command[3] & 7 # 7 = 0b111
        channel3Number = tempNum if (command[3] & 0xf) > 7 else tempNum+8
        channel3Gain = (command[3] >> 4) & 7 # 7 = 0b111
        
        # Bit 1: Update IO
        # Bit 0: LED State
        bf = BitField()
        bf.bit1 = int(UpdateIO)
        bf.bit0 = int(LEDState)
        command[4] = int(bf)
        
        # Bit 7-4: 1100 (Command/Response)
        # Bit 3-0: Bits for IO3 through IO0 States
        bf.fromByte(0)
        bf.bit7 = 1
        bf.bit6 = 1
        
        bf.fromByte( int(bf) | int(IO3toIO0States) )
        command[5] = int(bf)
        
        command[7] = EchoValue
        
        self.write(command)
        results = self.read()
        
        bf = BitField()
        
        bf.fromByte(results[0])
        
        if bf.bit7 != 1 or bf.bit6 != 0:
            raise U12Exception("Expected a AIStream response, got %s instead." % results[0])
        
        returnDict = {}
        returnDict['EchoValue'] = results[1]
        returnDict['PGAOvervoltage'] = bool(bf.bit4)
        returnDict['IO3toIO0States'] = BitField(results[0], "IO", range(3, -1, -1), "Low", "High")
        
        channel0 = (results[2] >> 4) & 0xf
        channel1 = (results[2] & 0xf)
        channel2 = (results[5] >> 4) & 0xf
        channel3 = (results[5] & 0xf)
        
        channel0 = (channel0 << 8) + results[3]
        returnDict['Channel0'] = self.bitsToVolts(channel0Number, channel0Gain, channel0)
        
        channel1 = (channel1 << 8) + results[4]
        returnDict['Channel1'] = self.bitsToVolts(channel1Number, channel1Gain, channel1)
        
        channel2 = (channel2 << 8) + results[6]
        returnDict['Channel2'] = self.bitsToVolts(channel2Number, channel2Gain, channel2)
        
        channel3 = (channel3 << 8) + results[7]
        returnDict['Channel3'] = self.bitsToVolts(channel3Number, channel3Gain, channel3)
        
        return returnDict

    def rawDIO(self, D15toD8Directions = 0, D7toD0Directions = 0, D15toD8States = 0, D7toD0States = 0, IO3toIO0DirectionsAndStates = 0, UpdateDigital = False):
        """
        Name: U12.rawDIO(D15toD8Directions = 0, D7toD0Directions = 0,
                         D15toD8States = 0, D7toD0States = 0,
                         IO3toIO0DirectionsAndStates = 0, UpdateDigital = 1)
        
        Args: D15toD8Directions, A byte where 0 = Output, 1 = Input for D15-8
              D7toD0Directions, A byte where 0 = Output, 1 = Input for D7-0
              D15toD8States, A byte where 0 = Low, 1 = High for D15-8
              D7toD0States, A byte where 0 = Low, 1 = High for D7-0
              IO3toIO0DirectionsAndStates, Bits 7-4: Direction, 3-0: State
              UpdateDigital, True if you want to update the IO/D line. False to 
                             False to just read their values.
        
        Desc: This commands reads the direction and state of all the digital
              I/O. See Section 5.2 of the U12 User's Guide.
        
              By default, it just reads the directions and states.
        
        Returns: A dictionary with the following keys:
            D15toD8Directions, a BitField representing the directions of D15-D8
            D7toD0Directions, a BitField representing the directions of D7-D0.
            D15toD8States, a BitField representing the states of D15-D8.
            D7toD0States, a BitField representing the states of D7-D0.
            IO3toIO0States, a BitField representing the states of IO3-IO0.
            D15toD8OutputLatchStates, BitField of output latch states for D15-8
            D7toD0OutputLatchStates, BitField of output latch states for D7-0
        
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> d.rawDIO()
        {
          
          'D15toD8Directions':
            <BitField object: [ D15 = Input (1), D14 = Input (1),
                                D13 = Input (1), D12 = Input (1),
                                D11 = Input (1), D10 = Input (1),
                                D9 = Input (1), D8 = Input (1) ] >,
                                
          'D7toD0Directions':
            <BitField object: [ D7 = Input (1), D6 = Input (1), D5 = Input (1),
                                D4 = Input (1), D3 = Input (1), D2 = Input (1),
                                D1 = Input (1), D0 = Input (1) ] >,
                                
          'D15toD8States':
            <BitField object: [ D15 = Low (0), D14 = Low (0), D13 = Low (0),
                                D12 = Low (0), D11 = Low (0), D10 = Low (0),
                                D9 = Low (0), D8 = Low (0) ] >,
        
          'D7toD0States':
            <BitField object: [ D7 = Low (0), D6 = Low (0), D5 = Low (0),
                                D4 = Low (0), D3 = Low (0), D2 = Low (0),
                                D1 = Low (0), D0 = Low (0) ] >,
        
          'IO3toIO0States':
            <BitField object: [ IO3 = Low (0), IO2 = Low (0), IO1 = Low (0),
                                IO0 = Low (0) ] >,

          'D15toD8OutputLatchStates':
            <BitField object: [ D15 = 0 (0), D14 = 0 (0), D13 = 0 (0),
                                D12 = 0 (0), D11 = 0 (0), D10 = 0 (0),
                                D9 = 0 (0), D8 = 0 (0) ] >,
          
          'D7toD0OutputLatchStates':
            <BitField object: [ D7 = 0 (0), D6 = 0 (0), D5 = 0 (0), D4 = 0 (0),
                                D3 = 0 (0), D2 = 0 (0), D1 = 0 (0),
                                D0 = 0 (0) ] >
        }

        """
        command = [ 0 ] * 8
        
        # Bits for D15 through D8 Direction
        command[0] = int(D15toD8Directions)
        
        # Bits for D7 through D0 Direction ( 0 = Output, 1 = Input)
        command[1] = int(D7toD0Directions)
        
        # Bits for D15 through D8 State ( 0 = Low, 1 = High)
        command[2] = int(D15toD8States)
        
        # Bits for D7 through D0 State ( 0 = Low, 1 = High)
        command[3] = int(D7toD0States)
        
        # Bits 7-4: Bits for IO3 through IO0 Direction
        # Bits 3-0: Bits for IO3 through IO0 State
        command[4] = int(IO3toIO0DirectionsAndStates)
        
        # 01X10111 (DIO)
        command[5] = 0x57 # 0b01010111
        
        # Bit 0: Update Digital
        command[6] = int(bool(UpdateDigital))
        
        #XXXXXXXX
        # command[7] = XXXXXXXX
        
        self.write(command)
        results = self.read()
        
        returnDict = {}
        
        if results[0] != 87:
            raise U12Exception("Expected a DIO response, got %s instead." % results[0])
        
        returnDict['D15toD8States'] = BitField(results[1], "D", range(15, 7, -1), "Low", "High")
        returnDict['D7toD0States'] = BitField(results[2], "D", range(7, -1, -1), "Low", "High")
        
        returnDict['D15toD8Directions'] = BitField(results[4], "D", range(15, 7, -1), "Output", "Input")
        returnDict['D7toD0Directions'] = BitField(results[5], "D", range(7, -1, -1), "Output", "Input")
        
        returnDict['D15toD8OutputLatchStates'] = BitField(results[6], "D", range(15, 7, -1))
        returnDict['D7toD0OutputLatchStates'] = BitField(results[7], "D", range(7, -1, -1))
        
        returnDict['IO3toIO0States'] = BitField((results[3] >> 4), "IO", range(3, -1, -1), "Low", "High")
        
        return returnDict
    
    def rawCounter(self, StrobeEnabled = False, ResetCounter = False):
        """
        Name: U12.rawCounter(StrobeEnabled = False, ResetCounter = False)
        Args: StrobeEnable, set to True to enable strobe.
              ResetCounter, set to True to reset the counter AFTER reading.
        Desc: This command controls and reads the 32-bit counter. See
              Section 5.3 of the User's Guide.
        
        Returns: A dictionary with the following keys:
            D15toD8States, a BitField representing the states of D15-D8.
            D7toD0States, a BitField representing the states of D7-D0.
            IO3toIO0States, a BitField representing the states of IO3-IO0.
            Counter, the value of the counter
        
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> d.rawCounter()
        {
          'D15toD8States':
            <BitField object: [ D15 = Low (0), D14 = Low (0), D13 = Low (0),
                                D12 = Low (0), D11 = Low (0), D10 = Low (0),
                                D9 = Low (0), D8 = Low (0) ] >,
        
          'D7toD0States':
            <BitField object: [ D7 = Low (0), D6 = Low (0), D5 = Low (0),
                                D4 = Low (0), D3 = Low (0), D2 = Low (0),
                                D1 = Low (0), D0 = Low (0) ] >,
        
          'IO3toIO0States':
            <BitField object: [ IO3 = Low (0), IO2 = Low (0), IO1 = Low (0),
                                IO0 = Low (0) ] >,
          
          'Counter': 0
        }


        """
        command = [ 0 ] * 8
        
        bf = BitField()
        bf.bit1 = int(StrobeEnabled)
        bf.bit0 = int(ResetCounter)
        
        command[0] = int(bf)
        
        bf.fromByte(0)
        bf.bit6 = 1
        bf.bit4 = 1
        bf.bit1 = 1
        command[5] = int(bf)
        
        self.write(command)
        results = self.read()
        
        returnDict = {}
        
        if results[0] != command[5]:
            raise U12Exception("Expected a Counter response, got %s instead." % results[0])
        
        returnDict['D15toD8States'] = BitField(results[1], "D", range(15, 7, -1), "Low", "High")
        returnDict['D7toD0States'] = BitField(results[2], "D", range(7, -1, -1), "Low", "High")
        returnDict['IO3toIO0States'] = BitField((results[3] >> 4), "IO", range(3, -1, -1), "Low", "High")
        
        counter = results[7]
        counter += results[6] << 8
        counter += results[5] << 16
        counter += results[4] << 24
        returnDict['Counter'] = counter
        
        return returnDict

    def rawCounterPWMDIO(self, D15toD8Directions = 0, D7toD0Directions = 0, D15toD8States = 0, D7toD0States = 0, IO3toIO0DirectionsAndStates = 0, ResetCounter = False, UpdateDigital = 0, PWMA = 0, PWMB = 0):
        """
        Name: U12.rawCounterPWMDIO( D15toD8Directions = 0, D7toD0Directions = 0,
                                    D15toD8States = 0, D7toD0States = 0,
                                    IO3toIO0DirectionsAndStates = 0,
                                    ResetCounter = False, UpdateDigital = 0,
                                    PWMA = 0, PWMB = 0)
        
        Args: D15toD8Directions, A byte where 0 = Output, 1 = Input for D15-8
              D7toD0Directions, A byte where 0 = Output, 1 = Input for D7-0
              D15toD8States, A byte where 0 = Low, 1 = High for D15-8
              D7toD0States, A byte where 0 = Low, 1 = High for D7-0
              IO3toIO0DirectionsAndStates, Bits 7-4: Direction, 3-0: State
              ResetCounter, If True, reset the counter after reading.
              UpdateDigital, True if you want to update the IO/D line. False to 
                             False to just read their values.
              PWMA, Voltage to set AO0 to output.
              PWMB, Voltage to set AO1 to output.
        
        Desc: This command controls all 20 digital I/O, and the 2 PWM outputs.
              The response provides the state of all I/O and the current count.
              See Section 5.4 of the User's Guide.
              
              By default, sets the AOs to 0 and reads the states and counters.
              
        Returns: A dictionary with the following keys:
            D15toD8States, a BitField representing the states of D15-D8.
            D7toD0States, a BitField representing the states of D7-D0.
            IO3toIO0States, a BitField representing the states of IO3-IO0.
            Counter, the value of the counter
        
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> d.rawCounterPWMDIO()
        {
          'D15toD8States':
            <BitField object: [ D15 = Low (0), D14 = Low (0), D13 = Low (0),
                                D12 = Low (0), D11 = Low (0), D10 = Low (0),
                                D9 = Low (0), D8 = Low (0) ] >,
          
          'D7toD0States':
            <BitField object: [ D7 = Low (0), D6 = Low (0), D5 = Low (0),
                                D4 = Low (0), D3 = Low (0), D2 = Low (0),
                                D1 = Low (0), D0 = Low (0) ] >,
        
          'IO3toIO0States':
            <BitField object: [ IO3 = Low (0), IO2 = Low (0),
                                IO1 = Low (0), IO0 = Low (0) ] >,
          
          'Counter': 0
        }
        """
        command = [ 0 ] * 8
        
        # Bits for D15 through D8 Direction
        command[0] = int(D15toD8Directions)
        
        # Bits for D7 through D0 Direction ( 0 = Output, 1 = Input)
        command[1] = int(D7toD0Directions)
        
        # Bits for D15 through D8 State ( 0 = Low, 1 = High)
        command[2] = int(D15toD8States)
        
        # Bits for D7 through D0 State ( 0 = Low, 1 = High)
        command[3] = int(D7toD0States)
        
        # Bits 7-4: Bits for IO3 through IO0 Direction
        # Bits 3-0: Bits for IO3 through IO0 State
        command[4] = int(IO3toIO0DirectionsAndStates)
        
        bf = BitField()
        bf.bit5 = int(ResetCounter)
        bf.bit4 = int(UpdateDigital)
        
        binPWMA = int((1023 * (float(PWMA)/5.0)))
        binPWMB = int((1023 * (float(PWMB)/5.0)))
        
        bf2 = BitField()
        bf2.fromByte( binPWMA & 3 ) # 3 = 0b11
        bf.bit3 = bf2.bit1
        bf.bit2 = bf2.bit0
        
        bf2.fromByte( binPWMB & 3 ) # 3 = 0b11
        bf.bit1 = bf2.bit1
        bf.bit0 = bf2.bit0
        
        command[5] = int(bf)
        
        command[6] = (binPWMA >> 2) & 0xff
        command[7] = (binPWMB >> 2) & 0xff
        
        self.write(command)
        results = self.read()
        
        returnDict = {}
        
        returnDict['D15toD8States'] = BitField(results[1], "D", range(15, 7, -1), "Low", "High")
        returnDict['D7toD0States'] = BitField(results[2], "D", range(7, -1, -1), "Low", "High")
        returnDict['IO3toIO0States'] = BitField((results[3] >> 4), "IO", range(3, -1, -1), "Low", "High")
        
        counter = results[7]
        counter += results[6] << 8
        counter += results[5] << 16
        counter += results[4] << 24
        returnDict['Counter'] = counter
        
        return returnDict
        
    def rawAIBurst(self, channel0PGAMUX = 8, channel1PGAMUX = 9, channel2PGAMUX = 10, channel3PGAMUX = 11, NumberOfScans = 8, TriggerIONum = 0, TriggerState = 0, UpdateIO = False, LEDState = True, IO3ToIO0States = 0, FeatureReports = False, TriggerOn = False, SampleInterval = 15000):
        """
        Name: U12.rawAIBurst( channel0PGAMUX = 8, channel1PGAMUX = 9,
                              channel2PGAMUX = 10, channel3PGAMUX = 11,
                              NumberOfScans = 8, TriggerIONum = 0,
                              TriggerState = 0, UpdateIO = False,
                              LEDState = True, IO3ToIO0States = 0,
                              FeatureReports = False, TriggerOn = False,
                              SampleInterval = 15000 )
        
        Args: channel0PGAMUX, A byte that contains channel0 information
              channel1PGAMUX, A byte that contains channel1 information
              channel2PGAMUX, A byte that contains channel2 information
              channel3PGAMUX, A byte that contains channel3 information
              NumberOfScans, The number of scans you wish to take. Rounded up
                             to a power of 2.
              TriggerIONum, IO to trigger burst on.
              TriggerState, State to trigger on.
              UpdateIO, True if you want to update the IO/D line. False to 
                        False to just read their values.
              LEDState, Turns the status LED on or off.
              IO3ToIO0States, 4 bits for IO3-0 states
              FeatureReports, Use feature reports, or not.
              TriggerOn, Use trigger to start acquisition.
              SampleInterval, = int(6000000.0/(ScanRate * NumberOfChannels))
                              must be greater than (or equal to) 733.
        
        Desc: After receiving a AIBurst command, the LabJack collects 4
              channels at the specified data rate, and puts data in the buffer.
              This continues until the buffer is full, at which time the
              LabJack starts sending the data to the host. Data is sent to the
              host 1 scan at a time while checking for a command from the host.
              If a command is received the burst operation is canceled and the
              command is executed normally. If the LED is enabled, it blinks at
              4 Hz while waiting for a trigger, is off during acquisition,
              blinks at about 8 Hz during data delivery, and is set on when
              done or stopped. See Section 5.5 of the User's Guide.
              
              This function sends the AIBurst command, then reads all the
              responses. Separating the write and read is not currently
              supported (like in the UW driver).
              
              By default, it does single-ended readings on AI0-4 at 100Hz for 8
              scans.
              
        Returns: A dictionary with the following keys:
            Channel0-3, A list of the readings on the channels
            PGAOvervoltages, A list of the over-voltage flags
            IO3toIO0State, A list of the IO states
            IterationCounters, A list of the values of the iteration counter
            Backlogs, value*256 = number of packets in the backlog.
            BufferOverflowOrChecksumErrors, If True and Backlog = 31,
                                            then a buffer overflow occurred. If
                                            True and Backlog = 0, then Checksum
                                            error occurred.
        
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> d.rawAIBurst()
        {
          'Channel0': [1.484375, 1.513671875, ... , 1.46484375],
          
          'Channel1': [1.455078125, 1.455078125, ... , 1.455078125],
          
          'Channel2': [1.46484375, 1.474609375, ... , 1.46484375],
          
          'Channel3': [1.435546875, 1.42578125, ... , 1.435546875],
          
          'PGAOvervoltages': [False, False, ..., False],
          
          'IO3toIO0States': 
            [<BitField object: [ IO3 = Low (0), IO2 = Low (0), IO1 = Low (0),
                                 IO0 = Low (0) ] >, ... ],
          
          'IterationCounters': [0, 1, 2, 3, 4, 5, 6, 0],
          
          'Backlogs': [0, 0, 0, 0, 0, 0, 0, 0],
          
          'BufferOverflowOrChecksumErrors': [False, False, ... , False]
        }

        
        """
        command = [ 0 ] * 8
        
        # Bits 6-4: PGA for 1st Channel
        # Bits 3-0: MUX command for 1st Channel
        command[0] = int(channel0PGAMUX)
        
        tempNum = command[0] & 7 # 7 = 0b111
        channel0Number = tempNum if (command[0] & 0xf) > 7 else tempNum+8
        channel0Gain = (command[0] >> 4) & 7 # 7 = 0b111
        
        command[1] = int(channel1PGAMUX)
        
        tempNum = command[1] & 7 # 7 = 0b111
        channel1Number = tempNum if (command[1] & 0xf) > 7 else tempNum+8
        channel1Gain = (command[1] >> 4) & 7 # 7 = 0b111
        
        command[2] = int(channel2PGAMUX)
        
        tempNum = command[2] & 7 # 7 = 0b111
        channel2Number = tempNum if (command[2] & 0xf) > 7 else tempNum+8
        channel2Gain = (command[2] >> 4) & 7 # 7 = 0b111
        
        command[3] = int(channel3PGAMUX)
        
        tempNum = command[3] & 7 # 7 = 0b111
        channel3Number = tempNum if (command[3] & 0xf) > 7 else tempNum+8
        channel3Gain = (command[3] >> 4) & 7 # 7 = 0b111

        if NumberOfScans > 1024 or NumberOfScans < 8:
            raise U12Exception("The number of scans must be between 1024 and 8 (inclusive)")
        
        NumScansExponentMod = 10 - int(math.ceil(math.log(NumberOfScans, 2)))
        NumScans = 2 ** (10 - NumScansExponentMod)
        
        bf = BitField( rawByte = (NumScansExponentMod << 5) )
        # bits 4-3: IO to Trigger on
        bf.bit2 = 0
        bf.bit1 = int(bool(UpdateIO))
        bf.bit0 = int(bool(LEDState))
        command[4] = int(bf)
        
        bf2 = BitField(rawByte = int(IO3ToIO0States))
        #Bits 7-4: 1010 (Start Burst)
        bf2.bit7 = 1
        bf2.bit5 = 1
        command[5] = int(bf2)
        
        if SampleInterval < 733:
            raise U12Exception("SampleInterval must be greater than 733.")
        
        bf3 = BitField( rawByte = ((SampleInterval >> 8) & 0xf) )
        bf3.bit7 = int(bool(FeatureReports))
        bf3.bit6 = int(bool(TriggerOn))
        command[6] = int(bf3)
        
        command[7] = SampleInterval & 0xff
        
        self.write(command)
        
        resultsList = []
        for i in range(NumScans):
            resultsList.append(self.read())
            
            
        returnDict = {}
        
        returnDict['BufferOverflowOrChecksumErrors'] = list()
        returnDict['PGAOvervoltages'] = list()
        returnDict['IO3toIO0States'] = list()
        
        returnDict['IterationCounters'] = list()
        returnDict['Backlogs'] = list()

        returnDict['Channel0'] = list()
        
        returnDict['Channel1'] = list()
        
        returnDict['Channel2'] = list()
        
        returnDict['Channel3'] = list()
        
        for results in resultsList:
            bf = BitField(rawByte = results[0])
            
            if bf.bit7 != 1 or bf.bit6 != 0:
                raise U12Exception("Expected a AIBurst response, got %s instead." % results[0])
            
            returnDict['BufferOverflowOrChecksumErrors'].append(bool(bf.bit5))
            returnDict['PGAOvervoltages'].append(bool(bf.bit4))
            returnDict['IO3toIO0States'].append(BitField(results[0], "IO", range(3, -1, -1), "Low", "High"))
            
            returnDict['IterationCounters'].append((results[1] >> 5))
            returnDict['Backlogs'].append(results[1] & 0xf)
            
            channel0 = (results[2] >> 4) & 0xf
            channel1 = (results[2] & 0xf)
            channel2 = (results[5] >> 4) & 0xf
            channel3 = (results[5] & 0xf)
            
            channel0 = (channel0 << 8) + results[3]
            returnDict['Channel0'].append(self.bitsToVolts(channel0Number, channel0Gain, channel0))
            
            channel1 = (channel1 << 8) + results[4]
            returnDict['Channel1'].append(self.bitsToVolts(channel1Number, channel1Gain, channel1))
            
            channel2 = (channel2 << 8) + results[6]
            returnDict['Channel2'].append(self.bitsToVolts(channel2Number, channel2Gain, channel2))
            
            channel3 = (channel3 << 8) + results[7]
            returnDict['Channel3'].append(self.bitsToVolts(channel3Number, channel3Gain, channel3))
            
        return returnDict

        
        
    def rawAIContinuous(self, channel0PGAMUX = 8, channel1PGAMUX = 9, channel2PGAMUX = 10, channel3PGAMUX = 11, FeatureReports = False, CounterRead = False, UpdateIO = False, LEDState = True, IO3ToIO0States = 0, SampleInterval = 15000):
        """
        Currently in development.
        
        The function is mostly implemented, but is currently too slow to be 
        useful.
        """
        command = [ 0 ] * 8
        
        # Bits 6-4: PGA for 1st Channel
        # Bits 3-0: MUX command for 1st Channel
        command[0] = int(channel0PGAMUX)
        
        tempNum = command[0] & 7 # 7 = 0b111
        channel0Number = tempNum if (command[0] & 0xf) > 7 else tempNum+8
        channel0Gain = (command[0] >> 4) & 7 # 7 = 0b111
        
        command[1] = int(channel1PGAMUX)
        
        tempNum = command[1] & 7 # 7 = 0b111
        channel1Number = tempNum if (command[1] & 0xf) > 7 else tempNum+8
        channel1Gain = (command[1] >> 4) & 7 # 7 = 0b111
        
        command[2] = int(channel2PGAMUX)
        
        tempNum = command[2] & 7 # 7 = 0b111
        channel2Number = tempNum if (command[2] & 0xf) > 7 else tempNum+8
        channel2Gain = (command[2] >> 4) & 7 # 7 = 0b111
        
        command[3] = int(channel3PGAMUX)
        
        tempNum = command[3] & 7 # 7 = 0b111
        channel3Number = tempNum if (command[3] & 0xf) > 7 else tempNum+8
        channel3Gain = (command[3] >> 4) & 7 # 7 = 0b111
        
        bf = BitField()
        bf.bit7 = int(bool(FeatureReports))
        bf.bit6 = int(bool(CounterRead))
        bf.bit1 = int(bool(UpdateIO))
        bf.bit0 = int(bool(LEDState))
        
        command[4] = int(bf)
        
        # Bits 7-4: 1001 (Start Continuous)
        bf2 = BitField( rawByte = int(IO3ToIO0States) )
        bf2.bit7 = 1
        bf2.bit4 = 1
        
        command[5] = int(bf2)
        
        command[6] = ( SampleInterval >> 8)
        command[7] = SampleInterval & 0xff
        
        byte0bf = BitField()
        returnDict = dict()
        
        self.write(command)
        while True:
            results = self.read()
            
            byte0bf.fromByte(results[0])
            
            returnDict['Byte0'] = byte0bf
            returnDict['IterationCounter'] = (results[1] >> 5)
            returnDict['Backlog'] = results[1] & 0xf
            
            
            yield returnDict
    
    
    def rawPulseout(self, B1 = 10, C1 = 2, B2 = 10, C2 = 2, D7ToD0PulseSelection = 1, ClearFirst = False, NumberOfPulses = 5):
        """
        Name: U12.rawPulseout( B1 = 10, C1 = 2, B2 = 10, C2 = 2,
                               D7ToD0PulseSelection = 1, ClearFirst = False,
                               NumberOfPulses = 5)
        
        Args: B1, the B component of the first half cycle
              C1, the C component of the first half cycle
              B2, the B component of the second half cycle
              C2, the C component of the second half cycle
              D7ToD0PulseSelection, which D lines to pulse.
              ClearFirst, True = Start Low.
              NumberOfPulses, the number of pulses
        
        Desc: This command creates pulses on any, or all, of D0-D7. The desired
              D lines must be set to output with some other function. See
              Section 5.7 of the User's Guide.
              
              By default, pulses D0 5 times at 400us high, then 400 us low.
        
        Returns: None
        
        Example:
        Have a jumper wire connected from D0 to CNT.
        
        >>> import u12
        >>> d = u12.U12()
        >>> d.rawDIO(D7toD0Directions = 0, UpdateDigital = True)
        >>> d.rawCounter(ResetCounter = True)
        >>> d.rawPulseout(ClearFirst = True)
        >>> print d.rawCounter()
        { 'IO3toIO0States': ... , 
          'Counter': 5, 
          'D7toD0States': ... ,
          'D15toD8States': ...
        }
        """
        command = [ 0 ] * 8
        
        command[0] = B1
        command[1] = C1
        command[2] = B2
        command[3] = C2
        command[4] = int(D7ToD0PulseSelection)
        
        # 01100100 (Pulseout)
        bf = BitField()
        bf.bit6 = 1
        bf.bit5 = 1
        bf.bit2 = 1
        
        command[5] = int(bf)
        
        bf2 = BitField( rawByte = ( NumberOfPulses >> 8 ) )
        bf2.bit7 = int(bool(ClearFirst))
        
        command[6] = int(bf2)
        command[7] = NumberOfPulses & 0xff
        
        self.write(command)
        results = self.read()
        
        if command[5] != results[5]:
            raise U12Exception("Expected Pulseout response, got %s instead." % results[5])
        
        if results[4] != 0:
            errors = BitField(rawByte = command[4], labelPrefix = "D", zeroLabel = "Ok", oneLabel = "Error")
            raise U12Exception("D7-D0 Direction error detected: %s" % errors)
        
        return None
        
    
    def rawReset(self):
        """
        Name: U12.rawReset()
        
        Desc: Sits in an infinite loop until micro watchdog timeout after about
              2 seconds. See Section 5.8 of the User's Guide.
              
              Note: The function will close the device after it has written the 
                    command.
        
        Returns: None
        
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> d.rawReset()
        """
        command = [ 0 ] * 8
        
        # 0b01011111 ( Reset )
        bf = BitField()
        bf.bit6 = 1
        bf.bit4 = 1
        bf.bit3 = 1
        bf.bit2 = 1
        bf.bit1 = 1
        bf.bit0 = 1

        command[5] = int(bf)
        self.write(command)
        self.close()
        
    def rawReenumerate(self):
        """
        Name: U12.rawReenumerate()
        
        Desc: Detaches from the USB, reloads config parameters, and then
              reattaches so the device can be re-enumerated. See Section 5.9 of
              the User's Guide.
              
              Note: The function will close the device after it has written the 
                    command.
        
        Returns: None
        
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> d.rawReenumerate()
        """
        command = [ 0 ] * 8
        
        # 0b01000000 (Re-Enumerate)
        bf = BitField()
        bf.bit6 = 1
        command[5] = int(bf)
        self.write(command)
        self.close()
    
    def rawWatchdog(self, IgnoreCommands = False, D0Active = False, D0State = False, D1Active = False, D1State = False, D8Active = False, D8State = False, ResetOnTimeout = False, WatchdogActive = False, Timeout = 60):
        """
        Name: U12.rawWatchdog( IgnoreCommands = False, D0Active = False,
                               D0State = False, D1Active = False,
                               D1State = False, D8Active = False,
                               D8State = False, ResetOnTimeout = False,
                               WatchdogActive = False, Timeout = 60)
        
        Desc: Sets the settings for the watchdog, or just reads the firmware
              version of the U12. See section 5.10 of the User's Guide.
              
              By defaults, just reads the firmware version.
              
        Returns: A dictionary with the following keys:
            FirmwareVersion, the firmware version of the U12.
        
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> print d.rawWatchdog()
        {'FirmwareVersion': '1.10'}
        """
        command = [ 0 ] * 8
        
        command[0] = int(bool(IgnoreCommands))
        
        bf = BitField()
        bf.bit7 = int(D0Active)
        bf.bit6 = int(D0State)
        bf.bit5 = int(D1Active)
        bf.bit4 = int(D1State)
        bf.bit3 = int(D8Active)
        bf.bit2 = int(D8State)
        bf.bit1 = int(ResetOnTimeout)
        bf.bit0 = int(WatchdogActive)
        
        command[4] = int(bf)
        
        # 01X1X011 (Watchdog)
        bf2 = BitField()
        bf2.bit6 = 1
        bf2.bit4 = 1
        bf2.bit1 = 1
        bf2.bit0 = 1
        command[5] = int(bf2)
        
        # Timeout is increments of 2^16 cycles.
        # 2^16 cycles is about 0.01 seconds.
        binTimeout = int((float(Timeout) / 0.01))
        command[6] = ( binTimeout >> 8 ) & 0xff
        command[7] = binTimeout & 0xff
        
        self.write(command)
        results = self.read()
        
        returnDict = dict()
        
        returnDict['FirmwareVersion'] = "%s.%.2d" % (results[0], results[1])
        
        return returnDict
    
    def rawReadRAM(self, Address = 0):
        """
        Name: U12.rawReadRAM(Address = 0)
        
        Args: Address, the starting address to read from
        
        Desc: Reads 4 bytes out of the U12's internal memory. See section 5.11
              of the User's Guide.
              
              By default, reads the bytes that make up the serial number.
              
        Returns: A dictionary with the following keys:
            DataByte0, the data byte at Address - 0
            DataByte1, the data byte at Address - 1
            DataByte2, the data byte at Address - 2
            DataByte3, the data byte at Address - 3
            
        Example:
        >>> import u12, struct
        >>> d = u12.U12()
        >>> r = d.rawReadRAM()
        >>> print r
        {'DataByte3': 5, 'DataByte2': 246, 'DataByte1': 139, 'DataByte0': 170}
        >>> bytes = [ r['DataByte3'], r['DataByte2'], r['DataByte1'], r['DataByte0'] ]
        >>> print struct.unpack(">I", struct.pack("BBBB", *bytes))[0]
        100043690
        """
        command = [ 0 ] * 8
        
        # 01010000 (Read RAM)
        bf = BitField()
        bf.bit6 = 1
        bf.bit4 = 1
        command[5] = int(bf)
        
        command[6] = (Address >> 8) & 0xff
        command[7] = Address & 0xff
        
        self.write(command)
        results = self.read()
        
        if results[0] != int(bf):
            raise U12Exception("Expected ReadRAM response, got %s" % results[0])
        
        if (results[6] != command[6]) or (results[7] != command[7]):
            receivedAddress = (results[6] << 8) + results[7]
            raise U12Exception("Wanted address %s got address %s" % (Address, receivedAddress))
        
        returnDict = dict()
        
        returnDict['DataByte3'] = results[1]
        returnDict['DataByte2'] = results[2]
        returnDict['DataByte1'] = results[3]
        returnDict['DataByte0'] = results[4]
        
        return returnDict
        
    def rawWriteRAM(self, Data, Address):
        """
        Name: U12.rawWriteRAM(Data, Address)
        
        Args: Data, a list of 4 bytes to write to memory.
              Address, the starting address to write to.
        
        Desc: Writes 4 bytes to the U12's internal memory. See section 5.13 of
              the User's Guide.
              
              No default behavior, you must pass Data and Address.
              
        Returns: A dictionary with the following keys:
            DataByte0, the data byte at Address - 0
            DataByte1, the data byte at Address - 1
            DataByte2, the data byte at Address - 2
            DataByte3, the data byte at Address - 3
        
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> print d.rawWriteRAM([1, 2, 3, 4], 0x200)
        {'DataByte3': 4, 'DataByte2': 3, 'DataByte1': 2, 'DataByte0': 1}
        """
        command = [ 0 ] * 8
        
        if not isinstance(Data, list) or len(Data) > 4:
            raise U12Exception("Data wasn't a list, or was too long.")
        
        Data.reverse()
        
        command[:len(Data)] = Data
        
        # 01010001 (Write RAM)
        bf = BitField()
        bf.bit6 = 1
        bf.bit4 = 1
        bf.bit0 = 1
        command[5] = int(bf)
        
        command[6] = (Address >> 8) & 0xff
        command[7] = Address & 0xff
        
        self.write(command)
        results = self.read()
         
        if results[0] != int(bf):
            raise U12Exception("Expected ReadRAM response, got %s" % results[0])
        
        if (results[6] != command[6]) or (results[7] != command[7]):
            receivedAddress = (results[6] << 8) + results[7]
            raise U12Exception("Wanted address %s got address %s" % (Address, receivedAddress))
         
        returnDict = dict()
        
        returnDict['DataByte3'] = results[1]
        returnDict['DataByte2'] = results[2]
        returnDict['DataByte1'] = results[3]
        returnDict['DataByte0'] = results[4]
        
        return returnDict
        
    def rawAsynch(self, Data, AddDelay = False, TimeoutActive = False, SetTransmitEnable = False, PortB = False, NumberOfBytesToWrite = 0, NumberOfBytesToRead = 0):
        """
        Name: U12.rawAsynch(Data, AddDelay = False, TimeoutActive = False,
                            SetTransmitEnable = False, PortB = False,
                            NumberOfBytesToWrite = 0, NumberOfBytesToRead = 0)
                            
        Args: Data, A list of bytes to write.
              AddDelay, True to add a 1 bit delay between each transmit byte.
              TimeoutActive, True to enable timeout for the receive phase.
              SetTransmitEnable, True to set Transmit Enable to high during
                                 transmit and low during receive.
              PortB, True to use PortB instead of PortA.
              NumberOfBytesToWrite, Number of bytes to write.
              NumberOfBytesToRead, Number of bytes to read.
        
        Desc: Requires firmware V1.1 or higher. This function writes and then
              reads half-duplex asynchronous data on 1 of two pairs of D lines.
              See section 5.13 of the User's Guide.
              
        Returns: A dictionary with the following keys,
            DataByte0-3, the first four data bytes read over the RX line
            ErrorFlags, a BitField representing the error flags.
        
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> # Set the full and half A,B,C to 9600
        >>> d.rawWriteRAM([0, 1, 1, 200], 0x073)
        >>> d.rawWriteRAM([5, 1, 2, 48], 0x076)
        >>> print d.rawAsynch([1, 2, 3, 4], NumberOfBytesToWrite = 4, NumberOfBytesToRead = 4)
        {
         'DataByte3': 4,
         'DataByte2': 3,
         'DataByte1': 2,
         'DataByte0': 1,
         'ErrorFlags': <BitField object: [ Timeout Error Flag = 0 (0), ... ] >
        }
        
        """
        command = [ 0 ] * 8
        
        if not isinstance(Data, list) or len(Data) > 4:
            raise U12Exception("Data wasn't a list, or was too long.")
        
        NumberOfBytesToWrite = NumberOfBytesToRead & 0xff
        NumberOfBytesToRead = NumberOfBytesToRead & 0xff
        if NumberOfBytesToWrite > 18:
            raise U12Exception("Can only write 18 or fewer bytes at a time.")
        if NumberOfBytesToRead > 18:
            raise U12Exception("Can only read 18 or fewer bytes at a time.")
        
        Data.reverse()
        
        command[:len(Data)] = Data
        
        bf = BitField()
        bf.bit3 = int(bool(AddDelay))
        bf.bit2 = int(bool(TimeoutActive))
        bf.bit1 = int(bool(SetTransmitEnable))
        bf.bit0 = int(bool(PortB))
        
        command[4] = int(bf)
        
        #01100001 (Asynch)
        bf2 = BitField()
        bf2.bit6 = 1
        bf2.bit5 = 1
        bf2.bit0 = 1
        
        command[5] = int(bf2)
        command[6] = NumberOfBytesToWrite
        command[7] = NumberOfBytesToRead
        
        self.write(command)
        results = self.read()
        
        if command[5] != results[5]:
            raise U12Exception("Expected Asynch response, got %s instead." % results[5])
        
        returnDict = dict()
        returnDict['DataByte3'] = results[0]
        returnDict['DataByte2'] = results[1]
        returnDict['DataByte1'] = results[2]
        returnDict['DataByte0'] = results[3]
        
        bfLabels = ["Timeout Error Flag", "STRT Error Flag", "FRM Error Flag", "RXTris Error Flag", "TETris Error Flag", "TXTris Error Flag"]
        bf = BitField( rawByte = results[4], labelPrefix = "", labelList = bfLabels )
        
        returnDict["ErrorFlags"] = bf
        
        return returnDict
        
    SPIModes = ['A', 'B', 'C', 'D']
    def rawSPI(self, Data, AddMsDelay = False, AddHundredUsDelay = False, SPIMode = 'A', NumberOfBytesToWriteRead = 0, ControlCS = False, StateOfActiveCS = False, CSLineNumber = 0):
        """
        Name: U12.rawSPI( Data, AddMsDelay = False, AddHundredUsDelay = False,
                          SPIMode = 'A', NumberOfBytesToWriteRead = 0,
                          ControlCS = False, StateOfActiveCS = False,
                          CSLineNumber = 0)
        
        Args: Data, A list of four bytes to write using SPI
              AddMsDelay, If True, a 1 ms delay is added between each bit
              AddHundredUsDelay, if True, 100us delay is added
              SPIMode, 'A', 'B', 'C', or 'D'
              NumberOfBytesToWriteRead, number of bytes to write and read.
              ControlCS, D0-D7 is automatically controlled as CS. The state and
                         direction of CS is only tested if control is enabled.
              StateOfActiveCS, Active state for CS line.
              CSLineNumber, D line to use as CS if enabled (0-7).
        
        Desc: This function performs SPI communication. See Section 5.14 of the
              User's Guide.
              
        Returns: A dictionary with the following keys,
            DataByte0-3, the first four data bytes read
            ErrorFlags, a BitField representing the error flags.
            
        Example:
        >>> import u12
        >>> d = u12.U12()
        >>> d.rawSPI([1,2,3,4], NumberOfBytesToWriteRead = 4)
        {
         'DataByte3': 4,
         'DataByte2': 3,
         'DataByte1': 2,
         'DataByte0': 1,
         'ErrorFlags':
          <BitField object: [ CSStateTris Error Flag = 0 (0), ... ] >
        }
        
        """
        command = [ 0 ] * 8
        
        if not isinstance(Data, list) or len(Data) > 4:
            raise U12Exception("Data wasn't a list, or was too long.")
        
        NumberOfBytesToWriteRead = NumberOfBytesToWriteRead & 0xff
        
        if NumberOfBytesToWriteRead == 0:
            NumberOfBytesToWriteRead = len(Data)
            
        if NumberOfBytesToWriteRead > 18 or NumberOfBytesToWriteRead < 1:
            raise U12Exception("Can only read/write 1 to 18 bytes at a time.")
        
        Data.reverse()
        command[:len(Data)] = Data
        
        bf = BitField()
        bf.bit7 = int(bool(AddMsDelay))
        bf.bit6 = int(bool(AddHundredUsDelay))
        
        modeIndex = self.SPIModes.index(SPIMode)
        bf[7-modeIndex] = 1
        
        command[4] = int(bf)
        
        # 01100010 (SPI)
        bf2 = BitField()
        bf2.bit6 = 1
        bf2.bit5 = 1
        bf2.bit1 = 1
        
        command[5] = int(bf2)
        command[6] = NumberOfBytesToWriteRead
        
        bf3 = BitField(rawByte = CSLineNumber)
        bf3.bit7 = int(bool(ControlCS))
        bf3.bit6 = int(bool(StateOfActiveCS))
        
        command[7] = int(bf3)
        
        self.write(command)
        results = self.read()
        
        if results[5] != command[5]:
            raise U12Exception("Expected SPI response, got %s instead." % results[5])
        
        returnDict = dict()
        returnDict['DataByte3'] = results[0]
        returnDict['DataByte2'] = results[1]
        returnDict['DataByte1'] = results[2]
        returnDict['DataByte0'] = results[3]
        
        bfLabels = ["CSStateTris Error Flag", "SCKTris Error Flag", "MISOTris Error Flag", "MOSITris Error Flag"]
        bf = BitField( rawByte = results[4], labelPrefix = "", labelList = bfLabels )
        
        returnDict["ErrorFlags"] = bf
        
        return returnDict
        
    def rawSHT1X(self, Data = [3,0,0,0], WaitForMeasurementReady = True, IssueSerialReset = False, Add1MsDelay = False, Add300UsDelay = False, IO3State = 1, IO2State = 1, IO3Direction = 1, IO2Direction = 1, NumberOfBytesToWrite = 1, NumberOfBytesToRead = 3):
        """
        Name: U12.rawSHT1X( Data = [3, 0, 0, 0],
                            WaitForMeasurementReady = True,
                            IssueSerialReset = False, Add1MsDelay = False,
                            Add300UsDelay = False, IO3State = 1, IO2State = 1,
                            IO3Direction = 1, IO2Direction = 1,
                            NumberOfBytesToWrite = 1, NumberOfBytesToRead = 3)
        
        Args: Data, a list of bytes to write to the SHT.
              WaitForMeasurementReady, Wait for the measurement ready signal.
              IssueSerialReset, perform a serial reset
              Add1MsDelay, adds 1ms delay
              Add300UsDelay, adds a 300us delay
              IO3State, sets the state of IO3
              IO2State, sets the state of IO2
              IO3Direction, sets the direction of IO3 ( 1 = Output )
              IO2Direction, sets the direction of IO3 ( 1 = Output )
              NumberOfBytesToWrite, how many bytes to write
              NumberOfBytesToRead, how may bytes to read back
              
        Desc: Sends and receives data from a SHT1X T/RH sensor from Sensirion.
              See Section 5.15 of the User's Guide.
              
              By default, reads the temperature from the SHT.
              
        Returns: A dictionary with the following keys,
            DataByte0-3, the four data bytes read
            ErrorFlags, a BitField representing the error flags.
        
        Example:
        Uses an EI-1050 Temp/Humidity probe wired as follows:
        Data ( Green ) -> IO0
        Clock ( White ) -> IO1
        Ground ( Black ) -> GND
        Power ( Red ) -> +5V
        Enable ( Brown ) -> IO2
        
        >>> import u12
        >>> d = u12.U12()
        >>> results = d.rawSHT1X()
        >>> print results
        {
         'DataByte3': 0,
         'DataByte2': 69,
         'DataByte1': 48,
         'DataByte0': 25,
         'ErrorFlags':
          <BitField object: [ Serial Reset Error Flag = 0 (0), ... ] >
        }
        >>> tempC = (results['DataByte0'] * 256 ) + results['DataByte1']
        >>> tempC = (tempC * 0.01) - 40
        >>> print tempC
        24.48
        >>> results = d.rawSHT1X(Data = [5,0,0,0])
        >>> print results
        {
         'DataByte3': 0,
         'DataByte2': 200,
         'DataByte1': 90,
         'DataByte0': 2,
         'ErrorFlags':
          <BitField object: [ Serial Reset Error Flag = 0 (0), ... ] >
        }
        >>> sorh = (results['DataByte0'] * 256 ) + results['DataByte1']
        >>> rhlinear = (-0.0000028*sorh*sorh)+(0.0405*sorh)-4.0
        >>> rh = ((tempC-25.0)*(0.01+(0.00008*sorh)))+rhlinear
        >>> print rh
        19.3360256
        """
        command = [ 0 ] * 8
        
        if NumberOfBytesToWrite != 0:
            if not isinstance(Data, list) or len(Data) > 4:
                raise U12Exception("Data wasn't a list, or was too long.")
                
            Data.reverse()
            command[:len(Data)] = Data
        
        if max(NumberOfBytesToWrite, NumberOfBytesToRead) > 4:
            raise U12Exception("Can only read/write up to 4 bytes at a time.")
            
        bf = BitField()
        bf.bit7 = int(bool(WaitForMeasurementReady))
        bf.bit6 = int(bool(IssueSerialReset))
        bf.bit5 = int(bool(Add1MsDelay))
        bf.bit4 = int(bool(Add300UsDelay))
        bf.bit3 = int(bool(IO3State))
        bf.bit2 = int(bool(IO2State))
        bf.bit1 = int(bool(IO3Direction))
        bf.bit0 = int(bool(IO2Direction))
        
        command[4] = int(bf)
        
        # 01101000 (SHT1X)
        bf2 = BitField()
        bf2.bit6 = 1
        bf2.bit5 = 1
        bf2.bit3 = 1
        command[5] = int(bf2)
        
        command[6] = NumberOfBytesToWrite
        command[7] = NumberOfBytesToRead
        
        self.write(command)
        results = self.read()
        
        if results[5] != command[5]:
            raise U12Exception("Expected SHT1x response, got %s instead." % results[5])
        
        returnDict = dict()
        returnDict['DataByte3'] = results[0]
        returnDict['DataByte2'] = results[1]
        returnDict['DataByte1'] = results[2]
        returnDict['DataByte0'] = results[3]
        
        bfLabels = ["Serial Reset Error Flag", "Measurement Ready Error Flag", "Ack Error Flag"]
        bf = BitField( rawByte = results[4], labelPrefix = "", labelList = bfLabels )
        
        returnDict["ErrorFlags"] = bf
        
        return returnDict

    def eAnalogIn(self, channel, idNum = None, demo=0, gain=0):
        """
        Name: U12.eAnalogIn(channel, idNum = None, demo=0, gain=0)
        Args: See section 4.1 of the User's Guide
        Desc: This is a simplified version of AISample. Reads the voltage from 1 analog input

        >>> import u12
        >>> d = u12.U12()
        >>> d.eAnalogIn(0)
        {'overVoltage': 0, 'idnum': 1, 'voltage': 1.435546875}
        """
        if idNum is None:
            idNum = self.id
        
        if ON_WINDOWS:
            ljid = ctypes.c_long(idNum)
            ad0 = ctypes.c_long(999)
            ad1 = ctypes.c_float(999)
    
            ecode = staticLib.EAnalogIn(ctypes.byref(ljid), demo, channel, gain, ctypes.byref(ad0), ctypes.byref(ad1))
    
            if ecode != 0: raise U12Exception(ecode)
    
            return {"idnum":ljid.value, "overVoltage":ad0.value, "voltage":ad1.value}
        else:
            # Bits 6-4: PGA for 1st Channel
            # Bits 3-0: MUX command for 1st Channel
            channel0PGAMUX = ( ( gain & 7 ) << 4)
            channel0PGAMUX += channel-8 if channel > 7 else channel+8

            results = self.rawAISample(channel0PGAMUX = channel0PGAMUX)
            
            return {"idnum" : self.id, "overVoltage" : int(results['PGAOvervoltage']), 'voltage' : results['Channel0']}

    def eAnalogOut(self, analogOut0, analogOut1, idNum = None, demo=0):
        """
        Name: U12.eAnalogOut(analogOut0, analogOut1, idNum = None, demo=0)
        Args: See section 4.2 of the User's Guide
        Desc: This is a simplified version of AOUpdate. Sets the voltage of both analog outputs.

        >>> import u12
        >>> d = u12.U12()
        >>> d.eAnalogOut(2, 2)
        {'idnum': 1}
        """
        if idNum is None:
            idNum = self.id
        
        if ON_WINDOWS:
            ljid = ctypes.c_long(idNum)
            ecode = staticLib.EAnalogOut(ctypes.byref(ljid), demo, ctypes.c_float(analogOut0), ctypes.c_float(analogOut1))
    
            if ecode != 0: raise U12Exception(ecode)
    
            return {"idnum":ljid.value}
        else:
            if analogOut0 < 0:
                analogOut0 = self.pwmAVoltage
            
            if analogOut1 < 0:
                analogOut1 = self.pwmBVoltage
            
            self.rawCounterPWMDIO(PWMA = analogOut0, PWMB = analogOut1)
            
            self.pwmAVoltage = analogOut0
            self.pwmBVoltage = analogOut1
            
            return {"idnum": self.id}

    def eCount(self, idNum = None, demo = 0, resetCounter = 0):
        """
        Name: U12.eCount(idNum = None, demo = 0, resetCounter = 0)
        Args: See section 4.3 of the User's Guide
        Desc: This is a simplified version of Counter. Reads & resets the counter (CNT).

        >>> import u12
        >>> d = u12.U12()
        >>> d.eCount()
        {'count': 1383596032.0, 'ms': 251487257.0}
        """

        # Check id num
        if idNum is None:
            idNum = self.id
        
        if ON_WINDOWS:
            ljid = ctypes.c_long(idNum)
            count = ctypes.c_double()
            ms = ctypes.c_double()
    
            ecode = staticLib.ECount(ctypes.byref(ljid), demo, resetCounter, ctypes.byref(count), ctypes.byref(ms))
    
            if ecode != 0: raise U12Exception(ecode)
    
            return {"idnum":ljid.value, "count":count.value, "ms":ms.value}
        else:
            results = self.rawCounter( ResetCounter = resetCounter)
            
            return {"idnum":self.id, "count":results['Counter'], "ms": (time() * 1000)}
            

    def eDigitalIn(self, channel, idNum = None, demo = 0, readD=0):
        """
        Name: U12.eDigitalIn(channel, idNum = None, demo = 0, readD=0)
        Args: See section 4.4 of the User's Guide
        Desc: This is a simplified version of DigitalIO that reads the state of
              one digital input. Also configures the requested pin to input and
              leaves it that way.

        >>> import u12
        >>> d = u12.U12()
        >>> d.eDigitalIn(0)
        {'state': 0, 'idnum': 1}
        """

        # Check id num
        if idNum is None:
            idNum = self.id
        
        if ON_WINDOWS:
            ljid = ctypes.c_long(idNum)
            state = ctypes.c_long(999)
            
            ecode = staticLib.EDigitalIn(ctypes.byref(ljid), demo, channel, readD, ctypes.byref(state))
            
            if ecode != 0: raise U12Exception(ecode)
            
            return {"idnum":ljid.value, "state":state.value}
        else:
            oldstate = self.rawDIO()
            
            if readD:
                if channel > 7:
                    channel = channel-8
                    direction = BitField(rawByte = int(oldstate['D15toD8Directions']))
                    direction[7-channel] = 1
                    
                    results = self.rawDIO(D15toD8Directions = direction, UpdateDigital = True)
                    
                    state = results['D15toD8States'][7-channel]
                    
                else:
                    direction = BitField(rawByte = int(oldstate['D7toD0Directions']))
                    direction[7-channel] = 1
                    results = self.rawDIO(D7toD0Directions = direction, UpdateDigital = True)
                    
                    state = results['D7toD0States'][7-channel]
            else:
                results = self.rawDIO(IO3toIO0DirectionsAndStates = 255, UpdateDigital = True)
                state = results['IO3toIO0States'][3-channel]
            
            return {"idnum" : self.id, "state" : state}

    def eDigitalOut(self, channel, state, idNum = None, demo = 0, writeD=0):
        """
        Name: U12.eDigitalOut(channel, state, idNum = None, demo = 0, writeD=0)
        Args: See section 4.5 of the User's Guide
        Desc: This is a simplified version of DigitalIO that sets/clears the
              state of one digital output. Also configures the requested pin to
              output and leaves it that way.

        >>> import u12
        >>> d = u12.U12()
        >>> d.eDigitalOut(0, 1)
        {idnum': 1}
        """

        # Check id num
        if idNum is None:
            idNum = self.id
        
        if ON_WINDOWS:
            ljid = ctypes.c_long(idNum)
            
            ecode = staticLib.EDigitalOut(ctypes.byref(ljid), demo, channel, writeD, state)
    
            if ecode != 0: raise U12Exception(ecode)
    
            return {"idnum":ljid.value}
        else:
            oldstate = self.rawDIO()
            
            if writeD:
                if channel > 7:
                    channel = channel-8
                    direction = BitField(rawByte = int(oldstate['D15toD8Directions']))
                    direction[7-channel] = 0
                    
                    states = BitField(rawByte = int(oldstate['D15toD8States']))
                    states[7-channel] = state
                    
                    self.rawDIO(D15toD8Directions = direction, D15toD8States = states, UpdateDigital = True)
                    
                else:
                    direction = BitField(rawByte = int(oldstate['D7toD0Directions']))
                    direction[7-channel] = 0
                    
                    states = BitField(rawByte = int(oldstate['D7toD0States']))
                    states[7-channel] = state
                    
                    self.rawDIO(D7toD0Directions = direction, D7toD0States = states, UpdateDigital = True)
                    
            else:
                bf = BitField()
                bf[7-(channel+4)] = 0
                bf[7-channel] = state
                self.rawDIO(IO3toIO0DirectionsAndStates = bf, UpdateDigital = True)
            
            return {"idnum" : self.id}

    def aiSample(self, numChannels, channels, idNum=None, demo=0, stateIOin=0, updateIO=0, ledOn=0, gains=[0, 0, 0, 0], disableCal=0):
        """
        Name: U12.aiSample(channels, idNum=None, demo=0, stateIOin=0, updateIO=0, ledOn=0, gains=[0, 0, 0, 0], disableCal=0)
        Args: See section 4.6 of the User's Guide
        Desc: Reads the voltages from 1,2, or 4 analog inputs. Also controls/reads the 4 IO ports.

        >>> dev = U12()
        >>> dev.aiSample(2, [0, 1])
        {'stateIO': [0, 0, 0, 0], 'overVoltage': 0, 'idnum': 1, 'voltages': [1.4208984375, 1.4306640625]}
        """
        
        # Check id num
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        # Check to make sure that everything is checked
        if not isIterable(channels): raise TypeError("channels must be iterable")
        if not isIterable(gains): raise TypeError("gains must be iterable")
        if len(channels) < numChannels: raise ValueError("channels must have atleast numChannels elements")
        if len(gains) < numChannels: raise ValueError("gains must have atleast numChannels elements")
        
        # Convert lists to arrays and create other ctypes
        channelsArray = listToCArray(channels, ctypes.c_long)
        gainsArray = listToCArray(gains, ctypes.c_long)
        overVoltage = ctypes.c_long(999)
        longArrayType = (ctypes.c_long * 4)
        floatArrayType = (ctypes.c_float * 4)
        voltages = floatArrayType(0, 0, 0, 0)
        stateIOin = ctypes.c_long(stateIOin)
        
        ecode = staticLib.AISample(ctypes.byref(idNum), demo, ctypes.byref(stateIOin), updateIO, ledOn, numChannels, ctypes.byref(channelsArray), ctypes.byref(gainsArray), disableCal, ctypes.byref(overVoltage), ctypes.byref(voltages))

        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value, "stateIO":stateIOin.value, "overVoltage":overVoltage.value, "voltages":voltages[0:numChannels]}

    def aiBurst(self, numChannels, channels, scanRate, numScans, idNum=None, demo=0, stateIOin=0, updateIO=0, ledOn=0, gains=[0, 0, 0, 0], disableCal=0, triggerIO=0, triggerState=0, timeout=1, transferMode=0):
        """
        Name: U12.aiBurst(numChannels, channels, scanRate, numScans, idNum=None, demo=0, stateIOin=[0, 0, 0, 0], updateIO=0, ledOn=0, gains=[0, 0, 0, 0], disableCal=0, triggerIO=0, triggerState=0, timeout=1, transferMode=0)
        Args: See section 4.7 of the User's Guide
        Desc: Reads a specified number of scans (up to 4096) at a specified scan rate (up to 8192 Hz) from 1,2, or 4 analog inputs

        >>> dev = U12()
        >>> dev.aiBurst(1, [0], 400, 10)
        {'overVoltage': 0, 'scanRate': 400.0, 'stateIOout': <u12.c_long_Array_4096 object at 0x00DB4BC0>, 'idnum': 1, 'voltages': <u12.c_float_Array_4096_Array_4 object at 0x00DB4B70>}
        """
        
        # Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        # check list sizes
        if len(channels) < numChannels: raise ValueError("channels must have atleast numChannels elements")
        if len(gains) < numChannels: raise ValueError("gains must have atleast numChannels elements")
        
        # Convert lists to arrays and create other ctypes
        channelsArray = listToCArray(channels, ctypes.c_long)
        gainsArray = listToCArray(gains, ctypes.c_long)
        scanRate = ctypes.c_float(scanRate)
        pointerArray = (ctypes.c_void_p * 4)
        arr4096_type = ctypes.c_float * 4096 
        voltages_type = arr4096_type * 4 
        voltages = voltages_type() 
        stateIOout = (ctypes.c_long * 4096)()
        overVoltage = ctypes.c_long(999)
        
        ecode = staticLib.AIBurst(ctypes.byref(idNum), demo, stateIOin, updateIO, ledOn, numChannels, ctypes.byref(channelsArray), ctypes.byref(gainsArray), ctypes.byref(scanRate), disableCal, triggerIO, triggerState, numScans, timeout, ctypes.byref(voltages), ctypes.byref(stateIOout), ctypes.byref(overVoltage), transferMode)

        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value, "scanRate":scanRate.value, "voltages":voltages, "stateIOout":stateIOout, "overVoltage":overVoltage.value}
    
    def aiStreamStart(self, numChannels, channels, scanRate, idNum=None, demo=0, stateIOin=0, updateIO=0, ledOn=0, gains=[0, 0, 0, 0], disableCal=0, readCount=0):
        """
        Name: U12.aiStreamStart(numChannels, channels, scanRate, idNum=None, demo=0, stateIOin=0, updateIO=0, ledOn=0, gains=[0, 0, 0, 0], disableCal=0, readCount=0)
        Args: See section 4.8 of the User's Guide
        Desc: Starts a hardware timed continuous acquisition

        >>> dev = U12()
        >>> dev.aiStreamStart(1, [0], 200)
        {'scanRate': 200.0, 'idnum': 1}
        """
        
        # Configure return type
        staticLib.AIStreamStart.restype = ctypes.c_long
        
        # check list sizes
        if len(channels) < numChannels: raise ValueError("channels must have atleast numChannels elements")
        if len(gains) < numChannels: raise ValueError("gains must have atleast numChannels elements")
        #if len(stateIOin) < 4: raise ValueError("stateIOin must have atleast 4 elements")

        # Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        # Convert lists to arrays and create other ctypes
        channelsArray = listToCArray(channels, ctypes.c_long)
        gainsArray = listToCArray(gains, ctypes.c_long)
        scanRate = ctypes.c_float(scanRate)
        
        ecode = staticLib.AIStreamStart(ctypes.byref(idNum), demo, stateIOin, updateIO, ledOn, numChannels, ctypes.byref(channelsArray), ctypes.byref(gainsArray), ctypes.byref(scanRate), disableCal, 0, readCount)

        if ecode != 0: raise U12Exception(ecode) # TODO: Switch this out for exception
        
        # The ID number must be saved for AIStream
        self.id = idNum.value

        self.streaming = True
        
        return {"idnum":idNum.value, "scanRate":scanRate.value}

    def aiStreamRead(self, numScans, localID=None, timeout=1):
        """
        Name: U12.aiStreamRead(numScans, localID=None, timeout=1)
        Args: See section 4.9 of the User's Guide
        Desc: Waits for a specified number of scans to be available and reads them.

        >>> dev = U12()
        >>> dev.aiStreamStart(1, [0], 200)
        >>> dev.aiStreamRead(10)
        {'overVoltage': 0, 'ljScanBacklog': 0, 'stateIOout': <u12.c_long_Array_4096 object at 0x00DF4AD0>, 'reserved': 0, 'voltages': <u12.c_float_Array_4096_Array_4 object at 0x00DF4B20>}
        """
        
        # Check to make sure that we are streaming
        if not self.streaming:
            raise U12Exception(-1, "Streaming has not started")
        
        # Check id number
        if localID is None:
            localID = self.id
            
        # Create arrays and other ctypes
        arr4096_type = ctypes.c_float * 4096 
        voltages_type = arr4096_type * 4 
        voltages = voltages_type() 
        stateIOout = (ctypes.c_long * 4096)()
        reserved = ctypes.c_long(0)
        ljScanBacklog = ctypes.c_long(99999)
        overVoltage = ctypes.c_long(999)
        
        ecode = staticLib.AIStreamRead(localID, numScans, timeout, ctypes.byref(voltages), ctypes.byref(stateIOout), ctypes.byref(reserved), ctypes.byref(ljScanBacklog), ctypes.byref(overVoltage))
        
        if ecode != 0: raise U12Exception(ecode) # TODO: Switch this out for exception
        
        return {"voltages":voltages, "stateIOout":stateIOout, "reserved":reserved.value, "ljScanBacklog":ljScanBacklog.value, "overVoltage":overVoltage.value}
    
    def aiStreamClear(self, localID=None):
        """
        Name: U12.aiClear()
        Args: See section 4.10 of the User's Guide
        Desc: This function stops the continuous acquisition. It should be called once when finished with the stream.

        >>> dev = U12()
        >>> dev.aiStreamStart(1, [0], 200)
        >>> dev.aiStreamRead(10)
        >>> dev.aiStreamClear()
        """
        
        # Check to make sure that we are streaming
        if not self.streaming:
            raise U12Exception(-1, "Streaming has not started")
        
        # Check id number
        if localID is None:
            localID = self.id
        
        ecode = staticLib.AIStreamClear(localID)

        if ecode != 0: raise U12Exception(ecode) # TODO: Switch this out for exception
        
    def aoUpdate(self, idNum=None, demo=0, trisD=None, trisIO=None, stateD=None, stateIO=None, updateDigital=0, resetCounter=0, analogOut0=0, analogOut1=0):
        """
        Name: U12.aoUpdate()
        Args: See section 4.11 of the User's Guide
        Desc: Sets the voltages of the analog outputs. Also controls/reads all 20 digital I/O and the counter.

        >>> dev = U12()
        >>> dev.aoUpdate()
        >>> {'count': 2, 'stateIO': 3, 'idnum': 1, 'stateD': 0}
        """
        
        # Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        #  Check tris and state arguments
        if updateDigital > 0:
            if trisD is None: raise ValueError("keyword argument trisD must be set")
            if trisIO is None: raise ValueError("keyword argument trisIO must be set")
            if stateD is None: raise ValueError("keyword argument stateD must be set")
            if stateIO is None: raise ValueError("keyword argument stateIO must be set")

        # Create ctypes
        if stateD is None: stateD = ctypes.c_long(0)
        else: stateD = ctypes.c_long(stateD)
        if stateIO is None: stateIO = ctypes.c_long(0)
        else: stateIO = ctypes.c_long(stateIO)
        count = ctypes.c_ushort(999)
        
        # Create arrays and other ctypes
        ecode = staticLib.AOUpdate(ctypes.byref(idNum), demo, trisD, trisIO, ctypes.byref(stateD), ctypes.byref(stateIO), updateDigital, resetCounter, ctypes.byref(count), ctypes.c_float(analogOut0), ctypes.c_float(analogOut1))
        
        if ecode != 0: raise U12Exception(ecode) # TODO: Switch this out for exception
        
        return {"idnum":idNum.value, "stateD":stateD.value, "stateIO":stateIO.value, "count":count.value}

    def asynchConfig(self, fullA, fullB, fullC, halfA, halfB, halfC, idNum=None, demo=None, timeoutMult=1, configA=0, configB=0, configTE=0):
        """
        Name: U12.asynchConfig(fullA, fullB, fullC, halfA, halfB, halfC, idNum=None, demo=None, timeoutMult=1, configA=0, configB=0, configTE=0)
        Args: See section 4.12 of the User's Guide
        Desc: Requires firmware V1.1 or higher. This function writes to the asynch registers and sets the direction of the D lines (input/output) as needed.

        >>> dev = U12()
        >>> dev.asynchConfig(96,1,1,22,2,1)
        >>> {'idNum': 1}
        """
        
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        ecode = staticLib.AsynchConfig(ctypes.byref(idNum), demo, timeoutMult, configA, configB, configTE, fullA, fullB, fullC, halfA, halfB, halfC)
        
        if ecode != 0: raise U12Exception(ecode) # TODO: Switch this out for exception
        
        return {"idNum":idNum.value}
    
    def asynch(self, baudrate, data, idNum=None, demo=0, portB=0, enableTE=0, enableTO=0, enableDel=0, numWrite=0, numRead=0):
        """
        Name: U12.asynchConfig(fullA, fullB, fullC, halfA, halfB, halfC, idNum=None, demo=None, timeoutMult=1, configA=0, configB=0, configTE=0)
        Args: See section 4.13 of the User's Guide
        Desc: Requires firmware V1.1 or higher. This function writes to the asynch registers and sets the direction of the D lines (input/output) as needed.

        >>> dev = U12()
        >>> dev.asynch(96,1,1,22,2,1)
        >>> dev.asynch(19200, [0, 0])
        >>> {'data': <u12.c_long_Array_18 object at 0x00DEFB70>, 'idnum': <type 'long'>}
        """
        
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        # Check size of data
        if len(data) > 18: raise ValueError("data can not be larger than 18 elements")
        
        # Make data 18 elements large
        dataArray = [0] * 18
        for i in range(0, len(data)):
            dataArray[i] = data[i]
        print dataArray
        dataArray = listToCArray(dataArray, ctypes.c_long)
        
        ecode = staticLib.Asynch(ctypes.byref(idNum), demo, portB, enableTE, enableTO, enableDel, baudrate, numWrite, numRead, ctypes.byref(dataArray))
        
        if ecode != 0: raise U12Exception(ecode) # TODO: Switch this out for exception
        
        return {"idnum":long, "data":dataArray}
    
    GainMapping = [ 1.0, 2.0, 4.0, 5.0, 8.0, 10.0, 16.0, 20.0 ] 
    def bitsToVolts(self, chnum, chgain, bits):
        """
        Name: U12.bitsToVolts(chnum, chgain, bits)
        Args: See section 4.14 of the User's Guide
        Desc: Converts a 12-bit (0-4095) binary value into a LabJack voltage. No hardware communication is involved.

        >>> dev = U12()
        >>> dev.bitsToVolts(0, 0, 2662)
        >>> {'volts': 2.998046875}
        """
        if ON_WINDOWS:
            volts = ctypes.c_float()
            ecode = staticLib.BitsToVolts(chnum, chgain, bits, ctypes.byref(volts))
    
            if ecode != 0: print ecode
    
            return volts.value
        else:
            if chnum < 8:
                return ( float(bits) * 20.0 / 4096.0 ) - 10.0
            else:
                volts = ( float(bits) * 40.0 / 4096.0 ) - 20.0
                return volts / self.GainMapping[chgain]

    def voltsToBits(self, chnum, chgain, volts):
        """
        Name: U12.voltsToBits(chnum, chgain, bits)
        Args: See section 4.15 of the User's Guide
        Desc: Converts a voltage to it's 12-bit (0-4095) binary representation. No hardware communication is involved.

        >>> dev = U12()
        >>> dev.voltsToBits(0, 0, 3)
        >>> {'bits': 2662}
        """
        if ON_WINDOWS:
            bits = ctypes.c_long(999)
            ecode = staticLib.VoltsToBits(chnum, chgain, ctypes.c_float(volts), ctypes.byref(bits))

            if ecode != 0: raise U12Exception(ecode)

            return bits.value
        else:
            pass
            #*bits = RoundFL((volts+10.0F)/(20.0F/4096.0F));
    
    def counter(self, idNum=None, demo=0, resetCounter=0, enableSTB=1):
        """
        Name: U12.counter(idNum=None, demo=0, resetCounter=0, enableSTB=1)
        Args: See section 4.15 of the User's Guide
        Desc: Converts a voltage to it's 12-bit (0-4095) binary representation. No hardware communication is involved.

        >>> dev = U12()
        >>> dev.counter(0, 0, 3)
        >>> {'bits': 2662}
        """
        
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        # Create ctypes
        stateD = ctypes.c_long(999)
        stateIO = ctypes.c_long(999)
        count = ctypes.c_ulong(999)
        
        print idNum
        ecode = staticLib.Counter(ctypes.byref(idNum), demo, ctypes.byref(stateD), ctypes.byref(stateIO), resetCounter, enableSTB, ctypes.byref(count))

        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value, "stateD": stateD.value, "stateIO":stateIO.value, "count":count.value}

    def digitalIO(self, idNum=None, demo=0, trisD=None, trisIO=None, stateD=None, stateIO=None, updateDigital=0):
        """
        Name: U12.digitalIO(idNum=None, demo=0, trisD=None, trisIO=None, stateD=None, stateIO=None, updateDigital=0)
        Args: See section 4.17 of the User's Guide
        Desc: Reads and writes to all 20 digital I/O.

        >>> dev = U12()
        >>> dev.digitalIO()
        >>> {'stateIO': 0, 'stateD': 0, 'idnum': 1, 'outputD': 0, 'trisD': 0}
        """
        
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)

        # Check tris and state parameters
        if updateDigital > 0:
            if trisD is None: raise ValueError("keyword argument trisD must be set")
            if trisIO is None: raise ValueError("keyword argument trisIO must be set")
            if stateD is None: raise ValueError("keyword argument stateD must be set")
            if stateIO is None: raise ValueError("keyword argument stateIO must be set")
        
        # Create ctypes
        if trisD is None: trisD = ctypes.c_long(999)
        else:trisD = ctypes.c_long(trisD)
        if stateD is None:stateD = ctypes.c_long(999)
        else: stateD = ctypes.c_long(stateD)
        if stateIO is None: stateIO = ctypes.c_long(0)
        else: stateIO = ctypes.c_long(stateIO)
        outputD = ctypes.c_long(999)
        
        # Check trisIO
        if trisIO is None: trisIO = 0

        ecode = staticLib.DigitalIO(ctypes.byref(idNum), demo, ctypes.byref(trisD), trisIO, ctypes.byref(stateD), ctypes.byref(stateIO), updateDigital, ctypes.byref(outputD))
        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value, "trisD":trisD.value, "stateD":stateD.value, "stateIO":stateIO.value, "outputD":outputD.value}
        
    def getDriverVersion(self):
        """
        Name: U12.getDriverVersion()
        Args: See section 4.18 of the User's Guide
        Desc: Returns the version number of ljackuw.dll. No hardware communication is involved.

        >>> dev = U12()
        >>> dev.getDriverVersion()
        >>> 1.21000003815
        """
        staticLib.GetDriverVersion.restype = ctypes.c_float
        return staticLib.GetDriverVersion()

    def getFirmwareVersion(self, idNum=None):
        """
        Name: U12.getErrorString(idnum=None)
        Args: See section 4.20 of the User's Guide
        Desc: Retrieves the firmware version from the LabJack's processor

        >>> dev = U12()
        >>> dev.getFirmwareVersion()
        >>> Unkown error
        """
        
        # Check ID number
        if idNum is None: idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        staticLib.GetFirmwareVersion.restype = ctypes.c_float
        firmware = staticLib.GetFirmwareVersion(ctypes.byref(idNum))

        if firmware > 512: raise U12Exception(firmware-512)

        return {"idnum" : idNum.value, "firmware" : firmware}
    
    def getWinVersion(self):
        """
        Name: U12.getErrorString()
        Args: See section 4.21 of the User's Guide
        Desc: Uses a Windows API function to get the OS version
        
        >>> dev = U12()
        >>> dev.getWinVersion()
        >>> {'majorVersion': 5L, 'minorVersion': 1L, 'platformID': 2L, 'buildNumber': 2600L, 'servicePackMajor': 2L, 'servicePackMinor': 0L}
        """
        
        # Create ctypes
        majorVersion = ctypes.c_ulong()
        minorVersion = ctypes.c_ulong()
        buildNumber = ctypes.c_ulong()
        platformID = ctypes.c_ulong()
        servicePackMajor = ctypes.c_ulong()
        servicePackMinor = ctypes.c_ulong()
        
        ecode = staticLib.GetWinVersion(ctypes.byref(majorVersion), ctypes.byref(minorVersion), ctypes.byref(buildNumber), ctypes.byref(platformID), ctypes.byref(servicePackMajor), ctypes.byref(servicePackMinor))
        
        if ecode != 0: raise U12Exception(ecode)
        
        return {"majorVersion":majorVersion.value, "minorVersion":minorVersion.value, "buildNumber":buildNumber.value, "platformID":platformID.value, "servicePackMajor":servicePackMajor.value, "servicePackMinor":servicePackMinor.value}
    
    def listAll(self):
        """
        Name: U12.listAll()
        Args: See section 4.22 of the User's Guide
        Desc: Searches the USB for all LabJacks, and returns the serial number and local ID for each
        
        >>> dev = U12()
        >>> dev.listAll()
        >>> {'serialnumList': <u12.c_long_Array_127 object at 0x00E2AD50>, 'numberFound': 1, 'localIDList': <u12.c_long_Array_127 object at 0x00E2ADA0>}
        """
        
        # Create arrays and ctypes
        productIDList = listToCArray([0]*127, ctypes.c_long)
        serialnumList = listToCArray([0]*127, ctypes.c_long)
        localIDList = listToCArray([0]*127, ctypes.c_long)
        powerList = listToCArray([0]*127, ctypes.c_long)
        arr127_type = ctypes.c_long * 127 
        calMatrix_type = arr127_type * 20
        calMatrix = calMatrix_type() 
        reserved = ctypes.c_long()
        numberFound = ctypes.c_long()
        
        ecode = staticLib.ListAll(ctypes.byref(productIDList), ctypes.byref(serialnumList), ctypes.byref(localIDList), ctypes.byref(powerList), ctypes.byref(calMatrix), ctypes.byref(numberFound), ctypes.byref(reserved), ctypes.byref(reserved))
        if ecode != 0: raise U12Exception(ecode)
        
        return {"serialnumList": serialnumList, "localIDList":localIDList, "numberFound":numberFound.value}
        
    def localID(self, localID, idNum=None):
        """
        Name: U12.localID(localID, idNum=None)
        Args: See section 4.23 of the User's Guide
        Desc: Changes the local ID of a specified LabJack
        
        >>> dev = U12()
        >>> dev.localID(1)
        >>> {'idnum':1}
        """
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        ecode = staticLib.LocalID(ctypes.byref(idNum), localID)
        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value}
    
    def noThread(self, noThread, idNum=None):
        """
        Name: U12.localID(noThread, idNum=None)
        Args: See section 4.24 of the User's Guide
        Desc: This function is needed when interfacing TestPoint to the LabJack DLL on Windows 98/ME
        
        >>> dev = U12()
        >>> dev.noThread(1)
        >>> {'idnum':1}
        """
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        ecode = staticLib.NoThread(ctypes.byref(idNum), noThread)
        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value}
    
    def pulseOut(self, bitSelect, numPulses, timeB1, timeC1, timeB2, timeC2, idNum=None, demo=0, lowFirst=0):
        """
        Name: U12.pulseOut(bitSelect, numPulses, timeB1, timeC1, timeB2, timeC2, idNum=None, demo=0, lowFirst=0)
        Args: See section 4.25 of the User's Guide
        Desc: This command creates pulses on any/all of D0-D7
        
        >>> dev = U12()
        >>> dev.pulseOut(0, 1, 1, 1, 1, 1)
        >>> {'idnum':1}
        """
        
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        ecode = staticLib.PulseOut(ctypes.byref(idNum), demo, lowFirst, bitSelect, numPulses, timeB1, timeC1, timeB2, timeC2)
        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value}
    
    def pulseOutStart(self, bitSelect, numPulses, timeB1, timeC1, timeB2, timeC2, idNum=None, demo=0, lowFirst=0):
        """
        Name: U12.pulseOutStart(bitSelect, numPulses, timeB1, timeC1, timeB2, timeC2, idNum=None, demo=0, lowFirst=0)
        Args: See section 4.26 of the User's Guide
        Desc: PulseOutStart and PulseOutFinish are used as an alternative to PulseOut (See PulseOut for more information)
        
        >>> dev = U12()
        >>> dev.pulseOutStart(0, 1, 1, 1, 1, 1)
        >>> {'idnum':1}
        """
        
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        ecode = staticLib.PulseOutStart(ctypes.byref(idNum), demo, lowFirst, bitSelect, numPulses, timeB1, timeC1, timeB2, timeC2)
        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value}

    def pulseOutFinish(self, timeoutMS, idNum=None, demo=0):
        """
        Name: U12.pulseOutFinish(timeoutMS, idNum=None, demo=0)
        Args: See section 4.27 of the User's Guide
        Desc: See PulseOutStart for more information
        
        >>> dev = U12()
        >>> dev.pulseOutStart(0, 1, 1, 1, 1, 1)
        >>> dev.pulseOutFinish(100)
        >>> {'idnum':1}
        """
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        ecode = staticLib.PulseOutFinish(ctypes.byref(idNum), demo, timeoutMS)
        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value}
    
    def pulseOutCalc(self, frequency):
        """
        Name: U12.pulseOutFinish(frequency)
        Args: See section 4.28 of the User's Guide
        Desc: This function can be used to calculate the cycle times for PulseOut or PulseOutStart.
        
        >>> dev = U12()
        >>> dev.pulseOutCalc(100)
        >>> {'frequency': 100.07672882080078, 'timeB': 247, 'timeC': 1}
        """
        
        # Create ctypes
        frequency = ctypes.c_float(frequency)
        timeB = ctypes.c_long(0)
        timeC = ctypes.c_long(0)
        
        ecode = staticLib.PulseOutCalc(ctypes.byref(frequency), ctypes.byref(timeB), ctypes.byref(timeC))
        if ecode != 0: raise U12Exception(ecode)
        
        return {"frequency":frequency.value, "timeB":timeB.value, "timeC":timeC.value}
    
    def reEnum(self, idNum=None):
        """
        Name: U12.reEnum(idNum=None)
        Args: See section 4.29 of the User's Guide
        Desc: Causes the LabJack to electrically detach from and re-attach to the USB so it will re-enumerate
        
        >>> dev = U12()
        >>> dev.reEnum()
        >>> {'idnum': 1}
        """
        
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        ecode = staticLib.ReEnum(ctypes.byref(idNum))
        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value}
    
    def reset(self, idNum=None):
        """
        Name: U12.reset(idNum=None)
        Args: See section 4.30 of the User's Guide
        Desc: Causes the LabJack to reset after about 2 seconds
        
        >>> dev = U12()
        >>> dev.reset()
        >>> {'idnum': 1}
        """
        
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        ecode = staticLib.Reset(ctypes.byref(idNum))
        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value}
    
    def resetLJ(self, idNum=None):
        """
        Name: U12.resetLJ(idNum=None)
        Args: See section 4.30 of the User's Guide
        Desc: Causes the LabJack to reset after about 2 seconds
        
        >>> dev = U12()
        >>> dev.resetLJ()
        >>> {'idnum': 1}
        """
        return reset(idNum)
    
    def sht1X(self, idNum=None, demo=0, softComm=0, mode=0, statusReg=0):
        """
        Name: U12.sht1X(idNum=None, demo=0, softComm=0, mode=0, statusReg=0)
        Args: See section 4.31 of the User's Guide
        Desc: This function retrieves temperature and/or humidity readings from an SHT1X sensor.
        
        >>> dev = U12()
        >>> dev.sht1X()
        >>> {'tempC': 24.69999885559082, 'rh': 39.724445343017578, 'idnum': 1, 'tempF': 76.459999084472656}
        """
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        # Create ctypes
        tempC = ctypes.c_float(0)
        tempF = ctypes.c_float(0)
        rh = ctypes.c_float(0)
        
        ecode = staticLib.SHT1X(ctypes.byref(idNum), demo, softComm, mode, statusReg, ctypes.byref(tempC), ctypes.byref(tempF), ctypes.byref(rh))
        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value, "tempC":tempC.value, "tempF":tempF.value, "rh":rh.value}
    
    def shtComm(self, numWrite, numRead, datatx, idNum=None, softComm=0, waitMeas=0, serialReset=0, dataRate=0):
        """
        Name: U12.shtComm(numWrite, numRead, datatx, idNum=None, softComm=0, waitMeas=0, serialReset=0, dataRate=0)
        Args: See section 4.32 of the User's Guide
        Desc: Low-level public function to send and receive up to 4 bytes to from an SHT1X sensor
        """
        
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        # Check size of datatx
        if len(datatx) != 4: raise ValueError("datatx must have exactly 4 elements")
        
        # Create ctypes
        datatx = listToCArray(datatx, ctypes.c_ubyte)
        datarx = (ctypes.c_ubyte * 4)((0) * 4)
        
        ecode = staticLib.SHTComm(ctypes.byref(idNum), softComm, waitMeas, serialReset, dataRate, numWrite, numRead, ctypes.byref(datatx), ctypes.byref(datarx))
        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value, "datarx":datarx}
    
    def shtCRC(self, numWrite, numRead, datatx, datarx, statusReg=0):
        """
        Name: U12.shtCRC(numWrite, numRead, datatx, datarx, statusReg=0)
        Args: See section 4.33 of the User's Guide
        Desc: Checks the CRC on an SHT1X communication
        """
        # Create ctypes
        datatx = listToCArray(datatx, ctypes.c_ubyte)
        datarx = listToCArray(datarx, ctypes.c_ubyte)
        
        return staticLib.SHTCRC(statusReg, numWrite, numRead, ctypes.byref(datatx), ctypes.byref(datarx))

    def synch(self, mode, numWriteRead, data, idNum=None, demo=0, msDelay=0, husDelay=0, controlCS=0, csLine=None, csState=0, configD=0):
        """
        Name: U12.synch(mode, numWriteRead, data, idNum=None, demo=0, msDelay=0, husDelay=0, controlCS=0, csLine=None, csState=0, configD=0)
        Args: See section 4.35 of the User's Guide
        Desc: This function retrieves temperature and/or humidity readings from an SHT1X sensor.
        """
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        if controlCS > 0 and csLine is None: raise ValueError("csLine must be specified")
        
        # Make sure data is 18 elements
        cData = [0] * 18
        for i in range(0, len(data)):
            cData[i] = data[i]
        cData = listToCArray(cData, ctypes.c_long)
        
        ecode = staticLib.Synch(ctypes.byref(idNum), demo, mode, msDelay, husDelay, controlCS, csLine, csState, configD, numWriteRead, ctypes.byref(cData))
        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value, "data":cData}
    
    def watchdog(self, active, timeout, activeDn, stateDn, idNum=None, demo=0, reset=0):
        """
        Name: U12.watchdog(active, timeout, activeDn, stateDn, idNum=None, demo=0, reset=0)
        Args: See section 4.35 of the User's Guide
        Desc: Controls the LabJack watchdog function.
        
        >>> dev = U12()
        >>> dev.watchdog(1, 1, [0, 0, 0], [0, 0, 0])
        >>> {'idnum': 1}
        """
        
        #Check id number
        if idNum is None:
            idNum = self.id
        idNum = ctypes.c_long(idNum)
        
        if len(activeDn) is not 3: raise ValueError("activeDn must have 3 elements")
        if len(stateDn) is not 3: raise Value("stateDn must have 3 elements")
        
        ecode = staticLib.Watchdog(ctypes.byref(idNum), demo, active, timeout, reset, activeDn[0], activeDn[1], activeDn[2], stateDn[0], stateDn[1], stateDn[2])
        if ecode != 0: raise U12Exception(ecode)
        
        return {"idnum":idNum.value}
        
    def readMem(self, address, idnum = None):
        """
        Name: U12.readMem(address, idnum=None)
        Args: See section 4.36 of the User's Guide
        Desc: Reads 4 bytes from a specified address in the LabJack's nonvolatile memory
        
        >>> dev = U12()
        >>> dev.readMem(0)
        >>> [5, 246, 16, 59]
        """
        
        if address is None:
            raise Exception, "Must give an Address."
        
        if idnum is None:
            idnum = self.id
            
        ljid = ctypes.c_ulong(idnum)
        ad0 = ctypes.c_ulong()
        ad1 = ctypes.c_ulong()
        ad2 = ctypes.c_ulong()
        ad3 = ctypes.c_ulong()

        ec = staticLib.ReadMem(ctypes.byref(ljid), ctypes.c_long(address), ctypes.byref(ad3), ctypes.byref(ad2), ctypes.byref(ad1), ctypes.byref(ad0))
        if ec != 0: raise U12Exception(ec)
        
        addr = [0] * 4
        addr[0] = int(ad3.value & 0xff)
        addr[1] = int(ad2.value & 0xff)
        addr[2] = int(ad1.value & 0xff)
        addr[3] = int(ad0.value & 0xff)

        return addr
    
    def writeMem(self, address, data, idnum=None, unlocked=False):
        """
        Name: U12.writeMem(self, address, data, idnum=None, unlocked=False)
        Args: See section 4.37 of the User's Guide
        Desc: Writes 4 bytes to the LabJack's 8,192 byte nonvolatile memory at a specified address.
        
        >>> dev = U12()
        >>> dev.writeMem(0, [5, 246, 16, 59])
        >>> 1
        """
        if address is None or data is None:
            raise Exception, "Must give both an Address and data."
        if type(data) is not list or len(data) != 4:
            raise Exception, "Data must be a list and have a length of 4"
        
        if idnum is None:
            idnum = self.id
        
        ljid = ctypes.c_ulong(idnum)
        ec = staticLib.WriteMem(ctypes.byref(ljid), int(unlocked), address, data[3] & 0xff, data[2] & 0xff, data[1] & 0xff, data[0] & 0xff)
        if ec != 0: raise U12Exception(ec)
        
        return ljid.value
        
    def LJHash(self, hashStr, size):
        outBuff = (ctypes.c_char * 16)()
        retBuff = ''
        
        staticLib = ctypes.windll.LoadLibrary("ljackuw")
        
        ec = staticLib.LJHash(ctypes.cast(hashStr, ctypes.POINTER(ctypes.c_char)),
                              size, 
                              ctypes.cast(outBuff, ctypes.POINTER(ctypes.c_char)), 
                              0)
        if ec != 0: raise U12Exception(ec)

        for i in range(16):
            retBuff += outBuff[i]
            
        return retBuff

def isIterable(var):
    try:
        iter(var)
        return True
    except Exception:
        return False
    
def listToCArray(list, dataType):
    arrayType = dataType * len(list)
    array = arrayType()
    for i in range(0,len(list)):
        array[i] = list[i]
    
    return array

def cArrayToList(array):
    list = []
    for item in array:
        list.append(item)
    
    return list

def getErrorString(errorcode):
    """
    Name: U12.getErrorString(errorcode)
    Args: See section 4.19 of the User's Guide
    Desc: Converts a LabJack errorcode, returned by another function, into a string describing the error. No hardware communication is involved.

    >>> dev = U12()
    >>> dev.getErrorString(1)
    >>> Unkown error
    """
    errorString = ctypes.c_char_p(" "*50)
    staticLib.GetErrorString(errorcode, errorString)
    return errorString.value

def hexWithoutQuotes(l):
    """ Return a string listing hex without all the single quotes.
    
    >>> l = range(10)
    >>> print hexWithoutQuotes(l)
    [0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9]

    """
    return str([hex (i) for i in l]).replace("'", "")
