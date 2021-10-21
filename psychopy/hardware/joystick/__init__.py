#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Control joysticks and gamepads from within PsychoPy.

You do need a window (and you need to be flipping it) for the joystick to be
updated.

Known issues:
    - currently under pyglet the joystick axes initialise to a value of zero
      and stay like this until the first time that axis moves

    - currently pygame (1.9.1) spits out lots of debug messages about the
      joystick and these can't be turned off :-/

Typical usage::

    from psychopy.hardware import joystick
    from psychopy import visual

    joystick.backend='pyglet'  # must match the Window
    win = visual.Window([400,400], winType='pyglet')

    nJoys = joystick.getNumJoysticks()  # to check if we have any
    id = 0
    joy = joystick.Joystick(id)  # id must be <= nJoys - 1

    nAxes = joy.getNumAxes()  # for interest
    while True:  # while presenting stimuli
        joy.getX()
        # ...
        win.flip()  # flipping implicitly updates the joystick info
"""

try:
    import pygame.joystick
    havePygame = True
except Exception:
    havePygame = False

try:
    from pyglet import input as pyglet_input  # pyglet 1.2+
    from pyglet import app as pyglet_app
    havePyglet = True
except Exception:
    havePyglet = False

try:
    import glfw
    haveGLFW = True
except ImportError:
    print("failed to import GLFW.")
    haveGLFW = False

from psychopy import logging, visual
backend = 'pyglet'  # 'pyglet' or 'pygame'


def getNumJoysticks():
    """Return a count of the number of joysticks available."""
    if backend == 'pyglet':
        return len(pyglet_input.get_joysticks())
    elif backend == 'glfw':
        n_joys = 0
        for joy in range(glfw.JOYSTICK_1, glfw.JOYSTICK_LAST):
            if glfw.joystick_present(joy):
                n_joys += 1

        return n_joys
    else:
        pygame.joystick.init()
        return pygame.joystick.get_count()


if havePyglet:
    class PygletDispatcher:
        def dispatch_events(self):
            pyglet_app.platform_event_loop.step(timeout=0.001)

    pyglet_dispatcher = PygletDispatcher()


class Joystick:

    def __init__(self, id):
        """An object to control a multi-axis joystick or gamepad.

        .. note:

            You do need to be flipping frames (or dispatching events manually)
            in order for the values of the joystick to be updated.

        :Known issues:

            Currently under pyglet backends the axis values initialise to zero
            rather than reading the current true value. This gets fixed on the
            first change to each axis.
        """
        self.id = id
        if backend == 'pyglet':
            joys = pyglet_input.get_joysticks()
            if id >= len(joys):
                logging.error("You don't have that many joysticks attached "
                              "(remember that the first joystick has id=0 "
                              "etc...)")
            else:
                self._device = joys[id]
                self._device.open()
                self.name = self._device.device.name
            if len(visual.openWindows) == 0:
                logging.error(
                    "You need to open a window before creating your joystick")
            else:
                for win in visual.openWindows:
                    win()._eventDispatchers.append(pyglet_dispatcher)
        elif backend == 'glfw':
            # We can create a joystick anytime after glfwInit() is called, but
            # there should be a window open first.
            # Joystick events are processed when flipping the associated window.
            if not glfw.init():
                logging.error("GLFW could not be initialized. Exiting.")

            # get all available joysticks, GLFW supports up to 16.
            joys = []
            for joy in range(glfw.JOYSTICK_1, glfw.JOYSTICK_LAST):
                if glfw.joystick_present(joy):
                    joys.append(joy)

            # error checks
            if not joys:  # if the list is empty, no joysticks were found
                error_msg = ("No joysticks were found by the GLFW runtime. "
                             "Check connections and try again.")
                logging.error(error_msg)
                raise RuntimeError(error_msg)
            elif id not in joys:
                error_msg = ("You don't have that many joysticks attached "
                             "(remember that the first joystick has id=0 "
                             "etc...)")
                logging.error(error_msg)
                raise RuntimeError(error_msg)

            self._device = id  # just need the ID for GLFW
            self.name = glfw.get_joystick_name(self._device).decode("utf-8")

            if len(visual.openWindows) == 0:
                logging.error(
                    "You need to open a window before creating your joystick")
            else:
                for win in visual.openWindows:
                    # sending the raw ID to the window.
                    win()._eventDispatchers.append(self._device)

        else:
            pygame.joystick.init()
            self._device = pygame.joystick.Joystick(id)
            self._device.init()
            self.name = self._device.get_name()

    def getName(self):
        """Return the manufacturer-defined name describing the device."""
        return self.name

    def getNumButtons(self):
        """Return the number of digital buttons on the device."""
        if backend == 'pyglet':
            return len(self._device.buttons)
        elif backend == 'glfw':
            _, count = glfw.get_joystick_buttons(self._device)
            return count
        else:
            return self._device.get_numbuttons()

    def getButton(self, buttonId):
        """Get the state of a given button.

        buttonId should be a value from 0 to the number of buttons-1
        """
        if backend == 'pyglet':
            return self._device.buttons[buttonId]
        elif backend == 'glfw':
            bs, _ = glfw.get_joystick_buttons(self._device)
            return bs[buttonId]
        else:
            return self._device.get_button(buttonId)

    def getAllButtons(self):
        """Get the state of all buttons as a list."""
        if backend == 'pyglet':
            return self._device.buttons
        elif backend == 'glfw':
            bs, count = glfw.get_joystick_buttons(self._device)
            return [bs[i] for i in range(count)]
        else:
            bs = []
            for id in range(self._device.get_numbuttons()):
                bs.append(self._device.get_button(id))
            return bs

    def getAllHats(self):
        """Get the current values of all available hats as a list of tuples.

        Each value is a tuple (x, y) where x and y can be -1, 0, +1
        """
        hats = []
        if backend == 'pyglet':
            for ctrl in self._device.device.get_controls():
                if ctrl.name != None and 'hat' in ctrl.name:
                    hats.append((self._device.hat_x, self._device.hat_y))
        elif backend == 'glfw':
            # GLFW treats hats as buttons
            pass
        else:
            for n in range(self._device.get_numhats()):
                hats.append(self._device.get_hat(n))
        return hats

    def getNumHats(self):
        """Get the number of hats on this joystick.

        The GLFW backend makes no distinction between hats and buttons. Calling
        'getNumHats()' will return 0.

        """
        if backend == 'pyglet':
            return len(self.getAllHats())
        elif backend == 'glfw':
            return 0
        else:
            return self._device.get_numhats()

    def getHat(self, hatId=0):
        """Get the position of a particular hat.

        The position returned is an (x, y) tuple where x and y
        can be -1, 0 or +1
        """
        if backend == 'pyglet':
            if hatId == 0:
                return self._device.hat
            else:
                return self.getAllHats()[hatId]
        elif backend == 'glfw':
            # does nothing, hats are buttons in GLFW
            pass
        else:
            return self._device.get_hat(hatId)

    def getX(self):
        """Return the X axis value (equivalent to joystick.getAxis(0))."""
        if backend == 'pyglet':
            return self._device.x
        elif backend == 'glfw':
            return self.getAxis(0)
        else:
            return self._device.get_axis(0)

    def getY(self):
        """Return the Y axis value (equivalent to joystick.getAxis(1))."""
        if backend == 'pyglet':
            return self._device.y
        elif backend == 'glfw':
            return self.getAxis(1)
        else:
            return self._device.get_axis(1)

    def getZ(self):
        """Return the Z axis value (equivalent to joystick.getAxis(2))."""
        if backend == 'pyglet':
            return self._device.z
        elif backend == 'glfw':
            return self.getAxis(2)
        else:
            return self._device.get_axis(2)

    def getAllAxes(self):
        """Get a list of all current axis values."""
        axes = []
        if backend == 'pyglet':
            names = ['x', 'y', 'z', 'rx', 'ry', 'rz', ]
            for axName in names:
                if hasattr(self._device, axName):
                    axes.append(getattr(self._device, axName))
        elif backend == 'glfw':
            _axes, count = glfw.get_joystick_axes(self._device)
            for i in range(count):
                axes.append(_axes[i])
        else:
            for id in range(self._device.get_numaxes()):
                axes.append(self._device.get_axis(id))
        return axes

    def getNumAxes(self):
        """Return the number of joystick axes found.

        """
        if backend == 'pyglet':
            return len(self.getAllAxes())
        elif backend == 'glfw':
            _, count = glfw.get_joystick_axes(self._device)
            return count
        else:
            return self._device.get_numaxes()

    def getAxis(self, axisId):
        """Get the value of an axis by an integer id.

        (from 0 to number of axes - 1)
        """
        if backend == 'pyglet':
            val = self.getAllAxes()[axisId]
            if val is None:
                val = 0
            return val
        elif backend == 'glfw':
            val, _ = glfw.get_joystick_axes(self._device)
            return val[axisId]
        else:
            return self._device.get_axis(axisId)


class XboxController(Joystick):
    """Joystick template class for the XBox 360 controller.

    Usage:

        xbctrl = XboxController(0)  # joystick ID
        y_btn_state = xbctrl.y  # get the state of the 'Y' button

    """
    def __init__(self, id, *args, **kwargs):
        super(XboxController, self).__init__(id)

        # validate if this is an Xbox controller by its reported name
        if self.name.find("Xbox 360") == -1:
            logging.warning("The connected controller does not appear "
                            "compatible with the 'XboxController' template. "
                            "Unexpected input behaviour may result!")

        if backend != 'glfw':
            logging.error("Controller templates are only supported when using "
                          "the GLFW window backend. You must also set "
                          "joystick.backend='glfw' prior to creating a "
                          "joystick.")


        # button mapping for the XBox controller
        self._button_mapping = {'a': 0,
                                'b': 1,
                                'x': 2,
                                'y': 3,
                                'left_shoulder': 4,
                                'right_shoulder': 5,
                                'back': 6,
                                'start': 7,
                                'left_stick': 8,
                                'right_stick': 9,
                                'up': 10,  # hat
                                'down': 11,
                                'left': 12,
                                'right': 13}

        # axes groups
        self._axes_mapping = {'left_thumbstick': (0, 1),
                              'right_thumbstick': (2, 3),
                              'triggers': (4, 5),
                              'dpad': (6, 7)}

    @property
    def a(self):
        return self.get_a()

    def get_a(self):
        """Get the 'A' button state.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['a'])

    @property
    def b(self):
        return self.get_b()

    def get_b(self):
        """Get the 'B' button state.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['b'])

    @property
    def x(self):
        return self.get_x()

    def get_x(self):
        """Get the 'X' button state.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['x'])

    @property
    def y(self):
        return self.get_y()

    def get_y(self):
        """Get the 'Y' button state.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['y'])

    @property
    def left_shoulder(self):
        return self.get_left_shoulder()

    def get_left_shoulder(self):
        """Get left 'shoulder' trigger state.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['left_shoulder'])

    @property
    def right_shoulder(self):
        return self.get_right_shoulder()

    def get_right_shoulder(self):
        """Get right 'shoulder' trigger state.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['right_shoulder'])

    @property
    def back(self):
        return self.get_back()

    def get_back(self):
        """Get 'back' button state (button to the right of the left joystick).

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['back'])

    @property
    def start(self):
        return self.get_start()

    def get_start(self):
        """Get 'start' button state (button to the left of the 'X' button).

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['start'])

    @property
    def hat_axis(self):
        return self.get_hat_axis()

    def get_hat_axis(self):
        """Get the states of the hat (sometimes called the 'directional pad').
        The hat can only indicate direction but not displacement.

        This function reports hat values in the same way as a joystick so it may
        be used interchangeably with existing analog joystick code.

        Returns a tuple (X,Y) indicating which direction the hat is pressed
        between -1.0 and +1.0. Positive values indicate presses in the right or
        up direction.

        :return: tuple, zero centered X, Y values.
        """
        # get button states
        button_states = self.getAllButtons()
        up = button_states[self._button_mapping['up']]
        dn = button_states[self._button_mapping['down']]
        lf = button_states[self._button_mapping['left']]
        rt = button_states[self._button_mapping['right']]

        # convert button states to 'analog' values
        return -1.0 * lf + rt, -1.0 * dn + up

    @property
    def left_thumbstick(self):
        return self.get_left_thumbstick()

    def get_left_thumbstick(self):
        """Get the state of the left joystick button; activated by pressing
        down on the stick.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['left_stick'])

    @property
    def right_thumbstick(self):
        return self.get_right_thumbstick()

    def get_right_thumbstick(self):
        """Get the state of the right joystick button; activated by pressing
        down on the stick.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['right_stick'])

    def get_named_buttons(self, button_names):
        """Get the states of multiple buttons using names. A list of button
        states is returned for each string in list 'names'.

        :param button_names: tuple or list of button names
        :return:
        """

        button_states = []
        for button in button_names:
            button_states.append(self.getButton(self._button_mapping[button]))

        return button_states

    @property
    def left_thumbstick_axis(self):
        return self.get_left_thumbstick_axis()

    def get_left_thumbstick_axis(self):
        """Get the axis displacement values of the left thumbstick.

        Returns a tuple (X,Y) indicating thumbstick displacement between -1.0
        and +1.0. Positive values indicate the stick is displaced right or up.

        :return: tuple, zero centered X, Y values.
        """
        ax, ay = self._axes_mapping['left_thumbstick']

        # we sometimes get values slightly outside the range of -1.0 < x < 1.0,
        # so clip them to give the user what they expect
        ax_val = self._clip_range(self.getAxis(ax))
        ay_val = self._clip_range(self.getAxis(ay))

        return ax_val, ay_val

    @property
    def right_thumbstick_axis(self):
        return self.get_right_thumbstick_axis()

    def get_right_thumbstick_axis(self):
        """Get the axis displacement values of the right thumbstick.

        Returns a tuple (X,Y) indicating thumbstick displacement between -1.0
        and +1.0. Positive values indicate the stick is displaced right or up.

        :return: tuple, zero centered X, Y values.
        """
        ax, ay = self._axes_mapping['right_thumbstick']

        ax_val = self._clip_range(self.getAxis(ax))
        ay_val = self._clip_range(self.getAxis(ay))

        return ax_val, ay_val

    @property
    def trigger_axis(self):
        return self.get_trigger_axis()

    def get_trigger_axis(self):
        """Get the axis displacement values of both index triggers.

        Returns a tuple (L,R) indicating index trigger displacement between -1.0
        and +1.0. Values increase from -1.0 to 1.0 the further a trigger is
        pushed.

        :return: tuple, zero centered L, R values.
        """
        al, ar = self._axes_mapping['triggers']

        al_val = self._clip_range(self.getAxis(al))
        ar_val = self._clip_range(self.getAxis(ar))

        return al_val, ar_val

    def _clip_range(self, val):
        """Clip the range of a value between -1.0 and +1.0. Needed for joystick
        axes.

        :param val:
        :return:
        """
        if -1.0 > val:
            val = -1.0

        if val > 1.0:
            val = 1.0

        return val
