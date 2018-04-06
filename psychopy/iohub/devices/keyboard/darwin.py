# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from copy import copy
import Quartz as Qz
from AppKit import NSEvent  # NSKeyUp, NSSystemDefined, NSEvent
from . import ioHubKeyboardDevice
from ...constants import KeyboardConstants, DeviceConstants, EventConstants
from .. import Computer, Device

#>>>>>>>>>>>>>>>>>>>>>>>>

import ctypes
import ctypes.util
import CoreFoundation
import objc
from ...errors import print2err, printExceptionDetailsToStdErr

try:
    unichr
except NameError:
    unichr = chr

import unicodedata

from .darwinkey import code2label

#print2err("code2label: ",code2label)
carbon_path = ctypes.util.find_library('Carbon')
carbon = ctypes.cdll.LoadLibrary(carbon_path)

_objc = ctypes.PyDLL(objc._objc.__file__)
_objc.PyObjCObject_New.restype = ctypes.py_object
_objc.PyObjCObject_New.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]


def objcify(ptr):
    return _objc.PyObjCObject_New(ptr, 0, 1)

kTISPropertyUnicodeKeyLayoutData_p = ctypes.c_void_p.in_dll(
    carbon, 'kTISPropertyUnicodeKeyLayoutData')
kTISPropertyUnicodeKeyLayoutData = objcify(kTISPropertyUnicodeKeyLayoutData_p)

carbon.TISCopyCurrentKeyboardInputSource.argtypes = []
carbon.TISCopyCurrentKeyboardInputSource.restype = ctypes.c_void_p
carbon.TISGetInputSourceProperty.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
carbon.TISGetInputSourceProperty.restype = ctypes.c_void_p
carbon.LMGetKbdType.argtypes = []
carbon.LMGetKbdType.restype = ctypes.c_uint32
OptionBits = ctypes.c_uint32
UniCharCount = ctypes.c_uint8
UniChar = ctypes.c_uint16
UniChar4 = UniChar * 4

carbon.UCKeyTranslate.argtypes = [ctypes.c_void_p,  # keyLayoutPtr
                                  ctypes.c_uint16,  # virtualKeyCode
                                  ctypes.c_uint16,  # keyAction
                                  ctypes.c_uint32,  # modifierKeyState
                                  ctypes.c_uint32,  # keyboardType
                                  OptionBits,      # keyTranslateOptions
                                  ctypes.POINTER(
                                      ctypes.c_uint32),  # deadKeyState
                                  UniCharCount,    # maxStringLength
                                  # actualStringLength
                                  ctypes.POINTER(UniCharCount),
                                  UniChar4]

carbon.UCKeyTranslate.restype = ctypes.c_uint32  # OSStatus
kUCKeyActionDisplay = 3
kUCKeyTranslateNoDeadKeysBit = 0

kTISPropertyUnicodeKeyLayoutData = ctypes.c_void_p.in_dll(
    carbon, 'kTISPropertyUnicodeKeyLayoutData')

#<<<<<<<<<<<<<<<<<<<<<<<<
from unicodedata import category as ucategory

getTime = Computer.getTime

eventHasModifiers = lambda v: Qz.kCGEventFlagMaskNonCoalesced - v != 0
keyFromNumpad = lambda v: Qz.kCGEventFlagMaskNumericPad & v == Qz.kCGEventFlagMaskNumericPad
caplocksEnabled = lambda v: Qz.kCGEventFlagMaskAlphaShift & v == Qz.kCGEventFlagMaskAlphaShift
shiftModifierActive = lambda v: Qz.kCGEventFlagMaskShift & v == Qz.kCGEventFlagMaskShift
altModifierActive = lambda v: Qz.kCGEventFlagMaskAlternate & v == Qz.kCGEventFlagMaskAlternate
controlModifierActive = lambda v: Qz.kCGEventFlagMaskControl & v == Qz.kCGEventFlagMaskControl
fnModifierActive = lambda v: Qz.kCGEventFlagMaskSecondaryFn & v == Qz.kCGEventFlagMaskSecondaryFn

modifier_name_mappings = dict(
    lctrl='lctrl',
    rctrl='rctrl',
    lshift='lshift',
    rshift='rshift',
    lalt='lalt',
    ralt='lalt',
    lcmd='lcmd',
    rcmd='lcmd',
    capslock='capslock',
    # MOD_SHIFT=512,
    # MOD_ALT=1024,
    # MOD_CTRL=2048,
    # MOD_CMD=4096,
    numlock='numlock',
    function='function',
    modhelp='modhelp')


class Keyboard(ioHubKeyboardDevice):
    _last_mod_names = []
    _OS_MODIFIERS = ([(0x00001, 'lctrl'), (0x02000, 'rctrl'),
                      (0x00002, 'lshift'), (0x00004, 'rshift'),
                      (0x00020, 'lalt'), (0x00040, 'ralt'),
                      (0x000008, 'lcmd'), (0x000010, 'rcmd'),
                      (Qz.kCGEventFlagMaskAlphaShift, 'capslock'),
                      (Qz.kCGEventFlagMaskSecondaryFn, 'function'),
                      (Qz.kCGEventFlagMaskHelp, 'modhelp')])        # 0x400000

    DEVICE_TIME_TO_SECONDS = 0.000000001

    _EVENT_TEMPLATE_LIST = [0,  # experiment id
                            0,  # session id
                            0,  # device id (not currently used)
                            0,  # Device._getNextEventID(),
                            0,  # ioHub Event type
                            0.0,  # event device time,
                            0.0,  # event logged_time,
                            0.0,  # event iohub Time,
                            0.0,  # confidence_interval,
                            0.0,  # delay,
                            0,  # filtered by ID (always 0 right now)
                            0,  # auto repeat count
                            0,  # ScanCode
                            0,  # KeyID
                            0,  # ucode
                            u'',  # key
                            None,  # mods
                            0,  # win num
                            u'',  # char
                            0.0,  # duration
                            0]  # press evt id
    __slots__ = [
        '_loop_source',
        '_tap',
        '_device_loop',
        '_CGEventTapEnable',
        '_loop_mode',
        '_last_general_mod_states',
        '_codedict']

    def __init__(self, *args, **kwargs):
        ioHubKeyboardDevice.__init__(self, *args, **kwargs['dconfig'])

        # TODO: This dict should be reset whenever monitoring is turned off for the device OR
        # whenever events are cleared fpr the device.
        # Same to do for the _active_modifiers bool lookup array
        self._last_general_mod_states = dict(
            shift_on=False, alt_on=False, cmd_on=False, ctrl_on=False)

        #self._codedict = {self._createStringForKey(code,0): code for code in range(128)}

        self._loop_source = None
        self._tap = None
        self._device_loop = None
        self._loop_mode = None

        self._tap = Qz.CGEventTapCreate(
            Qz.kCGSessionEventTap,
            Qz.kCGHeadInsertEventTap,
            Qz.kCGEventTapOptionDefault,
            Qz.CGEventMaskBit(Qz.kCGEventKeyDown) |
            Qz.CGEventMaskBit(Qz.kCGEventKeyUp) |
            Qz.CGEventMaskBit(Qz.kCGEventFlagsChanged),
            self._nativeEventCallback,
            None)

        self._CGEventTapEnable = Qz.CGEventTapEnable
        self._loop_source = Qz.CFMachPortCreateRunLoopSource(
            None, self._tap, 0)

        self._device_loop = Qz.CFRunLoopGetCurrent()

        self._loop_mode = Qz.kCFRunLoopDefaultMode

        Qz.CFRunLoopAddSource(
            self._device_loop,
            self._loop_source,
            self._loop_mode)

    def _createStringForKey(self, keycode, modifier_state):
        keyboard_p = carbon.TISCopyCurrentKeyboardInputSource()
        keyboard = objcify(keyboard_p)
        layout_p = carbon.TISGetInputSourceProperty(
            keyboard_p, kTISPropertyUnicodeKeyLayoutData)
        layout = objcify(layout_p)
        layoutbytes = layout.bytes()
        if hasattr(layoutbytes, 'tobytes'):
            layoutbytes_vp = layoutbytes.tobytes()
        else:
            layoutbytes_vp = memoryview(bytearray(layoutbytes)).tobytes()
        keysdown = ctypes.c_uint32()
        length = UniCharCount()
        chars = UniChar4()
        retval = carbon.UCKeyTranslate(layoutbytes_vp,
                                       keycode,
                                       kUCKeyActionDisplay,
                                       modifier_state,
                                       carbon.LMGetKbdType(),
                                       kUCKeyTranslateNoDeadKeysBit,
                                       ctypes.byref(keysdown),
                                       4,
                                       ctypes.byref(length),
                                       chars)
        s = u''.join(unichr(chars[i]) for i in range(length.value))
        CoreFoundation.CFRelease(keyboard)
        return s

    # def _keyCodeForChar(self, c):
    #    return self._codedict[c]

    def _poll(self):
        self._last_poll_time = getTime()
        while Qz.CFRunLoopRunInMode(
                self._loop_mode,
                0.0,
                True) == Qz.kCFRunLoopRunHandledSource:
            pass

    def _nativeEventCallback(self, *args):
        event = None
        try:
            proxy, etype, event, refcon = args

            if self.isReportingEvents():
                logged_time = getTime()

                if etype == Qz.kCGEventTapDisabledByTimeout:
                    print2err(
                        '** WARNING: Keyboard Tap Disabled due to timeout. Re-enabling....: ', etype)
                    Qz.CGEventTapEnable(self._tap, True)
                    return event

                confidence_interval = logged_time - self._last_poll_time
                delay = 0.0
                iohub_time = logged_time - delay
                char_value = None
                key_value = None
                ioe_type = None
                device_time = Qz.CGEventGetTimestamp(
                    event) * self.DEVICE_TIME_TO_SECONDS
                key_code = Qz.CGEventGetIntegerValueField(
                    event, Qz.kCGKeyboardEventKeycode)

                # Check Auto repeats
                if etype == Qz.kCGEventKeyDown and self._report_auto_repeats is False and self._key_states.get(
                        key_code, None):
                    return event

                nsEvent = NSEvent.eventWithCGEvent_(event)
                # should NSFunctionKeyMask, NSNumericPadKeyMask be used??

                window_number = nsEvent.windowNumber()

                if etype in [
                        Qz.kCGEventKeyDown,
                        Qz.kCGEventKeyUp,
                        Qz.kCGEventFlagsChanged]:
                    key_mods = Qz.CGEventGetFlags(event)
                    ioHubKeyboardDevice._modifier_value, mod_names = self._checkForLeftRightModifiers(
                        key_mods)

                    if fnModifierActive(key_mods) and keyFromNumpad(key_mods):
                        # Atleast on mac mini wireless kb, arrow keys have
                        # fnModifierActive at all times, even when fn key is not pressed.
                        # When fn key 'is' pressed, and arrow key is pressed,
                        # then keyFromNumpad becomes false.
                        mod_names.remove('function')
                        ioHubKeyboardDevice._modifier_value -= KeyboardConstants._modifierCodes.getID(
                            'function')

                    if etype != Qz.kCGEventFlagsChanged:
                        char_value = nsEvent.characters()
                        if etype == Qz.kCGEventKeyUp:
                            ioe_type = EventConstants.KEYBOARD_RELEASE
                        elif etype == Qz.kCGEventKeyDown:
                            ioe_type = EventConstants.KEYBOARD_PRESS
                    else:
                        if len(mod_names) > len(self._last_mod_names):
                            ioe_type = EventConstants.KEYBOARD_PRESS
                        else:
                            ioe_type = EventConstants.KEYBOARD_RELEASE
                    Keyboard._last_mod_names = mod_names

                    if char_value is None or fnModifierActive(key_mods):
                        char_value = self._createStringForKey(
                            key_code, key_mods)

                    if len(char_value) != 1 or unicodedata.category(
                            char_value).lower() == 'cc':
                        char_value = ''

                    key_value = self._createStringForKey(key_code, 0)
                    if len(key_value) == 0 or unicodedata.category(
                            key_value).lower() == 'cc':
                        key_value = code2label.get(key_code, '')

                    if key_value == 'tab':
                        char_value = '\t'
                    elif key_value == 'return':
                        char_value = '\n'

                    is_auto_repeat = Qz.CGEventGetIntegerValueField(
                        event, Qz.kCGKeyboardEventAutorepeat)

                    # TODO: CHeck WINDOW BOUNDS

                    # report_system_wide_events=self.getConfiguration().get('report_system_wide_events',True)
                    # Can not seem to figure out how to get window handle id from evt to match with pyget in darwin, so
                    # Comparing event target process ID to the psychopy windows process ID,
                    # yglet_window_hnds=self._iohub_server._pyglet_window_hnds
                    #print2err("pyglet_window_hnds: ",window_number, " , ",pyglet_window_hnds)
                    #targ_proc = Qz.CGEventGetIntegerValueField(event,Qz.kCGEventTargetUnixProcessID)
                    #psych_proc = Computer.psychopy_process.pid
                    # if targ_proc == psych_proc:
                    #    pass
                    # elif report_system_wide_events is False:
                    # For keyboard, when report_system_wide_events is false
                    # do not record kb events that are not targeted for
                    # a PsychoPy window, still allow them to pass to the desktop
                    # apps.
                    #    return event

                if ioe_type:

                    ioe = self._EVENT_TEMPLATE_LIST
                    ioe[3] = Device._getNextEventID()
                    ioe[4] = ioe_type
                    ioe[5] = device_time
                    ioe[6] = logged_time
                    ioe[7] = iohub_time
                    ioe[8] = confidence_interval
                    ioe[9] = delay
                    # index 10 is filter id, not used at this time
                    ioe[11] = is_auto_repeat

                    # Quartz does not give the scancode, so fill this with
                    # keycode
                    ioe[12] = key_code
                    ioe[13] = key_code  # key_code
                    ioe[14] = 0  # unicode number field no longer used.
                    ioe[15] = key_value
                    ioe[16] = ioHubKeyboardDevice._modifier_value
                    ioe[17] = window_number
                    ioe[18] = char_value.encode('utf-8')

                    ioe = copy(ioe)
                    ioHubKeyboardDevice._updateKeyboardEventState(
                        self, ioe, ioe_type == EventConstants.KEYBOARD_PRESS)

                    self._addNativeEventToBuffer(ioe)
                else:
                    print2err('\nWARNING: KEYBOARD RECEIVED A [ {0} ] KB EVENT, BUT COULD NOT GENERATE AN IOHUB EVENT FROM IT !!'.format(
                        etype), ' [', key_name, '] ucode: ', ucode, ' key_code: ', key_code)

                self._last_callback_time = logged_time
            return event
        except Exception:
            printExceptionDetailsToStdErr()
            Qz.CGEventTapEnable(self._tap, False)

        return event

    @classmethod
    def _checkForLeftRightModifiers(cls, mod_state):
        mod_value = 0
        mod_strs = []
        for k, v in cls._OS_MODIFIERS:
            if mod_state & k > 0:
                mod_value += KeyboardConstants._modifierCodes.getID(v)
                mod_strs.append(
                    modifier_name_mappings.get(
                        v, 'MISSING_MOD_NAME'))
        return mod_value, mod_strs

    def _getIOHubEventObject(self, native_event_data):
        return native_event_data

    def _close(self):
        try:
            Qz.CGEventTapEnable(self._tap, False)
        except Exception:
            pass
        try:
            if Qz.CFRunLoopContainsSource(
                    self._device_loop,
                    self._loop_source,
                    self._loop_mode) is True:
                Qz.CFRunLoopRemoveSource(
                    self._device_loop, self._loop_source, self._loop_mode)
        finally:
            self._loop_source = None
            self._tap = None
            self._device_loop = None
            self._loop_mode = None
        ioHubKeyboardDevice._close(self)
