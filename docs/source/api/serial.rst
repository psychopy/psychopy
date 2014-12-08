:mod:`psychopy.serial` - functions for interacting with the serial port
=================================================================================

PsychoPy is compatible with Chris Liechti's `pyserial <http://pyserial.sourceforge.net>`_ package. You can use it like this::
    
    import serial
    ser = serial.Serial(0, 19200, timeout=1)  # open first serial port
    #ser = serial.Serial('/dev/ttyS1', 19200, timeout=1)#or something like this for Mac/Linux machines
    ser.write('someCommand')
    line = ser.readline()   # read a '\n' terminated line
    ser.close()
    
Ports are fully configurable with all the options you would expect of RS232 communications. See http://pyserial.sourceforge.net  for further details and documentation.

pyserial is packaged in the Standalone (Windows and Mac distributions), for manual installations you should install this yourself.

    
