from . import keyboard, mouse, serialdevice as sd, camera
from psychopy.sound import microphone
from psychopy.tools import systemtools as st
from serial.tools import list_ports

# dict to store references to add methods by device key
_deviceAddMethods = {}


def deviceAddMethod(key):
    """Decorator which adds the decorated method to _deviceAddMethods against 
    the given key.

    Parameters
    ----------
    key : str
        Key to link the decorated method to.

    """
    # make decorator function
    def _decorator(fcn):
        # map function to key
        _deviceAddMethods[key] = fcn
        # return function unchanged
        return fcn
    # return decorator function
    return _decorator


class DeviceManager(list):
    """Class for managing hardware devices relevant to PsychoPy connected to the 
    computer.

    """
    instance = None  # singleton instance

    def __new__(cls):
        if cls.instance is None:
            cls.instance = list.__new__(cls)
        return cls.instance

    # --- managing devices ---
    @deviceAddMethod("Keyboard")
    def addKeyboard(self, backend="iohub", device=-1):
        return keyboard.Keyboard(backend=backend, device=device)

    @deviceAddMethod("Mouse")
    def addMouse(self, name):
        self[name] = mouse.Mouse()

        return self[name]

    @deviceAddMethod("Microphone")
    def addMicrophone(self, name, device, sampleRate=44100, channels=1):
        self[name] = microphone.Microphone(
            device=device, sampleRateHz=sampleRate, channels=channels
        )

        return self[name]

    @deviceAddMethod("Camera")
    def addCamera(self, name, device=0, backend=u'ffpyplayer'):
        self[name] = camera.Camera(
            device=device, cameraLib=backend
        )

        return self[name]

    @deviceAddMethod("Serial")
    def addSerialDevice(self, name, port, baudrate=9600, byteSize=8, stopBits=1, parity="N"):
        self[name] = sd.SerialDevice(
            port=port, baudrate=baudrate,
            byteSize=byteSize, stopBits=stopBits,
            parity=parity
        )

        return self[name]

    @deviceAddMethod("TPad")
    def addTPad(self, name, port):
        raise NotImplementedError("BBTK TPad integration is a work in progress")

    def registerDevice(self, device):
        for obj in self:
            if hasattr(obj, "isSameDevice"):
                if obj.isSameDevice(params=device.__dict__):
                    return
                    
        self.append(device)

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

    # --- querying hardware ---
    @staticmethod
    def getKeyboards():
        st.getKeyboards()

    @staticmethod
    def getSpeakers():
        """Get a list of audio playback devices that have been initialized.

        Returns
        -------
        list
            List of audio playback devices that have been initialized.

        """
        return []

    @staticmethod
    def getMicrophones():
        """Get a list of audio capture devices that have been initialized.

        Returns
        -------
        list
            List of audio capture devices that have been initialized.

        """
        return []

    @staticmethod
    def getCameras():
        """Get a list of cameras that have been initialized.

        Returns
        -------
        list
            List of cameras that have been initialized.

        """
        return []

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
mgr = DeviceManager()


if __name__ == "__main__":
    pass
