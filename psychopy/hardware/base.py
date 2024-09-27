#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Base class for hardware device interfaces.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'BaseDevice'
]

import json
import inspect
import numpy as np
from psychopy import logging


class BaseResponse:
    """
    Base class for device responses.
    """
    # list of fields known to be a part of this response type
    fields = ["t", "value"]

    def __init__(self, t, value, device=None):
        self.device = device
        self.t = t
        self.value = value

    def __repr__(self):
        # make key=val strings
        attrs = []
        for key in self.fields:
            attrs.append(f"{key}={getattr(self, key)}")
        attrs = ", ".join(attrs)
        # construct
        return f"<{type(self).__name__} from {self.getDeviceName()}: {attrs}>"
    
    def getDeviceName(self):
        # if device isn't a device, and this method isn't overloaded, return None
        if not hasattr(self.device, "getDeviceProfile"):
            return None
        # get profile
        deviceProfile = self.device.getDeviceProfile()
        # get name from profile
        if "deviceName" in deviceProfile:
            return deviceProfile['deviceName']
        else:
            # if profile doesn't include name, use class name
            return type(self.device).__name__

    def getJSON(self):
        import json
        # get device profile
        deviceProfile = None
        if hasattr(self.device, "getDeviceProfile"):
            deviceProfile = self.device.getDeviceProfile()
        # construct message as dict
        message = {
            'type': "hardware_response",
            'class': type(self).__name__,
            'device': deviceProfile,
            'data': {}
        }
        # add all fields to "data"
        for key in self.fields:
            message['data'][key] = getattr(self, key)
            # sanitize numpy arrays
            if isinstance(message['data'][key], np.ndarray):
                message['data'][key] = message['data'][key].tolist()


        return json.dumps(message)


class BaseDevice:
    """
    Base class for device interfaces, includes support for DeviceManager and adding listeners.
    """
    # start off with no cached profile
    _profile = None
    
    def __init_subclass__(cls, aliases=None):
        from psychopy.hardware.manager import DeviceManager
        # handle no aliases
        if aliases is None:
            aliases = []
        # if given a class, get its class string
        mro = inspect.getmodule(cls).__name__ + "." + cls.__name__
        # register aliases
        for alias in aliases:
            DeviceManager.registerClassAlias(alias, mro)
        # store class string
        DeviceManager.deviceClasses.append(mro)

        return cls

    def __eq__(self, other):
        """
        For BaseDevice objects, the == operator functions as shorthand for isSameDevice
        """
        return self.isSameDevice(other)

    def getDeviceProfile(self):
        """
        Generate a dictionary describing this device by finding the profile from
        getAvailableDevices which represents the same physical device as this object.

        Returns
        -------
        dict
            Dictionary representing this device
        """
        # only iteratively find it if we haven't done so already
        if self._profile is None:
            # get class string
            cls = type(self)
            mro = inspect.getmodule(cls).__name__ + "." + cls.__name__
            # iterate through available devices for this class
            for profile in self.getAvailableDevices():
                if self.isSameDevice(profile):
                    # if current profile is this device, add deviceClass and return it
                    profile['deviceClass'] = mro
                    self._profile = profile
                    break
        
        return self._profile

    def getJSON(self, asString=True):
        """
        Convert the output of getDeviceProfile to a JSON string.

        Parameters
        ----------
        asString : bool
            If True, then the output will be converted to a string, otherwise will simply be a
            JSON-friendly dict.

        Returns
        -------
        str or dict
            JSON string (or JSON friendly dict) of getDeviceProfile.
        """
        profile = self.getDeviceProfile()
        if asString:
            profile = json.dumps(profile)

        return profile

    # the following methods must be implemented by subclasses of BaseDevice

    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical device as a given other object.

        Parameters
        ----------
        other : BaseDevice, dict
            Other device object to compare against, or a dict of params.

        Returns
        -------
        bool
            True if the two objects represent the same physical device
        """
        raise NotImplementedError(
            "All subclasses of BaseDevice must implement the method `isSameDevice`"
        )

    @staticmethod
    def getAvailableDevices():
        """
        Get all available devices of this type.

        Returns
        -------
        list[dict]
            List of dictionaries containing the parameters needed to initialise each device.
        """
        raise NotImplementedError(
            "All subclasses of BaseDevice must implement the method `getAvailableDevices`"
        )


class BaseResponseDevice(BaseDevice):

    responseClass = BaseResponse

    def __init__(self):
        # list to store listeners in
        self.listeners = []
        # list to store responses in
        self.responses = []
        # indicator to mute outside of registered apps
        self.muteOutsidePsychopy = False 

    def dispatchMessages(self):
        """
        Method to dispatch messages from the device to any nodes or listeners attached.
        """
        pass

    def hasUnfinishedMessage(self):
        """
        If there is a message which have been partially received but not finished (e.g. 
        getting the start of a message from a serial device but no end of line character 
        yet), this will return True.

        If not implemented or not relevant on a given device (e.g. Keyboard, which only 
        sends full messages), this will always return False.
        """
        return False

    def parseMessage(self, message):
        raise NotImplementedError(
            "All subclasses of BaseDevice must implement the method `parseMessage`"
        )

    def receiveMessage(self, message):
        """
        Method called when a parsed message is received. Includes code to send to any listeners and store the response.

        Parameters
        ----------
        message
            Parsed message, should be an instance of this Device's `responseClass`

        Returns
        -------
        bool
            True if completed successfully
        """
        # disregard any messages sent while the PsychoPy window wasn't in focus (for security)
        from psychopy.tools.systemtools import isRegisteredApp
        if self.muteOutsidePsychopy and not isRegisteredApp():
            return
        # make sure response is of the correct class
        assert isinstance(message, self.responseClass), (
            "{ownType}.receiveMessage() can only receive messages of type {targetType}, instead received "
            "{msgType}. Try parsing the message first using {ownType}.parseMessage()"
        ).format(ownType=type(self).__name__, targetType=self.responseClass.__name__, msgType=type(message).__name__)
        # add message to responses
        self.responses.append(message)
        # relay message to listener
        for listener in self.listeners:
            listener.receiveMessage(message)
        # relay to log file
        try:
            logging.exp(
                f"Device response: {message}"
            )
        except Exception as err:
            logging.error(
                f"Received a response from a {type(self).__name__} but couldn't print it: {err}"
            )

        return True

    def makeResponse(self, *args, **kwargs):
        """
        Programatically make a response on this device. The device won't necessarily physically register the response,
        but it will be stored in this object same as an actual response.

        Parameters
        ----------
        Function takes the same inputs as the response class for this device. For example, in KeyboardDevice, inputs
        are code, tDown and name.

        Returns
        -------
        BaseResponse
            The response object created
        """
        # create response
        resp = self.responseClass(*args, **kwargs)
        # receive response
        self.receiveMessage(resp)

        return resp

    def clearResponses(self):
        """
        Clear any responses stored on this Device.

        Returns
        -------
        bool
            True if completed successfully
        """
        # try to dispatch messages
        try:
            self.dispatchMessages()
        except:
            pass
        # clear resp list
        self.responses = []

        return True

    def getListenerNames(self):
        return [type(lsnr).__name__ for lsnr in self.listeners]

    def addListener(self, listener, startLoop=False):
        """
        Add a listener, which will receive all the same messages as this device.

        Parameters
        ----------
        listener : str or psychopy.hardware.listener.BaseListener
            Either a Listener object, or use one of the following strings to create one:
            - "liaison": Create a LiaisonListener with DeviceManager.liaison as the server
            - "print": Create a PrintListener with default settings
            - "log": Create a LoggingListener with default settings
        startLoop : bool
            If True, then upon adding the listener, start up an asynchronous loop to dispatch messages.
        """
        from . import listener as lsnr
        # dispatch existing events now (so listener doesn't get a lump of historic messages)
        self.dispatchMessages()
        # map listener classes to names
        listenerClasses = {
            'liaison': lsnr.LiaisonListener,
            'print': lsnr.PrintListener,
            'log': lsnr.LoggingListener
        }
        # if device already has a listener, log warning and skip
        for extantListener in self.listeners:
            # get class of requested listener
            listenerCls = listenerClasses.get(listener, type(listener))
            # if the same type as extant listener, return it rather than duplicating
            if isinstance(extantListener, listenerCls):
                return extantListener
        # make listener if needed
        if not isinstance(listener, lsnr.BaseListener):
            # if given a string rather than an object handle, make an object of correct type
            if listener == "liaison":
                from psychopy.hardware import DeviceManager
                if DeviceManager.liaison is None:
                    raise AttributeError(
                        "Cannot create a `liaison` listener as no liaison server is connected to DeviceManager."
                    )
                listener = lsnr.LiaisonListener(DeviceManager.liaison)
            elif listener in listenerClasses:
                listener = listenerClasses[listener]()
            else:
                raise ValueError(f"No known listener type '{listener}'")
        # add listener handle
        self.listeners.append(listener)
        # start loop if requested
        if startLoop:
            listener.startLoop(self)

        return listener

    def clearListeners(self):
        """
        Remove any listeners from this device.

        Returns
        -------
        bool
            True if completed successfully
        """
        # remove self from listener loop
        for listener in self.listeners:
            if self in listener.loop.devices:
                listener.loop.removeDevice(self)
        # clear list
        self.listeners = []

        return True

if __name__ == "__main__":
    pass
