class PluginDevicesMixin:
    """
    Mixin for Components and Routines which adds behaviour to get parameters and values from
    plugins and use them to create different devices for different plugin backends.
    """

    def __init_subclass__(cls):
        # list of backends for this component - each should be a subclass of DeviceBackend
        cls.backends = []

    def loadBackends(self):
        # add params from backends
        for backend in self.backends:
            # get params using backend's method
            params, order = backend.getParams(self)
            # get reference to package
            plugin = None
            if hasattr(backend, "__module__") and backend.__module__:
                pkg = backend.__module__.split(".")[0]
                if pkg != "psychopy":
                    plugin = pkg
            # add order
            self.order.extend(order)
            # add any params
            for key, param in params.items():
                if key in self.params:
                    # if this param already exists (i.e. from saved data), get the saved val
                    param.val = self.params[key].val
                    param.updates = self.params[key].updates
                # add param
                self.params[key] = param
                # store plugin reference
                self.params[key].plugin = plugin
                print("PARAM:", key, "PLUGIN:", plugin)

            # add dependencies so that backend params are only shown for this backend
            for name in params:
                self.depends.append(
                    {
                        "dependsOn": "deviceBackend",  # if...
                        "condition": f"== '{backend.key}'",  # meets...
                        "param": name,  # then...
                        "true": "show",  # should...
                        "false": "hide",  # otherwise...
                    }
                )
            # add requirements
            backend.addRequirements(self)

    def getBackendKeys(self):
        keys = []
        for backend in self.backends:
            keys.append(backend.key)

        return keys

    def getBackendLabels(self):
        labels = []
        for backend in self.backends:
            labels.append(backend.label)

        return labels

    def writeDeviceCode(self, buff):
        # write init code from backend
        for backend in self.backends:
            if backend.key == self.params['deviceBackend']:
                backend.writeDeviceCode(self, buff)


class DeviceBackend:
    # which component is this backend for?
    component = PluginDevicesMixin
    # what value should Builder use for this backend?
    key = ""
    # what label should be displayed by Builder for this backend?
    label = ""
    # values to append to the component's deviceClasses array
    deviceClasses = []

    def __init_subclass__(cls):
        # add class to list of backends for ButtonBoxComponent
        cls.component.backends = cls.component.backends.copy()
        cls.component.backends.append(cls)
        # add device classes to component
        if cls is not PluginDevicesMixin and hasattr(cls.component, "deviceClasses"):
            for deviceClass in cls.deviceClasses:
                if deviceClass not in cls.component.deviceClasses:
                    cls.component.deviceClasses = cls.component.deviceClasses.copy()
                    cls.component.deviceClasses.append(deviceClass)

    def getParams(self):
        """
        Get parameters from this backend to add to each new instance of ButtonBoxComponent

        Returns
        -------
        dict[str:Param]
            Dict of Param objects, which will be added to any Button Box Component's params, along
            with a dependency to only show them when this backend is selected
        list[str]
            List of param names, defining the order in which params should appear
        """
        raise NotImplementedError()

    def addRequirements(self):
        """
        Add any required module/package imports for this backend
        """
        raise NotImplementedError()

    def writeDeviceCode(self, buff):
        """
        Write the code to create a device for this backend
        """
        raise NotImplementedError()
