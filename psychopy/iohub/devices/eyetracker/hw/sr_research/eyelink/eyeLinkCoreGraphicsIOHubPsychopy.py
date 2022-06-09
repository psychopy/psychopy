# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import numpy as np
from PIL import Image, ImageOps
from psychopy import visual
import sys
import tempfile
import os
from ..... import DeviceEvent, Computer
from ......constants import EventConstants
from ......errors import print2err, printExceptionDetailsToStdErr
from ......util import convertCamelToSnake, win32MessagePump, updateSettings
import pylink


class FixationTarget():
    def __init__(self, psychopy_eyelink_graphics):
        win = psychopy_eyelink_graphics.window
        color_type = psychopy_eyelink_graphics.getCalibSetting(['color_type'])
        unit_type = psychopy_eyelink_graphics.getCalibSetting(['unit_type'])

        outer_fill_color = outer_line_color = psychopy_eyelink_graphics.getCalibSetting(['target_attributes', 'outer_color'])
        inner_fill_color = inner_line_color = psychopy_eyelink_graphics.getCalibSetting(['target_attributes', 'inner_color'])

        if outer_fill_color is None:
            outer_fill_color = psychopy_eyelink_graphics.getCalibSetting(['target_attributes', 'outer_fill_color'])
            outer_line_color = psychopy_eyelink_graphics.getCalibSetting(['target_attributes', 'outer_line_color'])
        if inner_fill_color is None:
            inner_fill_color = psychopy_eyelink_graphics.getCalibSetting(['target_attributes', 'inner_fill_color'])
            inner_line_color = psychopy_eyelink_graphics.getCalibSetting(['target_attributes', 'inner_line_color'])

        self.calibrationPoint = visual.TargetStim(
            win, name="CP", style="circles",
            radius=psychopy_eyelink_graphics.getCalibSetting(['target_attributes', 'outer_diameter']) / 2.0,
            fillColor=outer_fill_color,
            borderColor=outer_line_color,
            lineWidth=psychopy_eyelink_graphics.getCalibSetting(['target_attributes', 'outer_stroke_width']),
            innerRadius=psychopy_eyelink_graphics.getCalibSetting(['target_attributes', 'inner_diameter']) / 2.0,
            innerFillColor=inner_fill_color,
            innerBorderColor=inner_line_color,
            innerLineWidth=psychopy_eyelink_graphics.getCalibSetting(['target_attributes', 'inner_stroke_width']),
            pos=(0, 0),
            units=unit_type,
            colorSpace=color_type,
            autoLog=False
        )
        self.calibrationPointOuter = self.calibrationPoint.outer
        self.calibrationPointInner = self.calibrationPoint.inner

    def draw(self, pos=None):
        if pos:
            self.calibrationPointOuter.pos = pos
            self.calibrationPointInner.pos = pos
        self.calibrationPoint.draw()

# Intro Screen
class BlankScreen():

    def __init__(self, psychopy_win, color):
        self.display_size = psychopy_win.size
        w, h = self.display_size
        win = psychopy_win
        self.color = color
        self.background = visual.Rect(win, w, h,
                                      lineColor=self.color,
                                      colorSpace=win.colorSpace,
                                      fillColor=self.color,
                                      units='pix',
                                      name='BACKGROUND',
                                      opacity=1.0,
                                      interpolate=False)

    def draw(self):
        self.background.draw()


# Intro Screen
class TextLine():
    def __init__(self, parent):
        self.display_size = parent.window.size
        win = parent.window
        tcolor, tctype = parent.getTextColorAndType()
        self.textLine = visual.TextStim(
            win,
            text='***********************',
            pos=(0, 0),
            height=30,
            color=tcolor,
            colorSpace=tctype,
            opacity=1.0,
            contrast=1.0,
            units='pix',
            ori=0.0,
            antialias=True,
            bold=False,
            italic=False,
            wrapWidth=self.display_size[0] * .8)

    def draw(self, text=None):
        if text:
            self.textLine.text = text
        self.textLine.draw()


# Intro Screen
class IntroScreen():
    def __init__(self, parent):
        window = parent.window
        self.display_size = window.size
        font_height = 24
        space_per_lines = font_height * 2.5
        if window.useRetina:
            topline_y = window.size[1] / 4 - font_height * 2
        else:
            topline_y = window.size[1] / 2 - font_height * 2
        wrap_width = window.size[1] * .8

        tcolor, tctype = parent.getTextColorAndType()

        self.introlines = []

        self.introlines.append(visual.TextStim(window,
                                               text='>>>> Eyelink System Setup:  Keyboard Actions <<<<',
                                               pos=(0, topline_y),
                                               height=font_height * 1.2,
                                               color=tcolor,
                                               colorSpace=tctype,
                                               opacity=1.0,
                                               contrast=1.0,
                                               units='pix',
                                               ori=0.0,
                                               antialias=True,
                                               bold=True,
                                               italic=False,
                                               wrapWidth=wrap_width))

        if window.useRetina:
            left_margin = -window.size[0] / 4
        else:
            left_margin = -window.size[0] / 2
        left_margin = left_margin * .4
        topline_y = topline_y - space_per_lines / 3
        self.introlines.append(visual.TextStim(window,
                                               text='* ENTER: Begin Camera Setup Mode',
                                               pos=(left_margin, topline_y - space_per_lines * (len(self.introlines))),
                                               height=font_height,
                                               color=tcolor,
                                               colorSpace=tctype,
                                               opacity=1.0,
                                               contrast=1.0,
                                               units='pix',
                                               ori=0.0,
                                               antialias=True,
                                               bold=False,
                                               italic=False,
                                               alignText='left',
                                               anchorHoriz='left',
                                               wrapWidth=wrap_width))

        self.introlines.append(visual.TextStim(window,
                                               text='* C: Start Calibration Procedure',
                                               pos=(left_margin,
                                                    topline_y - space_per_lines * (len(self.introlines))),
                                               height=font_height,
                                               color=tcolor,
                                               colorSpace=tctype,
                                               opacity=1.0,
                                               contrast=1.0,
                                               units='pix',
                                               ori=0.0,
                                               antialias=True,
                                               bold=True,
                                               italic=False,
                                               alignText='left',
                                               anchorHoriz='left',
                                               wrapWidth=wrap_width))

        self.introlines.append(visual.TextStim(window,
                                               text='* V: Start Validation Procedure',
                                               pos=(left_margin, topline_y - space_per_lines * (len(self.introlines))),
                                               height=font_height,
                                               color=tcolor,
                                               colorSpace=tctype,
                                               opacity=1.0,
                                               contrast=1.0,
                                               units='pix',
                                               ori=0.0,
                                               antialias=True,
                                               bold=False,
                                               italic=False,
                                               alignText='left',
                                               anchorHoriz='left',
                                               wrapWidth=wrap_width))

        self.introlines.append(visual.TextStim(window,
                                               text='* ESCAPE: Exit EyeLink System Setup',
                                               pos=(left_margin, topline_y - space_per_lines * (len(self.introlines))),
                                               height=font_height,
                                               color=tcolor,
                                               colorSpace=tctype,
                                               opacity=1.0,
                                               contrast=1.0,
                                               units='pix',
                                               ori=0.0,
                                               antialias=True,
                                               bold=True,
                                               italic=False,
                                               alignText='left',
                                               anchorHoriz='left',
                                               wrapWidth=wrap_width))

        topline_y = topline_y - space_per_lines / 3
        self.introlines.append(visual.TextStim(window,
                                               text='------ Camera Setup Mode Specific Actions ------',
                                               pos=(0, topline_y - space_per_lines * (len(self.introlines))),
                                               height=font_height * 1.2,
                                               color=tcolor,
                                               colorSpace=tctype,
                                               opacity=1.0,
                                               contrast=1.0,
                                               units='pix',
                                               ori=0.0,
                                               antialias=True,
                                               bold=True,
                                               italic=False,
                                               wrapWidth=wrap_width))

        topline_y = topline_y - space_per_lines / 3
        self.introlines.append(visual.TextStim(window, text='* Left / Right Arrow: Switch Between Camera Views',
                                               pos=(left_margin, topline_y - space_per_lines * (len(self.introlines))),
                                               height=font_height,
                                               color=tcolor,
                                               colorSpace=tctype,
                                               opacity=1.0,
                                               contrast=1.0,
                                               units='pix',
                                               ori=0.0,
                                               antialias=True,
                                               bold=False,
                                               italic=False,
                                               alignText='left',
                                               anchorHoriz='left',
                                               wrapWidth=wrap_width))

        self.introlines.append(visual.TextStim(window,
                                               text='* A: Auto-Threshold Image',
                                               pos=(left_margin, topline_y - space_per_lines * (len(self.introlines))),
                                               height=font_height,
                                               color=tcolor,
                                               colorSpace=tctype,
                                               opacity=1.0,
                                               contrast=1.0,
                                               units='pix',
                                               ori=0.0,
                                               antialias=True,
                                               bold=False,
                                               italic=False,
                                               alignText='left',
                                               anchorHoriz='left',
                                               wrapWidth=wrap_width))

        self.introlines.append(visual.TextStim(window,
                                               text='* Up / Down Arrow: Manually Adjust Pupil Threshold',
                                               pos=(left_margin, topline_y - space_per_lines * (len(self.introlines))),
                                               height=font_height,
                                               color=tcolor,
                                               colorSpace=tctype,
                                               opacity=1.0,
                                               contrast=1.0,
                                               units='pix',
                                               ori=0.0,
                                               antialias=True,
                                               bold=False,
                                               italic=False,
                                               alignText='left',
                                               anchorHoriz='left',
                                               wrapWidth=wrap_width))

        self.introlines.append(visual.TextStim(window,
                                               text='* + or -: Manually Adjust CR Threshold.',
                                               pos=(left_margin, topline_y - space_per_lines * (len(self.introlines))),
                                               height=font_height,
                                               color=tcolor,
                                               colorSpace=tctype,
                                               opacity=1.0,
                                               contrast=1.0,
                                               units='pix',
                                               ori=0.0,
                                               antialias=True,
                                               bold=False,
                                               italic=False,
                                               alignText='left',
                                               anchorHoriz='left',
                                               wrapWidth=wrap_width))

    def draw(self):
        for s in self.introlines:
            s.draw()


class EyeLinkCoreGraphicsIOHubPsychopy(pylink.EyeLinkCustomDisplay):
    # seconds between forced run through of micro threads, since one is blocking
    # on camera setup.
    IOHUB_HEARTBEAT_INTERVAL = 0.050

    def __init__(self, eyetrackerInterface, calibration_args):
        pylink.EyeLinkCustomDisplay.__init__(self)
        self._eyetrackerinterface = eyetrackerInterface
        display = eyetrackerInterface._display_device
        self._device_config = self._eyetrackerinterface.getConfiguration()
        updateSettings(self._device_config.get('calibration'), calibration_args)
        self._calibration_args = self._device_config.get('calibration')
        #print2err("self._calibration_args:", self._calibration_args)
        unit_type = self.getCalibSetting('unit_type')
        if unit_type is None:
            unit_type = display.getCoordinateType()
            self._calibration_args['unit_type'] = unit_type
        color_type = self.getCalibSetting('color_type')
        if color_type is None:
            color_type = display.getColorSpace()
            self._calibration_args['color_type'] = color_type

        if display.getCoordinateType() != unit_type:
            raise RuntimeWarning("EyeLink Calibration requires same unit type"
                                 " as window {} vs {}.".format(display.getCoordinateType(),
                                                               unit_type))

        self.tracker = eyetrackerInterface._eyelink
        self._ioKeyboard = None
        self._ioMouse = None

        self.imgstim_size = None
        self.rgb_index_array = None

        self.screenSize = display.getPixelResolution()
        self.width = self.screenSize[0]
        self.height = self.screenSize[1]

        self.keys = []
        self.mouse_pos = []
        self.mouse_button_state = 0

        if sys.byteorder == 'little':
            self.byteorder = 1
        else:
            self.byteorder = 0

        self.tmp_file = os.path.join(tempfile.gettempdir(), '_eleye.png')

        self.tracker.setOfflineMode()
        self.tracker_version = self.tracker.getTrackerVersion()
        if self.tracker_version >= 3:
            self.tracker.sendCommand('enable_search_limits=YES')
            self.tracker.sendCommand('track_search_limits=YES')
            self.tracker.sendCommand('autothreshold_click=YES')
            self.tracker.sendCommand('autothreshold_repeat=YES')
            self.tracker.sendCommand('enable_camera_position_detect=YES')

        self.window = visual.Window(display.getPixelResolution(),
                                    monitor=display.getPsychopyMonitorName(),
                                    units=unit_type,
                                    color=self.getCalibSetting(['screen_background_color']),
                                    colorSpace=color_type,
                                    fullscr=True,
                                    allowGUI=False,
                                    screen=display.getIndex()
                                    )

        self.blankdisplay = BlankScreen(self.window, self.getCalibSetting(['screen_background_color']))
        self.textmsg = TextLine(self)
        self.introscreen = IntroScreen(self)
        self.fixationpoint = FixationTarget(self)
        self.imagetitlestim = None
        self.eye_image = None
        self.state = None
        self.eye_frame_size = (0, 0)

        self._registerEventMonitors()
        self._lastMsgPumpTime = Computer.getTime()
        self.clearAllEventBuffers()

    def getCalibSetting(self, setting):
        if isinstance(setting, str):
            setting = [setting, ]
        calibration_args = self._calibration_args
        if setting:
            for s in setting[:-1]:
                calibration_args = calibration_args.get(s)
            return calibration_args.get(setting[-1])

    def getTextColorAndType(self):
        color_type = self.getCalibSetting('color_type')
        if color_type is None:
            color_type = self.window.colorSpace
        tcolor = self.getCalibSetting(['text_color'])
        if tcolor is None:
            # If no calibration text color provided, base it on the window background color
            from psychopy.iohub.util import complement
            sbcolor = self.getCalibSetting(['screen_background_color'])
            if sbcolor is None:
                sbcolor = self.window.color
            from psychopy.colors import Color
            tcolor_obj = Color(sbcolor, color_type)
            tcolor = complement(*tcolor_obj.rgb255)
            color_type = 'rgb255'
        return tcolor, color_type

    def clearAllEventBuffers(self):
        pylink.flushGetkeyQueue()
        self.tracker.resetData()
        self._iohub_server.eventBuffer.clear()
        for d in self._iohub_server.devices:
            d.clearEvents()

    def _registerEventMonitors(self):
        self._iohub_server = self._eyetrackerinterface._iohub_server
        kbDevice = None
        mouseDevice = None
        if self._iohub_server:
            for dev in self._iohub_server.devices:
                if dev.__class__.__name__ == 'Keyboard':
                    kbDevice = dev
                elif dev.__class__.__name__ == 'Mouse':
                    mouseDevice = dev

        if kbDevice:
            eventIDs = []
            for event_class_name in kbDevice.__class__.EVENT_CLASS_NAMES:
                eventIDs.append(getattr(EventConstants, convertCamelToSnake(event_class_name[:-5], False)))

            self._ioKeyboard = kbDevice
            self._ioKeyboard._addEventListener(self, eventIDs)
        else:
            print2err(
                'Warning: elCG could not connect to Keyboard device for events.')

        if mouseDevice:
            eventIDs = []
            for event_class_name in mouseDevice.__class__.EVENT_CLASS_NAMES:
                eventIDs.append(getattr(EventConstants, convertCamelToSnake(event_class_name[:-5], False)))

            self._ioMouse = mouseDevice
            self._ioMouse._addEventListener(self, eventIDs)
        else:
            print2err(
                'Warning: elCG could not connect to Mouse device for events.')

    def _unregisterEventMonitors(self):
        if self._ioKeyboard:
            self._ioKeyboard._removeEventListener(self)
        if self._ioMouse:
            self._ioMouse._removeEventListener(self)

    def _handleEvent(self, event):
        event_type_index = DeviceEvent.EVENT_TYPE_ID_INDEX
        if event[event_type_index] == EventConstants.KEYBOARD_RELEASE:
            from .....keyboard import KeyboardInputEvent
            key_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key')
            char = event[key_index]
            if isinstance(char, bytes):
                char = str(event[key_index], 'utf-8')

            if char:
                char = char.lower()
            else:
                return

            pylink_key = None
            if char == 'escape':
                pylink_key = pylink.ESC_KEY
                self.state = None
            elif char == 'return':
                pylink_key = pylink.ENTER_KEY
                self.state = None
            elif char == ' ' or char == 'space':
                pylink_key = ord(' ')
            elif char == 'c':
                pylink_key = ord(char)
                self.state = 'calibration'
            elif char == 'v':
                pylink_key = ord(char)
                self.state = 'validation'
            elif char == 'a':
                pylink_key = ord(char)
            elif char == 'o':
                pylink_key = ord(char)
            elif char == 'pageup':
                pylink_key = pylink.PAGE_UP
            elif char == 'pagedown':
                pylink_key = pylink.PAGE_DOWN
            elif char == '-' or char == 'minus':
                pylink_key = ord('-')
            elif char == '=' or char == 'equal':
                pylink_key = ord('=')
            elif char == 'up':
                pylink_key = pylink.CURS_UP
            elif char == 'down':
                pylink_key = pylink.CURS_DOWN
            elif char == 'left':
                pylink_key = pylink.CURS_LEFT
            elif char == 'right':
                pylink_key = pylink.CURS_RIGHT
            else:
                return
            self.keys.append(pylink.KeyInput(pylink_key, 0))

        elif event[event_type_index] == EventConstants.MOUSE_BUTTON_PRESS:
            self.mouse_button_state = 1

        elif event[event_type_index] == EventConstants.MOUSE_BUTTON_RELEASE:
            self.mouse_button_state = 0

        elif event[event_type_index] == EventConstants.MOUSE_MOVE:
            self.mouse_pos = self._ioMouse.getPosition()

    def get_input_key(self):
        if Computer.getTime() - self._lastMsgPumpTime > self.IOHUB_HEARTBEAT_INTERVAL:
            if self._iohub_server:
                win32MessagePump()
                for dm in self._iohub_server.deviceMonitors:
                    dm.device._poll()
                self._iohub_server.processDeviceEvents()
            self._lastMsgPumpTime = Computer.getTime()
        if len(self.keys) > 0:
            k = self.keys
            self.keys = []
            return k
        else:
            return None

    def setup_cal_display(self):
        """Sets up the initial calibration display, which contains a menu with
        instructions."""
        self.blankdisplay.draw()
        self.introscreen.draw()
        self.window.flip()

    def exit_cal_display(self):
        """Exits calibration display and return to initial menu with
        instructions."""
        self.setup_cal_display()


    def clear_cal_display(self):
        """Clears the calibration display."""
        self.blankdisplay.draw()
        self.window.flip()

    def erase_cal_target(self):
        """Removes any visible calibration target graphic from display."""
        self.clear_cal_display()

    def draw_cal_target(self, x, y):
        """Draws calibration target."""
        # convert to psychopy pix coords
        x, y = self._eyetrackerinterface._eyeTrackerToDisplayCoords((x, y))

        self.blankdisplay.draw()
        self.fixationpoint.draw((x, y))
        self.window.flip()

    def setup_image_display(self, width, height):
        """Initialize the index array that will contain camera image data."""

        if width and height:
            self.eye_frame_size = (width, height)
            self.clear_cal_display()
            self.last_mouse_state = -1
            if self.rgb_index_array is None:
                self.rgb_index_array = np.zeros((int(height / 2), int(width / 2)), dtype=np.uint8)

    def exit_image_display(self):
        """Exits the image display."""
        self.clear_cal_display()

    def image_title(self, text):
        """Display the current camera, Pupil, and CR thresholds above the
        camera image when in Camera Setup Mode."""
        if self.imagetitlestim is None:
            tcolor, tctype = self.getTextColorAndType()
            self.imagetitlestim = visual.TextStim(
                self.window,
                text=text,
                pos=(0, self.window.size[1] / 2 - 15),
                height=28,
                color=tcolor,
                colorSpace=tctype,
                opacity=1.0,
                contrast=1.0,
                units='pix',
                ori=0.0,
                antialias=True,
                bold=False,
                italic=False,
                anchorVert='top',
                wrapWidth=self.window.size[0] * .8)
        else:
            self.imagetitlestim.setText(text)
        # self.imagetitlestim.draw()

    def draw_image_line(self, width, line, totlines, buff):
        """Collects all lines for an eye image, saves the image, then creates a
        psychopy imagestim from it."""
        for i in range(width):
            try:
                self.rgb_index_array[line - 1, i] = buff[i]
            except Exception as e:
                printExceptionDetailsToStdErr()
                print2err(
                    'FAILED TO DRAW PIXEL TO IMAGE LINE: %d %d' %
                    (line - 1, i))

        # Once all lines have been collected, go through the hoops needed
        # to display the frame as an image; scaled to fit the display
        # resolution.
        if line == totlines:
            try:
                image = Image.fromarray(self.rgb_index_array,
                                        mode='P')
                image.putpalette(self.rgb_pallete)
                image = ImageOps.fit(image, [640, 480])
                if self.eye_image is None:
                    self.eye_image = visual.ImageStim(
                        self.window, image)
                else:
                    self.eye_image.setImage(image)

                # Redraw the Camera Setup Mode graphics
                self.blankdisplay.draw()
                self.eye_image.draw()
                if self.imagetitlestim:
                    self.imagetitlestim.draw()
                self.window.flip()

            except Exception as err:
                print2err('Error during eye image display: ', err)
                printExceptionDetailsToStdErr()

    def set_image_palette(self, r, g, b):
        """Set color palette used by host pc when sending images.

        Saves the different r,g,b values provided by the eyelink host
        palette. When building up each eye image frame, eyelink sends
        the palette index for each pixel; so an eyelink eye image frame
        can be a 2D lookup array into this palette.

        """
        self.clear_cal_display()
        sz = len(r)
        self.rgb_pallete = np.zeros((sz, 3), dtype=np.uint8)
        i = 0
        while i < sz:
            self.rgb_pallete[i:] = int(r[i]), int(g[i]), int(b[i])
            i += 1

    def alert_printf(self, msg):
        """Prints alert message to psychopy stderr."""
        print2err('eyelink_graphics.alert_printf(): %s' % msg)

    ###

    def play_beep(self, pylink_sound_index):
        """
        TODO: Plays a sound.
        """
        if pylink_sound_index == pylink.CAL_TARG_BEEP:
            pass
        elif pylink_sound_index == pylink.CAL_ERR_BEEP or pylink_sound_index == pylink.DC_ERR_BEEP:
            self.textmsg.draw('Calibration Failed or Incomplete.')
            self.window.flip()
        elif pylink_sound_index == pylink.CAL_GOOD_BEEP:
            if self.state == 'calibration':
                self.textmsg.draw('Calibration Passed.')
                self.window.flip()
            elif self.state == 'validation':
                self.textmsg.draw('Validation Passed.')
                self.window.flip()
        else:
            pass

    def draw_line(self, x1, y1, x2, y2, color_index):
        """TODO."""
        pass

    def draw_lozenge(self, x, y, width, height, color_index):
        """TODO."""
        pass

    def record_abort_hide(self):
        """TODO."""
        pass

    def get_mouse_state(self):
        """TODO."""
        pass
