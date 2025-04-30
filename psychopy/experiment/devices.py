from psychopy import logging
from psychopy.experiment.params import Param
from psychopy.localization import _translate


class DeviceBackend:
    """
    Representation of a hardware class in Builder.
    """
    # name of this backend to display in Device Manager
    backendName = None
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
    
    def __repr__(self):
        return (
            f"<{type(self).__name__}: name={self.name}>"
        )
    
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
            "    deviceName=%(deviceLabel)s,\n"
        )
        buff.writeIndentedLines(code % self.params)
        # add options from profile
        code = ""
        for key, value in self.profile.items():
            code += f"{key}={value},\n"
        buff.writeIndentedLines(code)
        # if close requested, add closing bracket
        if close:
            code = (
                ")\n"
            )
            buff.writeIndentedLines(code)

    def writeDeviceCode(self, buff):
        """
        Write the code to create a device for this backend
        """
        return self.writeBaseDeviceCode(buff, close=True)
      
    @property
    def name(self):
        print("NAME", self.params['deviceLabel'].val)
        return self.params['deviceLabel'].val
    
    @name.setter
    def name(self, value):
        # update param value
        self.params['deviceLabel'].val = value
        
