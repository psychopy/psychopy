#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
"""Utilities for extending PsychoPy with plugins."""

from __future__ import absolute_import

__all__ = [
    'loadPlugin',
    'listPlugins',
    'computeChecksum',
    'startUpPlugins',
    'pluginMetadata',
    'pluginEntryPoints',
    'scanPlugins',
    'requirePlugin',
    'isPluginLoaded',
    'isStartUpPlugin',
    'registerAttribute']

# ------------------------------------------------------------------------------
# Imports
#

import os
import sys
import inspect
import collections
import hashlib
import importlib
import pkg_resources
import pluginbase
import psychopy.app as app
import zipfile
import tempfile

from psychopy import logging
from psychopy.preferences import prefs
import psychopy.experiment.components as components

# ------------------------------------------------------------------------------
# Module constants
#

# package dotted path which loaded plugins appear
PLUGIN_PACKAGE = 'psychopy.plugins'
# prefix for temporary directories for plugins extracted from Zip files
PLUGIN_TEMP_FILE_PREFIX = 'psychopy_plugin'
# Keep track of plugins that have been loaded. Keys are plugin names and values
# are their entry point mappings.
_loaded_plugins_ = collections.OrderedDict()
# Entry points for all plugins installed on the system, this is populated by
# calling `scanPlugins`. We are caching entry points to avoid having to rescan
# packages for them.
_installed_plugins_ = list()
# Keep track of plugins that failed to load here
_failed_plugins_ = list()
# Initialize the `PluginBase` plugin manager. Specify the dotted path where our
# plugins will appear to the user as `package`.
_plugin_base_ = pluginbase.PluginBase(package=PLUGIN_PACKAGE)
# _plugin_paths_ = _plugin_source_ = None  # defined below


# ------------------------------------------------------------------------------
# Helper functions
#

def _getPluginSearchPaths():
    """Get a list of search paths for plugins.

    This function gets the value of 'Preferences > General > pluginPaths' and
    checks if the specified paths are valid. If so, each directory is scanned
    for sub-folders and zip files (only one level deep) and added to the list of
    paths to be returned. Any zip files which are found will be extracted to
    temporary directories automatically.

    Returns
    -------
    list
        List of strings representing paths to plugins.

    """
    # Specify the directories where the plugins are stored on the system.
    pluginPaths = list()
    try:
        # load the plugin path from user prefs
        pluginPaths = list(prefs.general['pluginPaths'])
    except KeyError:
        logging.error(
            'Preferences does not have key `pluginPaths`! Plugins unavailable.')

    # Check the preference value for empty strings and invalid paths, just flag
    # either issue with `None` to avoid resizing the array during iteration
    INVALID_PLUGIN_PATH = object()  # flag for invalid paths
    for i, val in enumerate(pluginPaths):
        # remove empty values, flag them if found
        if val == '':
            pluginPaths[i] = INVALID_PLUGIN_PATH
            continue

        # make sure directory exists, flag invalid is so
        absPath = os.path.abspath(val)
        if not os.path.isdir(absPath):
            logging.error('Invalid plugin path specified. Ignoring.')
            pluginPaths[i] = INVALID_PLUGIN_PATH
            continue

        pluginPaths[i] = absPath  # set full path

    # remove invalid paths
    pluginPaths = [p for p in pluginPaths if p is not INVALID_PLUGIN_PATH]

    # scan for top-level folders in plugin directories
    pluginPathsDeep = []
    for _dir in pluginPaths:
        items = os.listdir(_dir)
        for item in items:
            absPath = os.path.join(_dir, item)
            # ZIP archives can be used as plugin packages, we extract them to a
            # temp directory and load them.
            if zipfile.is_zipfile(absPath):
                fileName = item.split('.')[0]  # remove ext
                tempPluginDir = tempfile.mkdtemp(
                    suffix=None,
                    prefix=PLUGIN_TEMP_FILE_PREFIX + '-' + fileName + '-')
                with zipfile.ZipFile(absPath, 'r') as zipFile:
                    zipFile.extractall(tempPluginDir)

                # tell the user we extracted a zip file
                msg = ("Found zip file in plugin directory, extracted contents "
                       "to temporary directory `{}`".format(tempPluginDir))
                logging.debug(msg)

                # add temp dir to search path for plugins
                absPath = tempPluginDir

            # ignore if not a directory
            if not os.path.isdir(absPath):
                continue

            # tell the user we extracted a zip file
            msg = ("Added plugin search path `{}`".format(absPath))
            logging.debug(msg)

            pluginPathsDeep.append(absPath)

    return pluginPaths + pluginPathsDeep


# Specify the directories where the plugins are stored on the system.
_plugin_paths_ = _getPluginSearchPaths()
_plugin_source_ = _plugin_base_.make_plugin_source(searchpath=_plugin_paths_)


def resolveObjectFromName(name, basename=None, resolve=True, error=True):
    """Get an object within a module's namespace using a fully-qualified or
    relative dotted name.

    This function is mainly used to get objects associated with entry point
    groups, so entry points can be assigned to them. It traverses through
    objects along `name` until it reaches the end, then returns a reference to
    that object.

    You can also use this function to dynamically import modules and fully
    realize target names without needing to call ``import`` on intermediate
    modules. For instance, by calling the following::

        Window = resolveObjectFromName('psychopy.visual.Window')

    The function will first import `psychopy.visual` then get a reference to the
    unbound `Window` class within it and assign it to `Window`.

    Parameters
    ----------
    name : str
        Fully-qualified or relative name to the object (eg.
        `psychopy.visual.Window` or `.Window`). If name is relative, `basename`
        must be specified.
    basename : str, ModuleType or None
        If `name` is relative (starts with '.'), `basename` should be the
        `__name__` of the module or reference to the module itself `name` is
        relative to. Leave `None` if `name` is already fully qualified.
    resolve : bool
        If `resolve=True`, any name encountered along the way that isn't present
        will be assumed to be a module and imported. This guarantees the target
        object is fully-realized and reachable if the target is valid. If
        `False`, this function will fail if the `name` is not reachable and
        raise an error or return `None` if `error=False`.
    error : bool
        Raise an error if an object is not reachable. If `False`, this function
        will return `None` instead and suppress the error. This may be useful in
        cases where having access to the target object is a "soft" requirement
        and the program can still operate without it.

    Returns
    -------
    object
        Object referred to by the name. Returns `None` if the object is not
        reachable and `error=False`.

    Raises
    ------
    ModuleNotFoundError
        The base module the FQN is referring to has not been imported.
    NameError
        The provided name does not point to a valid object.
    ValueError
        A relative name was given to `name` but `basename` was not specified.

    Examples
    --------
    Get a reference to the `psychopy.visual.Window` class (will import `visual`
    in doing so)::

        Window = resolveObjectFromName('psychopy.visual.Window')

    Get the `Window` class if `name` is relative to `basename`::

        import psychopy.visual as visual
        Window = resolveObjectFromName('.Window', visual)

    Check if an object exists::

        Window = resolveObjectFromName(
            'psychopy.visual.Window',
            resolve=False,  # False since we don't want to import anything
            error=False)  # suppress error, makes function return None

        if Window is None:
            print('Window has not been imported yet!')

    """
    # make sure a basename is given if relative
    if name.startswith('.') and basename is None:
        raise ValueError('`name` specifies a relative name but `basename` is '
                         'not specified.')

    # if basename is a module object
    if inspect.ismodule(basename):
        basename = basename.__name__

    # get fqn and split
    fqn = (basename + name if basename is not None else name).split(".")

    # get the object the fqn refers to
    try:
        objref = sys.modules[fqn[0]]  # base name
    except KeyError:
        raise ModuleNotFoundError(
            'Base module cannot be found, has it been imported yet?')

    # walk through the FQN to get the object it refers to
    path = fqn[0]
    for attr in fqn[1:]:
        path += '.' + attr
        if not hasattr(objref, attr):
            # try importing the module
            if resolve:
                try:
                    importlib.import_module(path)
                except ImportError:
                    if not error:  # return if suppressing error
                        return None
                    raise NameError(
                        "Specified `name` does not reference a valid object or "
                        "is unreachable.")
            else:
                if not error:  # return None if we want to suppress errors
                    return None
                raise NameError(
                    "Specified `name` does not reference a valid object or is "
                    "unreachable.")

        objref = getattr(objref, attr)

    return objref


def computeChecksum(fpath, method='sha256', writeOut=None):
    """Compute the checksum hash/key for a given package.

    Authors of PsychoPy plugins can use this function to compute a checksum
    hash and users can use it to check the integrity of their packages.

    Parameters
    ----------
    fpath : str
        Path to the plugin package or file.
    method : str
        Hashing method to use, values are 'md5' or 'sha256'. Default is
        'sha256'.
    writeOut : str
        Path to a text file to write checksum data to. If the file exists, the
        data will be written as a line at the end of the file.

    Returns
    -------
    str
        Checksum hash digested to hexadecimal format.

    Examples
    --------
    Compute a checksum for a package and write it to a file::

        with open('checksum.txt', 'w') as f:
            f.write(computeChecksum(
                '/path/to/plugin/psychopy_plugin-1.0-py3.6.egg'))

    """
    methodObj = {'md5': hashlib.md5,
                 'sha256': hashlib.sha256}

    hashobj = methodObj[method]()
    with open(fpath, "rb") as f:
        chunk = f.read(4096)
        while chunk != b"":
            chunk = f.read(4096)
            hashobj.update(chunk)

    checksumStr = hashobj.hexdigest()

    if writeOut is not None:
        with open(writeOut, 'a') as f:
            f.write('\n' + checksumStr)

    return checksumStr


# ------------------------------------------------------------------------------
# User classes and functions
#

def scanPlugins():
    """Scan the system for installed plugins.

    This function scans installed packages for the current Python environment
    and looks for ones that specify PsychoPy entry points in their metadata.
    Afterwards, you can call :func:`listPlugins()` to list them and
    :func:`loadPlugin()` to load them into the current session. This function is
    called automatically when this module is imported, so you do not need to
    call this unless packages have been added since the session began.

    Returns
    -------
    tuple
        Found plugin names.

    Examples
    --------
    Scan for plugins and get the number found on the system::

        num_plugins_found = len(scanPlugins())

    """
    global _plugin_paths_
    global _plugin_source_
    global _installed_plugins_

    _plugin_paths_ = _getPluginSearchPaths()  # get the paths

    # check if there are plugin paths specified
    if not _plugin_paths_:
        logging.info('No plugin paths specified.')

    _plugin_source_ = _plugin_base_.make_plugin_source(
        searchpath=_plugin_paths_)

    # find all packages with entry points defined
    _installed_plugins_ = _plugin_source_.list_plugins()

    return tuple(_installed_plugins_)  # prevents the user from modifying this


def listPlugins(which='all'):
    """Get a list of installed or loaded PsychoPy plugins.

    This function lists either all potential plugin packages installed on the
    system, those registered to be loaded automatically when PsychoPy starts, or
    those that have been previously loaded successfully this session.

    Parameters
    ----------
    which : str
        Category to list plugins. If 'all', all plugins installed on the system
        will be listed, whether they have been loaded or not. If 'loaded', only
        plugins that have been previously loaded successfully this session will
        be listed. If 'startup', plugins registered to be loaded when a PsychoPy
        session starts will be listed, whether or not they have been loaded this
        session. If 'unloaded', plugins that have not been loaded but are
        installed will be listed. If 'failed', returns a list of plugin names
        that attempted to load this session but failed for some reason.

    Returns
    -------
    list
        Names of PsychoPy related plugins as strings. You can load all installed
        plugins by passing list elements to `loadPlugin`.

    See Also
    --------
    loadPlugin : Load a plugin into the current session.

    Examples
    --------
    Load all plugins installed on the system into the current session (assumes
    all plugins don't require any additional arguments passed to them)::

        for plugin in plugins.listPlugins():
            plugins.loadPlugin(plugin)

    If certain plugins take arguments, you can do this give specific arguments
    when loading all plugins::

        pluginArgs = {'some-plugin': (('someArg',), {'setup': True, 'spam': 10})}
        for plugin in plugins.listPlugins():
            try:
                args, kwargs = pluginArgs[plugin]
                plugins.loadPlugin(plugin, *args, **kwargs)
            except KeyError:
                plugins.loadPlugin(plugin)

    Check if a plugin package named `plugin-test` is installed on the system and
    has entry points into PsychoPy::

        if 'plugin-test' in plugins.listPlugins():
            print("Plugin installed!")

    Check if all plugins registered to be loaded on startup are currently
    active::

        if not all([p in listPlugins('loaded') for p in listPlugins('startup')]):
            print('Please restart your PsychoPy session for plugins to take effect.')

    """
    if which not in ('all', 'startup', 'loaded', 'unloaded', 'failed'):
        raise ValueError("Invalid value specified to argument `which`.")

    if which == 'loaded':  # only list plugins we have already loaded
        return list(_loaded_plugins_.keys())
    elif which == 'startup':
        return list(prefs.general['startUpPlugins'])  # copy this
    elif which == 'unloaded':
        return [p for p in listPlugins('all') if p in listPlugins('loaded')]
    elif which == 'failed':
        return list(_failed_plugins_)  # copy
    else:
        return _installed_plugins_


def isPluginLoaded(plugin):
    """Check if a plugin has been previously loaded successfully by a
    :func:`loadPlugin` call.

    Parameters
    ----------
    plugin : str
        Name of the plugin package to check if loaded. This usually refers to
        the package or project name.

    Returns
    -------
    bool
        `True` if a plugin was successfully loaded and active, else `False`.

    See Also
    --------
    loadPlugin : Load a plugin into the current session.

    """
    return plugin in listPlugins(which='loaded')


def isStartUpPlugin(plugin):
    """Check if a plugin is registered to be loaded when PsychoPy starts.

    Parameters
    ----------
    plugin : str
        Name of the plugin package to check. This usually refers to the package
        or project name.

    Returns
    -------
    bool
        `True` if a plugin is registered to be loaded when a PsychoPy session
        starts, else `False`.

    Examples
    --------
    Check if a plugin was loaded successfully at startup::

        pluginName = 'psychopy-plugin'
        if isStartUpPlugin(pluginName) and isPluginLoaded(pluginName):
            print('Plugin successfully loaded at startup.')

    """
    return plugin in listPlugins(which='startup')


def loadPlugin(pluginName, *args, **kwargs):
    """Load a plugin to extend PsychoPy.

    Plugins are packages which extend upon PsychoPy's existing functionality by
    dynamically importing code at runtime, without modifying the existing
    installation files. Plugins create or redefine objects in the namespaces
    of modules (eg. `psychopy.visual`) and unbound classes, allowing them to be
    used as if they were part of PsychoPy. In some cases, objects exported by
    plugins will be registered for a particular function if they define entry
    points into specific modules.

    Parameters
    ----------
    pluginName : str
        Name of the plugin package to load. This usually refers to the package
        or project name.
    *args, **kwargs
        Optional arguments and keyword arguments to pass to the plugin's
        `setup_plugin()` function.

    Returns
    -------
    bool
        `True` if the plugin has valid entry points and was loaded successfully.
        Also returns `True` if the plugin was already loaded by a previous
        `loadPlugin` call this session, this function will have no effect in
        this case. `False` is returned if the plugin defines no entry points
        specific to PsychoPy or crashed (an error is logged).

    Warnings
    --------
    Make sure that plugins installed on your system are from reputable sources,
    as they may contain malware! PsychoPy is not responsible for undefined
    behaviour or bugs associated with the use of 3rd party plugins.

    See Also
    --------
    listPlugins : Search for and list installed or loaded plugins.
    requirePlugin : Require a plugin be previously loaded.

    Examples
    --------
    Load a plugin by specifying its package/project name::

        loadPlugin('psychopy-hardware-box')

    You can give arguments to this function which are passed on to the plugin::

        loadPlugin('psychopy-hardware-box', switchOn=True, baudrate=9600)

    You can use the value returned from `loadPlugin` to determine if the plugin
    is installed and supported by the platform::

        hasPlugin = loadPlugin('psychopy-hardware-box')
        if hasPlugin:
            # initialize objects which require the plugin here ...

    """
    global _plugin_source_
    global _loaded_plugins_

    # check if the plugin was already loaded
    if pluginName in _loaded_plugins_.keys():
        raise NameError(
            "Plugin with name '{}' already loaded.".format(pluginName))

    # load the plugin
    plugin_obj = _plugin_source_.load_plugin(pluginName)

    # check if there is a `setup()` function in the loaded plugin, this is used
    # to setup 'hooks' into PsychoPy.
    result = True
    if hasattr(plugin_obj, 'setup_plugin'):
        app_instance = app.getAppInstance()
        result = plugin_obj.setup_plugin(app_instance, *args, **kwargs)

    if result:
        _loaded_plugins_[pluginName] = plugin_obj

    return result


def requirePlugin(plugin):
    """Require a plugin to be already loaded.

    This function can be used to ensure if a plugin has already been loaded and
    is ready for use, raising an exception and ending the session if not.

    This function compliments :func:`loadPlugin`, which does not halt the
    application if plugin fails to load. This allows PsychoPy to continue
    working, giving the user a chance to deal with the problem (either by
    disabling or fixing the plugins). However, :func:`requirePlugin` can be used
    to guard against undefined behavior caused by a failed or partially loaded
    plugin by raising an exception before any code that uses the plugin's
    features is executed.

    Parameters
    ----------
    plugin : str
        Name of the plugin package to require. This usually refers to the package
        or project name.

    Raises
    ------
    RuntimeError
        Plugin has not been previously loaded this session.

    See Also
    --------
    loadPlugin : Load a plugin into the current session.

    Examples
    --------
    Ensure plugin `psychopy-plugin` is loaded at this point in the session::

        requirePlugin('psychopy-plugin')  # error if not loaded

    You can catch the error and try to handle the situation by::

        try:
            requirePlugin('psychopy-plugin')
        except RuntimeError:
            # do something about it ...

    """
    if not isPluginLoaded(plugin):
        raise RuntimeError('Required plugin `{}` has not been loaded.')


def startUpPlugins(plugins, add=True, verify=True):
    """Specify which plugins should be loaded automatically when a PsychoPy
    session starts.

    This function edits ``psychopy.preferences.prefs.general['startUpPlugins']``
    and provides a means to verify if entries are valid. The PsychoPy session
    must be restarted for the plugins specified to take effect.

    If using PsychoPy as a library, this function serves as a convenience to
    avoid needing to explicitly call :func:`loadPlugin` every time to use your
    favorite plugins.

    Parameters
    ----------
    plugins : `str`, `list` or `None`
        Name(s) of plugins to have load on startup.
    add : bool
        If `True` names of plugins will be appended to `startUpPlugins` unless a
        name is already present. If `False`, `startUpPlugins` will be set to
        `plugins`, overwriting the previous value. If `add=False` and
        `plugins=[]` or `plugins=None`, no plugins will be loaded in the next
        session.
    verify : bool
        Check if `plugins` are installed and have valid entry points to
        PsychoPy. Raises an error if any are not. This prevents undefined
        behavior arsing from invalid plugins being loaded in the next session.
        If `False`, plugin names will be added regardless if they are installed
        or not.

    Raises
    ------
    RuntimeError
        If `verify=True`, any of `plugins` is not installed or does not have
        entry points to PsychoPy. This is raised to prevent issues in future
        sessions where invalid plugins are written to the config file and are
        automatically loaded.

    Warnings
    --------
    Do not use this function within the builder or coder GUI! Use the plugin
    dialog to specify which plugins to load on startup. Only use this function
    when using PsychoPy as a library!

    Examples
    --------
    Adding plugins to load on startup::

        startUpPlugins(['plugin1', 'plugin2'])

    Clearing the startup plugins list, no plugins will be loaded automatically
    at the start of the next session::

        plugins.startUpPlugins([], add=False)
        # or ..
        plugins.startUpPlugins(None, add=False)

    If passing `None` or an empty list with `add=True`, the present value of
    `prefs.general['startUpPlugins']` will remain as-is.

    """
    # check if there is a config entry
    if 'startUpPlugins' not in prefs.general.keys():
        logging.warning(
            'Config file does not define `startUpPlugins`. Skipping.')

        return

    # if a string is specified
    if isinstance(plugins, str):
        plugins = [plugins]

    # if the list is empty or None, just clear
    if not plugins or plugins is None:
        if not add:  # adding nothing gives the original
            prefs.general['startUpPlugins'] = []
            prefs.saveUserPrefs()

        return

    # check if the plugins are installed before adding to `startUpPlugins`
    installedPlugins = listPlugins()
    if verify:
        notInstalled = [plugin not in installedPlugins for plugin in plugins]
        if any(notInstalled):
            missingIdx = [i for i, x in enumerate(notInstalled) if x]
            errStr = ''  # build up an error string
            for i, idx in enumerate(missingIdx):
                if i < len(missingIdx) - 1:
                    errStr += '`{}`, '.format(plugins[idx])
                else:
                    errStr += '`{}`;'.format(plugins[idx])

            raise RuntimeError(
                "Cannot add startup plugin(s): {} either not installed or has "
                "no PsychoPy entry points.".format(errStr))

    if add:  # adding plugin names to existing list
        for plugin in plugins:
            if plugin not in prefs.general['startUpPlugins']:
                prefs.general['startUpPlugins'].append(plugin)
    else:
        prefs.general['startUpPlugins'] = plugins  # overwrite

    prefs.saveUserPrefs()  # save after loading


def pluginMetadata(plugin):
    """Get metadata from a plugin package.

    Reads the package's PKG_INFO and gets fields as a dictionary. Only packages
    that have valid entry points to PsychoPy can be queried.

    Parameters
    ----------
    plugin : str
        Name of the plugin package to retrieve metadata from.

    Returns
    -------
    dict
        Metadata fields.

    """
    installedPlugins = listPlugins()
    if plugin not in installedPlugins:
        raise ModuleNotFoundError(
            "Plugin `{}` is not installed or does not have entry points for "
            "PsychoPy.".format(plugin))

    pkg = pkg_resources.get_distribution(plugin)
    metadata = pkg.get_metadata(pkg.PKG_INFO)

    metadict = {}
    for line in metadata.split('\n'):
        if not line:
            continue

        line = line.strip().split(': ')
        if len(line) == 2:
            field, value = line
            metadict[field] = value

    return metadict


def pluginEntryPoints(plugin, parse=False):
    """Get the entry point mapping for a specified plugin.

    You must call `scanPlugins` before calling this function to get the entry
    points for a given plugin.

    Note this function is intended for internal use by the PsychoPy plugin
    system only.

    Parameters
    ----------
    plugin : str
        Name of the plugin package to get advertised entry points.
    parse : bool
        Parse the entry point specifiers and convert them to fully-qualified
        names.

    Returns
    -------
    dict
        Dictionary of target groups/attributes and entry points objects.

    """
    global _installed_plugins_
    if plugin in _installed_plugins_.keys():
        if not parse:
            return _installed_plugins_[plugin]
        else:
            toReturn = {}
            for group, val in _installed_plugins_[plugin].items():
                if group not in toReturn.keys():
                    toReturn[group] = {}  # create a new group entry

                for attr, ep in val.items():
                    # parse the entry point specifier
                    ex = '.'.join(str(ep).split(' = ')[1].split(':'))  # make fqn
                    toReturn[group].update({attr: ex})

            return toReturn

    logging.error("Cannot retrieve entry points for plugin `{}`, either not "
                  " installed or reachable.")

    return None


def registerAttribute(fqn, name, obj):
    """Register a specified object to an attribute name somewhere in PsychoPy's
    namespace.

    Parameters
    ----------
    fqn : str
        Fully-qualified name (e.g., `psychopy.visual.Window`) to a module or
        class.
    name : str
        Attribute name to set.
    obj : object
        Reference to an object.

    """
    target = resolveObjectFromName(fqn, basename=None, resolve=True, error=True)
    setattr(target, name, obj)


def _registerWindowBackend(attr, ep):
    """Make an entry point discoverable as a window backend.

    This allows it the given entry point to be used as a window backend by
    specifying `winType`. All window backends must be subclasses of `BaseBackend`
    and define a `winTypeName` attribute. The value of `winTypeName` will be
    used for selecting `winType`.

    This function is called by :func:`loadPlugin`, it should not be used for any
    other purpose.

    Parameters
    ----------
    attr : str
        Attribute name the backend is being assigned in
        'psychopy.visual.backends'.
    ep : ModuleType of ClassType
        Entry point which defines an object with window backends. Can be a class
        or module. If a module, the module will be scanned for subclasses of
        `BaseBackend` and they will be added as backends.

    """
    # get reference to the backend class
    fqn = 'psychopy.visual.backends'
    backend = resolveObjectFromName(
        fqn, resolve=(fqn not in sys.modules), error=False)

    if backend is None:
        logging.error("Failed to resolve name `{}`.".format(fqn))
        return   # something weird happened, just exit

    # if a module, scan it for valid backends
    foundBackends = {}
    if inspect.ismodule(ep):  # if the backend is a module
        for attrName in dir(ep):
            _attr = getattr(ep, attrName)
            if not inspect.isclass(_attr):  # skip if not class
                continue
            if not issubclass(_attr, backend.BaseBackend):  # not backend
                continue
            # check if the class defines a name for `winType`
            if not hasattr(_attr, 'winTypeName'):  # has no backend name
                continue
            # found something that can be a backend
            foundBackends[_attr.winTypeName] = '.' + attr + '.' + attrName
            logging.debug(
                "Registered window backend class `{}` for `winType={}`.".format(
                    foundBackends[_attr.winTypeName], _attr.winTypeName))
    elif inspect.isclass(ep):  # backend passed as a class
        if not issubclass(ep, backend.BaseBackend):
            return
        if not hasattr(ep, 'winTypeName'):
            return
        foundBackends[ep.winTypeName] = '.' + attr
        logging.debug(
            "Registered window backend class `{}` for `winType={}`.".format(
                foundBackends[ep.winTypeName], ep.winTypeName))

    backend.winTypes.update(foundBackends)  # update installed backends


def _registerBuilderComponent(ep):
    """Register a PsychoPy builder component module.

    This function is called by :func:`loadPlugin` when encountering an entry
    point group for :mod:`psychopy.experiment.components`. It searches the
    module at the entry point for sub-classes of `BaseComponent` and registers
    it as a builder component. It will also search the module for any resources
    associated with the component (eg. icons and tooltip text) and register them
    for use.

    Builder component modules in plugins should follow the conventions and
    structure of a normal, stand-alone components. Any plugins that adds
    components to PsychoPy must be registered to load on startup.

    This function is called by :func:`loadPlugin`, it should not be used for any
    other purpose.

    Parameters
    ----------
    module : ModuleType
        Module containing the builder component to register.

    """
    if not inspect.ismodule(ep):  # not a module
        return

    # give a default category
    if not hasattr(ep, 'categories'):
        ep.categories = ['Custom']

    # check if module contains components
    for attrib in dir(ep):
        # name and reference to component class
        name = attrib
        cls = getattr(ep, attrib)

        if not inspect.isclass(cls):
            continue

        if not issubclass(cls, components.BaseComponent):
            continue

        components.pluginComponents[attrib] = getattr(ep, attrib)

        # skip if this class was imported, not defined here
        if ep.__name__ != components.pluginComponents[attrib].__module__:
            continue  # class was defined in different module

        if hasattr(ep, 'tooltip'):
            components.tooltips[name] = ep.tooltip

        if hasattr(ep, 'iconFile'):
            components.iconFiles[name] = ep.iconFile

        # assign the module categories to the Component
        if not hasattr(components.pluginComponents[attrib], 'categories'):
            components.pluginComponents[attrib].categories = ['Custom']


if __name__ == '__main__':
    pass
