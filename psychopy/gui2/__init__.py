import importlib
import sys


__all__ = [
    # functions for controlling which backend we're using
    "setBackend",
    "getBackend"
    # values for the actual module
    "Dialog"
]


_backend = None
Dialog = None


def setBackend(name):
    """
    Set the backend for psychopy.gui to use.

    Parameters
    ----------
    name : str
        Name of the backend, should match the backend module name. One of:
        - "wx"
        - "qt"
    """
    # import submodule by name
    submod = importlib.import_module("." + name, package="psychopy.gui2")
    # get Dialog class
    global Dialog
    Dialog = submod.Dialog
    # store value
    global _backend
    _backend = name


def getBackend():
    """
    Get the backend currently used by psychopy.gui.

    Returns
    -------
    str
        Name of the backend, should match the backend module name. One of:
        - "wx"
        - "qt"
    """
    return _backend


_found = False
# set backend according to what's imported (prioritise wx)
for moduleName, backendName in [
    ("wx", "wx"),
    ("PyQt5", "qt"),
    ("PyQt6", "qt"),
]:
    if moduleName in sys.modules:
        setBackend(backendName)
        _found = True
# if nothing is imported, set backend according to what's installed (prioritise qt)
if not _found:
    for moduleName, backendName in [
        ("wx", "wx"),
        ("PyQt4", "qt"),
        ("PyQt5", "qt"),
        ("PyQt6", "qt"),
    ]:
        try:
            importlib.import_module(moduleName)
        except ModuleNotFoundError:
            pass
        else:
            setBackend(backendName)
            _found = True
