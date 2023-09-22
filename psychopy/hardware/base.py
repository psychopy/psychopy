import inspect


class BaseDevice:
    def __new__(cls, *args, **kwargs):
        from .manager import mgr
        # put all args in one dict
        argNames = list(inspect.signature(cls.__init__).parameters)[1:]
        params = kwargs.copy()
        for i, arg in args:
            params[argNames[i]] = arg
        # check that this device doesn't already exist
        for device in mgr:
            # if they're a different class, they're definitely not the same device
            if not isinstance(device, cls):
                continue
            # use own class's comparison method to determine same device
            if device.isSameDevice(params):
                # if same device, return it rather than making a new object
                return device

        # if we got this far, it's a new device, continue as normal
        obj = object.__new__(cls)
        mgr.registerDevice(obj)
        return obj

    def isSameDevice(self, params):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


def deviceWrapper(deviceCls):
    def _decorator(cls):
        # docs
        cls.__docs__ = (
            f"Wrapper around {deviceCls.__name__} so that multiple objects can exist for the same physical device."
        )

        # alias init function of device
        def initAlias(self, *args, **kwargs):
            self.device = deviceCls(*args, **kwargs)
        cls.__init__ = initAlias
        # alias all methods of device
        for methodName in deviceCls.__dict__:
            # get method
            meth = getattr(deviceCls, methodName)
            # skip non-methods
            if not inspect.isfunction(meth):
                continue
            # skip private methods
            if methodName.startswith("_"):
                continue

            # create alias method
            def methodAlias(self, *args, **kwargs):
                return meth(self.device, *args, **kwargs)
            # assign alias method
            setattr(cls, methodName, methodAlias)

        return cls

    return _decorator


