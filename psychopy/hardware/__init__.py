import sys, glob
from psychopy import log
__all__=['forp','cedrus','minolta','pr', 'crs']


def findPhotometer(ports=None):
    """Try to find a connected photometer/photospectrometer! 
    PsychoPy will sweep a series of serial ports trying to open them. If a port 
    successfully opens then it will try to issue a command to the device. If it 
    responds with one of the expected values then it is assumed to be the 
    appropriate device. 
        
    :parameters:
        
        ports : a list of ports to search
            Each port can be a string (e.g. 'COM1', ''/dev/tty.Keyspan1.1') or a 
            number (for win32 comports only). If none are provided then PsychoPy 
            will sweep COM0-10 on win32 and search known likely port names on OS X.
            
    :returns:
    
        * An object representing the first photometer found
        * None if the ports didn't yield a valid response
        * -1 if there were not even any valid ports (suggesting a driver not being installed)
        
    e.g.::
    
        photom = findPhotometer() #sweeps ports 0 to 10 searching for a device
        print photom.getLum()
        if hasattr(photom, 'getSpectrum'):#can retrieve spectrum (e.g. a PR650)
            print photom.getSpectrum()
        
    """
    import minolta, pr
    photometers=[pr.PR650, minolta.LS100]#a list of photometer objects to test for
    
    #determine candidate ports
    if ports==None:
        if sys.platform=='darwin':
            ports=[]
            #try some known entries in /dev/tty. used by keyspan
            ports.extend(glob.glob('/dev/tty.USA*'))#keyspan twin adapter is usually USA28X13P1.1
            ports.extend(glob.glob('/dev/tty.Key*'))#some are Keyspan.1 or Keyserial.1
            ports.extend(glob.glob('/dev/tty.modem*'))#some are Keyspan.1 or Keyserial.1
            if len(ports)==0: 
                log.error("PscyhoPy couldn't find likely serial port in /dev/tty.* Check for " \
                    +"serial port name manually, check drivers installed etc...")
                return -1
        elif sys.platform=='win32':
            ports = range(11)
    elif type(ports) in [int,float]:
        ports=[ports] #so that we can iterate
        
    #go through each port in turn
    photom=None
    log.info('scanning serial ports...\n\t')
    log.console.flush()
    for thisPort in ports:
        log.info(str(thisPort)); log.console.flush()
        for Photometer in photometers:
            photom = Photometer(port=thisPort, verbose=True)
            if photom.OK: 
                log.info(' ...found a %s\n' %(photom.type)); log.console.flush()
                return photom#we found one so stop looking
            else:
                if photom.com and photom.com.isOpen: 
                    print 'closing port'
                    photom.com.close()

        #If we got here we didn't find one
        log.info('...nope!\n\t'); log.console.flush()
            
    return None