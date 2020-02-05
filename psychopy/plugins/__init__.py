#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
"""Utilities for extending PsychoPy with plugins."""

from __future__ import absolute_import
__all__ = ['loadPlugin', 'listPlugins', 'computeChecksum', 'startUpPlugins']

import sys
import inspect
import collections
import hashlib
import importlib
import pkg_resources

from psychopy import logging
from psychopy.preferences import prefs
import psychopy.experiment.components as components

# Keep track of plugins that have been loaded. Keys are plugin names and values
# are their entry point mappings.
_plugins_ = collections.OrderedDict()  # use OrderedDict for Py2 compatibility


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

    The function will first `psychopy.visual` then get a reference to the
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


def computeChecksum(fpath, method='sha256'):
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

    return hashobj.hexdigest()


def listPlugins(which='all'):
    """Get a list of installed or loaded PsychoPy plugins.

    This function lists either all potential plugin packages installed on the
    system, those registered to be loaded automatically when PsychoPy starts, or
    those that have been previously loaded successfully this session.

    When searching for installed plugin packages, names are listed if packages
    define entry points specifically for PsychoPy and support the current Python
    environment.

    Parameters
    ----------
    which : str
        Category to list plugins. If 'all', all plugins installed on the system
        will be listed, whether they have been loaded or not. If 'loaded', only
        plugins that have been previously loaded successfully this session will
        be listed. If 'startup', plugins registered to be loaded when a PsychoPy
        session starts will be listed, whether or not they have been loaded this
        session.

    Returns
    -------
    list
        Names of PsychoPy related plugins as strings. You can load all installed
        plugins by passing list elements to `loadPlugin`.

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
    if which not in ('all', 'startup', 'loaded',):
        raise ValueError("Invalid value specified to argument `which`.")

    if which == 'loaded':  # only list plugins we have already loaded
        return list(_plugins_.keys())
    elif which == 'startup':
        return prefs.general['startUpPlugins']

    # find all packages with entry points defined
    pluginEnv = pkg_resources.Environment()  # supported by the platform
    dists, _ = pkg_resources.working_set.find_plugins(pluginEnv)

    installed = []
    for dist in dists:
        if any([i.startswith('psychopy') for i in dist.get_entry_map().keys()]):
            installed.append(dist.project_name)

    return installed


def loadPlugin(plugin, *args, **kwargs):
    """Load a plugin to extend PsychoPy.

    Plugins are packages which extend upon PsychoPy's existing functionality by
    dynamically importing code at runtime, without modifying the existing
    installation files. Plugins create or redefine objects in the namespaces
    of modules (eg. `psychopy.visual`) and unbound classes, allowing them to be
    used as if they were part of PsychoPy. In some cases, objects exported by
    plugins will be registered for a particular function if they define entry
    points into specific modules.

    Plugins are simply Python packages,`loadPlugin` will search for them in
    directories specified in `sys.path`. Only packages which define entry points
    in their metadata which pertain to PsychoPy can be loaded with this
    function. This function also permits passing optional arguments to a
    callable object in the plugin module to run any initialization routines
    prior to loading entry points.

    Parameters
    ----------
    plugin : str
        Name of the plugin package to load. This usually refers to the package
        or project name.
    *args, **kwargs
        Optional arguments and keyword arguments to pass to the plugin's
        `__register__` function.

    Returns
    -------
    bool
        `True` if the plugin has valid entry points and was loaded successfully.
        Also returns `True` if the plugin was already loaded by a previous
        `loadPlugin` call this session, this function will have no effect in
        this case. `False` is returned if the plugin defines no entry points
        specific to PsychoPy (a warning is logged).

    Raises
    ------
    NameError
        The plugin attempted to overwrite an entire extant module or modify
        `psychopy.plugins`. Also raised if the plugin module defines
        `__register__` but the specified object is not valid or reachable.
    TypeError
        Plugin defines `__register__` which specifies an object that is not
        callable.

    Warnings
    --------
    Make sure that plugins installed on your system are from reputable sources,
    as they may contain malware! PsychoPy is not responsible for undefined
    behaviour or bugs associated with the use of 3rd party plugins.

    See Also
    --------
    listPlugins : Search for and list installed or loaded plugins.

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
    global _plugins_
    if plugin in _plugins_.keys():
        logging.info('Plugin `{}` already loaded. Skipping.'.format(plugin))
        return True  # already loaded, return True

    # find all plugins installed on the system
    pluginEnv = pkg_resources.Environment()  # supported by the platform
    dists, _ = pkg_resources.working_set.find_plugins(pluginEnv)

    # check if the plugin is in the distribution list
    try:
        pluginDist = dists[[dist.project_name for dist in dists].index(plugin)]
    except ValueError:
        logging.warning(
            'Package `{}` does not appear to be a valid plugin. '
            'Skipping.'.format(plugin))

        return False

    # get entry point map and check if there are any for PsychoPy
    entryMap = pluginDist.get_entry_map()
    if not any([i.startswith('psychopy') for i in entryMap.keys()]):
        logging.warning(
            'Specified package `{}` defines no entry points for PsychoPy. '
            'Skipping.'.format(pluginDist.project_name))

        return False  # can't do anything more here, so return

    # go over entry points, looking for objects explicitly for psychopy
    for fqn, attrs in entryMap.items():
        if not fqn.startswith('psychopy'):
            continue

        # forbid plugins from modifying this module
        if fqn.startswith('psychopy.plugins') or \
                (fqn == 'psychopy' and 'plugins' in attrs):
            raise NameError(
                "Plugins declaring entry points into the `psychopy.plugins` "
                "module is forbidden.")

        # Get the object the fully-qualified name points to the group which the
        # plugin wants to modify.
        targObj = resolveObjectFromName(fqn)

        # add and replace names with the plugin entry points
        for attr, ep in attrs.items():
            # Load the module the entry point belongs to, this happens
            # anyways when .load() is called, but we get to access it before
            # we start binding. If the module has already been loaded, don't
            # do this again.
            if ep.module_name not in sys.modules:
                # Do stuff before loading entry points here, any executable code
                # in the module will run to configure it.
                imp = importlib.import_module(ep.module_name)

                # call the register function, check if exists and valid
                if hasattr(imp, '__register__') and imp.__register__ is not None:
                    if isinstance(imp.__register__, str):
                        if hasattr(imp, imp.__register__):  # local to module
                            func = getattr(imp, imp.__register__)
                        else:  # could be a FQN?
                            func = resolveObjectFromName(imp.__register__)
                        # check if the reference object is callable
                        if not callable(func):
                            raise TypeError(
                                'Plugin module defines `__register__` but the '
                                'specified object is not a callable type.')
                    elif callable(imp.__register__):  # a function was supplied
                        func = imp.__register__
                    else:
                        raise TypeError(
                            'Plugin module defines `__register__` but is not '
                            '`str` or callable type.')

                    # call the register function with arguments
                    func(*args, **kwargs)

            # Ensure that we are not wholesale replacing an existing module.
            # We want plugins to be explicit about what they are changing.
            # This makes sure plugins play nice with each other, only
            # making changes to existing code where needed. However, plugins
            # are allowed to add new modules to the namespaces of existing
            # ones.
            if hasattr(targObj, attr):
                # handle what to do if an attribute exists already here ...
                if inspect.ismodule(getattr(targObj, attr)):
                    raise NameError(
                        "Plugin `{}` attempted to override module `{}`.".format(
                            plugin, fqn + '.' + attr))

            ep = ep.load()  # load the entry point

            # add the object to the module or unbound class
            setattr(targObj, attr, ep)
            logging.debug(
                "Assigning to entry point `{}` to `{}`.".format(
                    ep.__name__, fqn + '.' + attr))

            # --- handle special cases ---
            if fqn == 'psychopy.visual.backends':  # if window backend
                _registerWindowBackend(attr, ep)
            elif fqn == 'psychopy.experiment.components':  # if component
                _registerBuilderComponent(ep)

    # retain information about the plugin's entry points, we will use this for
    # conflict resolution
    _plugins_[pluginDist.project_name] = entryMap

    return True


def startUpPlugins(plugins, add=True, verify=True):
    """Specify which plugins should be loaded automatically when a PsychoPy
    session starts.

    This function edits ``psychopy.preferences.prefs.general['startUpPlugins']``
    and provides a means to verify if entries are valid. The PsychoPy session
    must be restarted for the plugins specified to take effect.

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


def _registerWindowBackend(attr, ep):
    """Make an entry point discoverable as a window backend. This allows it to
    be used by specifying `winType`. All window backends must be subclasses of
    `BaseBackend` and define a `winTypeName` attribute. The value of
    `winTypeName` will be used for selecting `winType`.

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
    backend = resolveObjectFromName(fqn, resolve=(fqn not in sys.modules))

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
