from psychopy import serial, core
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
        self._clearBuffer()
        
    def sendMessage(self, message):
        self.port.writelines(message)
        
    def _clearBuffer(self):
        """Empty the input buffer of all characters"""
        self.port.flushInput()
        #self.buffer=''
        
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
        """Returns an list of unique events (one event per button pressed)
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
    
        