from psychopy import logging


class PluginDevicesMixin:
    """
    Legacy placeholder class - used to handle device backends added by plugins before Builder had a dedicated device manager.
    """
    pass


from .devices import DeviceBackend
class DeviceBackend(DeviceBackend):
    """
    Legacy wrapper to convert plugins.DeviceBackend classes to the newer devices.DeviceBackend class.
    """
    key = "microphone"
    label = ""
    component = None
    deviceClasses = ["psychopy.hardware.soundsensor.MicrophoneSoundSensor"]
    component = PluginDevicesMixin
    key = ""
    label = ""
    deviceClasses = []


    def __init_subclass__(cls):
        # if component was specified by class attribute, register it
        if cls.component is not PluginDevicesMixin:
            cls.component.registerBackend(cls)
        # if we can get params without initialising, add them to the Component's legacy list
        # (as they're now parameters of the device rather than the Component)
        try:
            for name in cls.getParams(None)[0]:
                cls.component.legacyParams.append(name)
        except AttributeError:
            pass
        # placeholder value for icon
        cls.icon = None
        # use label for backendLabel
        cls.backendLabel = cls.label
        # a backend only has 1 device now
        cls.deviceClass = cls.deviceClasses[0]
