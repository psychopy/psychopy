import inspect
from pathlib import Path
from psychopy import logging
from psychopy.experiment.params import Param
from psychopy.localization import _translate


class DeviceMixin:
    """
    Mixin for base Component/Routine classes which adds necessary params and attributes to 
    interact with device manager. This shouldn't need to be mixed in directly - instead just use 
    BaseDeviceComponent or BaseDeviceRoutine which include this mixin.
    """
    
    def __init_subclass__(cls):
        cls.backends = set()
    
    def addDeviceParams(self, defaultLabel=""):
        from psychopy.preferences import prefs

        # require hardware
        self.exp.requirePsychopyLibs(
            ['hardware']
        )

        # --- Device params ---
        self.order += [
            "deviceLabel"
        ]
        # functions for getting device labels
        def getDevices():
            # start with default
            devices = [("", _translate("Default"))]
            # iterate through saved devices
            for name, device in prefs.devices.items():
                # iterate through backends for this Component
                for backend in self.backends:
                    # if device is the correct type, include it
                    if isinstance(device, backend):
                        devices.append(
                            (name, name)
                        )
            return devices
        def getLabels():
            return [device[1] for device in getDevices()]
        def getValues():
            return [device[0] for device in getDevices()]
        # label to refer to device by
        self.params['deviceLabel'] = Param(
            defaultLabel, valType="str", inputType="device", categ="Device",
            allowedVals=getValues,
            allowedLabels=getLabels,
            label=_translate("Device"),
            hint=_translate(
                "The named device from Device Manager to use for this Component."
            )
        )

    @classmethod
    def registerBackend(cls, backend):
        """
        Register a device backend as relevant to this Component.

        Parameters
        ----------
        backend : type
            Subclass of `psychopy.experiment.devices.DeviceBackend` to associate with this 
            Component.
        """
        if not hasattr(cls, "backends"):
            cls.backends = set()
        
        cls.backends.add(backend)


class DeviceBackend:
    """
    Representation of a hardware class in Builder.
    """
    # name of this backend to display in Device Manager
    backendLabel = None
    # icon to use for this backend (relative to current file path, leave as None for no icon)
    icon = None
    # class of the device which this backend corresponds to
    deviceClass = "psychopy.hardware.base.BaseDevice"
      
    def __init__(self, profile):
        # store device profile
        self.profile = profile
        # initialise params and order arrays
        self.params = {}
        self.order = []
        # add a param for the device label to all backends
        self.params['deviceLabel'] = Param(
            "", valType="str", inputType="name",
            label=_translate("Device label"),
            hint=_translate(
                "A name to refer to this device by in Device Manager."
            )
        )
        # device label always first
        self.order += [
            "deviceLabel"
        ]
        # get further params from subclass method
        params, order = self.getParams()
        self.params.update(params)
        self.order += order
    
    def __repr__(self):
        return (
            f"<{type(self).__name__}: name={self.name}>"
        )
    
    def getParams(self):
        """
        Get parameters from this backend to add to each new device from this backend.

        Returns
        -------
        dict[str:Param]
            Dict of Param objects for controlling devices in this backend
        list[str]
            List of param names, defining the order in which params should appear
        """
        return {}, []
    
    def writeDeviceCode(self, buff):
        """
        Write the code to create a device for this backend. This method must be overloaded by device backend subclasses.

        To write the basics of device initialisation, you can do: ::
            # this opens a call to DeviceManager.addDevice with the basic necessary arguments included, and does not close the brackets so you can add more
            self.writeBaseDeviceCode(buff, close=False)
            code = (
                # write any param-specific inits here (e.g. "threshold=%(threshold)s,\n")
                ")\n"
            )
            buff.writeIndentedLines
        
        To use just the basic device initialisation code, you can just do: ::
            return self.writeBaseDeviceCode(buff, close=True)
        """

        raise NotImplementedError()

    @classmethod
    def getIconFile(cls):
        """
        Get the file for this backend's icon as a Path, if there is one

        Returns
        -------
        Path or None
            File path for this backend's icon, or None if there is no icon
        """
        # return None if no icon
        if cls.icon is None:
            return
        # make sure it's a Path
        icon = cls.icon
        if isinstance(icon, str):
            icon = Path(icon)
        # get folder containing class def file
        folder = Path(inspect.getfile(cls)).parent
        # make absolute
        file = (folder / icon).resolve()

        return file
    
    @classmethod
    def fromJSON(cls, data):
        """
        Initialise an instance of this class from a JSON dict.

        Parameters
        ----------
        data : dict
            JSON data to initialise from
        """
        # initialise
        device = cls(
            profile=data['profile']
        )
        # apply param vals
        device.applyJSON(data)
        
        return device

    def applyJSON(self, data):
        """
        Apply data from a JSON dict to this object.

        Parameters
        ----------
        data : dict
            JSON data to apply
        """
        # get profile
        self.profile = data['profile']
        # apply param vals
        for name, val in data['params'].items():
            self.params[name].applyJSON(val)
    
    def toJSON(self):
        """
        Get this object as a JSON dict.

        Returns
        -------
        dict
            JSON dict representing this object, will be in the form:..

            {
                '__cls__': <import string for this class>,
                'profile': <dict from DeviceManager.getAvailableDevices>,
                'params': <dict of Param JSON objects>,
            }
        """
        # create dict
        data = {
            '__cls__': f"{type(self).__module__}.{type(self).__name__}",
            'profile': self.profile,
            'params': {}
        }
        # add params
        for key, param in self.params.items():
            data['params'][key] = param.toJSON()
        
        return data
    
    @staticmethod
    def getAllBackends():
        """
        Get all backends known to the current PsychoPy session.

        Returns
        -------
        list[type]
            List of backend classes
        """
        from psychopy.experiment import getAllElements
        allBackends = []
        for emt in getAllElements(fetchIcons=False).values():
            if hasattr(emt, "backends"):
                for backend in emt.backends:
                    if issubclass(backend, DeviceBackend) and backend not in allBackends:
                        allBackends.append(backend)
        
        return allBackends
        
    
    def writeBaseDeviceCode(self, buff, close=False):
        """
        Write the basic device code

        Parameters
        ----------
        buff : io.StringIO
            Buffer to write to
        close : bool, optional
            If False (default), won't close the `addDevice` call (so you need to write the closing 
            bracket yourself)
        """
        # write init call with device label
        code = (
            "# initialize %(deviceLabel)s\n"
            "deviceManager.addDevice(\n"
            "    deviceName='%(deviceLabel)s',\n"
        )
        buff.writeIndentedLines(code % self.params)
        # add options from profile
        code = ""
        for key, value in self.profile.items():
            # skip attributes already covered by a param
            if key in ("deviceName",):
                continue
            code += f"    {key}={repr(value)},\n"
        buff.writeIndentedLines(code)
        # if close requested, add closing bracket
        if close:
            code = (
                ")\n"
            )
            buff.writeIndentedLines(code)
      
    @property
    def name(self):
        return self.params['deviceLabel'].val
    
    @name.setter
    def name(self, value):
        # update param value
        self.params['deviceLabel'].val = value
        
