def loadPluginRoutines():
    """
    Load relevant defs for any plugins with entry points in psychopy.experiment.routines, so that they
    are available to Builder.

    Returns
    -------
    list[str]
        List of names for all plugins loaded
    """
    from psychopy.plugins import _installed_plugins_
    import importlib
    # iterate through entry points
    imported = []
    for name, ep in _installed_plugins_.items():
        # get points for routines folder
        points = ep.get('psychopy.experiment.routines', {})
        # import package for each point
        for point in points.values():
            importlib.import_module(point.name, package=point.module_name)
        # if we did any importing, add plugin name to output
        if len(points):
            imported.append(name)

    return imported
