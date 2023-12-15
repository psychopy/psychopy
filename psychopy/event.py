#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""To handle input from keyboard, mouse and joystick (joysticks require
pygame to be installed).
See demo_mouse.py and i{demo_joystick.py} for examples
"""
# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# 01/2011 modified by Dave Britton to get mouse event timing

import sys
import string
import copy
import numpy
from collections import namedtuple, OrderedDict
from psychopy.preferences import prefs

# try to import pyglet & pygame and hope the user has at least one of them!
try:
    from pygame import mouse, locals, joystick, display
    import pygame.key
    import pygame.event as evt
    havePygame = True
except ImportError:
    havePygame = False
try:
    import pyglet
    havePyglet = True
except ImportError:
    havePyglet = False
try:
    import glfw
    haveGLFW = True
except ImportError:
    haveGLFW = False

try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping

if havePygame:
    usePygame = True  # will become false later if win not initialised
else:
    usePygame = False

if haveGLFW:
    useGLFW = True
else:
    useGLFW = False


if havePyglet:
    # get the default display
    if pyglet.version < '1.4':
        _default_display_ = pyglet.window.get_platform().get_default_display()
    else:
        _default_display_ = pyglet.canvas.get_display()


import psychopy.core
from psychopy.tools.monitorunittools import cm2pix, deg2pix, pix2cm, pix2deg
from psychopy import logging
from psychopy.constants import NOT_STARTED


# global variable to keep track of mouse buttons
mouseButtons = [0, 0, 0]


if havePyglet or haveGLFW:
    # importing from mouse takes ~250ms, so do it now
    if havePyglet:
        from pyglet.window.mouse import LEFT, MIDDLE, RIGHT
        from pyglet.window.key import (
            MOD_SHIFT,
            MOD_CTRL,
            MOD_ALT,
            MOD_CAPSLOCK,
            MOD_NUMLOCK,
            MOD_WINDOWS,
            MOD_COMMAND,
            MOD_OPTION,
            MOD_SCROLLLOCK
        )

    _keyBuffer = []
    mouseWheelRel = numpy.array([0.0, 0.0])
    # list of 3 clocks that are reset on mouse button presses
    mouseClick = [psychopy.core.Clock(), psychopy.core.Clock(),
                  psychopy.core.Clock()]
    # container for time elapsed from last reset of mouseClick[n] for any
    # button pressed
    mouseTimes = [0.0, 0.0, 0.0]
    # clock for tracking time of mouse movement, reset when mouse is moved,
    # reset on mouse motion:
    mouseMove = psychopy.core.Clock()
    # global eventThread
    # eventThread = _EventDispatchThread()
    # eventThread.start()
    if haveGLFW:
        # GLFW keycodes for special characters
        _glfw_keycodes_ = {
            glfw.KEY_SPACE: 'space',
            glfw.KEY_ESCAPE: 'esc',
            glfw.KEY_ENTER: 'return',
            glfw.KEY_TAB: 'tab',
            glfw.KEY_BACKSPACE: 'backspace',
            glfw.KEY_INSERT: 'insert',
            glfw.KEY_DELETE: 'delete',
            glfw.KEY_RIGHT: 'right',
            glfw.KEY_LEFT: 'left',
            glfw.KEY_DOWN: 'down',
            glfw.KEY_UP: 'up',
            glfw.KEY_PAGE_UP: 'pageup',
            glfw.KEY_PAGE_DOWN: 'pagedn',
            glfw.KEY_HOME: 'home',
            glfw.KEY_END: 'end',
            glfw.KEY_CAPS_LOCK: 'capslock',
            glfw.KEY_SCROLL_LOCK: 'scrolllock',
            glfw.KEY_NUM_LOCK: 'numlock',
            glfw.KEY_PRINT_SCREEN: 'printscreen',
            glfw.KEY_PAUSE: 'pause',
            glfw.KEY_F1: 'f1',
            glfw.KEY_F2: 'f2',
            glfw.KEY_F3: 'f3',
            glfw.KEY_F4: 'f4',
            glfw.KEY_F5: 'f5',
            glfw.KEY_F6: 'f6',
            glfw.KEY_F7: 'f7',
            glfw.KEY_F8: 'f8',
            glfw.KEY_F9: 'f9',
            glfw.KEY_F10: 'f10',
            glfw.KEY_F11: 'f11',
            glfw.KEY_F12: 'f12',
            glfw.KEY_F13: 'f13',
            glfw.KEY_F14: 'f14',
            glfw.KEY_F15: 'f15',
            glfw.KEY_F16: 'f16',
            glfw.KEY_F17: 'f17',
            glfw.KEY_F18: 'f18',
            glfw.KEY_F19: 'f19',
            glfw.KEY_F20: 'f20',
            glfw.KEY_F21: 'f21',
            glfw.KEY_F22: 'f22',
            glfw.KEY_F23: 'f23',
            glfw.KEY_F24: 'f24',
            glfw.KEY_F25: 'f25',
        }

useText = False  # By default _onPygletText is not used


def _onPygletText(text, emulated=False):
    """handler for on_text pyglet events, or call directly to emulate a text
    event.

    S Mathot 2012: This function only acts when the key that is pressed
    corresponds to a non-ASCII text character (Greek, Arabic, Hebrew, etc.).
    In that case the symbol that is passed to _onPygletKey() is translated
    into a useless 'user_key()' string. If this happens, _onPygletText takes
    over the role of capturing the key. Unfortunately, _onPygletText()
    cannot solely handle all input, because it does not respond to spacebar
    presses, etc.
    """

    global useText
    if not useText:  # _onPygletKey has handled the input
        return
    # This is needed because sometimes the execution
    # sequence is messed up (somehow)
    useText = False
    # capture when the key was pressed:
    keyTime = psychopy.core.getTime()
    if emulated:
        keySource = 'EmulatedKey'
    else:
        keySource = 'KeyPress'
    _keyBuffer.append((text.lower(), lastModifiers, keyTime))
    logging.data("%s: %s" % (keySource, text))


def _onPygletKey(symbol, modifiers, emulated=False):
    """handler for on_key_press pyglet events; call directly to emulate a
    key press

    Appends a tuple with (keyname, timepressed) into the global _keyBuffer.
    The _keyBuffer can then be accessed as normal using event.getKeys(),
    .waitKeys(), clearBuffer(), etc.

    J Gray 2012: Emulated means add a key (symbol) to the buffer virtually.
    This is useful for fMRI_launchScan, and for unit testing (in testTheApp)
    Logging distinguishes EmulatedKey events from real Keypress events.
    For emulation, the key added to the buffer is unicode(symbol), instead of
    pyglet.window.key.symbol_string(symbol).

    S Mathot 2012: Implement fallback to _onPygletText

    5AM Solutions 2016: Add the keyboard modifier flags to the key buffer.

    M Cutone 2018: Added GLFW backend support.

    """
    global useText, lastModifiers

    keyTime = psychopy.core.getTime()  # capture when the key was pressed
    if emulated:
        if not isinstance(modifiers, int):
            msg = 'Modifiers must be passed as an integer value.'
            raise ValueError(msg)

        thisKey = str(symbol)
        keySource = 'EmulatedKey'
    else:
        thisKey = pyglet.window.key.symbol_string(
            symbol).lower()  # convert symbol into key string
        # convert pyglet symbols to pygame forms ( '_1'='1', 'NUM_1'='[1]')
        # 'user_key' indicates that Pyglet has been unable to make sense
        # out of the keypress. In that case, we fall back to _onPygletText
        # to handle the input.
        if 'user_key' in thisKey:
            useText = True
            lastModifiers = modifiers
            return
        useText = False
        thisKey = thisKey.lstrip('_').lstrip('NUM_')
        # Pyglet 1.3.0 returns 'enter' when Return key (0xFF0D) is pressed 
        # in Windows Python3. So we have to replace 'enter' with 'return'.
        if thisKey == 'enter':
            thisKey = 'return'
        keySource = 'Keypress'
    _keyBuffer.append((thisKey, modifiers, keyTime))  # tuple
    logging.data("%s: %s" % (keySource, thisKey))
    _process_global_event_key(thisKey, modifiers)


def _process_global_event_key(key, modifiers):
    if modifiers == 0:
        modifier_keys = ()
    else:
        modifier_keys = ['%s' % m.strip('MOD_').lower() for m in
                         (pyglet.window.key.modifiers_string(modifiers)
                          .split('|'))]

        # Ignore Num Lock.
        if 'numlock' in modifier_keys:
            modifier_keys.remove('numlock')

    index_key = globalKeys._gen_index_key((key, modifier_keys))

    if index_key in globalKeys:
        event = globalKeys[index_key]
        logging.exp('Global key event: %s. Calling %s.'
                    % (event.name, event.func))
        r = event.func(*event.func_args, **event.func_kwargs)
        return r


def _onPygletMousePress(x, y, button, modifiers, emulated=False):
    """button left=1, middle=2, right=4;
    specify multiple buttons with | operator
    """
    global mouseButtons, mouseClick, mouseTimes
    now = psychopy.clock.getTime()
    if emulated:
        label = 'Emulated'
    else:
        label = ''
    if button & LEFT:
        mouseButtons[0] = 1
        mouseTimes[0] = now - mouseClick[0].getLastResetTime()
        label += ' Left'
    if button & MIDDLE:
        mouseButtons[1] = 1
        mouseTimes[1] = now - mouseClick[1].getLastResetTime()
        label += ' Middle'
    if button & RIGHT:
        mouseButtons[2] = 1
        mouseTimes[2] = now - mouseClick[2].getLastResetTime()
        label += ' Right'
    logging.data("Mouse: %s button down, pos=(%i,%i)" % (label.strip(), x, y))


def _onPygletMouseRelease(x, y, button, modifiers, emulated=False):
    global mouseButtons
    if emulated:
        label = 'Emulated'
    else:
        label = ''
    if button & LEFT:
        mouseButtons[0] = 0
        label += ' Left'
    if button & MIDDLE:
        mouseButtons[1] = 0
        label += ' Middle'
    if button & RIGHT:
        mouseButtons[2] = 0
        label += ' Right'
    logging.data("Mouse: %s button up, pos=(%i,%i)" % (label, x, y))


def _onPygletMouseWheel(x, y, scroll_x, scroll_y):
    global mouseWheelRel
    mouseWheelRel = mouseWheelRel + numpy.array([scroll_x, scroll_y])
    msg = "Mouse: wheel shift=(%i,%i), pos=(%i,%i)"
    logging.data(msg % (scroll_x, scroll_y, x, y))


# will this work? how are pyglet event handlers defined?
def _onPygletMouseMotion(x, y, dx, dy):
    global mouseMove
    # mouseMove is a core.Clock() that is reset when the mouse moves
    # default is None, but start and stopMoveClock() create and remove it,
    # mouseMove.reset() resets it by hand
    if mouseMove:
        mouseMove.reset()


def startMoveClock():
    global mouseMove
    mouseMove = psychopy.core.Clock()


def stopMoveClock():
    global mouseMove
    mouseMove = None


def resetMoveClock():
    global mouseMove
    if mouseMove:
        mouseMove.reset()
    else:
        startMoveClock()

# class Keyboard:
#    """The keyboard class is currently just a helper class to allow common
#    attributes with other objects (like mouse and stimuli). In particular
#    it allows storage of the .status property (NOT_STARTED, STARTED, STOPPED).

#    It isn't really needed for most users - the functions it supports (e.g.
#    getKeys()) are directly callable from the event module.

#    Note that multiple Keyboard instances will not keep separate buffers.

#    """
#    def __init__(self):
#        self.status=NOT_STARTED
#    def getKeys(keyList=None, timeStamped=False):
#        return getKeys(keyList=keyList, timeStamped=timeStamped)
#    def waitKeys(maxWait = None, keyList=None):
#        return def waitKeys(maxWait = maxWait, keyList=keyList)


def modifiers_dict(modifiers):
    """Return dict where the key is a keyboard modifier flag
    and the value is the boolean state of that flag.

    """
    return {(mod[4:].lower()): modifiers & getattr(sys.modules[__name__], mod) > 0 for mod in [
        'MOD_SHIFT',
        'MOD_CTRL',
        'MOD_ALT',
        'MOD_CAPSLOCK',
        'MOD_NUMLOCK',
        'MOD_WINDOWS',
        'MOD_COMMAND',
        'MOD_OPTION',
        'MOD_SCROLLLOCK'
    ]}

def getKeys(keyList=None, modifiers=False, timeStamped=False):
    """Returns a list of keys that were pressed.

    :Parameters:
        keyList : **None** or []
            Allows the user to specify a set of keys to check for.
            Only keypresses from this set of keys will be removed from
            the keyboard buffer. If the keyList is `None`, all keys will be
            checked and the key buffer will be cleared completely.
            NB, pygame doesn't return timestamps (they are always 0)
        modifiers : **False** or True
            If True will return a list of tuples instead of a list of
            keynames. Each tuple has (keyname, modifiers). The modifiers
            are a dict of keyboard modifier flags keyed by the modifier
            name (eg. 'shift', 'ctrl').
        timeStamped : **False**, True, or `Clock`
            If True will return a list of tuples instead of a list of
            keynames. Each tuple has (keyname, time). If a `core.Clock`
            is given then the time will be relative to the `Clock`'s last
            reset.

    :Author:
        - 2003 written by Jon Peirce
        - 2009 keyList functionality added by Gary Strangman
        - 2009 timeStamped code provided by Dave Britton
        - 2016 modifiers code provided by 5AM Solutions
    """
    keys = []

    if havePygame and display.get_init():
        # see if pygame has anything instead (if it exists)
        windowSystem = 'pygame'
        for evts in evt.get(locals.KEYDOWN):
            # pygame has no keytimes
            keys.append((pygame.key.name(evts.key), 0))
    elif havePyglet:
        # for each (pyglet) window, dispatch its events before checking event
        # buffer
        windowSystem = 'pyglet'
        for win in _default_display_.get_windows():
            try:
                win.dispatch_events()  # pump events on pyglet windows
            except ValueError as e:  # pragma: no cover
                # Pressing special keys, such as 'volume-up', results in a
                # ValueError. This appears to be a bug in pyglet, and may be
                # specific to certain systems and versions of Python.
                logging.error(u'Failed to handle keypress')

        global _keyBuffer
        if len(_keyBuffer) > 0:
            # then pyglet is running - just use this
            keys = _keyBuffer
            # _keyBuffer = []  # DO /NOT/ CLEAR THE KEY BUFFER ENTIRELY

    elif haveGLFW:
        windowSystem = 'glfw'
        # 'poll_events' is called when a window is flipped, all the callbacks
        # populate the buffer
        if len(_keyBuffer) > 0:
            keys = _keyBuffer

    if keyList is None:
        _keyBuffer = []  # clear buffer entirely
        targets = keys  # equivalent behavior to getKeys()
    else:
        nontargets = []
        targets = []
        # split keys into keepers and pass-thrus
        for key in keys:
            if key[0] in keyList:
                targets.append(key)
            else:
                nontargets.append(key)
        _keyBuffer = nontargets  # save these

    # now we have a list of tuples called targets
    # did the user want timestamped tuples or keynames?
    if modifiers == False and timeStamped == False:
        keyNames = [k[0] for k in targets]
        return keyNames
    elif timeStamped == False:
        keyNames = [(k[0], modifiers_dict(k[1])) for k in targets]
        return keyNames
    elif timeStamped and windowSystem=='pygame':
        # provide a warning and set timestamps to be None
        logging.warning('Pygame keyboard events do not support timestamped=True')
        relTuple = [[_f for _f in (k[0], modifiers and modifiers_dict(k[1]) or None, None) if _f] for k in targets]
        return relTuple
    elif hasattr(timeStamped, 'getLastResetTime'):
        # keys were originally time-stamped with
        #   core.monotonicClock._lastResetTime
        # we need to shift that by the difference between it and
        # our custom clock
        _last = timeStamped.getLastResetTime()
        _clockLast = psychopy.core.monotonicClock.getLastResetTime()
        timeBaseDiff = _last - _clockLast
        relTuple = [[_f for _f in (k[0], modifiers and modifiers_dict(k[1]) or None, k[-1] - timeBaseDiff) if _f] for k in targets]
        return relTuple
    elif timeStamped is True:
        return [[_f for _f in (k[0], modifiers and modifiers_dict(k[1]) or None, k[-1]) if _f] for k in targets]
    elif isinstance(timeStamped, (float, int, int)):
        relTuple = [[_f for _f in (k[0], modifiers and modifiers_dict(k[1]) or None, k[-1] - timeStamped) if _f] for k in targets]
        return relTuple
    else: ## danger - catch anything that gets here because it shouldn't!
        raise ValueError("We received an unknown combination of params to "
                         "getKeys(): timestamped={}, windowSystem={}, "
                         "modifiers={}"
                        .format(timeStamped, windowSystem, modifiers))


def waitKeys(maxWait=float('inf'), keyList=None, modifiers=False,
             timeStamped=False, clearEvents=True):
    """Same as `~psychopy.event.getKeys`, but halts everything
    (including drawing) while awaiting input from keyboard.

    :Parameters:
        maxWait : any numeric value.
            Maximum number of seconds period and which keys to wait for.
            Default is float('inf') which simply waits forever.
        keyList : **None** or []
            Allows the user to specify a set of keys to check for.
            Only keypresses from this set of keys will be removed from
            the keyboard buffer. If the keyList is `None`, all keys will be
            checked and the key buffer will be cleared completely.
            NB, pygame doesn't return timestamps (they are always 0)
        modifiers : **False** or True
            If True will return a list of tuples instead of a list of
            keynames. Each tuple has (keyname, modifiers). The modifiers
            are a dict of keyboard modifier flags keyed by the modifier
            name (eg. 'shift', 'ctrl').
        timeStamped : **False**, True, or `Clock`
            If True will return a list of tuples instead of a list of
            keynames. Each tuple has (keyname, time). If a `core.Clock`
            is given then the time will be relative to the `Clock`'s last
            reset.
        clearEvents : **True** or False
            Whether to clear the keyboard event buffer (and discard preceding
            keypresses) before starting to monitor for new keypresses.

    Returns None if times out.

    """
    if clearEvents:
        # Only consider keypresses from here onwards.
        # We need to invoke clearEvents(), but our keyword argument is
        # also called clearEvents. We can work around this conflict by
        # accessing the global scope explicitly.
        globals()['clearEvents']('keyboard')

    # Check for keypresses until maxWait is exceeded
    #
    # NB pygame.event does have a wait() function that will
    # do this and maybe leave more cpu idle time?

    timer = psychopy.core.Clock()
    got_keypress = False

    while not got_keypress and timer.getTime() < maxWait:
        # Pump events on pyglet windows if they exist.
        if havePyglet:
            for win in _default_display_.get_windows():
                win.dispatch_events()

        # Get keypresses and return if anything is pressed.
        keys = getKeys(keyList=keyList, modifiers=modifiers,
                       timeStamped=timeStamped)
        if keys:
            got_keypress = True

    if got_keypress:
        return keys
    else:
        logging.data('No keypress (maxWait exceeded)')
        return None


def xydist(p1=(0.0, 0.0), p2=(0.0, 0.0)):
    """Helper function returning the cartesian distance between p1 and p2
    """
    return numpy.sqrt(pow(p1[0] - p2[0], 2) + pow(p1[1] - p2[1], 2))


class Mouse():
    """Easy way to track what your mouse is doing.

    It needn't be a class, but since Joystick works better
    as a class this may as well be one too for consistency

    Create your `visual.Window` before creating a Mouse.

    :Parameters:
        visible : **True** or False
            makes the mouse invisible if necessary
        newPos : **None** or [x,y]
            gives the mouse a particular starting position
            (pygame `Window` only)
        win : **None** or `Window`
            the window to which this mouse is attached
            (the first found if None provided)
    """

    def __init__(self,
                 visible=True,
                 newPos=None,
                 win=None):
        super(Mouse, self).__init__()
        self.visible = visible
        self.lastPos = None
        self.prevPos = None  # used for motion detection and timing
        if win:
            self.win = win
        else:
            try:
                # to avoid circular imports, core.openWindows is defined
                # by visual.py and updated in core namespace;
                # it's circular to "import visual" here in event
                self.win = psychopy.core.openWindows[0]()
                logging.info('Mouse: using default window')
            except (NameError, IndexError):
                logging.error('Mouse: failed to get a default visual.Window'
                              ' (need to create one first)')
                self.win = None

        # get the scaling factors for the display
        if self.win is not None:
            self._winScaleFactor = self.win.getContentScaleFactor()
        else:
            self._winScaleFactor = 1.0

        # for builder: set status to STARTED, NOT_STARTED etc
        self.status = None
        self.mouseClock = psychopy.core.Clock()
        self.movedistance = 0.0
        # if pygame isn't initialised then we must use pyglet
        global usePygame
        if havePygame and not pygame.display.get_init():
            usePygame = False
        self.setVisible(visible)
        if newPos is not None:
            self.setPos(newPos)

    @property
    def units(self):
        """The units for this mouse
        (will match the current units for the Window it lives in)
        """
        return self.win.units

    def setPos(self, newPos=(0, 0)):
        """Sets the current position of the mouse,
        in the same units as the :class:`~visual.Window`. (0,0) is the center.

        :Parameters:
            newPos : (x,y) or [x,y]
                the new position on the screen
        """
        newPosPix = self._windowUnits2pix(numpy.array(newPos))
        if usePygame:
            newPosPix[1] = self.win.size[1] / 2 - newPosPix[1]
            newPosPix[0] = self.win.size[0] / 2 + newPosPix[0]
            mouse.set_pos(newPosPix)
        else:
            if hasattr(self.win.winHandle, 'set_mouse_position'):
                if self.win.useRetina:
                    newPosPix = numpy.array(self.win.size) / 4 + newPosPix / 2
                else:
                    wsf = self._winScaleFactor 
                    newPosPix = \
                        numpy.array(self.win.size) / (2 * wsf) + newPosPix / wsf
                x, y = int(newPosPix[0]), int(newPosPix[1])
                self.win.winHandle.set_mouse_position(x, y)
                self.win.winHandle._mouse_x = x
                self.win.winHandle._mouse_y = y
            else:
                msg = 'mouse position could not be set (pyglet %s)'
                logging.error(msg % pyglet.version)

    def getPos(self):
        """Returns the current position of the mouse,
        in the same units as the :class:`~visual.Window` (0,0) is at centre
        """
        lastPosPix = numpy.zeros((2,), dtype=numpy.float32)
        if usePygame:  # for pygame top left is 0,0
            lastPosPix = numpy.array(mouse.get_pos())
            # set (0,0) to centre
            lastPosPix[1] = self.win.size[1] / 2 - lastPosPix[1]
            lastPosPix[0] = lastPosPix[0] - self.win.size[0] / 2
            self.lastPos = self._pix2windowUnits(lastPosPix)
        elif useGLFW and self.win.winType=='glfw':
            lastPosPix[:] = self.win.backend.getMousePos()
            if self.win.useRetina:
                lastPosPix *= 2.0
        else:  # for pyglet bottom left is 0,0
            # use default window if we don't have one
            if self.win:
                w = self.win.winHandle
            else:

                if psychopy.core.openWindows:
                    w = psychopy.core.openWindows[0]()
                else:
                    logging.warning("Called event.Mouse.getPos() for the mouse with no Window being opened")
                    return None

            # get position in window
            lastPosPix[:] = w._mouse_x, w._mouse_y

            # set (0,0) to centre
            if self.win.useRetina:
                lastPosPix = lastPosPix * 2 - numpy.array(self.win.size) / 2
            else:
                wsf = self._winScaleFactor 
                lastPosPix = lastPosPix * wsf - numpy.array(self.win.size) / 2

        self.lastPos = self._pix2windowUnits(lastPosPix)

        return copy.copy(self.lastPos)

    def mouseMoved(self, distance=None, reset=False):
        """Determine whether/how far the mouse has moved.

        With no args returns true if mouse has moved at all since last
        getPos() call, or distance (x,y) can be set to pos or neg
        distances from x and y to see if moved either x or y that
        far from lastPos, or distance can be an int/float to test if
        new coordinates are more than that far in a straight line
        from old coords.

        Retrieve time of last movement from self.mouseClock.getTime().

        Reset can be to 'here' or to screen coords (x,y) which allows
        measuring distance from there to mouse when moved. If reset is
        (x,y) and distance is set, then prevPos is set to (x,y) and
        distance from (x,y) to here is checked, mouse.lastPos is set as
        current (x,y) by getPos(), mouse.prevPos holds lastPos from
        last time mouseMoved was called.
        """
        # mouseMove = clock that gets reset by pyglet mouse movement handler:
        global mouseMove
        # needs initialization before getPos resets lastPos
        self.prevPos = copy.copy(self.lastPos)
        self.getPos()  # sets self.lastPos to current position
        if not reset:
            if distance is None:
                if self.prevPos[0] != self.lastPos[0]:
                    return True
                if self.prevPos[1] != self.lastPos[1]:
                    return True
            else:
                if isinstance(distance, int) or isinstance(distance, float):
                    self.movedistance = xydist(self.prevPos, self.lastPos)
                    if self.movedistance > distance:
                        return True
                    else:
                        return False
                if self.prevPos[0] + distance[0] - self.lastPos[0] > 0.0:
                    return True  # moved on X-axis
                if self.prevPos[1] + distance[1] - self.lastPos[0] > 0.0:
                    return True  # moved on Y-axis
            return False
        if reset is True:
            # just reset the last move time: starts/zeroes the move clock
            mouseMove.reset()  # resets the global mouseMove clock
            return False
        if reset == 'here':
            # set to wherever we are
            self.prevPos = copy.copy(self.lastPos)  # lastPos set in getPos()
            return False
        if hasattr(reset, '__len__'):
            # a tuple or list of (x,y)
            # reset to (x,y) to check movement from there
            self.prevPos = copy.copy(reset)
            if not distance:
                return False  # just resetting prevPos, not checking distance
            else:
                # checking distance of current pos to newly reset prevposition
                if isinstance(distance, int) or isinstance(distance, float):
                    self.movedistance = xydist(self.prevPos, self.lastPos)
                    if self.movedistance > distance:
                        return True
                    else:
                        return False
                # distance is x,y tuple, to check if the mouse moved that
                # far on either x or y axis
                # distance must be (dx,dy), and reset is (rx,ry), current pos
                # (cx,cy): Is cx-rx > dx ?
                if abs(self.lastPos[0] - self.prevPos[0]) > distance[0]:
                    return True  # moved on X-axis
                if abs(self.lastPos[1] - self.prevPos[1]) > distance[1]:
                    return True  # moved on Y-axis
            return False
        return False

    def mouseMoveTime(self):
        global mouseMove
        if mouseMove:
            return mouseMove.getTime()
        else:
            return 0  # mouseMove clock not started

    def getRel(self):
        """Returns the new position of the mouse relative to the
        last call to getRel or getPos, in the same units as the
        :class:`~visual.Window`.
        """
        if usePygame:
            relPosPix = numpy.array(mouse.get_rel()) * [1, -1]
            return self._pix2windowUnits(relPosPix)
        else:
            # NB getPost() resets lastPos so MUST retrieve lastPos first
            if self.lastPos is None:
                relPos = self.getPos()
            else:
                # DON't switch to (this-lastPos)
                relPos = -self.lastPos + self.getPos()
            return relPos

    def getWheelRel(self):
        """Returns the travel of the mouse scroll wheel since last call.
        Returns a numpy.array(x,y) but for most wheels y is the only
        value that will change (except Mac mighty mice?)
        """
        global mouseWheelRel
        rel = mouseWheelRel
        mouseWheelRel = numpy.array([0.0, 0.0])
        return rel

    def getVisible(self):
        """Gets the visibility of the mouse (1 or 0)
        """
        if usePygame:
            return mouse.get_visible()
        else:
            print("Getting the mouse visibility is not supported under"
                  " pyglet, but you can set it anyway")

    def setVisible(self, visible):
        """Sets the visibility of the mouse to 1 or 0

        NB when the mouse is not visible its absolute position is held
        at (0, 0) to prevent it from going off the screen and getting lost!
        You can still use getRel() in that case.
        """
        if self.win:  # use default window if we don't have one
            self.win.setMouseVisible(visible)
        elif usePygame:
            mouse.set_visible(visible)
        else:  # try communicating with window directly?
            from psychopy.visual import openWindows
            if psychopy.core.openWindows:
                w = psychopy.core.openWindows[0]()  # type: psychopy.visual.Window
            else:
                logging.warning("Called event.Mouse.getPos() for the mouse with no Window being opened")
                return None
            w.setMouseVisible(visible)

    def clickReset(self, buttons=(0, 1, 2)):
        """Reset a 3-item list of core.Clocks use in timing button clicks.

        The pyglet mouse-button-pressed handler uses their
        clock.getLastResetTime() when a button is pressed so the user
        can reset them at stimulus onset or offset to measure RT. The
        default is to reset all, but they can be reset individually as
        specified in buttons list
        """
        global mouseClick
        for c in buttons:
            mouseClick[c].reset()
            mouseTimes[c] = 0.0

    def getPressed(self, getTime=False):
        """Returns a 3-item list indicating whether or not buttons 0,1,2
        are currently pressed.

        If `getTime=True` (False by default) then `getPressed` will
        return all buttons that have been pressed since the last call
        to `mouse.clickReset` as well as their time stamps::

            buttons = mouse.getPressed()
            buttons, times = mouse.getPressed(getTime=True)

        Typically you want to call :ref:`mouse.clickReset()` at stimulus
        onset, then after the button is pressed in reaction to it, the
        total time elapsed from the last reset to click is in mouseTimes.
        This is the actual RT, regardless of when the call to `getPressed()`
        was made.

        """
        global mouseButtons, mouseTimes
        if usePygame:
            return mouse.get_pressed()
        else:
            # False:  # havePyglet: # like in getKeys - pump the events
            # for each (pyglet) window, dispatch its events before checking
            # event buffer

            for win in _default_display_.get_windows():
                win.dispatch_events()  # pump events on pyglet windows

            # else:
            if not getTime:
                return copy.copy(mouseButtons)
            else:
                return copy.copy(mouseButtons), copy.copy(mouseTimes)

    def isPressedIn(self, shape, buttons=(0, 1, 2)):
        """Returns `True` if the mouse is currently inside the shape and
        one of the mouse buttons is pressed. The default is that any of
        the 3 buttons can indicate a click; for only a left-click,
        specify `buttons=[0]`::

            if mouse.isPressedIn(shape):
            if mouse.isPressedIn(shape, buttons=[0]):  # left-clicks only

        Ideally, `shape` can be anything that has a `.contains()` method,
        like `ShapeStim` or `Polygon`. Not tested with `ImageStim`.
        """
        wanted = numpy.zeros(3, dtype=int)
        for c in buttons:
            wanted[c] = 1
        pressed = self.getPressed()
        return any(wanted & pressed) and shape.contains(self)

    def _pix2windowUnits(self, pos):
        if self.win.units == 'pix':
            if self.win.useRetina:
                pos /= 2.0
            return pos
        elif self.win.units == 'norm':
            return pos * 2.0 / self.win.size
        elif self.win.units == 'cm':
            return pix2cm(pos, self.win.monitor)
        elif self.win.units == 'deg':
            return pix2deg(pos, self.win.monitor)
        elif self.win.units == 'height':
            return pos / float(self.win.size[1])

    def _windowUnits2pix(self, pos):
        if self.win.units == 'pix':
            return pos
        elif self.win.units == 'norm':
            return pos * self.win.size / 2.0
        elif self.win.units == 'cm':
            return cm2pix(pos, self.win.monitor)
        elif self.win.units == 'deg':
            return deg2pix(pos, self.win.monitor)
        elif self.win.units == 'height':
            return pos * float(self.win.size[1])

    def setExclusive(self, exclusivity):
        """Binds the mouse to the experiment window. Only works in Pyglet.

        In multi-monitor settings, or with a window that is not fullscreen,
        the mouse pointer can drift, and thereby PsychoPy might not get the
        events from that window. setExclusive(True) works with Pyglet to
        bind the mouse to the experiment window.

        Note that binding the mouse pointer to a window will cause the
        pointer to vanish, and absolute positions will no longer be
        meaningful getPos() returns [0, 0] in this case.
        """
        if type(exclusivity) is not bool:
            raise ValueError('Exclusivity must be a boolean!')
        if not usePygame:
            msg = ('Setting mouse exclusivity in Pyglet will cause the '
                   'cursor to disappear, and getPos() will be rendered '
                   'meaningless, returning [0, 0]')
            psychopy.logging.warning(msg)
            self.win.winHandle.set_exclusive_mouse(exclusivity)
        else:
            print('Mouse exclusivity can only be set for Pyglet!')


class BuilderKeyResponse():
    """Used in scripts created by the builder to keep track of a clock and
    the current status (whether or not we are currently checking the keyboard)
    """

    def __init__(self):
        super(BuilderKeyResponse, self).__init__()
        self.status = NOT_STARTED
        self.keys = []  # the key(s) pressed
        self.corr = 0  # was the resp correct this trial? (0=no, 1=yes)
        self.rt = []  # response time(s)
        self.clock = psychopy.core.Clock()  # we'll use this to measure the rt


def clearEvents(eventType=None):
    """Clears all events currently in the event buffer.

    Optional argument, eventType, specifies only certain types to be
    cleared.

    :Parameters:
        eventType : **None**, 'mouse', 'joystick', 'keyboard'
            If this is not None then only events of the given type are cleared

    """
    if not havePygame or not display.get_init():  # pyglet
        # For each window, dispatch its events before
        # checking event buffer.
        for win in _default_display_.get_windows():
            win.dispatch_events()  # pump events on pyglet windows

        if eventType == 'mouse':
            pass
        elif eventType == 'joystick':
            pass
        else:  # eventType='keyboard' or eventType=None.
            global _keyBuffer
            _keyBuffer = []
    else:  # pygame
        if eventType == 'mouse':
            evt.get([locals.MOUSEMOTION, locals.MOUSEBUTTONUP,
                     locals.MOUSEBUTTONDOWN])
        elif eventType == 'keyboard':
            evt.get([locals.KEYDOWN, locals.KEYUP])
        elif eventType == 'joystick':
            evt.get([locals.JOYAXISMOTION, locals.JOYBALLMOTION,
                     locals.JOYHATMOTION, locals.JOYBUTTONUP,
                     locals.JOYBUTTONDOWN])
        else:
            evt.get()


class _GlobalEventKeys(MutableMapping):
    """
     Global event keys for the pyglet backend.

     Global event keys are single keys (or combinations of a single key
     and one or more "modifier" keys such as Ctrl, Alt, etc.) with an
     associated Python callback function. This function will be executed
     if the key (or key/modifiers combination) was pressed.

     PsychoPy fully automatically monitors and processes key presses
     during most portions of the experimental run, for example during
     `core.wait()` periods, or when calling `win.flip()`. If a global
     event key press is detected, the specified function will be run
     immediately. You are not required to manually poll and check for key
     presses. This can be particularly useful to implement a global
     "shutdown" key, or to trigger laboratory equipment on a key press
     when testing your experimental script -- without cluttering the code.
     But of course the application is not limited to these two scenarios.
     In fact, you can associate any Python function with a global event key.

     The PsychoPy preferences for `shutdownKey` and `shutdownKeyModifiers`
     (both unset by default) will be used to automatically create a global
     shutdown key once the `psychopy.event` module is being imported.

     :Notes:

     All keyboard -> event associations are stored in the `self._events`
     OrderedDict. The dictionary keys are namedtuples with the elements
     `key` and `mofifiers`. `key` is a string defining an (ordinary)
     keyboard key, and `modifiers` is a tuple of modifier key strings,
     e.g., `('ctrl', 'alt')`. The user does not access this attribute
     directly, but should index the class instance itself (via
     `globalKeys[key, modifiers]`). That way, the `modifiers` sequence
     will be transparently converted into a tuple (which is a hashable
     type) before trying to index `self._events`.

     """
    _GlobalEvent = namedtuple(
        '_GlobalEvent',
        ['func', 'func_args', 'func_kwargs', 'name'])

    _IndexKey = namedtuple('_IndexKey', ['key', 'modifiers'])

    _valid_keys = set(string.ascii_lowercase + string.digits
                      + string.punctuation + ' \t')
    _valid_keys.update(['escape', 'left', 'right', 'up', 'down', 'space'])

    _valid_modifiers = {'shift', 'ctrl', 'alt', 'capslock',
                        'scrolllock', 'command', 'option', 'windows'}

    def __init__(self):
        super(_GlobalEventKeys, self).__init__()
        self._events = OrderedDict()

        if prefs.general['shutdownKey']:
            msg = ('Found shutdown key definition in preferences; '
                   'enabling shutdown key.')
            logging.info(msg)
            self.add(key=prefs.general['shutdownKey'],
                     modifiers=prefs.general['shutdownKeyModifiers'],
                     func=psychopy.core.quit,
                     name='shutdown (auto-created from prefs)')

    def __repr__(self):
        info = ''
        for index_key, event in list(self._events.items()):
            info += '\n\t'
            if index_key.modifiers:
                _modifiers = ['[%s]' % m.upper() for m in index_key.modifiers]
                info += '%s + ' % ' + '.join(_modifiers)
            info += ("[%s] -> '%s' %s"
                     % (index_key.key.upper(), event.name, event.func))

        return '<_GlobalEventKeys : %s\n>' % info

    def __str__(self):
        return ('<_GlobalEventKeys : %i key->event mappings defined.>'
                % len(self))

    def __len__(self):
        return len(self._events)

    def __getitem__(self, key):
        index_key = self._gen_index_key(key)
        return self._events[index_key]

    def __setitem__(self, key, value):
        msg = 'Please use `.add()` to add a new global event key.'
        raise NotImplementedError(msg)

    def __delitem__(self, key):
        index_key = self._gen_index_key(key)
        event = self._events.pop(index_key, None)

        if event is None:
            msg = 'Requested to remove unregistered global event key.'
            raise KeyError(msg)
        else:
            logging.exp("Removed global key event: '%s'." % event.name)

    def __iter__(self):
        return iter(self._events.keys())

    def _gen_index_key(self, key):
        if isinstance(key, str):  # Single key, passed as a string.
            index_key = self._IndexKey(key, ())
        else:  # Convert modifiers into a hashable type.
            index_key = self._IndexKey(key[0], tuple(key[1]))

        return index_key

    def add(self, key, func, func_args=(), func_kwargs=None,
            modifiers=(), name=None):
        """
        Add a global event key.

        :Parameters:

        key : string
            The key to add.

        func : function
            The function to invoke once the specified keys were pressed.

        func_args : iterable
            Positional arguments to be passed to the specified function.

        func_kwargs : dict
            Keyword arguments to be passed to the specified function.

        modifiers : collection of strings
            Modifier keys. Valid keys are:
            'shift', 'ctrl', 'alt' (not on macOS), 'capslock',
            'scrolllock', 'command' (macOS only), 'option' (macOS only)

            Num Lock is not supported.

        name : string
            The name of the event. Will be used for logging. If None,
            will use the name of the specified function.

        :Raises:

        ValueError
            If the specified key or modifiers are invalid, or if the
            key / modifier combination has already been assigned to a global
            event.

        """
        if key not in self._valid_keys:
            raise ValueError('Unknown key specified: %s' % key)

        if not set(modifiers).issubset(self._valid_modifiers):
            raise ValueError('Unknown modifier key specified.')

        index_key = self._gen_index_key((key, modifiers))
        if index_key in self._events:
            msg = ('The specified key is already assigned to a global event. '
                   'Use `.remove()` to remove it first.')
            raise ValueError(msg)

        if func_kwargs is None:
            func_kwargs = {}
        if name is None:
            name = func.__name__

        self._events[index_key] = self._GlobalEvent(func, func_args,
                                                    func_kwargs, name)
        logging.exp('Added new global key event: %s' % name)

    def remove(self, key, modifiers=()):
        """
        Remove a global event key.

        :Parameters:

        key : string
            A single key name. If `'all'`, remove all event keys.

        modifiers : collection of strings
            Modifier keys. Valid keys are:
            'shift', 'ctrl', 'alt' (not on macOS), 'capslock', 'numlock',
            'scrolllock', 'command' (macOS only), 'option' (macOS only),
            'windows' (Windows only)

        """
        if key == 'all':
            self._events = OrderedDict()
            logging.exp('Removed all global key events.')
            return

        del self[key, modifiers]


def _onGLFWKey(*args, **kwargs):
    """Callback for key/character events for the GLFW backend.

    :return:
    """
    keyTime = psychopy.core.getTime()  # get timestamp

    # TODO - support for key emulation
    win_ptr, key, scancode, action, modifiers = args
    global useText
    
    if key == glfw.KEY_UNKNOWN:
        useText = True
        return
    useText = False

    # get the printable name, always make lowercase
    key_name = glfw.get_key_name(key, scancode)

    # if there is no localized key name or space
    if key_name is None or key_name == ' ':
        try:
            key_name = _glfw_keycodes_[key]
        except KeyError:
            pass
    else:
        key_name = key_name.lower()

    # TODO - modifier integration
    keySource = 'Keypress'
    _keyBuffer.append((key_name, modifiers, keyTime))  # tuple
    logging.data("%s: %s" % (keySource, key_name))


def _onGLFWText(*args, **kwargs):
    """Handle unicode character events if _onGLFWKey() cannot.

    :return:
    """
    keyTime = psychopy.core.getTime()  # get timestamp



    # TODO - support for key emulation
    win_ptr, codepoint, modifiers = args
    # win = glfw.get_window_user_pointer(win_ptr)
    text = chr(codepoint)  # convert to unicode character (Python 3.0)
    global useText
    if not useText:  # _onPygletKey has handled the input
        return
    keySource = 'KeyPress'
    _keyBuffer.append((text, keyTime))
    logging.data("%s: %s" % (keySource, text))


def _onGLFWMouseButton(*args, **kwargs):
    """Callback for mouse press events. Both press and release actions are
    handled by this function as they both invoke the same callback.

    """
    global mouseButtons, mouseClick, mouseTimes
    now = psychopy.core.getTime()
    win_ptr, button, action, modifier = args
    # win = glfw.get_window_user_pointer(win_ptr)

    # get current position of the mouse
    # this might not be at the exact location of the mouse press
    x, y = glfw.get_cursor_pos(win_ptr)

    # process actions
    if action == glfw.PRESS:
        if button == glfw.MOUSE_BUTTON_LEFT:
            mouseButtons[0] = 1
            mouseTimes[0] = now - mouseClick[0].getLastResetTime()
        elif button == glfw.MOUSE_BUTTON_MIDDLE:
            mouseButtons[1] = 1
            mouseTimes[1] = now - mouseClick[1].getLastResetTime()
        elif button == glfw.MOUSE_BUTTON_RIGHT:
            mouseButtons[2] = 1
            mouseTimes[2] = now - mouseClick[2].getLastResetTime()
    elif action == glfw.RELEASE:
        if button == glfw.MOUSE_BUTTON_LEFT:
            mouseButtons[0] = 0
        elif button == glfw.MOUSE_BUTTON_MIDDLE:
            mouseButtons[1] = 0
        elif button == glfw.MOUSE_BUTTON_RIGHT:
            mouseButtons[2] = 0


def _onGLFWMouseScroll(*args, **kwargs):
    """Callback for mouse scrolling events. For most computer mice with scroll
    wheels, only the vertical (Y-offset) is relevant.

    """
    window_ptr, x_offset, y_offset = args
    global mouseWheelRel
    mouseWheelRel = mouseWheelRel + numpy.array([x_offset, y_offset])
    msg = "Mouse: wheel shift=(%i,%i)"
    logging.data(msg % (x_offset, y_offset))


def _getGLFWJoystickButtons(*args, **kwargs):
    """
    :return:
    """
    pass


def _getGLFWJoystickAxes(*args, **kwargs):
    """
    :return:
    """
    pass


if havePyglet:
    globalKeys = _GlobalEventKeys()
