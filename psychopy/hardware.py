# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import serial, core, log
import struct, sys
  

class CedrusPad:
    """Class to control/read a Cedrus RB-series response box"""
    class KeyEvent:
        """Info about a keypress from Cedrus keypad XID string"""
        def __init__(self,XID):
            """XID should contain a "k"<info><rt> where info is a byte and rt is 4 bytes (=int)"""
            if len(XID)!=6:
                #log.error("The XID string %s is %i bytes long and should be 6 bytes" %(str([XID]),len(XID)))
                self.key=None
            else:
                info = struct.unpack('B',XID[1])[0]#a character and a ubyte of info
                
                #was the key going down or up?
                if (info>>4)%2: #this gives only the 4th bit
                    self.direction='down'
                else:
                    self.direction='up'
                    
                #what was the key?
                self.key = info>>5#bits 5-7 give the button number
                    
                #what was RT?
                self.rt = struct.unpack('i',XID[2:])[0] #integer in ms
                    
            
    def __init__(self, port, model='RB730', baudrate=115200, mode='XID'):
        self.model = model
        #set name of port
        if type(port) in [int, float]:
            self.portNumber = port
            self.portString = 'COM%i' %self.portNumber
        else:
            self.portString = port
            self.portNumber=None
        self.mode = mode #can be 'xid', 'rb', 'ascii'
        self.baudrate = baudrate
        #open the serial port
        self.port = serial.Serial(self.portString, baudrate=baudrate, bytesize=8, parity='N', stopbits=1, timeout=0.0001)
        self.port.open()
        #self.buffer = ''#our own buffer (in addition to the serial port buffer)
        self.clearBuffer()
        
    def sendMessage(self, message):
        self.port.writelines(message)
        
    def _clearBuffer(self):
        """DEPRECATED as of 1.00.05"""
        self.port.flushInput()
        
    def clearBuffer(self):
        """Empty the input buffer of all characters. Call this to clear any keypresses that haven't yet been handled."""
        self.port.flushInput()
        
    def getKeyEvents(self, allowedKeys=[1,2,3,4,5,6,7], downOnly=True):    
        """Return a list of keyEvents
            Each event has the following attributes:
            
                keyEvt.key is the button pressed (or released) (an int)
                keyEvt.rt [=float] is the time (in secs) since the rt clock was last reset (a float)
                keyEvt.direction is the direction the button was goin ('up' or 'down')
                
            allowedKeys will limit the set of keys that are returned (WARNING: info about other keys is discarded)
            downOnly limits the function to report only the downward stroke of the key
                """
        #get the raw string
        nToGet = self.port.inWaiting()        
        #self.buffer += self.port.read(nToGet)#extend our own buffer (then remove the bits we use)
        inputStr = self.port.read(nToGet)#extend our own buffer (then remove the bits we use)
        keys =[]#initialise
        
        #loop through messages for keys
        nKeys = inputStr.count('k')#find the "k"s
        for keyN in range(nKeys):
            start = inputStr.find('k')#find the next key
            stop = start+6
            #check we have that many characters(in case we read the buffer partway through output)
            if len(inputStr)<stop:
                inputStr+= self.port.read(stop-len(inputStr))
            keyString = inputStr[start:stop]
            keyEvt = self.KeyEvent(XID=keyString)
            if keyEvt.key not in allowedKeys:
                continue #ignore this keyEvt and move on
            if (downOnly==True and keyEvt.direction=='up'):
                continue #ignore this keyEvt and move on
            
            #we found a valid keyEvt
            keys.append(keyEvt)
            inputStr = inputStr.replace(keyString,'',1)#remove the (1st occurence of) string from the buffer
            
        return keys
    
    def readMessage(self):
        """Read and return an unformatted string from the device (and delete this from the buffer)"""
        nToGet = self.port.inWaiting()    
        return self.port.read(nToGet)
    
    def measureRoundTrip(self):
        #round trip
        self.sendMessage('e4')#start round trip
        #wait for 'X'
        while True:
            if self.readMessage()=='X':
                break     
        self.sendMessage('X')#send it back
        
        #wait for final time info
        msgBack = ''
        while len(msgBack)==0:
            msgBack=self.readMessage()        
        tStr = msgBack[2:]
        t = struct.unpack('H',tStr)[0]#2 bytes (an unsigned short)
        return t
        
    def waitKeyEvents(self, allowedKeys=[1,2,3,4,5,6,7], downOnly=True):
        """Like getKeyEvents, but waits until a key is pressed"""
        noKeyYet = True
        while noKeyYet:
            keys = self.getKeyEvents(allowedKeys=allowedKeys, downOnly=downOnly)
            if len(keys)>0:
                noKeyYet=False
        return keys
    def resetTrialTimer(self):
        self.sendMessage('e5')
    def resetBaseTimer(self):
        self.sendMessage('e1')
    def getBaseTimer(self):
        """Retrieve the current time on the base timer"""
        self.sendMessage('e3')
        #core.wait(0.05)
        localTimer=core.Clock()
        
        msg = self.readMessage()
        ii = msg.find('e3')
        tStr = msg[ii+2:ii+6]#4 bytes (an int) of time info
        t = struct.unpack('I',tStr)[0]
        return t
    def getInfo(self):
        """Get the name of this device"""
        self.sendMessage('_d1')
        core.wait(0.1)
        return self.readMessage()
        
class ForpBox:
    """Serial line interface to the fORP MRI response box
    
    Set the box use setting 0 or 1 and connect the serial line to
    use this object class. (Alternatively connect the USB cable and 
    use fORP to emulate a keyboard).
    
    fORP sends characters at 800Hz, so you should check the buffer frequently.
    Also note that the trigger event numpy the fORP is typically extremely short
    (occurs for a single 800Hz epoch).
    """
    def __init__(self, serialPort=1):
        """serialPort should be a number (where 1=COM1,...)"""
        self.port = serial.Serial(serialPort-1, baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=0.001)
        self.port.open()
        self.rawEvts = []
    
    def clearBuffer(self):
        """Empty the input buffer of all characters"""
        self.port.flushInput()
        
    def getEvents(self, returnRaw=False):
        """Returns a list of unique events (one event per button pressed)
        AND stores a copy of the full list of events since last getEvents() 
        (stored as ForpBox.rawEvts)
        """
        nToGet = self.port.inWaiting()
        evtStr = self.port.read(nToGet)
        self.rawEvts=[]
        #for each character convert to an ordinal int value (numpy the ascii chr)
        for thisChr in evtStr:
            self.rawEvts.append(ord(thisChr))
        #return the abbrieviated list if necess
        if returnRaw: 
            return self.rawEvts
        else:
            return self.getUniqueEvents()
            
    def getUniqueEvents(self, fullEvts=None):
        """Returns a Python set of the unique (unordered) events of either 
        a list given or the current rawEvts buffer"""
        
        evtSet=set([])#NB a python set never has duplicate elements
        if fullEvts==None: fullEvts=self.rawEvts
        for thisOrd in fullEvts:
            if thisOrd & int('00001', 2): evtSet.add(1)
            if thisOrd & int('00010', 2): evtSet.add(2)
            if thisOrd & int('00100', 2): evtSet.add(3)
            if thisOrd & int('01000', 2): evtSet.add(4)
            if thisOrd & int('10000', 2): evtSet.add(5)
        return evtSet
    
class PR650:
    """
    A class to define a calibration device that connects to
    a serial port. Currently it must be a PR650, but could
    well be expanded in the future

        ``myPR650 = Photometer(port, meterType="PR650")``

    jwp (12/2003)
    """
    def __init__(self, port, verbose=True):
        if type(port) in [int, float]:
            self.portNumber = port #add one so that port 1=COM1
            self.portString = 'COM%i' %self.portNumber#add one so that port 1=COM1
        else:
            self.portString = port
            self.portNumber=None
        self.isOpen=0
        self.lastQual=0
        
        #list of codes for returns
        self.code={'OK':'000\r\n',#this is returned after measure
            '18':'Light Low',#these is returned at beginning of data
            '10':'Light Low',
            '00':'OK'
            }
            
        try:
            #try to open the actual port
            if sys.platform =='darwin':
                self.com = serial.Serial(self.portString)
            elif sys.platform=='win32':
                self.com = serial.Serial(self.portString)
            else: log.error("I don't know how to handle serial ports on %s" %sys.platform)

            self.com.setBaudrate(9600)
            self.com.setParity('N')#none
            self.com.setStopbits(1)
            self.com.open()
            self.isOpen=1
            log.info("Successfully opened %s" %self.portString)
            self.OK = True
            time.sleep(1.0) #wait while establish connection
            reply = self.sendMessage('b1\n')        #turn on the backlight as feedback
        except:
            if verbose: log.error("Couldn't open serial port %s" %self.portString)
            self.OK = False
            return None #NB the user still receives a photometer object but with .OK=False

        #also check that the reply is what was expected
        if reply != self.codes['OK']:
            if verbose: log.error("pr650 isn't communicating")
            self.OK = False
        else:
            reply = self.sendMessage('s01,,,,,,01,1')#set command to make sure using right units etc...


    def sendMessage(self, message, timeout=0.5, DEBUG=False):
        """
        send a command to the photometer and wait an alloted
        timeout for a response (Timeout should be long for low
        light measurements)
        """
        if message[-1]!='\n': message+='\n'     #append a newline if necess

        #flush the read buffer first
        self.com.read(self.com.inWaiting())#read as many chars as are in the buffer

        #send the message
        self.com.write(message)
        self.com.flush()
            #time.sleep(0.1)  #PR650 gets upset if hurried!

        #get feedback (within timeout limit)
        self.com.setTimeout(timeout)
        log.debug(message)#send complete message
        if message in ['d5', 'd5\n']: #we need a spectrum which will have multiple lines
            return self.com.readlines()
        else:
            return self.com.readline()


    def measure(self, timeOut=30.0):
        t1 = time.clock()
        reply = self.sendMessage('m0\n', timeOut) #measure and hold data
        #using the hold data method the PR650 we can get interogate it
        #several times for a single measurement

        if reply==self.codes['OK']:
            raw = self.sendMessage('d2')
            xyz = string.split(raw,',')#parse into words
            self.lastQual = str(xyz[0])
            if self.codes[self.lastQual]=='OK':
                self.lastLum = float(xyz[3])
            else: self.lastLum = 0.0
        else:
            log.warning("Didn't collect any data (extend timeout?)")

    def getLastSpectrum(self, parse=True):
        """This retrieves the spectrum from the last call to ``.measure()``

        If ``parse=True`` (default):
        The format is a num array with 100 rows [nm, power]

        otherwise:
        The output will be the raw string from the PR650 and should then
        be passed to ``.parseSpectrumOutput()``. It's more
        efficient to parse R,G,B strings at once than each individually.
        """
        raw = self.sendMessage('d5')#returns a list where each list
        if parse:
            return self.parseSpectrumOutput(raw[2:])#skip the first 2 entries (info)
        else:
            return raw

    def parseSpectrumOutput(self, rawStr):
        """Parses the strings from the PR650 as received after sending
        the command 'd5'.
        The input argument "rawStr" can be the output from a single
        phosphor spectrum measurement or a list of 3 such measurements
        [rawR, rawG, rawB].
        """

        if len(rawStr)==3:
            RGB=True
            rawR=rawStr[0][2:]
            rawG=rawStr[1][2:]
            rawB=rawStr[2][2:]
            nPoints = len(rawR)
        else:
            RGB=False
            nPoints=len(rawStr)
            raw=raw[2:]

        nm = []
        if RGB:
            power=[[],[],[]]
            for n in range(nPoints):
                #each entry in list is a string like this:
                thisNm, thisR = string.split(rawR[n],',')
                thisR = thisR.replace('\r\n','')
                thisNm, thisG = string.split(rawG[n],',')
                thisG = thisG.replace('\r\n','')
                thisNm, thisB = string.split(rawB[n],',')
                thisB = thisB.replace('\r\n','')
                exec('nm.append(%s)' %thisNm)
                exec('power[0].append(%s)' %thisR)
                exec('power[1].append(%s)' %thisG)
                exec('power[2].append(%s)' %thisB)
                #if progDlg: progDlg.Update(n)
        else:
            power = []
            for n, point in enumerate(rawStr):
                #each entry in list is a string like this:
                thisNm, thisPower = string.split(point,',')
                nm.append(thisNm)
                power.append(thisPower.replace('\r\n',''))
            if progDlg: progDlg.Update(n)
        #if progDlg: progDlg.Destroy()
        return numpy.asarray(nm), numpy.asarray(power)


class MinoltaLS100:
    """
    A class to define a Minolta LS100 or LS110

        ``photom = MinoltaLS100(port, meterType="PR650")``

    jwp (12/2003)
    """
    def __init__(self, port, verbose=True):
        if type(port) in [int, float]:
            self.portNumber = port #add one so that port 1=COM1
            self.portString = 'COM%i' %self.portNumber#add one so that port 1=COM1
        else:
            self.portString = port
            self.portNumber=None
        self.isOpen=0
        self.lastQual=0
        self.lastLum=None
        
        self.codes={
            'ER00\r\n':'Unknown command sent to LS100/LS110',
            'ER01\r\n':'Setting error',
            'ER11\r\n':'Memory value error',
            'ER10\r\n':'Measuring range over',
            'ER19\r\n':'Display range over',
            'ER20\r\n':'EEPROM error (the photometer needs repair)',
            'ER30\r\n':'Photometer battery exhausted',}
        
        try:
            #try to open the actual port
            if sys.platform =='darwin':
                self.com = serial.Serial(self.portString)
            elif sys.platform=='win32':
                self.com = serial.Serial(self.portString)
            else: log.error("I don't know how to handle serial ports on %s" %sys.platform)

            self.com.setBaudrate(4800)
            self.com.setParity(serial.PARITY_EVEN)#none
            self.com.setStopbits(serial.STOPBITS_TWO)
            self.com.open()
            self.isOpen=1
            log.info("Successfully opened %s" %self.portString)
            self.OK = True
            time.sleep(0.5) #wait while establish connection
            reply = self.clearMemory()        #clear memory (and get OK)
        except:
            if verbose: log.error("Couldn't open serial port %s" %self.portString)
            self.OK = False
            return None #NB the user still receives a photometer object but with .OK=False

        #also check that the reply is what was expected
        self.OK = self.checkOK(reply)
        if self.OK:
            reply = self.sendMessage('MDS,04')#set to use absolute measurements
    def setMode(self, mode='04'):
        """Set the mode for measurements. Returns True (success) or False 
        
        '04' means absolute measurements.        
        '08' = peak
        '09' = cont
        
        See user manual for other modes
        """
        reply = self.sendMessage('MDS,%s' %mode)
        return self.checkOK(reply)
    def measure(self):
        """Measure the current luminance and set .lastLum to this value"""
        reply = self.sendMessage('MES')
        if self.checkOK(reply):
            print reply
            lum = float(reply[-6:])
        self.lastLum
    def checkOK(self,msg):
        """Check that the message from the photometer means OK. 
        If there's an error print it.
        
        Then return True (OK) or False.
        """        
        #also check that the reply is what was expected
        if reply[0:2] != 'OK':
            if verbose: log.error(self.codes[reply])
            return False
        else: 
            return True
        
    def sendMessage(self, message, timeout=0.5, DEBUG=False):
        """
        send a command to the photometer and wait an alloted
        timeout for a response (Timeout should be long for low
        light measurements)
        """
        if message[-1]!='\r\n': message+='\r\n'     #append a newline if necess

        #flush the read buffer first
        self.com.read(self.com.inWaiting())#read as many chars as are in the buffer

        #send the message
        self.com.write(message)
        self.com.flush()
            #time.sleep(0.1)  #PR650 gets upset if hurried!

        #get feedback (within timeout limit)
        self.com.setTimeout(timeout)
        log.debug(message)#send complete message
        retVal= self.com.readline()
        
        return retVal

    def measure(self, timeOut=30.0):
        t1 = time.clock()
        reply = self.sendMessage('m0\n', timeOut) #measure and hold data
        #using the hold data method the PR650 we can get interogate it
        #several times for a single measurement

        if reply==self.codes['OK']:
            raw = self.sendMessage('d2')
            xyz = string.split(raw,',')#parse into words
            self.lastQual = str(xyz[0])
            if self.codes[self.lastQual]=='OK':
                self.lastLum = float(xyz[3])
            else: self.lastLum = 0.0
        else:
            log.warning("Didn't collect any data (extend timeout?)")


