import importlib.metadata


def getEntryPoints(module, submodules=True, flatten=True):
    """
    Get entry points which target a particular module.

    Parameters
    ----------
    module : str
        Import string for the target module (e.g.
        `"psychopy.iohub.devices"`)
    submodules : bool, optional
        If True, will also get entry points which target a
        submodule of the given module. By default True.
    flatten : bool, optional
        If True, will return a flat list of entry points. If
        False, will return a dict arranged by target group. By
        default True.
    """
    # start off with a blank list/dict
    entryPointsList = []
    entryPointsDict = {}
    # iterate through groups
    for group, points in importlib.metadata.entry_points().items():
        # does this group correspond to the requested module?
        if submodules:
            targeted = group.startswith(module)
        else:
            targeted = group == module
        # if group is targeted, add entry points
        if targeted:
            entryPointsList += points
            entryPointsDict[group] = points
    # return list or dict according to flatten arg
    if flatten:
        return entryPointsList
    else:
        return entryPointsDict


class PluginRequiredError(Exception):
    pass


class PluginStub:
    """
    Class to handle classes which have moved out to plugins.

    Example
    -------
    ```
    class NoiseStim(
        PluginStub, 
        plugin="psychopy-visionscience", 
        docsHome="https://psychopy.github.io/psychopy-visionscience",
        docsRef="builder/components/NoiseStimComponent"
    ):
    ```
    """

    def __init_subclass__(cls, plugin, docsHome, docsRef="/"):
        """
        Subclassing PluginStub will create documentation pointing to the new documentation for the replacement class.
        """
        # remove trailing / 
        while docsHome.endswith("/"):
            docsHome = docsHome[:-1]
        # if docsRef includes docsHome root, remove it
        if docsRef.startswith(docsHome):
            docsRef = docsRef[len(docsHome):]
        # make sure docsRef has a /
        if not docsRef.startswith("/"):
            docsRef = "/" + docsRef
        # make sure docsHome has a http(s)://
        if not (docsHome.startswith("http://") or docsHome.startswith("https://")):
            docsHome = "https://" + docsHome
        # store ref to plugin and docs link
        cls.plugin = plugin
        cls.docsHome = docsHome
        cls.docsRef = docsRef
        cls.docsLink = docsHome + docsRef
        # create doc string point to new location
        cls.__doc__ = (
            "`{mro} <{docsLink}>`_ is now located within the `{plugin} <{docsHome}>`_ plugin."
        ).format(
            mro=cls.__module__,
            plugin=plugin,
            docsHome=docsHome,
            docsLink=cls.docsLink
        )


    def __init__(self, *args, **kwargs):
        """
        When initialised, rather than creating an object, will log an error.
        """
        raise PluginRequiredError((
            "Support for `{mro}` is not available this session. Please install "
            "`{plugin}` and restart the session to enable support."
        ).format(
            mro=type(self).__module__,
            plugin=self.plugin,
        ))
