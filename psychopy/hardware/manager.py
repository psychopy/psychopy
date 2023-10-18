#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hardware device management.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'mgr', 
    'getDeviceManager', 
    'DeviceManager',
    'closeAllDevices'
]

from . import keyboard, mouse, serialdevice as sd, camera
from psychopy.sound import microphone
from psychopy.tools import systemtools as st
from serial.tools import list_ports
import atexit


class DeviceManager:
    """Class for managing hardware devices.

    An instance of this class is used to manage hardware peripherals relevant 
    to PsychoPy. It can be used to initialize and access devices such as
    audio devices, serial devices, and cameras. It can also be used to get
    information about available devices installed on the system.
    
    It is recommended that devices are initialized through the device manager
    rather than directly. This allows the device manager to keep track of
    devices and prevent conflicts. For example, if a microphone is initialized
    with the same device number as another microphone, the device manager will
    raise an error.

    This class is implemented as a singleton, so there is only one
    instance of it per ssession after its initialized. The instance can be 
    accessed through the global variable `mgr` or by calling 
    `getDeviceManager()`.

    """
    _instance = None  # singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeviceManager, cls).__new__(cls)

        return cls._instance

    def __init__(self):
        # keep track of different classes of devices
        devClasses = [
            'microphone', 
            'speaker', 
            'camera', 
            'keyboard', 
            'mouse',
            'serial', 
            'parallel', 
            'tpad', 
            'trigger'
            # 'buttonbox'
        ]

        # initialize a dictionary to store dictionaries of devices for each device class
        self._devices = {devClass: {} for devClass in devClasses}

    # --- managing devices ---
    def addKeyboard(self, name, backend="iohub", device=-1):
        """Add a keyboard.

        Parameters
        ----------
        backend : str, optional
            Backend to use for keyboard input. Defaults to "iohub".
        device : int, optional
            Device number to use. Defaults to -1.

        Returns
        -------
        Keyboard
            Keyboard object.

        """
        if name in self._devices['keyboard'].keys():
            raise ValueError(f"Keyboard {name} already exists")

        dev = keyboard.Keyboard(backend=backend, device=device)
        toReturn = self._devices['keyboard'][name] = dev

        return toReturn

    def addMouse(self, name):
        """Add a mouse.

        Parameters
        ----------
        name : str
            Name of the mouse.

        Returns
        -------
        Mouse
            Mouse object.

        """
        if name in self._devices['mouse'].keys():
            raise ValueError(f"Mouse {name} already exists")

        toReturn = self._devices['mouse'][name] = mouse.Mouse()

        return toReturn

    def addMicrophone(self, name, device=0, sampleRate=44100, channels=1):
        """Add a microphone.

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

        """
        if name in self._devices['microphone'].keys():
            raise ValueError(f"Microphone {name} already exists")

        # check if we already have a microphone with the same device
        for mic in self._devices['microphone']:
            if mic.device == device:
                raise ValueError(
                    f"Microphone device {device} is already in use by {mic.name}")

        dev = microphone.Microphone(
            device=device, sampleRateHz=sampleRate, channels=channels
        )
        toReturn = self._devices['microphone'][name] = dev

        return dev

    def addCamera(self, name, device=0, backend=u'ffpyplayer'):
        """Add a camera.

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
        # check if the device is already in use
        for cam in self._devices['camera']:
            if cam.device == device:
                raise ValueError(
                    f"Camera device {device} is already in use by {cam.name}")

        dev = camera.Camera(device=device, cameraLib=backend)
        toReturn = self._devices['camera'][name] = dev

        return dev

    def addSerialDevice(self, name, port, baudrate=9600, byteSize=8, stopBits=1, 
            parity="N"):
        """Add a serial device interface.

        This creates a serial device interface object that can be used to
        communicate with a serial device.

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
        if name in self._devices['serial'].keys():
            raise ValueError(f"Serial device {name} already exists")

        # check if we have a serial device with the same port
        for dev in self._devices['serial']:
            if dev.port == port:
                raise ValueError(
                    f"Serial port {port} is already in use by {dev.name}")

        # open up a port and add it to the device manager
        toReturn = self._devices['serial'][name] = sd.SerialDevice(
            port=port, baudrate=baudrate,
            byteSize=byteSize, stopBits=stopBits,
            parity=parity
        )

        return toReturn

    def removeSerialDevice(self, name):
        """Remove a serial device interface.

        This frees the port by closing prior to removing the device interface.

        Parameters
        ----------
        name : str
            Name of the serial device.

        """
        if name not in self._devices['serial'].keys():
            raise ValueError(f"Serial device {name} does not exist")

        self._devices['serial'][name].close()
        del self._devices['serial'][name]

    def removeSerialDeviceByPort(self, port):
        """Remove a serial device interface by port.

        This frees the port by closing prior to removing the device interface.

        Parameters
        ----------
        port : str
            Port of the serial device.

        Examples
        --------
        Remove a serial device by port::

            mgr.removeSerialDeviceByPort('COM1')

        """
        for dev in self._devices['serial']:
            if dev.port == port:
                self.removeSerialDevice(dev.name)
                break

    def addTPad(self, name, port):
        raise NotImplementedError("BBTK TPad integration is a work in progress")

    def registerDevice(self, device):
        """Register a device.

        Parameters
        ----------
        device : Device
            Device to register.

        """
        if device.name in self.devices:
            raise ValueError(f"Device {device.name} already exists")

        self.devices[device.name] = device

    def addDevicesFromSpec(self, spec):
        for item in spec:
            # pop type key from spec
            ioType = item.pop("type")
            # figure out name
            if "name" in item:
                # if name is given, use it
                name = item.pop("name")
            else:
                # if not given, use input type as name
                name = ioType
                # add numbers for unique names
                i = 0
                while name in self.devices:
                    i += 1
                    name = f"{ioType}{i}"
            # call method associated with input type (according to decorators)
            _deviceAddMethods[ioType](name, **item)

    # --- manage devices ---
    @staticmethod
    def getKeyboards(self):
        """Get a mapping of keyboards that have been initialized.


        Returns
        -------
        dict
            Dictionary of keyboards that have been initialized. Where the keys
            are the names of the keyboards and the values are the keyboard
            objects.

        """
        return self._devices['keyboard']

    def getSpeakers(self):
        """Get a mapping of audio playback devices that have been initialized.

        Returns
        -------
        dict
            Dictionary of audio playback devices that have been initialized.
            Where the keys are the names of the devices and the values are the
            device objects.

        """
        return self._devices['speaker']

    def getAudioPlaybackDevice(self, name):
        """Get a playback device by name.

        Parameters
        ----------
        name : str
            Name of the playback device.

        Returns
        -------
        Speaker or `None`
            Speaker object or `None` if no device with the given name exists.
        
        """
        return self._devices['speaker'].get(name, None)

    def getMicrophones(self):
        """Get a mapping of audio capture devices that have been initialized.

        Returns
        -------
        dict
            Dictionary of audio capture devices that have been initialized.
            Where the keys are the names of the devices and the values are the
            device objects.

        """
        return self._devices['microphone']

    def getAudioCaptureDevice(self, name):
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

    def getCameras(self):
        """Get a mapping of cameras that have been initialized.

        Returns
        -------
        dict
            Dictionary of cameras that have been initialized. Where the keys are
            the names of the cameras and the values are the camera objects.

        """
        return self._devices['camera']

    def getSerialDevices(self):
        """Get a mapping of serial devices that have been initialized.

        Returns
        -------
        dict
            Dictionary of serial devices that have been initialized. Where the
            keys are the names of the devices and the values are the device
            objects.

        """
        return self._devices['serial']

    def getSerialDevice(self, name):
        """Get a serial device by name.

        Parameters
        ----------
        name : str
            Name of the serial device.

        Returns
        -------
        SerialDevice or `None`
            Serial device interface object or `None` if no device with the given
            name exists.
        
        """
        return self._devices['serial'].get(name, None)

    def getSerialDeviceByPort(self, port):
        """Get a serial device by port.

        Parameters
        ----------
        port : str
            Port of the serial device.

        Returns
        -------
        SerialDevice or `None`
            Serial device interface object or `None` if no device with the given
            port exists.

        """
        for dev in self._devices['serial']:
            if dev.port == port:
                return dev

        return None

    # --- get available devices ---

    @staticmethod
    def getAvailableSpeakers():
        """Get information about all available audio playback devices connected to 
        the system.
        
        Returns
        -------
        dict
            Dictionary of information about available audio playback devices 
            connected to the system.
        
        """
        return st.getInstalledDevices('speaker')

    @staticmethod
    def getAvailableMicrophones():
        """Get information about all available audio capture devices connected to
        the system.

        Returns
        -------
        dict
            Dictionary of information about available audio capture devices 
            connected to the system.

        """
        return st.getInstalledDevices('microphone')

    @staticmethod
    def getAvailableCameras():
        """Get information about all available cameras connected to the system.

        Returns
        -------
        dict
            Dictionary of information about available cameras connected to the 
            system.

        """
        return st.getInstalledDevices('camera')

    @staticmethod
    def getSerialDevices():
        spec = {}
        for info in list_ports.comports():
            spec[info.name] = info
        return spec

    def closeAll(self):
        """Close all devices.

        Close all devices that have been initialized. This is usually called on
        exit to free resources cleanly. It is not necessary to call this method
        manually as it's registed as an `atexit` handler.

        After this is called, all devices will be closed and the device manager
        will be empty.

        """
        devClasses = list(self._devices.keys())
        for devClass in devClasses:
            for dev in self._devices[devClass]:
                if hasattr(dev, 'close'):
                    dev.close()
                    logging.debug(f"Closed `{devClass}` device ({dev.name})")
                else:
                    logging.debug(
                        f"Device `{devClass}` ({dev.name}) has no close method")
                
            self._devices[devClass].clear()

            
# handle to the device manager, which is a singleton
mgr = DeviceManager()


def getDeviceManager():
    """Get the device manager.

    Returns
    -------
    DeviceManager
        The device manager.

    """
    return mgr


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
