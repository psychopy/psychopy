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
    if flatten:
        output = []
    else:
        output = {}
    # handle difference between importlib.metadata 5.0 and previous versions
    all = importlib.metadata.entry_points()
    if isinstance(all, dict):
        groups = list(all)
    else:
        groups = all.groups
    # filter groups
    if submodules:
        groups = [group for group in groups if group.startswith(module)]
    else:
        groups = [group for group in groups if group == module]
    # get points for each group
    for group in groups:
        points = importlib.metadata.entry_points(group=group)
        # append to output
        if flatten:
            output += points
        else:
            output[group] = points

    return output


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
