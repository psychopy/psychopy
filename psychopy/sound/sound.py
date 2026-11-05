import importlib.metadata
from psychopy.preferences import prefs


class Sound:
    """
    Class for playing a sound in PsychoPy. See specific sound backends for details and methods for 
    implementations of Sound.
    """
    
    # selected backend
    backend = None
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
        backend = cls.resolveBackend()

        return backend.Sound(*args, **kwargs)

    @classmethod
    def resolveBackend(cls):
        """
        Get the module for the selected Sound backend, importing it if needed.

        Returns
        -------
        module
            The backend module (e.g. `psychopy.sound.backend_ptb`).
        """
        return cls.backends[cls.resolveBackendName()].load()

    @classmethod
    def resolveBackendName(cls):
        """
        Get the name of the selected Sound backend without importing it.

        The backend is taken from `Sound.backend` if set, otherwise from
        `prefs.hardware['audioLib']`. Aliases (e.g. 'psychtoolbox') are
        resolved to their canonical name (e.g. 'ptb').

        Returns
        -------
        str
            Name of the selected backend.
        """
        backend = cls.backend
        # if backend is None, get from prefs
        if backend is None:
            backend = prefs.hardware['audioLib']
        # handle list
        if isinstance(backend, (list, tuple)):
            try:
                # try to get the first valid backend
                backend = [
                    val for val in backend if val in cls.backends
                ][0]
            except IndexError:
                # otherwise get the first backend
                backend = backend[0]
        # if not present, error
        if backend not in cls.backends:
            raise ModuleNotFoundError(
                f"Invalid value '{backend}' for {cls.__name__}.backend, known backends are: {list(cls.backends)}"
            )

        # use the entry point name so aliases map to the canonical name
        return cls.backends[backend].name
    
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
