"""Control joysticks and gamepads from within PsychoPy

You do need a window (and you need to be flipping it) for the joystick to be
updated.

Known issues:
    - currently under pyglet the joystick axes initialise to a value of zero and stay
      like this until the first time that axis moves

    - currently pygame (1.9.1) spits out lots of debug messages about the joystick and
      these can't be turned off :-/

Typical usage::

    from psychopy.hardware import joystick
    from psychopy import visual

    joystick.backend='pyglet'#must match the Window
    win = visual.Window([400,400], winType='pyglet')

    nJoys = joystick.getNumJoysticks()#to check if we have any
    id=0
    joy = joystick.Joystick(id)#id must be <= nJoys-1

    nAxes = joy.getNumAxes()#for interest
    while True:#while presenting stimuli
        currentjoy.getX()
        #...
        win.flip()#flipping implicitly updates the joystick info
"""
try:
    import pygame.joystick
    havePygame=True
except:
    havePygame=False
import pyglet_input
try:
    import pyglet_input
    havePyglet=True
except:
    havePyglet=False

from psychopy import logging, visual
backend = 'pyglet'#'pyglet' or 'pygame'

def getNumJoysticks():
    """Return a count of the number of joysticks available.
    """
    if backend=='pyglet':
        return len(pyglet_input.get_joysticks())
    else:
        pygame.joystick.init()
        return pygame.joystick.get_count()

class Joystick(object):
    def __init__(self, id):
        """An object to control a multi-axis joystick or gamepad

        .. note:

            You do need to be flipping frames (or dispatching events manually)
            in order for the values of the joystick to be updated.

        :Known issues:

            Currently under pyglet backends the axis values initialise to zero
            rather than reading the current true value. This gets fixed on the
            first change to each axis.
        """
        self.id=id
        if backend=='pyglet':
            joys=pyglet_input.get_joysticks()
            if id>=len(joys):
                logging.error("You don't have that many joysticks attached (remember that the first joystick has id=0 etc...)")
            else:
                self._device=joys[id]
                self._device.open()
                self.name=self._device.device.name
            if len(visual.openWindows)==0:
                logging.error("You need to open a window before creating your joystick")
            else:
                for win in visual.openWindows:
                    win()._eventDispatchers.append(self._device.device)
        else:
            pygame.joystick.init()
            self._device=pygame.joystick.Joystick(id)
            self._device.init()
            self.name=self._device.get_name()
    def getName(self):
        """Returns the manufacturer-defined name describing the device
        """
        return self.name
    def getNumButtons(self):
        """Returns the number of digital buttons on the device
        """
        if backend=='pyglet': return len(self._device.buttons)
        else: return self._device.get_numbuttons()
    def getButton(self, buttonId):
        """Get the state of a given button.

        buttonId should be a value from 0 to the number of buttons-1
        """
        if backend=='pyglet':
            return self._device.buttons[buttonId]
        else: return self._device.get_button(buttonId)
    def getAllButtons(self):
        """Get the state of all buttons as a list
        """
        if backend=='pyglet':
            return self._device.buttons
        else:
            bs=[]
            for id in range(self._device.get_numbuttons()):
                bs.append(self._device.get_button(id))
            return bs
    def getAllHats(self):
        """Get the current values of all available hats as a list of tuples.
        Each value is a tuple (x,y) where x and y can be -1,0,+1
        """
        hats=[]
        if backend=='pyglet':
            for ctrl in self._device.device.get_controls():
                if ctrl.name!=None and 'hat' in ctrl.name:
                    hats.append((self._device.hat_x,self._device.hat_y))
        else:
            for n in range(self._device.get_numhats()):
                hats.append(self._device.get_hat(n))
        return hats
    def getNumHats(self):
        """Get the number of hats on this joystick
        """
        if backend=='pyglet':
            return len(self.getAllHats())
        else: return self._device.get_numhats()
    def getHat(self,hatId=0):
        """Get the position of a particular hat.
        The position returned is an (x,y) tuple where x and y can be -1,0 or +1
        """
        if backend=='pyglet':
            if hatId==0:return self._device.hat
            else: return self.getAllHats()[hatId]
        else: return self._device.get_hat(hatId)
    def getX(self):
        """Returns the value on the X axis (equivalent to joystick.getAxis(0))
        """
        if backend=='pyglet':
            return self._device.x
        else: return self._device.get_axis(0)
    def getY(self):
        """Returns the value on the Y axis (equivalent to joystick.getAxis(1))
        """
        if backend=='pyglet':
            return self._device.y
        else: return self._device.get_axis(1)
    def getZ(self):
        """Returns the value on the Z axis (equivalent to joystick.getAxis(2))
        """
        if backend=='pyglet':
            return self._device.z
        else: return self._device.get_axis(2)
    def getAllAxes(self):
        """Get a list of all current axis values
        """
        axes=[]
        if backend=='pyglet':
            names=['x','y','z','rx','ry','rz',]
            for axName in names:
                if hasattr(self._device, axName):
                    axes.append(getattr(self._device, axName))
        else:
            for id in range(self._device.get_numaxes()):
                axes.append(self._device.get_axis(id))
        return axes
    def getNumAxes(self):
        """Returns the number of joystick axes found
        """
        if backend=='pyglet':
            return len(self.getAllAxes())
        else: return self._device.get_numaxes()
    def getAxis(self, axisId):
        """Get the value of an axis by an integer id (from 0 to number of axes-1)
        """
        if backend=='pyglet':
            val=self.getAllAxes()[axisId]
            if val is None:
                val=0
            return val
        else: return self._device.get_axis(axisId)
