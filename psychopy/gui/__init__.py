import importlib
import sys


__all__ = [
    # functions for controlling which backend we're using
    "setBackend",
    "getBackend",
    # values for the actual module
    "Dlg",
    "MessageDlg",
    "fileSaveDlg",
    "fileOpenDlg",
]
# handle aliases for legacy functions
legacyAliases = {
    'DlgFromDict': ("Dlg", "fromDict"),
    'infoDlg': ("MessageDlg", "info"),
    'warnDlg': ("MessageDlg", "warn"),
    'criticalDlg': ("MessageDlg", "critical"),
    'aboutDlg': ("MessageDlg", "about"),
}
__all__ += list(legacyAliases)


_backend = None


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
    # get everything from __all__
    for name in __all__:
        # skip functions which are genuinely here
        if name in ("setBackend", "getBackend"):
            continue
        # skip legacy aliases (for now)
        if name in legacyAliases:
            continue
        # alias function
        globals()[name] = getattr(submod, name)
    # handle legacy aliases
    for name, mro in legacyAliases.items():
        # start off in globals
        target = globals()[mro[0]]
        # for any further levels, tunnel down
        for lvl in mro[1:]:
            target = getattr(target, lvl)
        # do aliasing
        globals()[name] = target

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
