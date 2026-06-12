import importlib.metadata


class Sound:
    """
    Class for playing a sound in PsychoPy. See specific sound backends for details and methods for 
    implementations of Sound.
    """
    
    # selected backend
    backend = "sounddevice"
    # known backends
    backends = {
        'ptb': importlib.metadata.EntryPoint(
            name="ptb", 
            value="psychopy.sound.backend_ptb", 
            group="psychopy.sound.backends"
        ),
        'sounddevice': importlib.metadata.EntryPoint(
            name="sounddevice", 
            value="psychopy.sound.backend_sounddevice", 
            group="psychopy.sound.backends"
        )
    }
    # alias backend names
    backends['psychtoolbox'] = backends['ptb']
    backends['sd'] = backends['sounddevice']

    def __new__(cls, *args, **kwargs):
        # handle list
        if isinstance(cls.backend, (list, tuple)):
            try:
                # try to get the first valid backend
                cls.backend = [
                    val for val in cls.backend if val in cls.backends
                ][0]
            except:
                # otherwise get the first backend
                cls.backend = cls.backend[0]
        # if not present, error
        if cls.backend not in cls.backends:
            raise ModuleNotFoundError(
                f"Invalid value '{cls.backend}' for {cls.__name__}.backend, known backends are: {list(cls.backends)}"
            )
        # import backend
        backend = cls.backends[cls.backend].load()

        return backend.Sound(*args, **kwargs)
    
    @classmethod
    def getBackends(cls):
        """
        Get all available Sound backends (by name)

        Returns
        -------
        dict[str:importlib.metadata.EntryPoint]
            Dict mapping backend names to backend entry points - call `.load` on an entry point to 
            import the relevant module.
        """
        
        return cls.backends


# get sound backends from plugins
for ep in importlib.metadata.entry_points(group="psychopy.hardware.speaker.backends"):
    Sound.backends[ep.name] = ep
