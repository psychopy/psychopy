:mod:`psychopy.serial` - functions for interacting with the serial port
=================================================================================

psychopy.serial is simply Chris Liechti's `pyserial <http://pyserial.sourceforge.net>`_ package. You can import it like this::
    
    from psychopy import serial
    ser = serial.Serial(0, 19200, timeout=1)  # open first serial port
    #ser = serial.Serial('/dev/ttyS1', 19200, timeout=1)#or something like this for mac/linux machines
    ser.write('someCommand')
    line = ser.readline()   # read a '\n' terminated line
    ser.close()
    
Ports are fully configurable with all the options you would expect of RS232 communications. See http://pyserial.sourceforge.net  for further details and documentation.

.. note:: currently PsychoPy packages pyserial version 1.3 which will not work on 64bit Windows machines. The latest version, 2.5 apparently does not depend on the win32 functions and should therefore work on 64-bit windows. In future PsychoPy will probably not package serial itself (except in the Standalone bundles) and simply add it as a required dependency.

    