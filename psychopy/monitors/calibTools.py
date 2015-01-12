"""Tools to help with calibrations
"""
# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from calibData import *
from psychopy import __version__, logging, hardware
import time

try:
    import serial
    haveSerial=True
except:
    haveSerial=False
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
    oldMonitorFolder = join(os.path.expanduser('~'),'.psychopy2', 'monitors')
    monitorFolder = join(os.environ['APPDATA'],'psychopy2', 'monitors')
    if os.path.isdir(oldMonitorFolder) and not os.path.isdir(monitorFolder):
        os.renames(oldMonitorFolder, monitorFolder)
else:
    monitorFolder = join(os.environ['HOME'], '.psychopy2' , 'monitors')
# HACK! On system where `monitorFolder` contains special characters, for
# example because the Windows profile name does, `monitorFolder` must be
# decoded to Unicode to prevent errors later on. However, this is not a proper
# fix, since *everything* should be decoded to Unicode, and not just this
# specific pathname. Right now, errors will still occur if `monitorFolder` is
# combined with `str`-type objects that contain non-ASCII characters.
if isinstance(monitorFolder, str):
    monitorFolder = monitorFolder.decode(sys.getfilesystemencoding())

if not os.path.isdir(monitorFolder):
    os.makedirs(monitorFolder)

pr650code={'OK':'000\r\n',#this is returned after measure
    '18':'Light Low',#these is returned at beginning of data
    '10':'Light Low',
    '00':'OK'
    }

def findPR650(ports=None):
    """DEPRECATED (as of v.1.60.01). Use :func:`psychopy.hardware.findPhotometer()` instead, which
    finds a wider range of devices
    """
    logging.error("DEPRECATED (as of v.1.60.01). Use psychopy.hardware.findPhotometer() instead, which "\
    +"finds a wider range of devices")

    if ports is None:
        if sys.platform=='darwin':
            ports=[]
            #try some known entries in /dev/tty. used by keyspan
            ports.extend(glob.glob('/dev/tty.USA*'))#keyspan twin adapter is usually USA28X13P1.1
            ports.extend(glob.glob('/dev/tty.Key*'))#some are Keyspan.1 or Keyserial.1
            ports.extend(glob.glob('/dev/tty.modem*'))#some are Keyspan.1 or Keyserial.1
            if len(ports)==0: logging.error("couldn't find likely serial port in /dev/tty.* Check for \
                serial port name manually, check drivers installed etc...")
        elif sys.platform=='win32':
            ports = range(20)
    elif type(ports) in [int,float]:
        ports=[ports] #so that we can iterate
    pr650=None
    logging.info('scanning serial ports...\n\t')
    logging.console.flush()
    for thisPort in ports:
        logging.info(str(thisPort)); logging.console.flush()
        pr650 = Photometer(port=thisPort, meterType="PR650", verbose=False)
        if pr650.OK:
            logging.info(' ...OK\n'); logging.console.flush()
            break
        else:
            pr650=None
            logging.info('...Nope!\n\t'); logging.console.flush()
    return pr650

class Photometer:
    """
    Photometer class is deprecated (as of v.1.60.00):

    Import explicit flavour of photometer as needed e.g.::

        from psychopy.hardware.pr import PR650
        from psychopy.hardware.minolta import LS100

    Or simply::

        from psychopy import hardware
        photometer = hardware.findPhotometer()

    """
    def __init__(self, port, meterType="PR650", verbose=True):
        logging.error(self.__doc__)
        sys.exit()

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
        autoLog=True ):
        """
        """

        #make sure that all necessary settings have some value
        self.__type__ = 'psychoMonitor'
        self.name = name
        self.autoLog = autoLog
        self.currentCalib = currentCalib
        self.currentCalibName = strFromDate(time.localtime())
        self.calibs = {}
        self.calibNames = []
        self._gammaInterpolator=None
        self._gammaInterpolator2=None
        self._loadAll()
        if len(self.calibNames)>0:
            self.setCurrent(-1) #will fetch previous vals if monitor exists
            if self.autoLog:
                logging.info('Loaded monitor calibration from %s' %self.calibNames)
        else:
            self.newCalib()
            logging.warning("Monitor specification not found. Creating a temporary one...")

        #overide current monitor settings with the vals given
        if width: self.setWidth(width)
        if distance: self.setDistance(distance)
        if gamma: self.setGamma(gamma)
        if notes: self.setNotes(notes)
        if useBits!=None: self.setUseBits(useBits)

    def gammaIsDefault(self):
        """Determine whether we're using the default gamma values
        """
        thisGamma = self.getGamma()
        #run the test just on this
        if thisGamma is None \
            or numpy.alltrue(numpy.array(thisGamma)==numpy.array([1,1,1])):
            return True
        else:
            return False

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
        if date is None:
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
        self.currentCalib['linearizeMethod']=method
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
        self.setPsychopyVersion(__version__)
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
        if 'sizePix' in self.currentCalib:
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
        if 'gammaGrid' in self.currentCalib and not numpy.alltrue(self.getGammaGrid()[1:, 2]==1):
            return self.getGammaGrid()[1:, 2]
        elif 'gamma' in self.currentCalib:
            return self.currentCalib['gamma']
        else:
            return None
    def getGammaGrid(self):
        """Gets the min,max,gamma values for the each gun"""
        if 'gammaGrid' in self.currentCalib:
            # Make sure it's an array, so you can look at the shape
            grid = numpy.asarray(self.currentCalib['gammaGrid'])
            if grid.shape!=[4,6]:
                newGrid = numpy.zeros([4,6],'f')*numpy.nan#start as NaN
                newGrid[:grid.shape[0],:grid.shape[1]]=grid
                grid=self.currentCalib['gammaGrid']=newGrid
            return grid
        else:
            return None
    def getLinearizeMethod(self):
        """Gets the min,max,gamma values for the each gun"""
        if 'linearizeMethod' in self.currentCalib:
            return self.currentCalib['linearizeMethod']
        elif 'lineariseMethod' in self.currentCalib:
            return self.currentCalib['lineariseMethod']
        else:
            return None
    def getMeanLum(self):
        if 'meanLum' in self.currentCalib:
            return self.currentCalib['meanLum']
        else:
            return None
    def getLumsPre(self):
        """Gets the measured luminance values from last calibration"""
        if 'lumsPre' in self.currentCalib:
            return self.currentCalib['lumsPre']
        else: return None
    def getLumsPost(self):
        """Gets the measured luminance values from last calibration TEST"""
        if 'lumsPost' in self.currentCalib:
            return self.currentCalib['lumsPost']
        else: return None
    def getLevelsPre(self):
        """Gets the measured luminance values from last calibration"""
        if 'levelsPre' in self.currentCalib:
            return self.currentCalib['levelsPre']
        else: return None
    def getLevelsPost(self):
        """Gets the measured luminance values from last calibration TEST"""
        if 'levelsPost' in self.currentCalib:
            return self.currentCalib['levelsPost']
        else: return None
    def getSpectra(self):
        """Gets the wavelength values from the last spectrometer measurement
        (if available)

        usage:
            - nm, power = monitor.getSpectra()

            """
        if 'spectraNM' in self.currentCalib:
            return self.currentCalib['spectraNM'], self.currentCalib['spectraRGB']
        else:
            return None, None
    def getDKL_RGB(self, RECOMPUTE=False):
        """Returns the DKL->RGB conversion matrix.
        If one has been saved this will be returned.
        Otherwise, if power spectra are available for the
        monitor a matrix will be calculated.
        """
        if not 'dkl_rgb' in self.currentCalib: RECOMPUTE=True
        if RECOMPUTE:
            nm, power = self.getSpectra()
            if nm is None:
                return None
            else:
                return makeDKL2RGB(nm, power)
        else:
            return self.currentCalib['dkl_rgb']

    def getLMS_RGB(self, RECOMPUTE=False):
        """Returns the LMS->RGB conversion matrix.
        If one has been saved this will be returned.
        Otherwise (if power spectra are available for the
        monitor) a matrix will be calculated.
        """
        if not 'lms_rgb' in self.currentCalib: RECOMPUTE=True
        if RECOMPUTE:
            nm, power = self.getSpectra()
            if nm is None:
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
        if calibName is None:
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
        thisFile = open(thisFileName,'wb')
        cPickle.dump(self.calibs, thisFile)
        thisFile.close()

    def copyCalib(self, calibName=None):
        """
        Stores the settings for the current calibration settings as new monitor.
        """
        if calibName is None:
            calibName= strFromDate(time.localtime())
        #add to the list of calibrations
        self.calibNames.append(calibName)
        self.calibs[calibName]= deepcopy(self.currentCalib)
        self.setCurrent(calibName)

    def lineariseLums(self, desiredLums, newInterpolators=False, overrideGamma=None):
        """lums should be uncalibrated luminance values (e.g. a linear ramp)
        ranging 0:1"""
        linMethod = self.getLinearizeMethod()
        desiredLums = numpy.asarray(desiredLums)
        output = desiredLums*0.0 #needs same size as input

        #gamma interpolation
        if linMethod==3:
            lumsPre = copy(self.getLumsPre())
            if self._gammaInterpolator!=None and not newInterpolators:
                pass #we already have an interpolator
            elif lumsPre != None:
                if self.autoLog:
                    logging.info('Creating linear interpolation for gamma')
                #we can make an interpolator
                self._gammaInterpolator, self._gammaInterpolator2 =[],[]
                #each of these interpolators is a function!
                levelsPre = self.getLevelsPre()/255.0
                for gun in range(4):
                    lumsPre[gun,:] = (lumsPre[gun,:]-lumsPre[gun,0])/(lumsPre[gun,-1]-lumsPre[gun,0])#scale to 0:1
                    self._gammaInterpolator.append(interp1d(lumsPre[gun,:], levelsPre,kind='linear'))
                    #interpFunc = Interpolation.InterpolatingFunction((lumsPre[gun,:],), levelsPre)
                    #polyFunc = interpFunc.fitPolynomial(3)
                    #self._gammaInterpolator2.append( [polyFunc.coeff])
            else:
                #no way to do this! Calibrate the monitor
                logging.error("Can't do a gamma interpolation on your monitor without calibrating!")
                return desiredLums

            #then do the actual interpolations
            if len(desiredLums.shape)>1:
                for gun in range(3):
                    output[:,gun] = self._gammaInterpolator[gun+1](desiredLums[:,gun])#gun+1 because we don't want luminance interpolator

            else:#just luminance
                output = self._gammaInterpolator[0](desiredLums)

        #use a fitted gamma equation (1 or 2)
        elif linMethod in [1,2,4]:

            #get the min,max lums
            gammaGrid = self.getGammaGrid()
            if gammaGrid!=None:
                #if we have info about min and max luminance then use it
                minLum = gammaGrid[1,0]
                maxLum = gammaGrid[1:4,1]
                b = gammaGrid[1:4,4]
                if overrideGamma is not None: gamma=overrideGamma
                else: gamma = gammaGrid[1:4,2]
                maxLumWhite = gammaGrid[0,1]
                gammaWhite = gammaGrid[0,2]
                if self.autoLog:
                    logging.debug('using gamma grid'+str(gammaGrid))
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
                        minLum, maxLum[gun], gamma[gun],eq=linMethod, b=b[gun])
            else:
                output = gammaInvFun(desiredLums,
                    minLum, maxLumWhite, gammaWhite,eq=linMethod)

        else:
            logging.error("Don't know how to linearise with method %i" %linMethod)
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

    myTable.gammaModel
    myTable.gamma

    """

    def __init__(self,
        inputs=[],
        lums=[],
        gamma=None,
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
        if len(lums)==0 or gamma!=None:#user is specifying their own gamma value
            self.gamma = gamma
        elif len(lums)>0:
            self.min, self.max, self.gammaModel = self.fitGammaFun(self.inputs, self.lumsInitial)
            if eq==4:
                self.gamma, self.a, self.k = self.gammaModel
                self.b = (lums[0]-self.a)**(1.0/self.gamma)
            else:
                self.gamma=self.gammaModel[0]
                self.a = self.b = self.k = None
        else:
            raise AttributeError, "gammaTable needs EITHER a gamma value or some luminance measures"

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
        minLum = y[0]
        maxLum = y[-1]
        if self.eq==4:
            aGuess = minLum/5.0
            kGuess = (maxLum - aGuess)**(1.0/gammaGuess) - aGuess
            guess = [gammaGuess, aGuess, kGuess]
            bounds = [[0.8,5.0],[0.00001,minLum-0.00001],[2,200]]
        else:
            guess = [gammaGuess]
            bounds = [[0.8,5.0]]
        #gamma = optim.fmin(self.fitGammaErrFun, guess, (x, y, minLum, maxLum))
#        gamma = optim.fminbound(self.fitGammaErrFun,
#            minGamma, maxGamma,
#            args=(x,y, minLum, maxLum))
        params = optim.fmin_tnc(self.fitGammaErrFun, numpy.array(guess), approx_grad=True,
            args = (x,y, minLum, maxLum), bounds=bounds, messages=0)
        return minLum, maxLum, params[0]

    def fitGammaErrFun(self, params, x, y, minLum, maxLum):
        """
        Provides an error function for fitting gamma function

        (used by fitGammaFun)
        """
        if self.eq==4:
            gamma,a,k = params
            model = numpy.asarray(gammaFun(x, minLum, maxLum, gamma, eq=self.eq, a=a, k=k))
        else:
            gamma = params[0]
            model = numpy.asarray(gammaFun(x, minLum, maxLum, gamma, eq=self.eq))
        SSQ = numpy.sum((model-y)**2)
        return SSQ

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

    return cones_to_rgb

def getLumSeries(lumLevels=8,
    winSize=(800,600),
    monitor=None,
    gamma=1.0,
    allGuns = True,
    useBits=False,
    autoMode='auto',
    stimSize = 0.3,
    photometer=None,
    screen = 0):
    """
    Automatically measures a series of gun values and measures
    the luminance with a photometer.

    :Parameters:

        photometer : a photometer object
            e.g. a :class:`~psychopy.hardware.pr.PR65` or
            :class:`~psychopy.hardware.minolta.LS100` from hardware.findPhotometer()

        lumLevels : (default=8)
            array of values to test or single value for n evenly spaced test values

        gamma : (default=1.0) the gamma value at which to test

        autoMode : 'auto' or 'semi'(='auto')

            If 'auto' the program will present the screen
            and automatically take a measurement before moving on.

            If set to 'semi' the program will wait for a keypress before
            moving on but will not attempt to make a measurement (use this
            to make a measurement with your own device).

            Any other value will simply move on without pausing on each screen (use this to see
            that the display is performing as expected).

    """
    import psychopy.event, psychopy.visual
    from psychopy import core
    if photometer is None:
        havePhotom = False
    elif not hasattr(photometer, 'getLum'):
        logging.error("photometer argument to monitors.getLumSeries should be a type of photometer "+\
            "object, not a %s" %type(photometer))
        return None
    else: havePhotom = True

    if useBits:
        #all gamma transforms will occur in calling the Bits++ LUT
        #which improves the precision (14bit not 8bit gamma)
        bitsMode='fast'
    else: bitsMode=None

    if gamma==1:
        initRGB= 0.5**(1/2.0)*2-1
    else: initRGB=0.8
    #setup screen and "stimuli"
    myWin = psychopy.visual.Window(fullscr = 0, size=winSize,
        gamma=gamma,units='norm',monitor=monitor,allowGUI=True,winType='pyglet',
        bitsMode=bitsMode, screen=screen)
    instructions="Point the photometer at the central bar. Hit a key when ready (or wait 30s)"
    message = psychopy.visual.TextStim(myWin, text = instructions,height=0.1,
        pos=(0,-0.85), rgb=[1,-1,-1])
    noise = numpy.random.rand(512,512).round()*2-1
    backPatch = psychopy.visual.PatchStim(myWin, tex=noise, size=2, units='norm',
        sf=[winSize[0]/512.0, winSize[1]/512.0])
    testPatch = psychopy.visual.PatchStim(myWin,
        tex='sqr',
        size=stimSize,
        rgb=initRGB,
        units='norm')

    #stay like this until key press (or 30secs has passed)
    waitClock=core.Clock()
    tRemain=30
    while tRemain>0:
        tRemain = 30-waitClock.getTime()
        instructions="Point the photometer at the central white bar. Hit a key when ready (or wait %iss)" %tRemain
        backPatch.draw()
        testPatch.draw()
        message.setText(instructions, log=False)
        message.draw()
        myWin.flip()
        if len(psychopy.event.getKeys()):
            break#we got a keypress so move on

    if autoMode!='semi':
        message.setText('Q to quit at any time')
    else:
        message.setText('Spacebar for next patch')

    if havePhotom and photometer.type=='LS100': #LS100 likes to take at least one bright measurement
        junk=photometer.getLum()

    #what are the test values of luminance
    if (type(lumLevels) is int) or (type(lumLevels) is float):
        toTest= DACrange(lumLevels)
    else: toTest= numpy.asarray(lumLevels)

    if allGuns: guns=[0,1,2,3]#gun=0 is the white luminance measure
    else: allGuns=[0]
    lumsList = numpy.zeros((len(guns),len(toTest)), 'd') #this will hold the measured luminance values
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
            testPatch.setColor(rgb)
            testPatch.draw()
            message.draw()
            myWin.flip()

            time.sleep(0.2)#allowing the screen to settle (no good reason!)

            #take measurement
            if havePhotom and autoMode=='auto':
                actualLum = photometer.getLum()
                print "At DAC value %i\t: %.2fcd/m^2" % (DACval, actualLum)
                if lum==-1 or not allGuns:
                    #if the screen is black set all guns to this lum value!
                    lumsList[:,valN] = actualLum
                else:
                    #otherwise just this gun
                    lumsList[gun,valN] =  actualLum

                #check for quit request
                for thisKey in psychopy.event.getKeys():
                    if thisKey in ['q', 'Q', 'escape']:
                        myWin.close()
                        return numpy.array([])

            elif autoMode=='semi':
                print "At DAC value %i" % DACval

                done = False
                while not done:
                    #check for quit request
                    for thisKey in psychopy.event.getKeys():
                        if thisKey in ['q', 'Q', 'escape']:
                            myWin.close()
                            return numpy.array([])
                        elif thisKey in [' ','space']:
                            done = True

    myWin.close() #we're done with the visual stimuli
    if havePhotom: return lumsList
    else: return numpy.array([])


def getLumSeriesPR650(lumLevels=8,
    winSize=(800,600),
    monitor=None,
    gamma=1.0,
    allGuns = True,
    useBits=False,
    autoMode='auto',
    stimSize = 0.3,
    photometer='COM1'):
    """DEPRECATED (since v1.60.01): Use :class:`psychopy.monitors.getLumSeries()` instead"""

    logging.warning("DEPRECATED (since v1.60.01): Use monitors.getLumSeries() instead")
    val= getLumSeries(lumLevels,
        winSize,monitor,
        gamma,allGuns, useBits,
        autoMode,stimSize,photometer)
    return val

def getRGBspectra(stimSize=0.3, winSize=(800,600), photometer='COM1'):
    """
    usage:
        getRGBspectra(stimSize=0.3, winSize=(800,600), photometer='COM1')

    :params:

        - 'photometer' could be a photometer object or a serial port name on which
        a photometer might be found (not recommended)
    """
    import psychopy.event, psychopy.visual

    if hasattr(photometer, 'getLastSpectrum'):
        photom=photometer
    else:
        #setup photom
        photom = hardware.Photometer(photometer)
    if photom!=None: havephotom = 1
    else:       havephotom = 0

    #setup screen and "stimuli"
    myWin = psychopy.visual.Window(fullscr = 0, rgb=0.0, size=winSize,
        units='norm')

    instructions="Point the photometer at the central square. Hit a key when ready"
    message = psychopy.visual.TextStim(myWin, text = instructions, height=0.1,
        pos=(0.0,-0.8), rgb=-1.0)
    message.draw()
    testPatch = psychopy.visual.PatchStim(myWin,tex=None,
        size=stimSize*2,rgb=0.3)
    testPatch.draw()
    myWin.flip()
    #stay like this until key press (or 30secs has passed)
    psychopy.event.waitKeys(30)
    spectra=[]
    for thisColor in [[1,-1,-1], [-1,1,-1], [-1,-1,1]]:
        #update stimulus
        testPatch.setColor(thisColor)
        testPatch.draw()
        myWin.flip()
        #make measurement
        photom.measure()
        spectra.append(photom.getLastSpectrum(parse=False))
    myWin.close()
    nm, power = photom.parseSpectrumOutput(spectra)
    return nm, power

def DACrange(n):
    """
    returns an array of n DAC values spanning 0-255
    """
    #NB python ranges exclude final val
    return numpy.arange(0.0,256.0,255.0/(n-1)).astype(numpy.uint8)
def getAllMonitors():
    """Find the names of all monitors for which calibration files exist
    """
    monitorList = glob.glob(os.path.join(monitorFolder, '*.calib'))
    split = os.path.split
    splitext = os.path.splitext
    #skip the folder and the extension for each file
    monitorList = [splitext(split(thisFile)[-1])[0] for thisFile in monitorList]
    return monitorList

def gammaFun(xx, minLum, maxLum, gamma, eq=1, a=None, b=None, k=None):
    """
    Returns gamma-transformed luminance values.
    y = gammaFun(x, minLum, maxLum, gamma)

    a and b are calculated directly from minLum, maxLum, gamma

    **Parameters:**

        - **xx** are the input values (range 0-255 or 0.0-1.0)
        - **minLum** = the minimum luminance of your monitor
        - **maxLum** = the maximum luminance of your monitor (for this gun)
        - **gamma** = the value of gamma (for this gun)


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
    #eq4: y = a+(b+k*xx)**gamma #Pelli & Zhang 1991
    if eq==1:
        a = minLum
        b = (maxLum-a)**(1/gamma)
        yy = a + (b*xx)**gamma
    elif eq==2:
        a = minLum**(1/gamma)
        b = maxLum**(1/gamma)-a
        yy = (a + b*xx)**gamma
    elif eq==3:#NB method 3 was an interpolation method that didn't work well
        pass
    elif eq==4:
        nMissing = sum([a is None, b is None, k is None])
        #check params
        if nMissing>1:
            raise AttributeError, "For eq=4, gammaFun needs 2 of a,b,k to be specified"
        elif nMissing==1:
            if a is None:
                a = minLum-b**(1.0/gamma)       #when y=min, x=0
            elif b is None:
                if a>=minLum:
                    b=0.1**(1.0/gamma)#can't take inv power of -ve
                else:
                    b = (minLum-a)**(1.0/gamma)     #when y=min, x=0
            elif k is None:
                k = (maxLum - a)**(1.0/gamma) - b #when y=max, x=1
        #this is the same as Pelli and Zhang (but different inverse function)
        yy = a+(b+k*xx)**gamma #Pelli and Zhang (1991)

    return yy

def gammaInvFun(yy, minLum, maxLum, gamma, b=None, eq=1):
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
    #eq4: y = a+(b+kxx)**gamma
    if max(yy)==255:
        yy=numpy.asarray(yy,'d')/255.0
    elif min(yy)<0 or max(yy)>1:
        logging.warning('User supplied values outside the expected range (0:1)')
    else:
        yy=numpy.asarray(yy,'d')

    if eq==1:
        xx=numpy.asarray(yy)**(1.0/gamma)
    elif eq==2:
        yy = numpy.asarray(yy)*(maxLum - minLum) + minLum
        a = minLum**(1/gamma)
        b = maxLum**(1/gamma)-a
        xx = (yy**(1/gamma)-a)/b
        maxLUT = (maxLum**(1/gamma)-a)/b
        minLUT = (minLum**(1/gamma)-a)/b
        xx = xx/(maxLUT-minLUT) - minLUT
    elif eq==3:#NB method 3 was an interpolation method that didn't work well
        pass
    elif eq==4:
        #this is not the same as Zhang and Pelli's inverse
        #see http://www.psychopy.org/general/gamma.html for derivation
        a = minLum-b**gamma
        k = (maxLum-a)**(1./gamma) - b
        xx = (((1-yy)*b**gamma + yy*(b+k)**gamma)**(1/gamma)-b)/k

    #then return to range (0:1)
    #xx = xx/(maxLUT-minLUT) - minLUT
    return xx

def strFromDate(date):
    """Simply returns a string with a std format from a date object"""
    return time.strftime("%Y_%m_%d %H:%M", date)
