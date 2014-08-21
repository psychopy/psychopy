"""
ioHub
Common Eye Tracker Interface
.. file: ioHub/devices/eyeTracker/hw/sr_research/eyelink/eyeLinkCoreGraphicsIOHubPsychopy.py

Copyright (C) 2012-2013 iSolver Software Solutions

Copyright (C) 2012 Sol Simpson
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

---------------------------------------------------------------------------------------------------------------------
This file uses the pylink module, Copyright (C) SR Research Ltd. License type unknown as it is not provided in the
pylink distribution (atleast when downloaded May 2012). At the time of writing, Pylink is freely avalaible for
download from  www.sr-support.com once you are registered and includes the necessary C DLLs.
---------------------------------------------------------------------------------------------------------------------

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

import numpy as np
import scipy
import psychopy
from psychopy import visual
import sys
import tempfile
import os
from ..... import DeviceEvent, Computer
from ......constants import EventConstants, KeyboardConstants
from ...... import convertCamelToSnake, print2err, printExceptionDetailsToStdErr
import pylink

class FixationTarget(object):
    def __init__(self, psychopy_eyelink_graphics):
        self.calibrationPointOuter = visual.Circle(
                                psychopy_eyelink_graphics.window,
                                pos=(0,0),
                                lineWidth=1.0,
                                lineColor=psychopy_eyelink_graphics.CALIBRATION_POINT_OUTER_COLOR,
                                lineColorSpace='rgb255',
                                fillColor=psychopy_eyelink_graphics.CALIBRATION_POINT_OUTER_COLOR,
                                fillColorSpace='rgb255',
                                radius=psychopy_eyelink_graphics.CALIBRATION_POINT_OUTER_RADIUS,
                                name='CP_OUTER',
                                units='pix',
                                opacity=1.0,
                                interpolate=False)
        self.calibrationPointInner = visual.Circle(
                                psychopy_eyelink_graphics.window,
                                pos=(0,0),lineWidth=1.0,
                                lineColor=psychopy_eyelink_graphics.CALIBRATION_POINT_INNER_COLOR,
                                lineColorSpace='rgb255',
                                fillColor=psychopy_eyelink_graphics.CALIBRATION_POINT_INNER_COLOR,
                                fillColorSpace='rgb255',
                                radius=psychopy_eyelink_graphics.CALIBRATION_POINT_INNER_RADIUS,
                                name='CP_INNER',
                                units='pix',
                                opacity=1.0,
                                interpolate=False)
    def draw(self, pos = None):
        if pos:
            self.calibrationPointOuter.pos = pos
            self.calibrationPointInner.pos = pos
        self.calibrationPointOuter.draw()
        self.calibrationPointInner.draw()


# Intro Screen
class BlankScreen(object):
    WINDOW_BACKGROUND_COLOR=(128,128,128)
    def __init__(self,psychopy_win):
        self.display_size = psychopy_win.size
        w,h = self.display_size
        self.win = psychopy_win
        self.background = visual.Rect(self.win, w, h,
                                                   lineColor=self.WINDOW_BACKGROUND_COLOR,
                                                   lineColorSpace='rgb255',
                                                   fillColor=self.WINDOW_BACKGROUND_COLOR,
                                                   fillColorSpace='rgb255',
                                                   units='pix',
                                                   name='BACKGROUND',
                                                   opacity=1.0,
                                                   interpolate=False)
    def draw(self):
        self.background.draw()


# Intro Screen
class TextLine(object):
    def __init__(self,psychopy_win):
        self.display_size = psychopy_win.size
        self.win = psychopy_win

        self.textLine = visual.TextStim(self.win,
            text="***********************",
            pos=(0,0),
            height = 30,
            color=(0, 0, 0), colorSpace='rgb255',
            opacity=1.0, contrast=1.0, units='pix',
            ori=0.0, antialias=True,
            bold=False, italic=False, alignHoriz='center',
            alignVert='center', wrapWidth=self.display_size[0]*.8)
    def draw(self, text=None):
        if text:
            self.textLine.text = text
        self.textLine.draw()


# Intro Screen
class IntroScreen(object):
    def __init__(self,psychopy_win):
        self.display_size = psychopy_win.size
        self.window = psychopy_win
        line_count = 13
        font_height = 30
        space_per_lines = int(font_height*2.5)
        total_line_height = space_per_lines*line_count
        topline_y = int(min(total_line_height/1.5, self.display_size[1]/2-20))

        left_margin = -self.display_size[0]/6
        self.introlines = []

        self.introlines.append(visual.TextStim(self.window,
            text=">>>> Eyelink System Setup:  Keyboard Actions <<<<",
            pos=(0, topline_y),
            height = int(font_height*1.66),
            color=(0, 0, 0),
            colorSpace='rgb255',
            opacity=1.0,
            contrast=1.0,
            units='pix',
            ori=0.0,
            antialias=True,
            bold=True,
            italic=False,
            alignHoriz='center',
            alignVert='top',
            wrapWidth=self.display_size[0]*.8))

        self.introlines.append(visual.TextStim(self.window,
            text="* ENTER: Begin Camera Setup Mode",
            pos=(left_margin,topline_y-space_per_lines*(len(self.introlines)+2)), height = font_height,
            color=(0, 0, 0), colorSpace='rgb255',
            opacity=1.0, contrast=1.0, units='pix',
            ori=0.0, antialias=True,
            bold=False, italic=False, alignHoriz='left',
            alignVert='center', wrapWidth=self.display_size[0]*.8))

        self.introlines.append(visual.TextStim(self.window,
            text="* C: Start Calibration Procedure",
            pos=(left_margin,topline_y-space_per_lines*(len(self.introlines)+2)),
            height = font_height,
            color=(0, 0, 0),
            colorSpace='rgb255',
            opacity=1.0,
            contrast=1.0,
            units='pix',
            ori=0.0,
            antialias=True,
            bold=False,
            italic=False,
            alignHoriz='left',
            alignVert='center',
            wrapWidth=self.display_size[0]*.8))

        self.introlines.append(visual.TextStim(self.window,
            text="* V: Start Calidation Procedure",
            pos=(left_margin,topline_y-space_per_lines*(len(self.introlines)+2)),
            height = font_height,
            color=(0, 0, 0), colorSpace='rgb255',
            opacity=1.0, contrast=1.0, units='pix',
            ori=0.0, antialias=True,
            bold=False, italic=False, alignHoriz='left',
            alignVert='center', wrapWidth=self.display_size[0]*.8))

        self.introlines.append(visual.TextStim(self.window,
            text="* ESCAPE or Q: Exit EyeLink System Setup",
            pos=(left_margin,topline_y-space_per_lines*(len(self.introlines)+2)),
            height = font_height,
            color=(0, 0, 0), colorSpace='rgb255',
            opacity=1.0, contrast=1.0, units='pix',
            ori=0.0, antialias=True,
            bold=False, italic=False, alignHoriz='left',
            alignVert='center', wrapWidth=self.display_size[0]*.8))

        self.introlines.append(visual.TextStim(self.window,
            text="-- Camera Setup Mode Specific Actions --",
            pos=(0,topline_y-space_per_lines*(len(self.introlines)+2)), height = font_height,
            color=(0, 0, 0), colorSpace='rgb255',
            opacity=1.0, contrast=1.0, units='pix',
            ori=0.0, antialias=True,
            bold=False, italic=False, alignHoriz='center',
            alignVert='center', wrapWidth=self.display_size[0]*.8))

        self.introlines.append(visual.TextStim(self.window,
            text="* Left / Right Arrow: Switch Between Camera Views",
            pos=(left_margin,topline_y-space_per_lines*(len(self.introlines)+2)), height = font_height,
            color=(0, 0, 0), colorSpace='rgb255',
            opacity=1.0, contrast=1.0, units='pix',
            ori=0.0, antialias=True,
            bold=False, italic=False, alignHoriz='left',
            alignVert='center', wrapWidth=self.display_size[0]*.8))

        self.introlines.append(visual.TextStim(self.window,
            text="* A: Auto-Threshold Image",
            pos=(left_margin,topline_y-space_per_lines*(len(self.introlines)+2)), height = font_height,
            color=(0, 0, 0), colorSpace='rgb255',
            opacity=1.0, contrast=1.0, units='pix',
            ori=0.0, antialias=True,
            bold=False, italic=False, alignHoriz='left',
            alignVert='center', wrapWidth=self.display_size[0]*.8))

        self.introlines.append(visual.TextStim(self.window,
            text="* Up / Down Arrow: Manually Adjust Pupil Threshold",
            pos=(left_margin,topline_y-space_per_lines*(len(self.introlines)+2)),
            height = font_height,
            color=(0, 0, 0), colorSpace='rgb255',
            opacity=1.0, contrast=1.0, units='pix',
            ori=0.0, antialias=True,
            bold=False, italic=False, alignHoriz='left',
            alignVert='center', wrapWidth=self.display_size[0]*.8))

        self.introlines.append(visual.TextStim(self.window,
            text="* + or -: Manually Adjust CR Threshold.",
            pos=(left_margin,topline_y-space_per_lines*(len(self.introlines)+2)),
            height = font_height,
            color=(0, 0, 0), colorSpace='rgb255',
            opacity=1.0, contrast=1.0, units='pix',
            ori=0.0, antialias=True,
            bold=False, italic=False, alignHoriz='left',
            alignVert='center', wrapWidth=self.display_size[0]*.8))

    def draw(self):
        for s in self.introlines:
            s.draw()

class EyeLinkCoreGraphicsIOHubPsychopy(pylink.EyeLinkCustomDisplay):
    IOHUB_HEARTBEAT_INTERVAL=0.050   # seconds between forced run through of
                                     # micro threads, since one is blocking
                                     # on camera setup.

    WINDOW_BACKGROUND_COLOR = (128,128,128)
    CALIBRATION_POINT_OUTER_RADIUS = 15.0,15.0
    CALIBRATION_POINT_OUTER_EDGE_COUNT = 64
    CALIBRATION_POINT_OUTER_COLOR = (255,255,255)
    CALIBRATION_POINT_INNER_RADIUS = 3.0,3.0
    CALIBRATION_POINT_INNER_EDGE_COUNT = 32
    CALIBRATION_POINT_INNER_COLOR = (25,25,25)

    def __init__(self, eyetrackerInterface, targetForegroundColor=None,
                 targetBackgroundColor=None, screenColor=None,
                 targetOuterDiameter=None, targetInnerDiameter=None):
        pylink.EyeLinkCustomDisplay.__init__(self)

        self._eyetrackerinterface=eyetrackerInterface
        self.tracker = eyetrackerInterface._eyelink
        self._ioKeyboard=None
        self._ioMouse=None

        self.imgstim_size = None
        self.rgb_index_array = None

        self.screenSize = self._eyetrackerinterface._display_device.getPixelResolution()
        self.width = self.screenSize[0]
        self.height = self.screenSize[1]

        self.keys = []
        self.mouse_pos = []
        self.mouse_button_state = 0

        if sys.byteorder == 'little':
            self.byteorder = 1
        else:
            self.byteorder = 0

        EyeLinkCoreGraphicsIOHubPsychopy.CALIBRATION_POINT_OUTER_COLOR=targetForegroundColor
        EyeLinkCoreGraphicsIOHubPsychopy.CALIBRATION_POINT_INNER_COLOR=targetBackgroundColor
        EyeLinkCoreGraphicsIOHubPsychopy.WINDOW_BACKGROUND_COLOR=screenColor
        EyeLinkCoreGraphicsIOHubPsychopy.CALIBRATION_POINT_OUTER_RADIUS=targetOuterDiameter/2.0,targetOuterDiameter/2.0
        EyeLinkCoreGraphicsIOHubPsychopy.CALIBRATION_POINT_INNER_RADIUS=targetInnerDiameter/2.0,targetInnerDiameter/2.0

        self.tmp_file = os.path.join(tempfile.gettempdir(),'_eleye.png')

        self.tracker.setOfflineMode();
        self.tracker_version = self.tracker.getTrackerVersion()
        if self.tracker_version >= 3:
            self.tracker.sendCommand("enable_search_limits=YES")
            self.tracker.sendCommand("track_search_limits=YES")
            self.tracker.sendCommand("autothreshold_click=YES")
            self.tracker.sendCommand("autothreshold_repeat=YES")
            self.tracker.sendCommand("enable_camera_position_detect=YES")


        display=self._eyetrackerinterface._display_device
        self.window = visual.Window(display.getPixelResolution(),
                                  monitor=display.getPsychopyMonitorName(),
                                  units=display.getCoordinateType(),
                                  fullscr=True,
                                  allowGUI=False,
                                  screen=display.getIndex()
                                  )

        self.window.setColor(color=self.WINDOW_BACKGROUND_COLOR,
                             colorSpace='rgb255')
        self.window.flip(clearBuffer=True)

        self.blankdisplay = BlankScreen(self.window)
        self.textmsg = TextLine(self.window)
        self.introscreen = IntroScreen(self.window)
        self.fixationpoint = FixationTarget(self)
        self.imagetitlestim = None
        self.eye_image = None
        self.state = None
        self.size = (0, 0)

        self._registerEventMonitors()
        self._ioMouse.setSystemCursorVisibility(False)
        self._lastMsgPumpTime = Computer.getTime()
        self.clearAllEventBuffers()

    def clearAllEventBuffers(self):
        pylink.flushGetkeyQueue();
        self.tracker.resetData()
        self._iohub_server.eventBuffer.clear()
        for d in self._iohub_server.devices:
            d.clearEvents()

    def _registerEventMonitors(self):
        self._iohub_server=self._eyetrackerinterface._iohub_server

        if self._iohub_server:
            for dev in self._iohub_server.devices:
                #print2err("dev: ",dev.__class__.__name__)
                if dev.__class__.__name__ == 'Keyboard':
                    kbDevice=dev
                elif dev.__class__.__name__ == 'Mouse':
                    mouseDevice=dev

        if kbDevice:
            eventIDs=[]
            for event_class_name in kbDevice.__class__.EVENT_CLASS_NAMES:
                eventIDs.append(getattr(EventConstants,convertCamelToSnake(event_class_name[:-5],False)))

            self._ioKeyboard=kbDevice
            self._ioKeyboard._addEventListener(self,eventIDs)
        else:
            print2err("Warning: elCG could not connect to Keyboard device for events.")

        if mouseDevice:
            eventIDs=[]
            for event_class_name in mouseDevice.__class__.EVENT_CLASS_NAMES:
                eventIDs.append(getattr(EventConstants,convertCamelToSnake(event_class_name[:-5],False)))

            self._ioMouse=mouseDevice
            self._ioMouse._addEventListener(self,eventIDs)
        else:
            print2err("Warning: elCG could not connect to Mouse device for events.")

    def _unregisterEventMonitors(self):
        if self._ioKeyboard:
            self._ioKeyboard._removeEventListener(self)
        if self._ioMouse:
            self._ioMouse._removeEventListener(self)

    def _handleEvent(self, event):
        event_type_index = DeviceEvent.EVENT_TYPE_ID_INDEX
        if event[event_type_index] == EventConstants.KEYBOARD_RELEASE:
            from psychopy.iohub.devices.keyboard import KeyboardInputEvent
            char_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('char')
            modifiers_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('modifiers')
            char = event[char_index]
            #mods = event[modifiers_index]

            if char:
                char = char.lower()
            else:
                return

            pylink_key = None
            if char == "escape":
                pylink_key = pylink.ESC_KEY
                self.state = None
            elif char == "return":
                pylink_key = pylink.ENTER_KEY
                self.state = None
            elif char == " ":
                pylink_key = ord(char)
            elif char == "c":
                pylink_key = ord(char)
                self.state = "calibration"
            elif char == "v":
                pylink_key = ord(char)
                self.state = "validation"
            elif char == "a":
                pylink_key = ord(char)
            elif char == "page_up":
                pylink_key = pylink.PAGE_UP
            elif char == "page_down":
                pylink_key = pylink.PAGE_DOWN
            elif char == "-":
                pylink_key = ord(char)
            elif char == "=":
                pylink_key = ord(char)
            elif char == "up":
                pylink_key = pylink.CURS_UP
            elif char == "down":
                pylink_key = pylink.CURS_DOWN
            elif char == "left":
                pylink_key = pylink.CURS_LEFT
            elif char == "right":
                pylink_key = pylink.CURS_RIGHT
            else:
                #print2err("EyeLink Setup: Unhandled keyboard evt: [%s] [%s]"%(char, mods))
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
                for dm in self._iohub_server.deviceMonitors:
                    dm.device._poll()
                self._iohub_server._processDeviceEventIteration()
            self._lastMsgPumpTime=Computer.getTime()
        if len(self.keys) > 0:
            k = self.keys
            self.keys=[]
            return k
        else:
            return None

    def setup_cal_display(self):
        """
        Sets up the initial calibration display, which contains a menu with
        instructions.
        """
        self.blankdisplay.draw()
        self.introscreen.draw()
        self.window.flip()

    def exit_cal_display(self):
        """Exits calibration display."""
        self.clear_cal_display()

    def clear_cal_display(self):
        """Clears the calibration display"""
        self.blankdisplay.draw()
        self.window.flip()

    def erase_cal_target(self):
        """Removes any visible calibration target graphic from display."""
        self.clear_cal_display()

    def draw_cal_target(self, x, y):
        """
        Draws calibration target.
        """
        # convert to psychopy pix coords
        x = x-self.window.size[0]/2
        y = -(y-self.window.size[1]/2)
        self.blankdisplay.draw()
        self.fixationpoint.draw((x,y))
        self.window.flip()

    def setup_image_display(self, width, height):
        """
        Initialize the index array that will contain camera image data.
        """

        self.size = (width,height)
        self.clear_cal_display()
        self.last_mouse_state = -1
        if self.rgb_index_array is None:
            self.rgb_index_array =  np.zeros((height, width), dtype = np.uint8)

    def exit_image_display(self):
        """Exits the image display."""
        self.clear_cal_display()

    def image_title(self, text):
        """
        Display the current camera, Pupil, and CR thresholds above
        the camera image when in Camera Setup Mode.
        """
        if self.imagetitlestim is None:
           self.imagetitlestim = visual.TextStim(self.window,
                text=text,
                pos=(0,self.window.size[1]/2-15), height = 28,
                color=(0, 0, 0), colorSpace='rgb255',
                opacity=1.0, contrast=1.0, units='pix',
                ori=0.0, antialias=True,
                bold=False, italic=False, alignHoriz='center',
                alignVert='top', wrapWidth=self.window.size[0]*.8)
        else:
            self.imagetitlestim.setText(text)
        #self.imagetitlestim.draw()

    def draw_image_line(self, width, line, totlines, buff):
        """
        Collects all lines for an eye image, saves the image,
        then creates a psychopy imagestim from it.
        """
        for i in range(width):
            try:
                self.rgb_index_array[line-1, i] = buff[i]
            except Exception, e:
                printExceptionDetailsToStdErr()
                print2err("FAILED TO DRAW PIXEL TO IMAGE LINE: %d %d"%(line-1,i))

        # Once all lines have been collected, go through the hoops needed
        # to display the frame as an image; scaled to fit the display resolution.
        if line == totlines:
            try:
                image = scipy.misc.toimage(self.rgb_index_array,
                                           pal=self.rgb_pallete,
                                           mode='P')
                if self.imgstim_size is None:
                    maxsz = self.width/2
                    mx = 1.0
                    while (mx+1) * self.size[0] <= maxsz:
                        mx += 1.0
                    self.imgstim_size = int(self.size[0]*mx), int(self.size[1]*mx)
                image = image.resize(self.imgstim_size)

                #TODO: There must be a way to just hand an ImageSTim a nxmx3
                # array for the image data??
                image.save(self.tmp_file, 'PNG')
                if self.eye_image is None:
                    self.eye_image = visual.ImageStim(self.window, self.tmp_file)
                else:
                    self.eye_image.setImage(self.tmp_file)

                # Redraw the Camera Setup Mode graphics
                self.blankdisplay.draw()
                self.eye_image.draw()
                if self.imagetitlestim:
                    self.imagetitlestim.draw()
                self.window.flip()

            except Exception, err:
                import traceback
                print2err("Error during eye image display: ", err)
                printExceptionDetailsToStdErr()

    def set_image_palette(self, r, g, b):
        """
        Set color palette ued by host pc when sending images.
        Saves the different r,g,b values provided by the eyelink host palette.
        When building up each eye image frame, eyelink sends the palette
        index for each pixel; so an eyelink eye image frame can be a 2D lookup
        array into this palette.
        """
        self.clear_cal_display()
        sz = len(r)
        self.rgb_pallete = np.zeros((sz, 3), dtype=np.uint8)
        i = 0
        while i < sz:
            self.rgb_pallete[i:] = int(r[i]), int(g[i]), int(b[i])
            i += 1

    def alert_printf(self, msg):
        """
        Prints alert message to psychopy stderr.
        """
        print2err ("eyelink_graphics.alert_printf(): %s" % msg)

###

    def play_beep(self, pylink_sound_index):
        """
        TODO: Plays a sound.
        """
        if pylink_sound_index == pylink.CAL_TARG_BEEP:
            pass
        elif pylink_sound_index == pylink.CAL_ERR_BEEP or pylink_sound_index == pylink.DC_ERR_BEEP:
            self.textmsg.draw("Calibration Failed or Incomplete.")
            self.window.flip()
        elif pylink_sound_index == pylink.CAL_GOOD_BEEP:
            if self.state == "calibration":
                self.textmsg.draw("Calibration Passed.")
                self.window.flip()
            elif self.state == "validation":
                self.textmsg.draw("Validation Passed.")
                self.window.flip()
        else:
            pass

    def draw_line(self, x1, y1, x2, y2, color_index):
        """ TODO """
        pass

    def draw_lozenge(self, x, y, width, height, color_index):
        """ TODO """
        pass

    def record_abort_hide(self):
        """ TODO """
        pass

    def get_mouse_state(self):
        """ TODO """
        pass
############# From Pyglet Custom Graphics #####################################
#
## NOT YET CONVERTED
#
#
#
###############################################################################
#
#
#   pyglet impl.
#    def get_mouse_state(self):
#        #print2err('get_mouse_state entered')
#        if len(self.pos) > 0 :
#            l = (int)(self.width*0.5-self.width*0.5*0.75)
#            r = (int)(self.width*0.5+self.width*0.5*0.75)
#            b = (int)(self.height*0.5-self.height*0.5*0.75)
#            t = (int)(self.height*0.5+self.height*0.5*0.75)
#
#            mx, my = 0,0
#            if self.pos[0]<l:
#                mx = l
#            elif self.pos[0] >r:
#                mx = r
#            else:
#                mx = self.pos[0]
#
#            if self.pos[1]<b:
#                my = b
#            elif self.pos[1]>t:
#                my = t
#            else:
#                my = self.pos[1]
#
#            mx = (int)((mx-l)*self.img_size[0]//(r-l))
#            my = self.img_size[1] - (int)((my-b)*self.img_size[1]//(t-b))
#            #ioHub.print2err('get_mouse_state exiting')
#            return ((mx, my),self.state)
#        else:
#            #ioHub.print2err('get_mouse_state exiting')
#            return((0,0), 0)
#
#
#
#   PYGLET Imp.
#    def draw_image_line(self, width, line, totlines,buff):
#        pass
#        ioHub.print2err('draw_image_line entered')
#        i =0
#        while i <width:
#            if buff[i]>=len(self.pal):
#                buff[i]=len(self.pal)-1
#            self.imagebuffer.append(self.pal[buff[i]&0x000000FF])
#            i = i+1
#        if line == totlines:
#            #asp = ((float)(self.size[1]))/((float)(self.size[0]))
#            asp = 1
#            r = (float)(self.width*0.5-self.width*0.5*0.75)
#            l = (float)(self.width*0.5+self.width*0.5*0.75)
#            t = (float)(self.height*0.5+self.height*0.5*asp*0.75)
#            b = (float)(self.height*0.5-self.height*0.5*asp*0.75)
#
#            self.window.clearBuffer()
#            
#            tx = (int)(self.width*0.5)
#            ty = b - 30
#            self.stim.drawStim('imageTitle',{'setPos':(tx,ty)})            
#
#            self.draw_cross_hair()
#            glEnable(GL_TEXTURE_RECTANGLE_ARB)
#            glBindTexture(GL_TEXTURE_RECTANGLE_ARB, self.texid.value)
#            glTexParameteri(GL_TEXTURE_RECTANGLE_ARB, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
#            glTexParameteri(GL_TEXTURE_RECTANGLE_ARB, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
#            glTexEnvi( GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE, GL_REPLACE )
#            glTexImage2D( GL_TEXTURE_RECTANGLE_ARB, 0,GL_RGBA8, width, totlines, 0, GL_RGBA, GL_UNSIGNED_BYTE, self.imagebuffer.tostring())
#
#            glBegin(GL_QUADS)
#            glTexCoord2i(0, 0)
#            glVertex2f(r,t)
#            glTexCoord2i(0, self.img_size[1])
#            glVertex2f(r, b)
#            glTexCoord2i(self.img_size[0],self.img_size[1])
#            glVertex2f(l, b)
#            glTexCoord2i(self.img_size[1],0)
#            glVertex2f(l, t)
#            glEnd()
#            glDisable(GL_TEXTURE_RECTANGLE_ARB)
#            self.draw_cross_hair()
#
#            self.window.flip(clearBuffer=True)
#            
#            self.imagebuffer = array.array('I')
#        ioHub.print2err('draw_image_line exiting')
###############################################################################
#
#   Pyglet impl.
#    def draw_line(self,x1,y1,x2,y2,colorindex):
#        pass
#    
#        ioHub.print2err('draw_line entered')
#        if colorindex   ==  pylink.CR_HAIR_COLOR:          color = (1.0,1.0,1.0,1.0)
#        elif colorindex ==  pylink.PUPIL_HAIR_COLOR:       color = (1.0,1.0,1.0,1.0)
#        elif colorindex ==  pylink.PUPIL_BOX_COLOR:        color = (0.0,1.0,0.0,1.0)
#        elif colorindex ==  pylink.SEARCH_LIMIT_BOX_COLOR: color = (1.0,0.0,0.0,1.0)
#        elif colorindex ==  pylink.MOUSE_CURSOR_COLOR:     color = (1.0,0.0,0.0,1.0)
#        else: color =(0.0,0.0,0.0,0.0)
#
#        #asp = ((float)(self.size[1]))/((float)(self.size[0]))
#        asp = 1
#        r = (float)(self.width*0.5-self.width*0.5*0.75)
#        l = (float)(self.width*0.5+self.width*0.5*0.75)
#        t = (float)(self.height*0.5+self.height*0.5*asp*0.75)
#        b = (float)(self.height*0.5-self.height*0.5*asp*0.75)
#
#        x11= float(float(x1)*(l-r)/float(self.img_size[0]) + r)
#        x22= float(float(x2)*(l-r)/float(self.img_size[0]) + r)
#        y11= float(float(y1)*(b-t)/float(self.img_size[1]) + t)
#        y22= float(float(y2)*(b-t)/float(self.img_size[1]) + t)
#
##        glBegin(GL_LINES)
##        glColor4f(color[0],color[1],color[2],color[3] )
##        glVertex2f(x11,y11)
##        glVertex2f(x22,y22)
##        glEnd()
#        ioHub.print2err('draw_line exiting')
#
###############################################################################
#
#   Pyglet Implementation
#    def draw_lozenge(self,x,y,width,height,colorindex):
#        pass
#        ioHub.print2err('draw_lozenge entered')
#        if colorindex   ==  pylink.CR_HAIR_COLOR:          color = (1.0,1.0,1.0,1.0)
#        elif colorindex ==  pylink.PUPIL_HAIR_COLOR:       color = (1.0,1.0,1.0,1.0)
#        elif colorindex ==  pylink.PUPIL_BOX_COLOR:        color = (0.0,1.0,0.0,1.0)
#        elif colorindex ==  pylink.SEARCH_LIMIT_BOX_COLOR: color = (1.0,0.0,0.0,1.0)
#        elif colorindex ==  pylink.MOUSE_CURSOR_COLOR:     color = (1.0,0.0,0.0,1.0)
#        else: color =(0.0,0.0,0.0,0.0)
#
#        width=int((float(width)/float(self.img_size[0]))*self.img_size[0])
#        height=int((float(height)/float(self.img_size[1]))*self.img_size[1])
#
#        #asp = ((float)(self.size[1]))/((float)(self.size[0]))
#        asp = 1
#        r = (float)(self.width*0.5-self.width*0.5*0.75)
#        l = (float)(self.width*0.5+self.width*0.5*0.75)
#        t = (float)(self.height*0.5+self.height*0.5*asp*0.75)
#        b = (float)(self.height*0.5-self.height*0.5*asp*0.75)
#
#        x11= float(float(x)*(l-r)/float(self.img_size[0]) + r)
#        x22= float(float(x+width)*(l-r)/float(self.img_size[0]) + r)
#        y11= float(float(y)*(b-t)/float(self.img_size[1]) + t)
#        y22= float(float(y+height)*(b-t)/float(self.img_size[1]) + t)
#
#        r=x11
#        l=x22
#        b=y11
#        t=y22
#
#        #glColor4f(color[0],color[1],color[2],color[3])
#
#        xw = math.fabs(float(l-r))
#        yw = math.fabs(float(b-t))
#        sh = min(xw,yw)
#        rad = float(sh*0.5)
#
#        x = float(min(l,r)+rad)
#        y = float(min(t,b)+rad)
#
#        if xw==sh:
#            st = 180
#        else:
#            st = 90
#        glBegin(GL_LINE_LOOP)
#        i=st
#        degInRad = (float)(float(i)*(3.14159/180.0))
#
#        for i in range (st, st+180):
#            degInRad = (float)(float(i)*(3.14159/180.0))
#            glVertex2f((float)(float(x)+math.cos(degInRad)*rad),float(y)+(float)(math.sin(degInRad)*rad))
#
#        if xw == sh:    #short horizontally
#            y = (float)(max(t,b)-rad)
#        else:  		  # short vertically
#            x = (float)(max(l,r)-rad)
#
#        i = st+180
#        for i in range (st+180, st+360):
#            degInRad = (float)(float(i)*(3.14159/180.0))
#            glVertex2f((float)(float(x)+math.cos(degInRad)*rad),float(y)+(float)(math.sin(degInRad)*rad))
#
#        glEnd()
#        ioHub.print2err('draw_lozenge exiting')
