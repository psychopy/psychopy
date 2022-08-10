# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).


from psychopy import visual
import gevent
from psychopy.iohub.util import convertCamelToSnake, updateSettings, createCustomCalibrationStim
from psychopy.iohub.devices import DeviceEvent, Computer
from psychopy.iohub.constants import EventConstants as EC
from psychopy.iohub.devices.keyboard import KeyboardInputEvent
from psychopy.iohub.errors import print2err
from psychopy.constants import PLAYING

currentTime = Computer.getTime

target_position_count = dict(THREE_POINTS=3,
                             FIVE_POINTS=5,
                             NINE_POINTS=9,
                             THIRTEEN_POINTS=13)
target_positions = dict()
target_positions[3] = [(0.5, 0.1), (0.1, 0.9), (0.9, 0.9)]
target_positions[5] = [(0.5, 0.5), (0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
target_positions[9] = [(0.5, 0.5), (0.1, 0.5), (0.9, 0.5), (0.1, 0.1), (0.5, 0.1),
                       (0.9, 0.1), (0.9, 0.9), (0.5, 0.9), (0.1, 0.9)]
target_positions[13] = [(0.5, 0.5), (0.1, 0.5), (0.9, 0.5), (0.1, 0.1), (0.5, 0.1),
                        (0.9, 0.1), (0.9, 0.9), (0.5, 0.9), (0.1, 0.9), (0.25, 0.25),
                        (0.25, 0.75), (0.75, 0.75), (0.75, 0.25)]


class BaseCalibrationProcedure:
    IOHUB_HEARTBEAT_INTERVAL = 0.050
    CALIBRATION_POINT_LIST = target_positions[9]

    _keyboard_key_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key')

    def __init__(self, eyetrackerInterface, calibration_args, allow_escape_in_progress=True):
        self._eyetracker = eyetrackerInterface
        self.allow_escape = allow_escape_in_progress
        self.screenSize = eyetrackerInterface._display_device.getPixelResolution()
        self.width = self.screenSize[0]
        self.height = self.screenSize[1]
        self._ioKeyboard = None
        self._msg_queue = []
        self._lastCalibrationOK = False
        self._device_config = self._eyetracker.getConfiguration()
        display = self._eyetracker._display_device
        updateSettings(self._device_config.get('calibration'), calibration_args)
        self._calibration_args = self._device_config.get('calibration')
        unit_type = self.getCalibSetting('unit_type')
        if unit_type is None:
            unit_type = display.getCoordinateType()
            self._calibration_args['unit_type'] = unit_type
        color_type = self.getCalibSetting('color_type')
        if color_type is None:
            color_type = display.getColorSpace()
            self._calibration_args['color_type'] = color_type


        cal_type = self.getCalibSetting('type')

        if cal_type in target_position_count:
            num_points = target_position_count[cal_type]
            BaseCalibrationProcedure.CALIBRATION_POINT_LIST = target_positions[num_points]

        self.cal_target_list = self.CALIBRATION_POINT_LIST

        self.window = visual.Window(
            self.screenSize,
            monitor=display.getPsychopyMonitorName(),
            units=unit_type,
            fullscr=True,
            allowGUI=False,
            screen=display.getIndex(),
            color=self.getCalibSetting(['screen_background_color']),
            colorSpace=color_type)
        self.window.setMouseVisible(False)
        self.window.flip(clearBuffer=True)

        self.createGraphics()
        self._registerEventMonitors()
        self._lastMsgPumpTime = currentTime()

        self.clearAllEventBuffers()

    def getCalibSetting(self, setting):
        if isinstance(setting, str):
            setting = [setting, ]
        calibration_args = self._calibration_args
        if setting:
            for s in setting[:-1]:
                calibration_args = calibration_args.get(s)
            return calibration_args.get(setting[-1])

    def clearAllEventBuffers(self):
        self._eyetracker._iohub_server.eventBuffer.clear()
        for d in self._eyetracker._iohub_server.devices:
            d.clearEvents()

    def _registerEventMonitors(self):
        kbDevice = None
        if self._eyetracker._iohub_server:
            for dev in self._eyetracker._iohub_server.devices:
                if dev.__class__.__name__ == 'Keyboard':
                    kbDevice = dev

        if kbDevice:
            eventIDs = []
            for event_class_name in kbDevice.__class__.EVENT_CLASS_NAMES:
                eventIDs.append(getattr(EC, convertCamelToSnake(event_class_name[:-5], False)))

            self._ioKeyboard = kbDevice
            self._ioKeyboard._addEventListener(self, eventIDs)
        else:
            print2err('Warning: %s could not connect to Keyboard device for events.' % self.__class__.__name__)

    def _unregisterEventMonitors(self):
        if self._ioKeyboard:
            self._ioKeyboard._removeEventListener(self)

    def _handleEvent(self, event):
        event_type_index = DeviceEvent.EVENT_TYPE_ID_INDEX
        if event[event_type_index] == EC.KEYBOARD_RELEASE:
            ek = event[self._keyboard_key_index]
            if isinstance(ek, bytes):
                ek = ek.decode('utf-8')
            if ek == ' ' or ek == 'space':
                self._msg_queue.append('SPACE_KEY_ACTION')
                self.clearAllEventBuffers()
            elif ek == 'escape':
                self._msg_queue.append('QUIT')
                self.clearAllEventBuffers()

    def MsgPump(self):
        # keep the psychopy window happy ;)
        if currentTime() - self._lastMsgPumpTime > self.IOHUB_HEARTBEAT_INTERVAL:
            # try to keep ioHub from being blocked. ;(
            if self._eyetracker._iohub_server:
                for dm in self._eyetracker._iohub_server.deviceMonitors:
                    dm.device._poll()
                self._eyetracker._iohub_server.processDeviceEvents()
            self._lastMsgPumpTime = currentTime()

    def getNextMsg(self):
        if len(self._msg_queue) > 0:
            msg = self._msg_queue[0]
            self._msg_queue = self._msg_queue[1:]
            return msg

    def createGraphics(self):
        """
        """
        color_type = self.getCalibSetting('color_type')
        unit_type = self.getCalibSetting('unit_type')

        def setDefaultCalibrationTarget():
            self.targetStim = visual.TargetStim(
                self.window, name="CP", style="circles",
                radius=self.getCalibSetting(['target_attributes', 'outer_diameter']) / 2.0,
                fillColor=self.getCalibSetting(['target_attributes', 'outer_fill_color']),
                borderColor=self.getCalibSetting(['target_attributes', 'outer_line_color']),
                lineWidth=self.getCalibSetting(['target_attributes', 'outer_stroke_width']),
                innerRadius=self.getCalibSetting(['target_attributes', 'inner_diameter']) / 2.0,
                innerFillColor=self.getCalibSetting(['target_attributes', 'inner_fill_color']),
                innerBorderColor=self.getCalibSetting(['target_attributes', 'inner_line_color']),
                innerLineWidth=self.getCalibSetting(['target_attributes', 'inner_stroke_width']),
                pos=(0, 0),
                units=unit_type,
                colorSpace=color_type,
                autoLog=False
            )

        if self._calibration_args.get('target_type') == 'CIRCLE_TARGET':
            setDefaultCalibrationTarget()
        else:
            self.targetStim = createCustomCalibrationStim(self.window, self._calibration_args)
            if self.targetStim is None:
                # Error creating custom stim, so use default target stim type
                setDefaultCalibrationTarget()

        self.originalTargetSize = self.targetStim.size
        self.targetClassHasPlayPause = hasattr(self.targetStim, 'play') and hasattr(self.targetStim, 'pause')

        self.imagetitlestim = None

        tctype = color_type
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
            tctype = 'rgb255'

        instuction_text = 'Press SPACE to Start Calibration; ESCAPE to Exit.'
        self.textLineStim = visual.TextStim(self.window, text=instuction_text,
                                            pos=(0, 0), height=36,
                                            color=tcolor, colorSpace=tctype,
                                            units='pix', wrapWidth=self.width * 0.9)

    def startCalibrationHook(self):
        pass

    def registerCalibrationPointHook(self, pt):
        pass

    def finishCalibrationHook(self, aborted=False):
        pass

    def runCalibration(self):
        """Run calibration sequence
        """

        if self.showIntroScreen() is False:
            # User pressed escape  to exit calibration
            return False

        target_delay = self.getCalibSetting('target_delay')
        target_duration = self.getCalibSetting('target_duration')
        auto_pace = self.getCalibSetting('auto_pace')
        randomize_points = self.getCalibSetting('randomize')
        if randomize_points is True:
            # Randomize all but first target position.
            self.cal_target_list = self.CALIBRATION_POINT_LIST[1:]
            import random
            random.seed(None)
            random.shuffle(self.cal_target_list)
            self.cal_target_list.insert(0, self.CALIBRATION_POINT_LIST[0])

        left, top, right, bottom = self._eyetracker._display_device.getCoordBounds()
        w, h = right - left, top - bottom

        self.clearCalibrationWindow()

        self.startCalibrationHook()

        i = 0
        abort_calibration = False
        for pt in self.cal_target_list:
            if abort_calibration:
                break
            # Convert normalized positions to psychopy window unit positions
            # by using iohub display/window getCoordBounds.
            x, y = left + w * pt[0], bottom + h * (1.0 - pt[1])
            start_time = currentTime()

            self.clearAllEventBuffers()

            # Target animate / delay
            animate_enable = self.getCalibSetting(['target_attributes', 'animate', 'enable'])
            animate_expansion_ratio = self.getCalibSetting(['target_attributes', 'animate', 'expansion_ratio'])
            animate_contract_only = self.getCalibSetting(['target_attributes', 'animate', 'contract_only'])

            while currentTime()-start_time <= target_delay:
                if animate_enable and i > 0:
                    t = (currentTime()-start_time) / target_delay
                    v1 = self.cal_target_list[i-1]
                    v2 = pt
                    t = 60.0 * ((1.0 / 10.0) * t ** 5 - (1.0 / 4.0) * t ** 4 + (1.0 / 6.0) * t ** 3)
                    mx, my = ((1.0 - t) * v1[0] + t * v2[0], (1.0 - t) * v1[1] + t * v2[1])
                    moveTo = left + w * mx, bottom + h * (1.0 - my)
                    self.drawCalibrationTarget(moveTo)
                elif animate_enable is False:
                    if self.targetClassHasPlayPause and self.targetStim.status == PLAYING:
                        self.targetStim.pause()
                    self.window.flip(clearBuffer=True)

            gevent.sleep(0.001)
            self.MsgPump()
            msg = self.getNextMsg()
            if self.allow_escape and msg == 'QUIT':
                abort_calibration = True
                break

            # Target expand / contract phase on done if target is a visual.TargetStim class
            self.resetTargetProperties()
            if self.targetClassHasPlayPause and self.targetStim.status != PLAYING:
                self.targetStim.play()
            self.drawCalibrationTarget((x, y))

            start_time = currentTime()
            stim_size = self.targetStim.size[0]
            min_stim_size = self.targetStim.size[0] / animate_expansion_ratio
            if hasattr(self.targetStim, 'minSize'):
                min_stim_size = self.targetStim.minSize[0]

            while currentTime()-start_time <= target_duration:
                elapsed_time = currentTime()-start_time
                new_size = t = None
                if animate_contract_only:
                    # Change target size from outer diameter to inner diameter over target_duration seconds.
                    t = elapsed_time / target_duration
                    new_size = stim_size - t * (stim_size - min_stim_size)
                elif animate_expansion_ratio not in [1, 1.0]:
                    if elapsed_time <= target_duration/2:
                        # In expand phase
                        t = elapsed_time / (target_duration/2)
                        new_size = stim_size + t * (stim_size*animate_expansion_ratio - stim_size)
                    else:
                        # In contract phase
                        t = (elapsed_time-target_duration/2) / (target_duration/2)
                        new_size = stim_size*animate_expansion_ratio - t * (stim_size*animate_expansion_ratio - min_stim_size)
                if new_size:
                    self.targetStim.size = new_size, new_size

                self.targetStim.draw()
                self.window.flip()

            if auto_pace is False:
                while 1:
                    if self.targetClassHasPlayPause and self.targetStim.status == PLAYING:
                        self.targetStim.draw()
                        self.window.flip()
                    gevent.sleep(0.001)
                    self.MsgPump()
                    msg = self.getNextMsg()
                    if msg == 'SPACE_KEY_ACTION':
                        break
                    elif self.allow_escape and msg == 'QUIT':
                        abort_calibration = True
                        break

            gevent.sleep(0.001)
            self.MsgPump()
            msg = self.getNextMsg()
            while msg:
                if self.allow_escape and msg == 'QUIT':
                    abort_calibration = True
                    break
                gevent.sleep(0.001)
                self.MsgPump()
                msg = self.getNextMsg()

            self.registerCalibrationPointHook(pt)

            self.clearCalibrationWindow()
            self.clearAllEventBuffers()
            i += 1

        if self.targetClassHasPlayPause:
            self.targetStim.pause()

        self.finishCalibrationHook(abort_calibration)

        if abort_calibration is False:
            self.showFinishedScreen()

        return not abort_calibration

    def clearCalibrationWindow(self):
        self.window.flip(clearBuffer=True)

    def showIntroScreen(self, text_msg='Press SPACE to Start Calibration; ESCAPE to Exit.'):

        self.clearAllEventBuffers()

        while True:
            self.textLineStim.setText(text_msg)
            self.textLineStim.draw()
            self.window.flip()

            msg = self.getNextMsg()
            if msg == 'SPACE_KEY_ACTION':
                self.clearAllEventBuffers()
                return True
            elif msg == 'QUIT':
                self.clearAllEventBuffers()
                return False
            self.MsgPump()
            gevent.sleep(0.001)

    def showFinishedScreen(self, text_msg="Calibration Complete. Press 'SPACE' key to continue."):

        self.clearAllEventBuffers()

        while True:
            self.textLineStim.setText(text_msg)
            self.textLineStim.draw()
            self.window.flip()

            msg = self.getNextMsg()
            if msg in ['SPACE_KEY_ACTION', 'QUIT']:
                self.clearAllEventBuffers()
                return True

            self.MsgPump()
            gevent.sleep(0.001)


    def resetTargetProperties(self):
        self.targetStim.size = self.originalTargetSize

    def drawCalibrationTarget(self, tp):
        self.targetStim.setPos(tp)
        self.targetStim.draw()
        return self.window.flip(clearBuffer=True)
