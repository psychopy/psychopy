#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hardware device management.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'deviceManager', 
    'getDeviceManager', 
    'DeviceManager',
    'closeAllDevices'
]

from psychopy.tools import systemtools as st
from serial.tools import list_ports
from psychopy import logging
import atexit


# reference methods by device (e.g. keyboard) and method (e.g. add)
_deviceMethods = {}


class DeviceMethod:
    """
    Decorator which adds the decorated method to _deviceMethods against the given key.

    Parameters
    ----------
    deviceType : str
        What kind of device the decorated method pertains to (e.g. keyboard, microphone, etc.)
    action : str or None
        What kind of action the decorated method does. Values are:
        - "add": Use this method for the given deviceType in `DeviceManager.addDevice`
        - "remove": Use this method for the given deviceType in `DeviceManager.removeDevice`
        - "get": Use this method for the given deviceType in `DeviceManager.getDevice`
        - "getall": Use this method for the given deviceType in `DeviceManager.getDevices`
        - "available": Use this method for the given deviceType in `DeviceManager.getAvailableDevices`
        - None: This method does not correspond to the given deviceType in any DeviceManager method
    """
    def __init__(self, deviceType, action=None):
        self.deviceType = deviceType
        self.action = action

    def __call__(self, fcn):
        # add method to DeviceManager
        setattr(DeviceManager, fcn.__name__, fcn)
        # if device has no mapped methods yet, make dict
        if self.deviceType not in _deviceMethods:
            _deviceMethods[self.deviceType] = {}
        # map function to key (if action is specified)
        if self.action is not None:
            _deviceMethods[self.deviceType][self.action] = fcn
        # return function unchanged
        return fcn


class DeviceManager:
    """Class for managing hardware devices.

    An instance of this class is used to manage various hardware peripherals 
    used by PsychoPy. It can be used to access devices such as microphones, 
    button boxes, and cameras though a common interface. It can also be used to 
    get information about available devices installed on the system, such as 
    their settings and capabilities prior to initializing them.
    
    It is recommended that devices are initialized through the device manager
    rather than directly. The device manager is responsible for keeping track
    of devices and ensuring that they are properly closed when the program
    exits. 

    This class is implemented as a singleton, so there is only one
    instance of it per ssession after its initialized. The instance can be 
    accessed through the global variable `deviceManager` or by calling 
    `getDeviceManager()`.

    DeviceManager can be extended by use of the `@DeviceMethod` decorator. Any
    class method with this decorator is added to DeviceManager on import, allowing
    DeviceManager to gain device management methods from plugins.

    """
    _instance = None  # singleton instance
    _deviceMethods = _deviceMethods  # reference methods by device and action
    ioServer = None  # reference to currently running ioHub ioServer object

    def __new__(cls):
        # when making a new DeviceManager, if an instance already exists, just return it
        # this means that all DeviceManager handles are the same object
        if cls._instance is None:
            cls._instance = super(DeviceManager, cls).__new__(cls)

        return cls._instance

    def __init__(self):
        # initialize a dictionary to store dictionaries of devices for each device class
        self._devices = {devClass: {} for devClass in _deviceMethods}

    # --- utility ---
    def makeUniqueName(self, deviceType):
        i = 0
        name = deviceType + str(i)
        while not self.checkDeviceNameAvailable(name):
            i += 1
            deviceType + str(i)

        return name

    def checkDeviceNameAvailable(self, name):
        """Check if a device name is available.

        Parameters
        ----------
        name : str
            Name of the device.

        Returns
        -------
        bool
            `True` if the device name is available, `False` otherwise. If `False`
            is returned, the device name cannot be used when adding another
            device.

        """
        for devClass in self._devices:
            if name in self._devices[devClass]:
                return False

        return True

    def _assertDeviceNameUnique(self, name):
        """Assert that the specified device name is unique.

        This checks if the device name specified is unique and not used by any
        of the other devices in the manager.

        Parameters
        ----------
        name : str
            Name of the device to check.

        Raises
        ------
        ValueError
            If the device name is not unique.

        """
        # check if there are any keys in the dictionaries inside of
        # `self._devices` that match the name
        if not self.checkDeviceNameAvailable(name):
            raise ValueError(
                f"Device name '{name}' is already in use by another "
                "device!")

    def _getSerialPortsInUse(self):
        """Get serial ports that are being used and the names of the devices
        that are using them.

        This will only work if the devices have a `portString` attribute, which
        requires they inherit from `SerialDevice`.

        Returns
        -------
        dict
            Mapping of serial port names to the names of the devices that are
            using them as a list.

        """
        ports = {}
        for devClass in self._devices:
            for devName, devObj in self._devices[devClass].items():
                if hasattr(devObj, 'portString'):
                    ports.setdefault(devObj.portString, []).append(devName)

        return ports

    def closeAll(self):
        """Close all devices.

        Close all devices that have been initialized. This is usually called on
        exit to free resources cleanly. It is not necessary to call this method
        manually as it is registered as an `atexit` handler.

        The device manager will be reset after this method is called.

        """
        devClasses = list(self._devices.keys())
        for devClass in devClasses:
            for devName, devObj in self._devices[devClass].items():
                if hasattr(devObj, 'close'):
                    try:
                        devObj.close()
                    except Exception:
                        logging.error(f"Failed to close {devName}")
                    logging.debug(f"Closed {devClass} device: {devName}")
                else:
                    logging.error(
                        f"Device {devName} does not have a `close()` method!")

            self._devices[devClass].clear()

    # --- generic device management ---

    def addDevice(self, deviceType, *args, name=None, **kwargs):
        """
        Calls the add method for the specified device type

        Parameters
        ----------
        deviceType : str
            Type of device (e.g. keyboard, microphone, etc.)
        args : list
            Whatever arguments would be passed to the linked add method (e.g. backend, name, etc.)
        name : str or None
            Arbitrary name to store device under. If None, will create a new ID for the device.
        kwargs : dict
            Whatever keyword arguments would be passed to the linked add method (e.g. backend, name, etc.)

        Returns
        -------
        BaseDevice
            Device created by the linked add method
        """
        # if no name given, generate unique name
        if name is None:
            name = self.makeUniqueName(deviceType=deviceType)

        return _deviceMethods[deviceType]["add"](self, *args, name=name, **kwargs)

    def removeDevice(self, name):
        """
        Remove the device matching a specified device type and name.

        Parameters
        ----------
        name : str
            Arbitrary name device is stored under.
        """
        # search all types
        deviceType = None
        for devClass in self._devices:
            if name in self._devices[devClass]:
                deviceType = devClass
                break

        if deviceType in _deviceMethods and "remove" in _deviceMethods[deviceType]:
            # if device type has special remove method, use it
            _deviceMethods[deviceType]["remove"](self, name=name)
        else:
            # otherwise just delete the handle
            del self._devices[deviceType][name]

    def getDevice(self, name):
        """
        Get the device matching a specified device type and name.

        Parameters
        ----------
        name : str
            Arbitrary name device is stored under.

        Returns
        -------
        BaseDevice
            Matching device handle
        """
        # search all types
        deviceType = None
        for devClass in self._devices:
            if name in self._devices[devClass]:
                deviceType = devClass
                break

        if deviceType in _deviceMethods and "get" in _deviceMethods[deviceType]:
            # if device has special getter, use it
            return _deviceMethods[deviceType]["get"](self, name=name)
        else:
            # otherwise just return from dict
            return self._devices[deviceType].get(name, None)

    def getDevices(self, deviceType="*"):
        """
        Get all devices of a given type which have been `add`ed to this DeviceManager

        Parameters
        ----------
        deviceType : str
            Type of device (e.g. keyboard, microphone, etc.), use * for any device type
        """
        if deviceType == "*":
            return self._devices
        return _deviceMethods[deviceType]["getall"](self)

    def getAvailableDevices(self, deviceType="*"):
        """
        Get all devices of a given type which are known by the operating system.

        Parameters
        ----------
        deviceType : str
            Type of device (e.g. keyboard, microphone, etc.), use * for any device type
        """
        if deviceType == "*":
            return st.getInstalledDevices()
        return _deviceMethods[deviceType]["available"]()


class KeyboardPlugin(DeviceManager):
    """
    Plugin class for DeviceManager, adding device methods for Keyboard devices via the DeviceMethod decorator.
    """

    @DeviceMethod("keyboard", "add")
    def addKeyboard(self, name=None, device=-1, bufferSize=10000, waitForStart=False, clock=None, backend=None):
        """
        Add a keyboard.

        Parameters
        ----------
        name : str or None
            Arbitrary name to refer to this keyboard by. Use None to generate a unique name.
        backend : str, optional
            Backend to use for keyboard input. Defaults to "iohub".
        device : int, optional
            Device number to use. Defaults to -1.
        bufferSize: int
            How many keys to store in the buffer (before dropping older ones)
        waitForStart: bool (default False)
            Normally we'll start polling the Keyboard at all times but you
            could choose not to do that and start/stop manually instead by
            setting this to True
        clock : psychopy.core.Clock
            Clock from which to add timestamps to KeyPress objects.

        Returns
        -------
        psychopy.hardware.keyboard.KeyboardDevice
            KeyboardDevice object.

        Examples
        --------
        Add a keyboard::

            import psychopy.hardware.manager as hm
            mgr = hm.getDeviceManager()
            mgr.addKeyboard('response_keyboard', backend='iohub', device=-1)
        
        Get the keyboard and use it to get a response::

            kb = mgr.getKeyboard('response_keyboard')
            kb.getKeys()

        """
        # if no name given, generate unique name
        if name is None:
            name = self.makeUniqueName(deviceType="keyboard")
        self._assertDeviceNameUnique(name)

        # check if the device id is alread in use
        for kb in self._devices['keyboard']:
            if kb.device == device:
                raise ValueError(
                    f"Keyboard device {device} is already in use by {kb.name}")

                # nb - device=-1 is a bit tricky to handle, since it's not
                # a valid device index.
        from psychopy.hardware import keyboard
        toReturn = self._devices['keyboard'][name] = keyboard.KeyboardDevice(
            device=device, bufferSize=bufferSize, waitForStart=waitForStart, clock=clock, backend=backend
        )

        return toReturn

    @DeviceMethod("keyboard", "remove")
    def removeKeyboard(self, name):
        """
        Remove a keyboard.

        Parameters
        ----------
        name : str
            Name of the keyboard.
        """
        del self._devices['keyboard'][name]

    @DeviceMethod("keyboard", "get")
    def getKeyboard(self, name):
        """
        Get a keyboard by name.

        Parameters
        ----------
        name : str
            Arbitrary name given to the keyboard when it was `add`ed.

        Returns
        -------
        BaseDevice
            The requested keyboard
        """
        return self._devices['keyboard'].get(name, None)

    @DeviceMethod("keyboard", "getall")
    def getKeyboards(self):
        """
        Get a mapping of keyboards that have been initialized.

        Returns
        -------
        dict
            Dictionary of keyboards that have been initialized. Where the keys
            are the names of the keyboards and the values are the keyboard
            objects.

        """
        return self._devices['keyboard']

    @DeviceMethod("keyboard", "available")
    def getAvailableKeyboards(self):
        """
        Get information about all available keyboards connected to the system.

        Returns
        -------
        dict
            Dictionary of information about available keyboards connected to
            the system.

        """
        return st.getInstalledDevices('keyboard')


class MousePlugin(DeviceManager):
    """
    Plugin class for DeviceManager, adding device methods for Mouse devices via the DeviceMethod decorator.
    """

    @DeviceMethod("mouse", "add")
    def addMouse(self, name=None, backend='iohub'):
        """
        Add a mouse.

        Parameters
        ----------
        name : str
            Name of the mouse.
        backend : str, optional
            Backend to use for mouse input. Defaults to "iohub".

        Returns
        -------
        Mouse
            Mouse object.

        Examples
        --------
        Add a pointing device to be managed by the device manager::

            import psychopy.hardware.manager as hm
            mgr = hm.getDeviceManager()

            mgr.addMouse('response_mouse')

        Get the mouse and use it to get a response::

            mouse = mgr.getMouse('response_mouse')
            pos = mouse.getPos()

        """
        # if no name given, generate unique name
        if name is None:
            name = self.makeUniqueName(deviceType="mouse")

        # todo - handle the `backend` parameter
        self._assertDeviceNameUnique(name)

        from psychopy.hardware import mouse
        toReturn = self._devices['mouse'][name] = mouse.Mouse()

        return toReturn

    @DeviceMethod("mouse", "remove")
    def removeMouse(self, name):
        """
        Remove a mouse.

        Parameters
        ----------
        name : str
            Name of the mouse.
        """
        del self._devices['mouse'][name]

    @DeviceMethod("mouse", "get")
    def getMouse(self, name):
        """
        Get a mouse by name.

        Parameters
        ----------
        name : str
            Arbitrary name given to the mouse when it was `add`ed.

        Returns
        -------
        BaseDevice
            The requested mouse
        """
        return self._devices['mouse'].get(name, None)

    @DeviceMethod("mouse", "getall")
    def getMice(self):
        """
        Get a mapping of mice that have been initialized.

        Returns
        -------
        dict
            Dictionary of mice that have been initialized. Where the keys
            are the names of the mice and the values are the mouse
            objects.

        """
        return self._devices['mouse']

    @DeviceMethod("mouse", "available")
    def getAvailableMice(self):
        """
        Get information about all available mice connected to the system.

        Returns
        -------
        dict
            Dictionary of information about available mice connected to
            the system.

        """
        return st.getInstalledDevices('mouse')


class SpeakerPlugin(DeviceManager):
    """
    Plugin class for DeviceManager, adding device methods for audio playback devices via the DeviceMethod decorator.
    """

    @DeviceMethod("speaker", "add")
    def addSpeaker(self, name=None, device=0, sampleRate=44100, channels=2):
        """
        Add a speaker.

        Parameters
        ----------
        name : str
            User-defined name of the speaker.
        device : int or str, optional
            Device index or name. Defaults to 0.
        sampleRate : int, optional
            Sample rate in Hz. Defaults to 44100.
        channels : int, optional
            Number of channels. Defaults to 2 for stereo. Use 1 for mono.

        Returns
        -------
        Speaker
            Speaker object.

        """
        # if no name given, generate unique name
        if name is None:
            name = self.makeUniqueName(deviceType="speaker")
        self._assertDeviceNameUnique(name)

        # We need to initialize the audio playback system here, right now that
        # all handled by the `sound` module in a fairly rigid way that can't be 
        # easily done like microphones.
        raise NotImplementedError("Speaker support is a work in progress")

    @DeviceMethod("speaker", "remove")
    def removeSpeaker(self, name):
        """
        Remove a speaker.

        Parameters
        ----------
        name : str
            Name of the speaker.
        """
        del self._devices['speaker'][name]

    @DeviceMethod("speaker", "get")
    def getSpeaker(self, name):
        """
        Get a speaker by name.

        Parameters
        ----------
        name : str
            Arbitrary name given to the speaker when it was `add`ed.

        Returns
        -------
        BaseDevice
            The requested speaker
        """
        return self._devices['speaker'].get(name, None)

    @DeviceMethod("speaker", "getall")
    def getSpeakers(self):
        """
        Get a mapping of audio playback devices that have been initialized.

        Returns
        -------
        dict
            Dictionary of audio playback devices that have been initialized.
            Where the keys are the names of the devices and the values are the
            device objects.

        """
        return self._devices['speaker']

    @DeviceMethod("speaker", "available")
    def getAvailableSpeakers(self):
        """
        Get information about all available speakers connected to the system.

        Returns
        -------
        dict
            Dictionary of information about available speakers connected to
            the system.

        """
        return st.getInstalledDevices('speaker')


class MicrophonePlugin(DeviceManager):
    """
    Plugin class for DeviceManager, adding device methods for audio recording devices via the DeviceMethod decorator.
    """

    @DeviceMethod("microphone", "add")
    def addMicrophone(self, name=None, device=0, sampleRate=44100, channels=1):
        """
        Add a microphone.

        Parameters
        ----------
        name : str
            User-defined name of the microphone.
        device : int or str, optional
            Device index or name. Defaults to 0.
        sampleRate : int, optional
            Sample rate in Hz. Defaults to 44100.
        channels : int, optional
            Number of channels. Defaults to 1 for mono. Use 2 for stereo.

        Returns
        -------
        Microphone
            Microphone object.

        Examples
        --------
        Get available microphones and add one to the device manager::

            import psychopy.hardware.manager as hm
            mgr = hm.getDeviceManager()

            allMics = mgr.getAvailableMicrophones()
            print(allMics.keys())  # show all available microphone names
            devSpec = allMics['Microphone (C922 Pro Stream Webcam)']
            mgr.addMicrophone('response_mic', device=devSpec['device_index'])

        Same as above but using settings obtained in advance::

            dm = hm.getDeviceManager()
            specs = dm.getAvailableMicrophones()
            spec = specs[0]  # get first microphone

            kwargs = {
                'device': spec['device_index'],
                'sampleRate': spec['sampling_rate'][0],  # use first supported
                'channels': spec['channels']
            }

            mic = dm.addMicrophone('default', **kwargs)

        Use the microphone to record audio::

            mic = mgr.getMicrophone('response_mic')
            mic.setSound(...)

        """
        # if no name given, generate unique name
        if name is None:
            name = self.makeUniqueName(deviceType="microphone")
        self._assertDeviceNameUnique(name)
        
        # import microphone here to avoid circular import
        import psychopy.sound.microphone as microphone

        # check if we already have a microphone with the same device
        for mic in self._devices['microphone']:
            if mic.device == device:
                raise ValueError(
                    f"Microphone device {device} is already in use by {mic.name}")

        dev = microphone.MicrophoneDevice(
            device=device, sampleRateHz=sampleRate, channels=channels
        )
        toReturn = self._devices['microphone'][name] = dev

        return dev

    @DeviceMethod("microphone", "remove")
    def removeMicrophone(self, name):
        """
        Remove a microphone.

        Parameters
        ----------
        name : str
            Name of the microphone.

        """
        self._assertDeviceNameUnique(name)

        self._devices['microphone'][name].close()
        del self._devices['microphone'][name]

    @DeviceMethod("microphone", "get")
    def getMicrophone(self, name):
        """Get an audio capture device by name.

        Parameters
        ----------
        name : str
            Name of the capture device.

        Returns
        -------
        Microphone or `None`
            Microphone object or `None` if no device with the given name exists.
        """
        return self._devices['microphone'].get(name, None)

    @DeviceMethod("microphone", "getall")
    def getMicrophones(self):
        """
        Get a mapping of audio capture devices that have been initialized.

        Returns
        -------
        dict
            Dictionary of audio capture devices that have been initialized.
            Where the keys are the names of the devices and the values are the
            device objects.

        """
        return self._devices['microphone']

    @DeviceMethod("microphone", "available")
    def getAvailableMicrophones(self):
        """
        Get information about all available audio capture devices connected to
        the system.

        Returns
        -------
        dict
            Dictionary of information about available audio capture devices
            connected to the system.

        """
        return st.getInstalledDevices('microphone')


class CameraPlugin(DeviceManager):
    """
    Plugin class for DeviceManager, adding device methods for video recording devices via the DeviceMethod decorator.
    """

    @DeviceMethod("camera", "add")
    def addCamera(self, name=None, device=0, backend=u'ffpyplayer'):
        """
        Add a camera.

        Parameters
        ----------
        name : str
            User-defined name of the camera.
        device : int or str, optional
            Device index or name. Defaults to 0.
        backend : str, optional
            Backend to use for camera input. Defaults to "ffpyplayer".
        
        Returns
        -------
        Camera
            Camera object.

        """
        # if no name given, generate unique name
        if name is None:
            name = self.makeUniqueName(deviceType="camera")
        self._assertDeviceNameUnique(name)

        # check if the device is already in use
        for cam in self._devices['camera']:
            if cam.device == device:
                raise ValueError(
                    f"Camera device {device} is already in use by {cam.name}")

        import psychopy.hardware.camera as camera
        dev = camera.Camera(device=device, cameraLib=backend)
        toReturn = self._devices['camera'][name] = dev

        return dev

    @DeviceMethod("camera", "remove")
    def removeCamera(self, name):
        """
        Remove a camera.

        Parameters
        ----------
        name : str
            Name of the camera.
        """
        del self._devices['camera'][name]

    @DeviceMethod("camera", "get")
    def getCamera(self, name):
        """
        Get a camera by name.

        Parameters
        ----------
        name : str
            Arbitrary name given to the camera when it was `add`ed.

        Returns
        -------
        BaseDevice
            The requested camera
        """
        return self._devices['camera'].get(name, None)

    @DeviceMethod("camera", "getall")
    def getCameras(self):
        """
        Get a mapping of cameras that have been initialized.

        Returns
        -------
        dict
            Dictionary of cameras that have been initialized. Where the keys are
            the names of the cameras and the values are the camera objects.

        """
        return self._devices['camera']

    @DeviceMethod("camera", "available")
    def getAvailableCameras(self):
        """
        Get information about all available cameras connected to the system.

        Returns
        -------
        dict
            Dictionary of information about available cameras connected to the
            system.

        """
        return st.getInstalledDevices('camera')


class SerialPlugin(DeviceManager):
    """
    Plugin class for DeviceManager, adding device methods for serial port devices via the DeviceMethod decorator.
    """

    @DeviceMethod("serial", "add")
    def addSerialDevice(self, name=None, port=None, baudrate=9600, byteSize=8, stopBits=1,
            parity="N"):
        """
        Add a generic serial device interface.

        This creates a serial device interface object that can be used to
        communicate with a serial device. This is a generic interface that can
        be used to communicate with any serial device, such as a button box or
        a TPad.

        Parameters
        ----------
        name : str
            User-defined name of the serial device.
        port : str
            Port of the serial device.
        baudrate : int, optional
            Baudrate of the serial device. Defaults to 9600.
        byteSize : int, optional
            Byte size of the serial device. Defaults to 8.
        stopBits : int, optional
            Stop bits of the serial device. Defaults to 1.
        parity : str, optional
            Parity of the serial device. Defaults to "N".

        Returns
        -------
        SerialDevice
            Serial device interface object.

        """
        # if no name given, generate unique name
        if name is None:
            name = self.makeUniqueName(deviceType="serial")
        self._assertDeviceNameUnique(name)

        if name in self._devices['serial'].keys():
            raise ValueError(f"Serial device {name} already exists")

        import psychopy.hardware.serialdevice as serialdevice

        # check if we have a serial device with the same port
        for dev in self._devices['serial']:
            if dev.port == port:
                raise ValueError(
                    f"Serial port {port} is already in use by {dev.name}")

        # open up a port and add it to the device manager
        toReturn = self._devices['serial'][name] = serialdevice.SerialDevice(
            port=port, baudrate=baudrate,
            byteSize=byteSize, stopBits=stopBits,
            parity=parity
        )

        return toReturn

    @DeviceMethod("serial", "remove")
    def removeSerialDevice(self, name):
        """Remove a serial device interface.

        This frees the port by closing prior to removing the device interface.

        Parameters
        ----------
        name : str
            Name or port of the serial device.

        """
        # if name isn't present, try to match port
        if name not in self._devices['serial']:
            for dev in self._devices['serial']:
                if dev.port == name:
                    name = dev.name
                    break
        # error if there's still no name
        if name not in self._devices['serial'].keys():
            raise ValueError(f"Serial device {name} does not exist")
        # close and delete device
        self._devices['serial'][name].close()
        del self._devices['serial'][name]

    @DeviceMethod("serial", "get")
    def getSerialDevice(self, name):
        """Get a serial device by name or port.

        Parameters
        ----------
        name : str
            Name or port of the serial device.

        Returns
        -------
        SerialDevice or `None`
            Serial device interface object or `None` if no device with the given
            name or port exists.

        """
        if name in self._devices['serial']:
            return self._devices['serial'][name]
        else:
            for dev in self._devices['serial']:
                if dev.port == name:
                    return dev

            return None

    @DeviceMethod("serial", "getall")
    def getSerialDevices(self):
        """
        Get a mapping of serial devices that have been initialized.

        Returns
        -------
        dict
            Dictionary of serial devices that have been initialized. Where the keys
            are the names of the serial devices and the values are the serialDevice
            objects.

        """
        return self._devices['serialDevice']

    @DeviceMethod("serial", "available")
    def getAvailableSerialDevices(self):
        """
        Get information about all available serial devices connected to the system.

        Returns
        -------
        dict
            Dictionary of information about available serial devices connected to
            the system.

        """
        return st.getInstalledDevices('serial')


class EyetrackerPlugin(DeviceManager):
    """
    Plugin class for eyetracker objects, adding device methods for eyetracker devices via the DeviceMethod
    decorator.
    """

    @DeviceMethod("eyetracker", "add")
    def addEyetracker(self, name=None, ):
        """
        Add a eyetracker.

        Parameters
        ----------
        name : str or None
            Arbitrary name to refer to this eyetracker by. Use None to generate a unique name.

        Returns
        -------
        iohub.Eyetracker object
            Added eyetracker.

        Examples
        --------
        Add a keyboard::

            import psychopy.hardware.manager as hm
            mgr = hm.getDeviceManager()
            mgr.addKeyboard('response_keyboard', backend='iohub', device=-1)

        Get the keyboard and use it to get a response::

            kb = mgr.getKeyboard('response_keyboard')
            kb.getKeys()

        """
        # if no name given, generate unique name
        if name is None:
            name = self.makeUniqueName(deviceType="eyetracker")
        self._assertDeviceNameUnique(name)
        # raise an error if there's no ioServer yet
        if self.ioServer is None:
            raise ConnectionError(
                "DeviceHandler could not find any ioServer associated with current process. Please start an ioServer "
                "before adding an eyetracker."
            )
        # only one eyetracker can be active and it will already have been set up by ioHub, so just get it
        self._devices['eyetracker'][name] = self.ioServer.getDevice('tracker')
        # activate eyetracker
        self._devices['eyetracker'][name].setConnectionState(True)

        return self._devices['eyetracker'][name]

    @DeviceMethod("eyetracker", "remove")
    def removeEyetracker(self, name):
        """
        Remove a eyetracker.

        Parameters
        ----------
        name : str
            Name of the eyetracker.
        """
        self._devices['eyetracker'][name].setConnectionState(False)
        del self._devices['eyetracker'][name]

    @DeviceMethod("eyetracker", "get")
    def getEyetracker(self, name):
        """
        Get a eyetracker by name.

        Parameters
        ----------
        name : str
            Arbitrary name given to the eyetracker when it was `add`ed.

        Returns
        -------
        BaseDevice
            The requested eyetracker
        """
        return self._devices['eyetracker'].get(name, None)

    @DeviceMethod("eyetracker", "getall")
    def getEyetrackers(self):
        """
        Get a mapping of eyetrackers that have been initialized.

        Returns
        -------
        dict
            Dictionary of eyetrackers that have been initialized. Where the keys
            are the names of the eyetrackers and the values are the eyetracker
            objects.

        """
        return self._devices['eyetracker']

    @DeviceMethod("eyetracker", "available")
    def getAvailableEyetrackers(self):
        """
        Get information about all available eyetrackers connected to the system.

        Returns
        -------
        dict
            Dictionary of information about available eyetrackers connected to
            the system.

        """
        return st.getInstalledDevices('eyetracker')

            
# handle to the device manager, which is a singleton
deviceManager = DeviceManager()


def getDeviceManager():
    """Get the device manager.

    Returns an instance of the device manager.

    Returns
    -------
    DeviceManager
        The device manager.

    """
    global deviceManager
    if deviceManager is None:
        deviceManager = DeviceManager()  # initialize

    return deviceManager


def closeAllDevices():
    """Close all devices.

    Close all devices that have been initialized. This is usually called on
    exit to free resources cleanly. It is not necessary to call this method
    manually as it's registed as an `atexit` handler.

    """
    devMgr = getDeviceManager()
    if devMgr is not None:
        devMgr.closeAll()


# register closeAllDevices as an atexit handler
atexit.register(closeAllDevices)


if __name__ == "__main__":
    pass
