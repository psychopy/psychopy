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

