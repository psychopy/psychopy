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