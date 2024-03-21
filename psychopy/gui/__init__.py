import importlib
import sys


__all__ = [
    # functions for controlling which backend we're using
    "setBackend",
    "getBackend"
    # values for the actual module
    "Dlg",
    "DlgFromDict"
]


_backend = None
Dlg = DlgFromDict = None


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
    submod = importlib.import_module("." + name, package="psychopy.gui")
    # get Dialog class
    global Dlg
    Dlg = submod.Dlg
    # legacy dialog from dict method
    global DlgFromDict
    DlgFromDict = Dlg.fromDict
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
    ("wx", "wxgui"),
    ("PyQt5", "qtgui"),
    ("PyQt6", "qtgui"),
]:
    if moduleName in sys.modules:
        setBackend(backendName)
        _found = True
# if nothing is imported, set backend according to what's installed (prioritise qt)
if not _found:
    for moduleName, backendName in [
        ("wx", "wxgui"),
        ("PyQt5", "qtgui"),
        ("PyQt6", "qtgui"),
    ]:
        try:
            importlib.import_module(moduleName)
        except ModuleNotFoundError:
            pass
        else:
            setBackend(backendName)
            _found = True
