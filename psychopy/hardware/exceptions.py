import json
import traceback


class DeviceNotConnectedError(Exception):
    """
    Raised when a subclass of BaseDevice is initialised but the physical device it represents can't 
    be found.

    Parameters
    ----------
    msg : str
        Message to display
    deviceClass : type
        Device class which the error came from
    context : dict, optional
        Dict of any additional information to store
    """
    def __init__(self, msg, deviceClass=None, context=None, *args):
        # make exception
        Exception.__init__(self, msg, *args)
        # store device class
        if deviceClass is not None and not isinstance(deviceClass, type):
            deviceClass = type(deviceClass)
        self.deviceClass = deviceClass
        # store additional context
        self.context = context
    
    def getJSON(self, asString=True):
        """
        Allow this type of error to be converted to JSON if requested.

        Parameters
        ----------
        asString : bool, optional
            Convert to a string or leave as a serializable dict? By default True
        """
        # construct message
        message = {
            'type': "device_not_connected_error",
            'device_type': self.deviceClass.__name__,
            'msg': str(self),
            'context': self.context
        }
        # stringify if requested
        if asString:
            message = json.dumps(message)

        return message


class ManagedDeviceError(BaseException):
    """
    Exception arising from a managed device, which will include information about the device from
    DeviceManager.
    """
    def __init__(self, msg, deviceName, traceback=None):
        # create exception
        BaseException.__init__(self, msg)
        # store device name
        self.deviceName = deviceName
        # store traceback
        if traceback is not None:
            self.traceback = traceback
        else:
            self.traceback = self.__traceback__

    def getJSON(self, asString=True):
        tb = traceback.format_exception(type(self), self, self.traceback)
        message = {
            'type': "hardware_error",
            'device': self.deviceName,
            'msg': "".join(tb),
            'context': getattr(self, "userdata", None)
        }
        # stringify if requested
        if asString:
            message = json.dumps(message)

        return message