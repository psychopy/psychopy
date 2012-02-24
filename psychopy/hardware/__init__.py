import sys, glob
from psychopy import logging
__all__=['forp','cedrus','minolta','pr', 'crs', 'ioLabs']


def findPhotometer(ports=None, device=None):
    """Try to find a connected photometer/photospectrometer! 
    PsychoPy will sweep a series of serial ports trying to open them. If a port 
    successfully opens then it will try to issue a command to the device. If it 
    responds with one of the expected values then it is assumed to be the 
    appropriate device. 
    
    :parameters:
        
        ports : a list of ports to search
            Each port can be a string (e.g. 'COM1', ''/dev/tty.Keyspan1.1') or a 
            number (for win32 comports only). If none are provided then PsychoPy 
            will sweep COM0-10 on win32 and search known likely port names on OS X
            and linux.
            
        device : string giving expected device (e.g. 'PR650', 'PR655', 'LS110').
            If this is not given then an attempt will be made to find a device of 
            any type, but this often fails
            
    :returns:
    
        * An object representing the first photometer found
        * None if the ports didn't yield a valid response
        * -1 if there were not even any valid ports (suggesting a driver not being installed)
        
    e.g.::
    
        photom = findPhotometer(device='PR655') #sweeps ports 0 to 10 searching for a PR655
        print photom.getLum()
        if hasattr(photom, 'getSpectrum'):#can retrieve spectrum (e.g. a PR650)
            print photom.getSpectrum()
        
    """
    import minolta, pr, crs
    if device.lower() in ['pr650']:
        photometers=[pr.PR650]
    elif device.lower() in ['pr655', 'pr670']:
        photometers=[pr.PR655]
    elif device.lower() in ['ls110', 'ls100']:
        photometers=[minolta.LS100]
    elif device.lower() in ['colorcal']:
        if not hasattr(crs, 'ColorCAL'):
            logging.error('ColorCAL support requires the pycrsltd library, version 0.1 or higher')
        photometers=[crs.ColorCAL]
    else:#try them all
        photometers=[pr.PR650, pr.PR655, minolta.LS100, crs.ColorCAL]#a list of photometer objects to test for
    
    #determine candidate ports
    if ports==None:
        if sys.platform=='darwin':
            ports=[]
            #try some known entries in /dev/tty. used by keyspan
            ports.extend(glob.glob('/dev/tty.USA*'))#keyspan twin adapter is usually USA28X13P1.1
            ports.extend(glob.glob('/dev/tty.Key*'))#some are Keyspan.1 or Keyserial.1
            ports.extend(glob.glob('/dev/tty.modem*'))#some are Keyspan.1 or Keyserial.1
            ports.extend(glob.glob('/dev/cu.usbmodem*'))#for PR650
            if len(ports)==0:
                logging.error("PsychoPy couldn't find any likely serial port in /dev/tty.* or /dev/cs* Check for " \
                    +"serial port name manually, check drivers installed etc...")
                return None
        elif sys.platform.startswith('linux'):
            ports = glob.glob('/dev/ttyACM?')#USB CDC devices (virtual serial ports)
            ports.extend(glob.glob("/dev/ttyUSB?")) # USB to serial adapters using the usb-serial kernel module
            ports.extend(glob.glob('/dev/ttyS?'))#genuine serial ports usually /dev/ttyS0 or /dev/ttyS1
        elif sys.platform=='win32':
            ports = range(11)
    elif type(ports) in [int,float]:
        ports=[ports] #so that we can iterate
        
    #go through each port in turn
    photom=None
    logging.info('scanning serial ports...')
    logging.flush()
    for thisPort in ports:
        logging.info('...'+str(thisPort)); logging.flush()
        for Photometer in photometers:
            photom = Photometer(port=thisPort)
            if photom.OK: 
                logging.info(' ...found a %s\n' %(photom.type)); logging.flush()
                #we're now sure that this is the correct device and that it's configured
                #now increase the number of attempts made to communicate for temperamental devices!
                if hasattr(photom,'setMaxAttempts'):photom.setMaxAttempts(10)
                return photom#we found one so stop looking
            else:
                if photom.com and photom.com.isOpen: 
                    logging.info('closing port')
                    photom.com.close()

        #If we got here we didn't find one
        logging.info('...nope!\n\t'); logging.flush()
            
    return None
