"""Interface to `ioLab button box <http://www.iolab.co.uk>`_

This provides a basic BBox class, and imports the `ioLab python library
<http://github.com/ioLab/python-ioLabs>`_ as iolab.ioLab.
The ioLab library needs to be installed. It is included in the *Standalone*
distributions of PsychoPy as of version 1.62.01. Otherwise try "pip install ioLabs"

Usage::

    from psychopy.hardware import iolabs

For examples see the demos menu of the PsychoPy Coder or go to the URL above.

"""
# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from numpy import ubyte
from psychopy import core, logging
try:
    import ioLabs
except:
    msg="""Failed to import the ioLabs library. If you're using your own copy of
        python (not the Standalone distribution of PsychoPy) then try installing it with:
           > pip install ioLabs
        """.replace('    ', '')
    logging.error(msg)


class BBox(ioLabs.USBBox):
    """Simplified interface to ioLabs.USBBox.

    Author: Jonathan Roberts
    PsychoPy integration (voice key untested): Jeremy Gray
    """
    def __init__(self):
        ioLabs.USBBox.__init__(self)

        #disable all buttons and lights
        self.buttons.enabled = 0x00  # 8 bit pattern 0=disabled 1=enabled
        self.port2.state = 0xFF  # port2 is the lights on the bbox - 8 bit pattern 0=on 1=off
        self.keyevents = []

        # set up callbacks for button and voice key events.
        # when the button box detects a button press or voice key, it will call
        # this function with a report describing the event
        def key_press(report):
            # this routine simply appends the report to the keyevents attribute of our BBox object
            # so when waiting for a button we simply watch self.keyevents to see if it is not empty
            self.keyevents.append(report)
        self.commands.add_callback(ioLabs.REPORT.KEYDN, key_press)

    def __del__(self):
        self.lightButtons(None)  # does nothing (?)

    def _makeBitPattern(self, buttonList):
        bits = 0  # buttonList == None
        if type(buttonList) == int:
            bits = 2 ** buttonList
        elif type(buttonList) in (list,tuple):
            for btn in buttonList:
                bits += 2 ** btn
        elif buttonList:
            raise ValueError('invalid button list - must be None, int, or list of int')
        return ubyte(bits)

    def enableButtons(self, buttonList=[0,1,2,3,4,5,6,7], voice=False):
        '''enable the specified buttons
        the argument should be one of the following:
        None - disable all buttons
        an integer - enable a single buttonList
        a list of integers - enable all buttons in the list

        set voice to True to enable the voiceKey - gets reported as button 64
        '''

        self.int0.enabled = int(voice)
        self.buttons.enabled = self._makeBitPattern(buttonList)

    def lightButtons(self, lightList=[0,1,2,3,4,5,6,7]):
        '''turn on only the specified LEDs:
        None - turn off all LEDs
        an integer - turn on a single LED
        a list of integers - turn on all LEDs in the list
        '''
        self.leds.state = ~self._makeBitPattern(lightList) # in the bit pattern for lights, 1 is on and 0 is off

    def waitButtons(self):
        '''Wait for the button box to report that an enabled button or voice
        key was pressed/triggered. voice key gets reported as button 64
        '''
        while not self.keyevents:
            self.process_received_reports()
        return self.keyevents[0].key_code

    def getButtons(self):
        '''Non-blocking, detect and return button events (like event.getKeys)
        '''
        self.process_received_reports()
        if self.keyevents:
            return self.keyevents[0].key_code

    def clearEvents(self):
        '''clear out any button or voice key events that have happened up to now'''
        self.keyevents[:] = []
        self.clear_received_reports()
