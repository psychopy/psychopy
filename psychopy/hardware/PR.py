"""PhotoResearch spectrophotometers
See http://www.photoresearch.com/

--------
"""
# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import core, log
import struct, sys, time

try: import serial
except: serial=False

class PR650:
    """An interface to the PR650 via the serial port.

    example usage::
    
        from psychopy.hardware.pr import PR650
        myPR650 = PR650(port)
        myPR650.getLum()#make a measurement
        nm, power = myPR650.getLastSpectrum()#get a power spectrum for the last measurement
        
    N.B. psychopy.hardware.findPhotometer() will locate and return any supported 
    device for you so you can also do::
    
        from psychopy import hardware
        phot = hardware.findPhotometer()
        print phot.getLum()
        
    :troubleshooting:
        
        Various messages are printed to the log regarding the function of this device, 
        but to see them you need to set the printing of the log to the correct level::
            from psychopy import log
            log.console.setLevel(log.ERROR)#error messages only
            log.console.setLevel(log.INFO)#will give a little more info
            log.console.setLevel(log.DEBUG)#will export a log of all communications
            
        If you're using a keyspan adapter (at least on OS X) be aware that it needs 
        a driver installed. Otherwise no ports wil be found.
        
        Also note that the attempt to connect to the PR650 must occur within the first
        few seconds after turning it on.
            
        Error messages:
        
        ``ERROR: Couldn't connect to Minolta LS100/110 on ____``:
            This likely means that the device is not connected to that port, or has not been 
            turned on with the F button depressed.
        
        ``ERROR: No reply from Photometer``:
            The port was found, the connection was made and an initial command worked,
            but then the device stopped communating. If the first measurement taken with 
            the device after connecting does not yield a reasonble intensity the device can 
            sulk (not a technical term!). The "[" on the display will disappear and you can no
            longer communicate with the device. Turn it off and on again (with F depressed)
            and use a reasonably bright screen for your first measurement. Subsequent
            measurements can be dark (or we really would be in trouble!!).
        
    """
    def __init__(self, port, verbose=None):
        if type(port) in [int, float]:
            self.portNumber = port #add one so that port 1=COM1
            self.portString = 'COM%i' %self.portNumber#add one so that port 1=COM1
        else:
            self.portString = port
            self.portNumber=None
        self.isOpen=0
        self.lastQual=0
        self.type='PR650'
        self.com=False
        self.OK=True#until we fail
        
        self.codes={'OK':'000\r\n',#this is returned after measure
            '18':'Light Low',#these is returned at beginning of data
            '10':'Light Low',
            '00':'OK'
            }
            
        #try to open the port
        if sys.platform in ['darwin', 'win32']: 
            try:self.com = serial.Serial(self.portString)
            except:
                self._error("Couldn't connect to port %s. Is it being used by another program?" %self.portString)
        else:
            self._error("I don't know how to handle serial ports on %s" %sys.platform)
        #setup the params for PR650 comms
        if self.OK:
            self.com.setBaudrate(9600)
            self.com.setParity('N')#none
            self.com.setStopbits(1)
            try:
                self.com.open()
                self.isOpen=1
            except:
                self._error("Couldn't open serial port %s" %self.portString)
        
        if self.OK:
            log.info("Successfully opened %s" %self.portString)
            time.sleep(0.1) #wait while establish connection
            reply = self.sendMessage('b1\n')        #turn on the backlight as feedback            
            if reply != self.codes['OK']:
                self._error("PR650 isn't communicating")
                
        if self.OK:
            reply = self.sendMessage('s01,,,,,,01,1')#set command to make sure using right units etc...
    
    def _error(self, msg):
        self.OK=False
        log.error(msg)
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
            xyz = raw.split(',')#parse into words
            self.lastQual = str(xyz[0])
            if self.codes[self.lastQual]=='OK':
                self.lastLum = float(xyz[3])
            else: self.lastLum = 0.0
        else:
            log.warning("Didn't collect any data (extend timeout?)")

    def getLum(self):
        """Makes a measurement and returns the luminance value
        """
        self.measure()
        return self.getLastLum()
    def getSpectrum(self, parse=True):
        """Makes a measurement and returns the current power spectrum
        
        If ``parse=True`` (default):
            The format is a num array with 100 rows [nm, power]

        If ``parse=False`` (default):
            The output will be the raw string from the PR650 and should then
            be passed to ``.parseSpectrumOutput()``. It's slightly more
            efficient to parse R,G,B strings at once than each individually.
        """
        self.measure()
        return self.getLastSpectrum(parse=parse)
    def getLastLum(self):
        """This retrieves the luminance (in cd/m**2) from the last call to ``.measure()``
        """
        return self.lastLum
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


class PR650new:
    """An interface to the PR650 via the serial port.

    example usage::
    
        from psychopy.hardware.pr import PR650
        myPR650 = PR650(port)
        myPR650.getLum()#make a measurement
        nm, power = myPR650.getLastSpectrum()#get a power spectrum for the last measurement
        
    N.B. psychopy.hardware.findPhotometer() will locate and return any supported 
    device for you so you can also do::
    
        from psychopy import hardware
        phot = hardware.findPhotometer()
        print phot.getLum()
        
    """
    def __init__(self, port, verbose=None):
        if type(port) in [int, float]:
            self.portNumber = port #add one so that port 1=COM1
            self.portString = 'COM%i' %self.portNumber#add one so that port 1=COM1
        else:
            self.portString = port
            self.portNumber=None
        self.isOpen=0
        self.lastQual=0
        self.lastLum=None
        self.type='PR650'
        
        if not serial:
            raise ImportError('The module serial is needed to connect to photometers. ' +\
                "On most systems this can be installed with\n\t easy_install pyserial")
                
        #list of codes for returns
        self.codes={'OK':'000\r\n',#this is returned after measure
            '18':'Light Low',#these is returned at beginning of data
            '10':'Light Low',
            '00':'OK'
            }
            
        #try to open the actual port
        if sys.platform =='darwin':
            self.com = serial.Serial(self.portString)
        elif sys.platform=='win32':
            self.com = serial.Serial(self.portString)
        else: log.error("I don't know how to handle serial ports on %s" %sys.platform)

        try:
            self.com.setBaudrate(9600)
            self.com.setParity('N')#none
            self.com.setStopbits(1)
            self.com.open()
            self.isOpen=1
            log.info("Successfully opened %s" %self.portString)
            self.OK = True
            time.sleep(1.0) #wait while establish connection
            reply = self.sendMessage('b1\n')        #turn on the backlight as feedback
            print 'pr650 reply:', reply
        except:
            print 'pr650 error'
            log.debug("Couldn't open serial port %s" %self.portString)
            self.OK = False
            self.com.close()#in this case we need to close the port again
            return None #NB the user still receives a photometer object but with .OK=False

        #also check that the reply is what was expected
        if reply != self.codes['OK']:
            log.debug("PR650 isn't communicating")
            self.OK = False
            self.com.close()#in this case we need to close the port again
        else:
            reply = self.sendMessage('s01,,,,,,01,1')#set command to make sure using right units etc...


    def sendMessage(self, message, timeout=0.5, DEBUG=False):
        """
        send a command to the photometer and wait an allotted
        timeout for a response (Timeout should be long for low
        light measurements)
        """
        if message[-1]!='\n': message+='\n'     #append a newline if necess

        #flush the read buffer first
        self.com.read(self.com.inWaiting())#read as many chars as are in the buffer

        #send the message
        self.com.write(message)
        self.com.flush()
        time.sleep(0.5)  #PR650 gets upset if hurried!

        #get feedback (within timeout limit)
        self.com.setTimeout(timeout)
        log.debug(message)#send complete message
        if message in ['d5', 'd5\n']: #we need a spectrum which will have multiple lines
            return self.com.readlines()
        else:
            print 'inwaiting:', self.com.inWaiting()
            return self.com.readline()


    def measure(self, timeOut=30.0):
        """Make a measurement with the device. For a PR650 the device is instructed 
        to make a measurement and then subsequent commands are issued to retrieve 
        info about that measurement
        """
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
    def getLum(self):
        """Makes a measurement and returns the luminance value
        """
        self.measure()
        return self.getLastLum()
    def getSpectrum(self, parse=True):
        """Makes a measurement and returns the current power spectrum
        
        If ``parse=True`` (default):
            The format is a num array with 100 rows [nm, power]

        If ``parse=False`` (default):
            The output will be the raw string from the PR650 and should then
            be passed to ``.parseSpectrumOutput()``. It's slightly more
            efficient to parse R,G,B strings at once than each individually.
        """
        self.measure()
        return self.getLastSpectrum(parse=parse)
    def getLastLum(self):
        """This retrieves the luminance (in cd/m**2) from the last call to ``.measure()``
        """
        return self.lastLum
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


