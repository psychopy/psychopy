#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
"""Utilities for extending PsychoPy with plugins."""

from __future__ import absolute_import
__all__ = ['loadPlugin', 'listPlugins', 'computeChecksum']

import sys
import inspect
import collections
import hashlib
import importlib
import pkg_resources

from psychopy import logging

# Keep track of plugins that have been loaded
_plugins_ = collections.OrderedDict()  # use OrderedDict for Py2 compatibility


def _objectFromFQN(fqn):
    """Get an object within a module's namespace using a fully-qualified name
    (FQN) string.

    Parameters
    ----------
    fqn : str
        Fully-qualified name to the object (eg. `psychopy.visual.Window`).

    Returns
    -------
    obj
        Object referred to by the FQN within PsychoPy's namespace. Can be a
        module, unbound class or method, function or variable.

    Raises
    ------
    ModuleNotFoundError
        The base module the FQN is referring to has not been imported.
    NameError
        The provided FQN does not point to a valid object.

    """
    fqn = fqn.split(".")  # split the fqn

    # get the object the fqn refers to
    try:
        objref = sys.modules[fqn[0]]  # base name
    except KeyError:
        raise ModuleNotFoundError(
            'Base module cannot be found, has it been imported yet?')

    # walk through the FQN to get the object it refers to
    for attr in fqn[1:]:
        if not hasattr(objref, attr):
            raise NameError(
                "Specified `fqn` does not reference a valid object or is "
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


def listPlugins(onlyLoaded=False):
    """Get a list of installed or loaded PsychoPy plugins.

    This function searches for potential plugin packages installed or loaded.
    When searching for installed plugin packages, only those the names of those
    which advertise entry points specifically for PsychoPy, the version of
    Python its currently running on, and operating system are returned.

    Parameters
    ----------
    onlyLoaded : bool
        If `False`, this function will return all installed packages which can
        be potentially loaded as plugins, regardless if they have been already
        loaded. If `True`, the returned values will only be names of plugins
        that have been successfully loaded previously in this session by
        `loadPlugin`. They will appear in the order of which they were loaded.

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

    """
    if onlyLoaded:  # only list plugins we have already loaded
        return list(_plugins_.keys())

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
    installation files. Plugins create or redefine objects into the namespaces
    of modules (eg. `psychopy.visual`) and unbound classes, allowing them to be
    used as if they were part of PsychoPy.

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
        `register` function.

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
        `__register__` but the specified object is not valid or present.
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

        # Get the object the fully-qualified name points to which the plugin
        # wants to modify.
        targObj = _objectFromFQN(fqn)

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
                            func = _objectFromFQN(imp.__register__)
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

            # add the object to the module or unbound class
            setattr(targObj, attr, ep.load())

    # retain information about the plugin's entry points, we will use this for
    # conflict resolution
    _plugins_[pluginDist.project_name] = entryMap

    return True
