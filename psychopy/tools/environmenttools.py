def getFromNames(names, namespace):
    """
    Get a component, or any other object handle, from a string containing its variable name.

    Parameters
    ==========
    names : str, list or tuple
        String representing the name of a variable, or a list/tuple (or listlike string) of names.
    namespace : dict or None
        dict mapping names to values, if unsure just use `globals()`
    """
    # If listlike string, split into list
    if isinstance(names, str) and "," in names:
        # Strip perentheses
        if (
                (names.startswith("[") and names.endswith("]"))
                or (names.startswith("(") and names.endswith(")"))
        ):
            names = names[1:-1]
        # Split at commas
        namesList = []
        for thisName in names.split(","):
            # Strip spaces
            thisName = thisName.strip()
            # Strip quotes
            if (
                    (thisName.startswith('"') and thisName.endswith('"'))
                    or (thisName.startswith("'") and thisName.endswith("'"))
            ):
                thisName = thisName[1:-1]
            # Append
            namesList.append(thisName)
        names = namesList

    # If single name, put in list
    from collections.abc import Iterable
    if isinstance(names, str) or not isinstance(names, Iterable):
        names = [names]

    # Get objects
    objs = []
    for nm in names:
        # Strip spaces
        if isinstance(nm, str):
            nm = nm.strip()
        # Get (use original value if not present)
        obj = namespace.get(nm, nm)
        # Append
        objs.append(obj)

    return objs


def setExecEnvironment(env):
    # Get builtin exec function
    import builtins
    # Create new exec function in given environment
    def exec(call_str):
        builtins.exec(call_str, env)
    exec.__doc__ = builtins.exec.__doc__
    # Return function
    return exec