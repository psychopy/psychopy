from . import keyboard, mouse, serialdevice as sd, camera
from psychopy.sound import microphone
from psychopy.tools import systemtools as st
from serial.tools import list_ports

# dict to store references to add methods by device key
_deviceAddMethods = {}


def deviceAddMethod(key):
    """
    Decorator which adds the decorated method to _deviceAddMethods against the given key.

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


class DeviceManager:
    def __init__(self):
        self.devices = {}

    # --- managing devices ---
    @deviceAddMethod("Keyboard")
    def addKeyboard(self, name, backend="iohub"):
        self.devices[name] = keyboard.Keyboard(backend=backend)

    @deviceAddMethod("Mouse")
    def addMouse(self, name):
        self.devices[name] = mouse.Mouse()

    @deviceAddMethod("Microphone")
    def addMicrophone(self, name, device, sampleRate=44100, channels=1):
        self.devices[name] = microphone.Microphone(
            device=device, sampleRateHz=sampleRate, channels=channels
        )

    @deviceAddMethod("Camera")
    def addCamera(self, name, device=0, backend=u'ffpyplayer'):
        self.devices[name] = camera.Camera(
            device=device, cameraLib=backend
        )

    @deviceAddMethod("TPad")
    def addTPad(self, name, port):
        raise NotImplementedError("BBTK TPad integration is a work in progress")

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
    def getMicrophones():
        return st.getAudioCaptureDevices()

    @staticmethod
    def getCameras():
        return st.getCameras()

    @staticmethod
    def getSerialDevices():
        spec = {}
        for info in list_ports.comports():
            spec[info.name] = info
        return spec
