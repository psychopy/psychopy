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
            'trigger',
            'unassigned'  # used for devices that don't have a category
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
        self._assertDeviceNameUnique(name)

        # check if the device id is alread in use
        for kb in self._devices['keyboard']:
            if kb.device == device:
                raise ValueError(
                    f"Keyboard device {device} is already in use by {kb.name}")

                # nb - device=-1 is a bit tricky to handle, since it's not
                # a valid device index.

        toReturn = self._devices['keyboard'][name] = keyboard.Keyboard(
            backend=backend, device=device)

        return toReturn

    def addMouse(self, name, backend='iohub'):
        """Add a mouse.

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
        # todo - handle the `backend` parameter
        self._assertDeviceNameUnique(name)

        from psychopy.hardware.mouse import mouse
        toReturn = self._devices['mouse'][name] = mouse.Mouse()

        return toReturn

    def addSpeaker(self, name, device=0, sampleRate=44100, channels=2):
        """Add a speaker.

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
        # We need to initialize the audio playback system here, right now that
        # all handled by the `sound` module in a fairly rigid way that can't be 
        # easily done like microphones.
        raise NotImplementedError("Speaker support is a work in progress")

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
        self._assertDeviceNameUnique(name)
        
        # import microphone here to avoid circular import
        import psychopy.sound.microphone as microphone

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

    def removeMicrophone(self, name):
        """Remove a microphone.

        Parameters
        ----------
        name : str
            Name of the microphone.

        """
        self._assertDeviceNameUnique(name)

        self._devices['microphone'][name].close()
        del self._devices['microphone'][name]

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

    def findDevice(self, name):
        """Find a device by name.

        This can be used to find a device by its user specified name, returning 
        its interface object.

        Parameters
        ----------
        name : str
            Name of the device.

        Returns
        -------
        object or `None`
            Device object associated with the given name. Returns `None` if no
            device with the given name exists.

        """
        for devClass in self._devices:
            if name in self._devices[devClass]:
                return self._devices[devClass][name]

        return None

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

    def addSerialDevice(self, name, port, baudrate=9600, byteSize=8, stopBits=1, 
            parity="N"):
        """Add a generic serial device interface.

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

    # --- manage devices ---
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

    def getSpeaker(self, name):
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
    def getAvailableKeyboards():
        """Get information about all available keyboards connected to the system.

        Returns
        -------
        dict
            Dictionary of information about available keyboards connected to 
            the system.

        """
        return st.getInstalledDevices('keyboard')

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
