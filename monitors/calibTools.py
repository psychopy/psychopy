"""Tools to help with calibrations
"""
from calibData import *
from psychopy import log, event, serial
import psychopy.visual #must be imported this way because of mutual import
import time
__version__ = psychopy.__version__
    
import string, os, time, glob, cPickle, sys
from copy import deepcopy, copy

import numpy
import scipy.optimize as optim
from scipy import interpolate

DEBUG= False

#set and create (if necess) the data folder
#this will be the 
#   Linux/Mac:  ~/.PsychoPy/monitors
#   win32:   <UserDocs>/Application Data/PsychoPy/monitors
join = os.path.join
if sys.platform=='win32':
    #we used this for a while (until 0.95.4) but not the proper place for windows app data
    oldMonitorFolder = join(os.path.expanduser('~'),'.PsychoPy', 'monitors') #this is the folder that this file is stored in
    monitorFolder = join(os.environ['APPDATA'],'PsychoPy', 'monitors') #this is the folder that this file is stored in
    if os.path.isdir(oldMonitorFolder) and not os.path.isdir(MonitorFolder):
        os.renames(oldMonitorFolder, monitorFolder)
else:
    monitorFolder = join(os.environ['HOME'], '.PsychoPy' , 'monitors')
    
if not os.path.isdir(monitorFolder):
    os.makedirs(monitorFolder)
    
    #try to import monitors from old location (PsychoPy <0.93 used site-packages/monitors instead)
    #this only gets done if there was no existing .psychopy folder (and so no calib files)
    import glob, shutil #these are just to copy old calib files across
    try: 
        calibFiles = glob.glob('C:\Python24\Lib\site-packages\monitors\*.calib')
        for thisFile in calibFiles:
            thisPath, fileName = os.path.split(thisFile)
            shutil.copyfile(thisFile, join(monitorFolder,fileName))
    except:
        pass #never mind - the user will have to do it!


pr650code={'OK':'000\r\n',#this is returned after measure
    '18':'Light Low',#these is returned at beginning of data
    '10':'Light Low',
    '00':'OK'
    }

def findPR650(ports=None):
    """Try to find a COM port with a PR650 connected! Returns a Photometer object

    pr650 = findPR650([portNumber, anotherPortNumber])#tests specific ports only
    pr650 = findPR650() #sweeps ports 0 to 10 searching for PR650
    pr650= None if PR650 wasn't found
    """
    if ports==None:
        if sys.platform=='darwin':
            ports=[]
            #try some known entries in /dev/tty. used by keyspan
            ports.extend(glob.glob('/dev/tty.USA*'))#keyspan twin adapter is usually USA28X13P1.1
            ports.extend(glob.glob('/dev/tty.Key*'))#some are Keyspan.1 or Keyserial.1
            ports.extend(glob.glob('/dev/tty.modem*'))#some are Keyspan.1 or Keyserial.1
            if len(ports)==0: log.error("couldn't find likely serial port in /dev/tty.* Check for \
                serial port name manually, check drivers installed etc...")
        elif sys.platform=='win32':
            ports = range(11)
    elif type(ports) in [int,float]:
        ports=[ports] #so that we can iterate
    pr650=None
    log.info('scanning serial ports...\n\t')
    log.console.flush()
    for thisPort in ports:
        log.info(str(thisPort)); log.console.flush()
        pr650 = Photometer(port=thisPort, meterType="PR650", verbose=False)
        if pr650.OK:
            log.info(' ...OK\n'); log.console.flush()
            break
        else:
            log.info('...Nope!\n\t'); log.console.flush()
    return pr650

class Photometer:
    """
    A class to define a calibration device that connects to
    a serial port. Currently it must be a PR650, but could
    well be expanded in the future

        ``myPR650 = Photometer(port, meterType="PR650")``

    jwp (12/2003)
    """
    def __init__(self, port, meterType="PR650", verbose=True):
        if type(port) in [int, float]:
            self.portNumber = port #add one so that port 1=COM1
            self.portString = 'COM%i' %self.portNumber#add one so that port 1=COM1
        else:
            self.portString = port
            self.portNumber=None
        self.type=meterType
        self.isOpen=0
        self.lastQual=0

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
        if reply != pr650code['OK']:
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

        if reply==pr650code['OK']:
            raw = self.sendMessage('d2')
            xyz = string.split(raw,',')#parse into words
            self.lastQual = str(xyz[0])
            if pr650code[self.lastQual]=='OK':
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


class Monitor:
    """Creates a monitor object for storing calibration details.
    This will be loaded automatically from disk if the
    monitor name is already defined (see methods).

    Many settings from the stored monitor can easilly be overridden
    either by adding them as arguments during the initial call.

    **arguments**:

        - ``width, distance, gamma`` are details about the calibration
        - ``notes`` is a text field to store any useful info
        - ``useBits`` True, False, None
        - ``verbose`` True, False, None
        - ``currentCalib`` is a dict object containing various fields for a calibration. Use with caution
            since the dict may not contain all the necessary fields that a monitor object expects to find.

    **eg**:

    ``myMon = Monitor('sony500', distance=114)``
    Fetches the info on the sony500 and overrides its usual distance
    to be 114cm for this experiment.

    ``myMon = Monitor('sony500')``
        followed by...
    ``myMon['distance']=114``
        ...does the same!

    For both methods, if you then save  any modifications
    will be saved as well.
    """

    def __init__(self, name,
        width=None,
        distance=None,
        gamma=None,
        notes=None,
        useBits=None,
        verbose=True,
        currentCalib={},
    ):
        """
        """

        #make sure that all necessary settings have some value
        self.__type__ = 'psychoMonitor'
        self.name = name
        self.currentCalib = currentCalib
        self.currentCalibName = strFromDate(time.localtime())
        self.calibs = {}
        self.calibNames = []
        self._gammaInterpolator=None
        self._gammaInterpolator2=None
        self._loadAll()
        if len(self.calibNames)>0:
            self.setCurrent(-1) #will fetch previous vals if monitor exists
        else:
            self.newCalib()

        log.info(self.calibNames)

        #overide current monitor settings with the vals given
        if width: self.setWidth(width)
        if distance: self.setDistance(distance)
        if gamma: self.setGamma(gamma)
        if notes: self.setNotes(notes)
        if useBits!=None: self.setUseBits(useBits)

#functions to set params of current calibration
    def setSizePix(self, pixels):
        self.currentCalib['sizePix']=pixels
    def setWidth(self, width):
        """Of the viewable screen (cm)"""
        self.currentCalib['width']=width
    def setDistance(self, distance):
        """To the screen (cm)"""
        self.currentCalib['distance']=distance
    def setCalibDate(self, date=None):
        """Sets the calibration to a given date/time or to the current
        date/time if none given. (Also returns the date as set)"""
        if date==None:
            date=time.localtime()
        self.currentCalib['calibDate'] = date
        return date
    def setGamma(self, gamma):
        """Sets the gamma value(s) for the monitor.
        This only uses a single gamma value for the three
        guns, which is fairly approximate. Better to use
        setGammaGrid (which uses one gamma value for each gun)"""
        self.currentCalib['gamma']=gamma
    def setGammaGrid(self, gammaGrid):
        """Sets the min,max,gamma values for the each gun"""
        self.currentCalib['gammaGrid']=gammaGrid
    def setLineariseMethod(self, method):
        """Sets the method for linearising
        0 uses y=a+(bx)^gamma
        1 uses y=(a+bx)^gamma
        2 uses linear interpolation over the curve"""
        self.currentCalib['lineariseMethod']=method
    def setMeanLum(self, meanLum):
        """Records the mean luminance (for reference only)"""
        self.currentCalib['meanLum']=meanLum
    def setLumsPre(self, lums):
        """Sets the last set of luminance values measured during calibration"""
        self.currentCalib['lumsPre']=lums
    def setLumsPost(self, lums):
        """Sets the last set of luminance values measured AFTER calibration"""
        self.currentCalib['lumsPost']=lums
    def setLevelsPre(self, levels):
        """Sets the last set of luminance values measured during calibration"""
        self.currentCalib['levelsPre']=levels
    def setLevelsPost(self, levels):
        """Sets the last set of luminance values measured AFTER calibration"""
        self.currentCalib['levelsPost']=levels
    def setDKL_RGB(self, dkl_rgb):
        """sets the DKL->RGB conversion matrix for a chromatically
        calibrated monitor (matrix is a 3x3 num array)."""
        self.currentCalib['dkl_rgb']=dkl_rgb
    def setSpectra(self,nm,rgb):
        """sets the phosphor spectra measured by the spectrometer"""
        self.currentCalib['spectraNM']=nm
        self.currentCalib['spectraRGB']=rgb
    def setLMS_RGB(self, lms_rgb):
        """sets the LMS->RGB conversion matrix for a chromatically
        calibrated monitor (matrix is a 3x3 num array)."""
        self.currentCalib['lms_rgb']=lms_rgb
    def setPsychopyVersion(self, version):
        self.currentCalib['psychopyVersion'] = version
    def setNotes(self, notes):
        """For you to store notes about the calibration"""
        self.currentCalib['notes']=notes
    def setUseBits(self, usebits):
        self.currentCalib['usebits']=usebits

    #equivalent get functions
    def getSizePix(self):
        """Returns the size of the current calibration in pixels, or None if not defined"""
        if self.currentCalib.has_key('sizePix'):
            return self.currentCalib['sizePix']
        else:
            return None
    def getWidth(self):
        """Of the viewable screen in cm, or None if not known"""
        return self.currentCalib['width']
    def getDistance(self):
        """Returns distance from viewer to the screen in cm, or None if not known"""
        return self.currentCalib['distance']
    def getCalibDate(self):
        """As a python date object (convert to string using
        calibTools.strFromDate"""
        return self.currentCalib['calibDate']
    def getGamma(self):
        if self.currentCalib.has_key('gamma'):
            return self.currentCalib['gamma']
        else:
            return None
    def getGammaGrid(self):
        """Gets the min,max,gamma values for the each gun"""
        if self.currentCalib.has_key('gammaGrid'):
            return self.currentCalib['gammaGrid']
        else:
            return None
    def getLineariseMethod(self):
        """Gets the min,max,gamma values for the each gun"""
        if self.currentCalib.has_key('lineariseMethod'):
            return self.currentCalib['lineariseMethod']
        else:
            return None
    def getMeanLum(self):
        if self.currentCalib.has_key('meanLum'):
            return self.currentCalib['meanLum']
        else:
            return None
    def getLumsPre(self):
        """Gets the measured luminance values from last calibration"""
        if self.currentCalib.has_key('lumsPre'):
            return self.currentCalib['lumsPre']
        else: return None
    def getLumsPost(self):
        """Gets the measured luminance values from last calibration TEST"""
        if self.currentCalib.has_key('lumsPost'):
            return self.currentCalib['lumsPost']
        else: return None
    def getLevelsPre(self):
        """Gets the measured luminance values from last calibration"""
        if self.currentCalib.has_key('levelsPre'):
            return self.currentCalib['levelsPre']
        else: return None
    def getLevelsPost(self):
        """Gets the measured luminance values from last calibration TEST"""
        if self.currentCalib.has_key('levelsPost'):
            return self.currentCalib['levelsPost']
        else: return None
    def getSpectra(self):
        """Gets the wavelength values from the last spectrometer measurement
        (if available)

        usage:
            - nm, power = monitor.getSpectra()

            """
        if self.currentCalib.has_key('spectraNM'):
            return self.currentCalib['spectraNM'], self.currentCalib['spectraRGB']
        else:
            return None, None
    def getDKL_RGB(self, RECOMPUTE=True):
        """Returns the DKL->RGB conversion matrix.
        If one has been saved this will be returned.
        Otherwise, if power spectra are available for the
        monitor a matrix will be calculated.
        """
        if not self.currentCalib.has_key('dkl_rgb'): RECOMPUTE=True
        if RECOMPUTE:
            nm, power = self.getSpectra()
            if nm==None:
                return None
            else:
                return makeDKL2RGB(nm, power)
        else:
            return self.currentCalib['dkl_rgb']

    def getLMS_RGB(self, RECOMPUTE=True):
        """Returns the LMS->RGB conversion matrix.
        If one has been saved this will be returned.
        Otherwise (if power spectra are available for the
        monitor) a matrix will be calculated.
        """
        if not self.currentCalib.has_key('lms_rgb'): RECOMPUTE=True
        if RECOMPUTE:
            nm, power = self.getSpectra()
            if nm==None:
                return None
            else:
                return makeLMS2RGB(nm, power)
        else:
            return self.currentCalib['lms_rgb']

    def getPsychopyVersion(self):
        return self.currentCalib['psychopyVersion']
    def getNotes(self):
        """Notes about the calibration"""
        return self.currentCalib['notes']
    def getUseBits(self):
        """Was this calibration carried out witha a bits++ box"""
        return self.currentCalib['usebits']

    #other (admin functions)
    def _loadAll(self):
        """Fetches the calibs for this monitor from disk, storing them
        as self.calibs"""

        thisFileName = os.path.join(\
            monitorFolder,
            self.name+".calib")     #the name of the actual file

        if not os.path.exists(thisFileName):
            log.warning("Creating new monitor...")
            self.calibNames = []
        else:
            thisFile = open(thisFileName,'r')
            self.calibs = cPickle.load(thisFile)
            self.calibNames = self.calibs.keys()
            self.calibNames.sort()
            thisFile.close()

    def newCalib(self,calibName=None,
        width=None,
        distance=None,
        gamma=None,
        notes=None,
        useBits=False,
        verbose=True):
        """create a new (empty) calibration for this monitor and
        makes this the current calibration"""
        if calibName==None:
            calibName= strFromDate(time.localtime())
        #add to the list of calibrations
        self.calibNames.append(calibName)
        self.calibs[calibName]={}

        self.setCurrent(calibName)
        #populate with some default values:
        self.setCalibDate(time.localtime())
        self.setGamma(gamma)
        self.setWidth(width)
        self.setDistance(distance)
        self.setNotes(notes)
        self.setPsychopyVersion(__version__)
        self.setUseBits(useBits)
        newGrid=numpy.ones((4,3), 'd')
        newGrid[:,0] *= 0
        self.setGammaGrid(newGrid)
        self.setLineariseMethod(1)

    def setCurrent(self, calibration=-1):
        """
        Sets the current calibration for this monitor.
        Note that a single file can hold multiple calibrations each
        stored under a different key (the date it was taken)

        The argument is either a string (naming the calib) or an integer
        **eg**:

            ``myMon.setCurrent'mainCalib')``
            fetches the calibration named mainCalib
            ``calibName = myMon.setCurrent(0)``
            fetches the first calibration (alphabetically) for this monitor
            ``calibName = myMon.setCurrent(-1)``
            fetches the last alphabetical calib for this monitor (this is default)
            If default names are used for calibs (ie date/time stamp) then
            this will import the most recent.
        """
        #find the appropriate file
        #get desired calibration name if necess
        if type(calibration) in [str, unicode] and (calibration in self.calibNames):
            self.currentCalibName = calibration
        elif type(calibration)==int and calibration<=len(self.calibNames):
            self.currentCalibName = self.calibNames[calibration]
        else:
            print "No record of that calibration"
            return False

        self.currentCalib = self.calibs[self.currentCalibName]      #do the import
        log.info("Loaded calibration from:%s" %self.currentCalibName)

        return self.currentCalibName

    def delCalib(self,calibName):
        """Remove a specific calibration from the current monitor.
        Won't be finalised unless monitor is saved"""
        #remove from our list
        self.calibNames.remove(calibName)
        self.calibs.pop(calibName)
        if self.currentCalibName==calibName:
            self.setCurrent(-1)
        return 1

    def saveMon(self):
        """saves the current dict of calibs to disk"""
        thisFileName = os.path.join(monitorFolder,self.name+".calib")
        thisFile = open(thisFileName,'w')
        cPickle.dump(self.calibs, thisFile)
        thisFile.close()

    def copyCalib(self, calibName=None):
        """
        Stores the settings for the current calibration settings as new monitor.
        """
        if calibName==None:
            calibName= strFromDate(time.localtime())
        #add to the list of calibrations
        self.calibNames.append(calibName)
        self.calibs[calibName]= deepcopy(self.currentCalib)
        self.setCurrent(calibName)

    def lineariseLums(self, desiredLums, newInterpolators=False, overrideGamma=None):
        """lums should be uncalibrated luminance values (e.g. a linear ramp)
        ranging 0:1"""
        linMethod = self.getLineariseMethod()
        desiredLums = numpy.asarray(desiredLums)
        output = desiredLums*0.0 #needs same size as input

        #gamma interpolation
        if linMethod==3:
            lumsPre = copy(self.getLumsPre())
            if self._gammaInterpolator!=None and not newInterpolators:
                pass #we already have an interpolator
            elif lumsPre != None:
                log.info('Creating linear interpolation for gamma')
                #we can make an interpolator
                self._gammaInterpolator, self._gammaInterpolator2 =[],[]
                #each of these interpolators is a function!
                levelsPre = self.getLevelsPre()/255.0
                for gun in range(4):
                    lumsPre[gun,:] = (lumsPre[gun,:]-lumsPre[gun,0])/(lumsPre[gun,-1]-lumsPre[gun,0])#scale to 0:1
                    self._gammaInterpolator.append(interp1d(lumsPre[gun,:], levelsPre,kind='linear'))
                    #interpFunc = Interpolation.InterpolatingFunction((lumsPre[gun,:],), levelsPre)
                    #polyFunc = interpFunc.fitPolynomial(3)
                    #print polyFunc.coeff
                    #print polyFunc.derivative(0)
                    #print polyFunc.derivative(0.5)
                    #print polyFunc.derivative(1.0)
                    #self._gammaInterpolator2.append( [polyFunc.coeff])
            else:
                #no way to do this! Calibrate the monitor
                log.error("Can't do a gamma interpolation on your monitor without calibrating!")
                return desiredLums

            #then do the actual interpolations
            if len(desiredLums.shape)>1:
                for gun in range(3):
                    output[:,gun] = self._gammaInterpolator[gun+1](desiredLums[:,gun])#gun+1 because we don't want luminance interpolator

            else:#just luminance
                output = self._gammaInterpolator[0](desiredLums)

        #use a fitted gamma equation (1 or 2)
        elif linMethod in [1,2]:

            #get the min,max lums
            gammaGrid = self.getGammaGrid()
            if gammaGrid!=None:
                #if we have info about min and max luminance then use it
                minLum = gammaGrid[1,0]
                maxLum = gammaGrid[1:4,1]
                if overrideGamma is not None: gamma=overrideGamma
                else: gamma = gammaGrid[1:4,2]
                maxLumWhite = gammaGrid[0,1]
                gammaWhite = gammaGrid[0,2]
                if DEBUG: print 'using gamma grid'
                if DEBUG: print gammaGrid
            else:
                #just do the calculation using gamma
                minLum=0
                maxLumR, maxLumG, maxLumB, maxLumWhite= 1,1,1, 1
                gamma = self.gamma
                gammaWhite = num.average(self.gamma)

            #get the inverse gamma
            if len(desiredLums.shape)>1:
                for gun in range(3):
                    output[:,gun] = gammaInvFun(desiredLums[:,gun],
                        minLum, maxLum[gun], gamma[gun],eq=linMethod)
                #print gamma
            else:
                output = gammaInvFun(desiredLums,
                    minLum, maxLumWhite, gammaWhite,eq=linMethod)

        else:
            log.error("Don't know how to linearise with method %i" %linMethod)
            output = desiredLums

        #if DEBUG: print 'LUT:', output[0:10,1], '...'
        return output

class GammaCalculator:
    """Class for managing gamma tables

    **Parameters:**

    - inputs (required)= values at which you measured screen luminance either
        in range 0.0:1.0, or range 0:255. Should include the min
        and max of the monitor

    Then give EITHER "lums" or "gamma":

        - lums = measured luminance at given input levels
        - gamma = your own gamma value (single float)
        - bitsIN = number of values in your lookup table
        - bitsOUT = number of bits in the DACs

    myTable then generates attributes for gammaVal (if not supplied)
    and lut_corrected (a gamma corrected lookup table) which can be
    accessed by;

    myTable.gammaTable
    myTable.gammaVal

    """

    def __init__(self,
        inputs=[],
        lums=[],
        gammaVal=[],
        bitsIN=8,              #how values in the LUT
        bitsOUT=8,
        eq=1 ):   #how many values can the DACs output
        self.lumsInitial =lums
        self.inputs = inputs
        self.bitsIN = bitsIN
        self.bitsOUT = bitsOUT
        self.eq=eq
        #set or or get input levels
        if len(inputs)==0 and len(lums)>0:
            self.inputs = DACrange(len(lums))
        else:
            self.inputs = inputs

        #set or get gammaVal
        if len(lums)==0 and type(gammaVal)!=list:#we had initialised gammaVal as a list
            self.gammaVal = gammaVal
        elif len(lums)>0 and type(gammaVal)==list:
            self.gammaModel = self.fitGammaFun(self.inputs, self.lumsInitial)
            self.gammaVal = self.gammaModel[2]
            self.a = self.gammaModel[0]
            self.b = self.gammaModel[1]
        else:
            raise AttributeError, "gammaTable needs EITHER a gamma value or some luminance measures"

        #create corrected lookup table
        #self.gammaTable = self.invertGamma()

    def fitGammaFun(self, x, y):
        """
        Fits a gamma function to the monitor calibration data.

        **Parameters:**
            -xVals are the monitor look-up-table vals (either 0-255 or 0.0-1.0)
            -yVals are the measured luminances from a photometer/spectrometer

        """
        minGamma = 0.8
        maxGamma = 20.0
        gammaGuess=2.0
        y = numpy.asarray(y)
        minLum = min(y) #offset
        maxLum = max(y) #gain
        guess = gammaGuess
        #gamma = optim.fmin(self.fitGammaErrFun, guess, (x, y, minLum, maxLum))

        gamma = optim.fminbound(self.fitGammaErrFun,
            minGamma, maxGamma,
            args=(x,y, minLum, maxLum))
        return minLum, maxLum, gamma

    def fitGammaErrFun(self, params, x, y, minLum, maxLum):
        """
        Provides an error function for fitting gamma function

        (used by fitGammaFun)
        """
        gamma = params
        model = numpy.asarray(gammaFun(x, minLum, maxLum, gamma, eq=self.eq))
        SSQ = numpy.sum((model-y)**2)
        return SSQ

    #def invertGamma(self):
        #"""
        #uses self.gammaVal, self.bitsIN & self.bitsOUT to
        #create a gamma-corrected lookup table
        #"""
        #gamLUTOut = numpy.arange(0,1.0, 1.0/(2**self.bitsIN)) #ramp (of length bitsIN)
        #gamLUTOut = gamLUTOut**(1.0/self.gammaVal)    #inverse gamma
        #gamLUTOut *= 2**self.bitsOUT   #convert to output range
        #return gamLUTOut.astype(numpy.uint8)

def makeDKL2RGB(nm,powerRGB):
    """
    creates a 3x3 DKL->RGB conversion matrix from the spectral input powers
    """
    interpolateCones = interpolate.interp1d(wavelength_5nm, cones_SmithPokorny)
    interpolateJudd = interpolate.interp1d(wavelength_5nm, juddVosXYZ1976_5nm)
    judd = interpolateJudd(nm)
    cones=interpolateCones(nm)
    judd = numpy.asarray(judd)
    cones = numpy.asarray(cones)
    rgb_to_cones = numpy.dot(cones,numpy.transpose(powerRGB))
    # get LMS weights for Judd vl
    lumwt = numpy.dot(judd[1,:], numpy.linalg.pinv(cones))

    #cone weights for achromatic primary
    dkl_to_cones = numpy.dot(rgb_to_cones,[[1,0,0],[1,0,0],[1,0,0]])

    # cone weights for L-M primary
    dkl_to_cones[0,1] = lumwt[1]/lumwt[0]
    dkl_to_cones[1,1] = -1
    dkl_to_cones[2,1] = lumwt[2]

    # weights for S primary
    dkl_to_cones[0,2] = 0
    dkl_to_cones[1,2] = 0
    dkl_to_cones[2,2] = -1
    # Now have primaries expressed as cone excitations

    #get coefficients for cones ->monitor
    cones_to_rgb = numpy.linalg.inv(rgb_to_cones)

    #get coefficients for DKL cone weights to monitor
    dkl_to_rgb = numpy.dot(cones_to_rgb,dkl_to_cones)
    #normalise each col
    dkl_to_rgb[:,0] /= max(abs(dkl_to_rgb[:,0]))
    dkl_to_rgb[:,1] /= max(abs(dkl_to_rgb[:,1]))
    dkl_to_rgb[:,2] /= max(abs(dkl_to_rgb[:,2]))
    return dkl_to_rgb

def makeLMS2RGB(nm,powerRGB):
    """
    Creates a 3x3 LMS->RGB conversion matrix from the spectral input powers
    """
    
    interpolateCones = interpolate.interp1d(wavelength_5nm, cones_SmithPokorny)
    coneSens = interpolateCones(nm)
    rgb_to_cones = numpy.dot(coneSens,numpy.transpose(powerRGB))
    cones_to_rgb = numpy.linalg.inv(rgb_to_cones)

    whiteLMS = numpy.dot(numpy.ones(3,'f'), rgb_to_cones)
    #normalise each col by max
    #cones_to_rgb[:,0] /= max(abs(cones_to_rgb[:,0]))
    #cones_to_rgb[:,1] /= max(abs(cones_to_rgb[:,1]))
    #cones_to_rgb[:,2] /= max(abs(cones_to_rgb[:,2]))

    #normalise each col by whitepoint LMS
    cones_to_rgb[:,0] *= whiteLMS
    cones_to_rgb[:,1] *= whiteLMS
    cones_to_rgb[:,2] *= whiteLMS
    return cones_to_rgb


def getLumSeriesPR650(lumLevels=8,
    winSize=(800,600),
    monitor=None,
    gamma=1.0,
    allGuns = True,
    useBits=False,
    autoMode='auto',
    stimSize = 0.3,
    photometer='COM1'):
    """
    Automatically measures a series of gun values and measures
    the luminance with a PR650.

    **Parameters:**

    - ``photometer`` is the number of the serial port PR650 is connected to, or
        or Photometer object, from findPR650()
    - ``lumLevels`` (=8) can be scalar (number of tests evenly spaced in range 0-255)
        or an array of actual values to test
    - ``testGamma`` (=1.0) the gamma value at which to test
    - ``autoMode`` (='auto'). If 'auto' the program will present the screen
        and automatically take a measurement before moving on.
        If set to 'semi' the program will wait for a keypress before
        moving on but will not attempt to make a measurement (use this
        to make a measurement with your own device). Any other text will
        simply move on without pausing on each screen (use this to see
        that the visual system is performing as expected).

    """

    #setup pr650
    if isinstance(photometer, Photometer):
        pr650=photometer
    else:
        pr650 = Photometer(photometer)

    if pr650!=None:
        havePR650 = 1
    else: havePR650 = 0

    if useBits:
        #all gamma transforms will occur in calling the Bits++ LUT
        #which improves the precision (14bit not 8bit gamma)
        bitsMode='fast'
    else: bitsMode=None

    if gamma==1:
        initRGB= 0.5**(1/2.0)*2-1
    else: initRGB=0.0
    #setup screen and "stimuli"
    myWin = psychopy.visual.Window(fullscr = 0, rgb=initRGB, size=winSize,
        gamma=gamma,units='norm',monitor=monitor,allowGUI=False,
        bitsMode=bitsMode)

    instructions="Point the PR650 at the central bar. Hit a key when ready (or wait 30s)"
    message = psychopy.visual.TextStim(myWin, text = instructions,
        pos=(0,-0.8), rgb=-1.0)
    message.draw()

    noise = numpy.random.rand(512,512).round()*2-1
    backPatch = psychopy.visual.AlphaStim(myWin, tex=noise, size=2, units='norm',
        sf=[winSize[0]/512.0, winSize[1]/512.0])
    testPatch = psychopy.visual.AlphaStim(myWin,
        tex='sqr',
        size=stimSize,
        rgb=0.3,
        units='norm')
    backPatch.draw()
    testPatch.draw()

    myWin.flip()

    #stay like this until key press (or 30secs has passed)
    event.waitKeys(30)

    #what are the test values of luminance
    if (type(lumLevels) is int) or (type(lumLevels) is float):
        toTest= DACrange(lumLevels)
    else: toTest= numpy.asarray(lumLevels)

    if allGuns: guns=[0,1,2,3]#gun=0 is the white luminance measure
    else: allGuns=[0]
    lumsList = numpy.zeros((len(guns),len(toTest)), 'd') #this will hoold the measured luminance values
    #for each gun, for each value run test
    for gun in guns:
        for valN, DACval in enumerate(toTest):
            lum = DACval/127.5-1 #get into range -1:1
            #only do luminanc=-1 once
            if lum==-1 and gun>0: continue
            #set hte patch color
            if gun>0:
                rgb=[-1,-1,-1];
                rgb[gun-1]=lum
            else:
                rgb = [lum,lum,lum]

            backPatch.draw()
            testPatch.setRGB(rgb)
            testPatch.draw()

            myWin.flip()
            time.sleep(0.5)#allowing the screen to settle (no good reason!)
            #check for quit request
            for thisKey in event.getKeys():
                if thisKey in ['q', 'Q']:
                    myWin.close()
                    return numpy.array([])
            #take measurement
            if havePR650 and autoMode=='auto':
                pr650.measure()
                print "At DAC value %i\t: %.2fcd/m^2" % (DACval, pr650.lastLum)
                if lum==-1 or not allGuns:
                    #if the screen is black set all guns to this lum value!
                    lumsList[:,valN] = pr650.lastLum
                else:
                    #otherwise just this gun
                    lumsList[gun,valN] =  pr650.lastLum
            elif autoMode=='semi':
                print "At DAC value %i" % DACval
                event.waitKeys()

    myWin.close() #we're done with the visual stimuli
    if havePR650:       return lumsList
    else: return numpy.array([])


def getRGBspectra(stimSize=0.3, winSize=(800,600), photometer='COM1'):
    """
    usage:
        getRGBspectra(stimSize=0.3, winSize=(800,600), photometer='COM1')

    where:
        'photometer' could be a photometer object or a serial port name on which
        a photometer
    """
    if isinstance(photometer, Photometer):
        pr650=photometer
    else:
        #setup pr650
        pr650 = Photometer(photometer)
    if pr650!=None:             havePR650 = 1
    else:       havePR650 = 0

    #setup screen and "stimuli"
    myWin = psychopy.visual.Window(fullscr = 0, rgb=0.0, size=winSize,
        units='norm')

    instructions="Point the PR650 at the central square. Hit a key when ready"
    message = psychopy.visual.TextStim(myWin, text = instructions,
        pos=(0.0,-0.5), rgb=-1.0)
    message.draw()
    testPatch = psychopy.visual.AlphaStim(myWin,tex=None,
        size=stimSize*2,rgb=0.3)
    testPatch.draw()
    myWin.flip()
    #stay like this until key press (or 30secs has passed)
    event.waitKeys(30)
    spectra=[]
    for thisColor in [[1,-1,-1], [-1,1,-1], [-1,-1,1]]:
        #update stimulus
        testPatch.setRGB(thisColor)
        testPatch.draw()
        myWin.flip()
        #make measurement
        pr650.measure()
        spectra.append(pr650.getLastSpectrum(parse=False))
    myWin.close()
    nm, power = pr650.parseSpectrumOutput(spectra)
    return nm, power

def DACrange(n):
    """
    returns an array of n DAC values spanning 0-255
    """
    #NB python ranges exclude final val
    return numpy.arange(0.0,256.0,255.0/(n-1)).astype(numpy.uint8)
def getAllMonitors():
    currDir = os.getcwd()
    os.chdir(monitorFolder)
    monitorList=glob.glob('*.calib')
    for monitorN,thisName in enumerate(monitorList):
        monitorList[monitorN] = monitorList[monitorN][:-6]

    os.chdir(currDir)
    return monitorList

def gammaFun(xx, minLum, maxLum, gamma, eq=1):
    """
    Returns gamma-transformed luminance values.
    y = gammaFun(x, minLum, maxLum, gamma)

    a and b are calculated directly from minLum, maxLum, gamma
    **Parameters:**

        - **xx** are the input values (range 0-255 or 0.0-1.0)
        - **params** = [gamma, a, b]
        - **eq** determines the gamma equation used;
            eq==1[default]: yy = a + (b*xx)**gamma
            eq==2: yy = (a + b*xx)**gamma

    """
    #scale x to be in range minLum:maxLum
    xx = numpy.array(xx,'d')
    maxXX = max(xx)
    if maxXX>2.0:
        #xx = xx*maxLum/255.0 +minLum
        xx=xx/255.0
    else: #assume data are in range 0:1
        pass
        #xx = xx*maxLum + minLum

    #eq1: y = a + (b*xx)**gamma
    #eq2: y = (a+b*xx)**gamma
    if eq==1:
        a = minLum
        b = (maxLum-a)**(1/gamma)
        yy = a + (b*xx)**gamma
    elif eq==2:
        a = minLum**(1/gamma)
        b = maxLum**(1/gamma)-a
        yy = (a + b*xx)**gamma
    #print 'a=%.3f      b=%.3f' %(a,b)
    return yy

def gammaInvFun(yy, minLum, maxLum, gamma, eq=1):
    """Returns inverse gamma function for desired luminance values.
    x = gammaInvFun(y, minLum, maxLum, gamma)

    a and b are calculated directly from minLum, maxLum, gamma
    **Parameters:**

        - **xx** are the input values (range 0-255 or 0.0-1.0)
        - **minLum** = the minimum luminance of your monitor
        - **maxLum** = the maximum luminance of your monitor (for this gun)
        - **gamma** = the value of gamma (for this gun)
        - **eq** determines the gamma equation used;
            eq==1[default]: yy = a + (b*xx)**gamma
            eq==2: yy = (a + b*xx)**gamma

    """

    #x should be 0:1
    #y should be 0:1, then converted to minLum:maxLum

    #eq1: y = a + (b*xx)**gamma
    #eq2: y = (a+b*xx)**gamma
    if max(yy)==255:
        yy=numpy.asarray(yy)/255.0
    elif min(yy)<0 or max(yy)>1:
        log.warning('User supplied values outside the expected range (0:1)')

    #get into range minLum:maxLum
    yy = numpy.asarray(yy)*(maxLum - minLum) + minLum

    if eq==1:
        a = minLum
        b = (maxLum-a)**(1/gamma)
        xx = ((yy-a)**(1/gamma))/b
        minLUT = ((minLum-a)**(1/gamma))/b
        maxLUT = ((maxLum-a)**(1/gamma))/b
    elif eq==2:
        a = minLum**(1/gamma)
        b = maxLum**(1/gamma)-a
        xx = (yy**(1/gamma)-a)/b
        maxLUT = (maxLum**(1/gamma)-a)/b
        minLUT = (minLum**(1/gamma)-a)/b

    #then return to range (0:1)
    xx = xx/(maxLUT-minLUT) - minLUT
    return xx

def strFromDate(date):
    """Simply returns a string with a std format from a date object"""
    return time.strftime("%Y_%m_%d %H:%M", date)
