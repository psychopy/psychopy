"""
ioSync MCU Program
===================

Analog Inputs
~~~~~~~~~~~~~~

- Add support for specifying a threshold level for each analog input; 
  effectively allowing an AI to be turned into a user adjustable DI. When
  the analog input value crosses threshold (up or down), generate a 
  DigitalInputEvent.
  
- Add support to specify which of the 8 analog inputs should actually be read
  during recording.

- User adjustable analog input settings:
    - resolution
    - HW level averaging count
    - AREF source
    - sampling rate ??
        
Digital Inputs
~~~~~~~~~~~~~~~

- Add support to specify which of the 8 digital inputs should actually be read
  during recording. The others can effectively be masked off.

- User adjustable digital input settings:
    - sampling rate ??

- Change DI reads to use interupts.

Misc.
~~~~~

- Add request type that resets the T3 to values like the chip was reset.
    - reset usec clock
    - ??

ioSync Python API
==================

- Document
   - API
   - examples
   

ioSync Hardware
===============

Base Teensy 3 Breakout
~~~~~~~~~~~~~~~~~~~~~~~

- Create a diagram showing what Teensy 3 pins map to ioSync lines.

- Create a schematic and associated text about the suggested way to mount the
  Teensy 3 and bring out the different ioSync pins.

ioSync HW Accessories
~~~~~~~~~~~~~~~~~~~~~~

- Create a list of hardware plug-ins that can be built and used with ioSync.
  For each accessory:
      - Document:
          - purpose
          - parts list
          - suggestions on build process.
          - How to connect to ioSync
          - How to access via ioSync Python API
          - Picture.

LED Control
------------

TBC

Light Meter
------------

TBC

Button Box
-----------

TBC


EOF
"""