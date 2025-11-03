import importlib.metadata


class Sound:
    """
    Class for playing a sound in PsychoPy. See specific sound backends for details and methods for 
    implementations of Sound.
    """
    
    # name of the backend to use for Sound objects
    backend = "ptb"

    def __new__(cls, *args, **kwargs):
        # get backends
        backends = cls.getBackends()
        # if not present, error
        if cls.backend not in backends:
            raise ModuleNotFoundError(f"Invalid value '{cls.backend}' for Sound.backend, known backends are: {list(backends)}")
        # import backend
        backend = backends[cls.backend].load()
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
        # start off with builtin backends
        backends = {
            ep.name: ep for ep in [
                importlib.metadata.EntryPoint(
                    name="ptb", 
                    value="psychopy.sound.backend_ptb", 
                    group="psychopy.sound.backends"
                ),
                importlib.metadata.EntryPoint(
                    name="pygame", 
                    value="psychopy.sound.backend_pygame", 
                    group="psychopy.sound.backends"
                ),
                importlib.metadata.EntryPoint(
                    name="pysound", 
                    value="psychopy.sound.backend_pysound", 
                    group="psychopy.sound.backends"
                )
            ]
        }
        # get others from plugins
        for ep in importlib.metadata.entry_points(group="psychopy.sound.backends"):
            backends[ep.name] = ep
        
        return backends