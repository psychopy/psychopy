#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
"""Utilities for loading plugins into PsychoPy."""

__all__ = ['loadPlugins', 'installPlugin',
           'uninstallPlugin', 'listPlugins', 'PLUGIN_PATH']

import sys
import os
import inspect
import collections
import shutil
import pkg_resources
from platform import python_version
import hashlib


from psychopy import logging

# get the plugin path
if sys.platform == 'win32':
    PLUGIN_PATH = os.path.join(os.environ['APPDATA'], 'psychopy3', 'plugins')
else:
    PLUGIN_PATH = os.path.join(os.environ['HOME'], '.psychopy3', 'plugins')

# set the environment for plugins
_plugin_ws_ = pkg_resources.WorkingSet(PLUGIN_PATH)
_plugin_env_ = pkg_resources.Environment([PLUGIN_PATH])

# Keep track of plugins that have been loaded
_plugins_ = collections.OrderedDict()  # use OrderedDict for Py2 compatibility


def checksumHash(fpath, method='sha256'):
    """Compute the checksum hash for a given package.

    Authors of PsychoPy plugins can use this function to compute a checksum
    hash and provide it to users to check the integrity of their packages. Users
    can pass the checksum value to `installPlugin` when installing the package
    to validate it.

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
        Checksum hash.

    """
    methodObj = {'md5': hashlib.md5,
                 'sha256': hashlib.sha256}

    hashobj = methodObj[method]()
    with open(fpath, "rb") as f:
        while 1:
            chunk = f.read(4096)
            if chunk == b"":  # EOF
                break
            hashobj.update(chunk)

    return hashobj.hexdigest()


def installPlugin(plugin, path=None, overwrite=True, checksum=None):
    """Install a plugin into PsychoPy.

    This function installs modules inside the specified package into PsychoPy's
    plugin `PLUGIN_PATH` directory.

    Parameters
    ----------
    plugin : str
        Path to the plugin package. The target file should be a ZIP archive.
    path : str or None, optional
        Path to look for the package. If `None`, `plugin` needs to be an
        absolute path, or relative to the PWD.
    overwrite : bool, optional
        Overwrite modules if present in `PLUGIN_PATH`.
    checksum : str
        SHA256 checksum hash to validate package data against. If `None`, no
        checksum will be computed. Raises an error if `checksum` does not match
        what is computed for the package.

    Returns
    -------
    list
        Names of modules installed from `package`. You can pass this list to
        `loadPlugins` to enable them in the current PsychoPy session.

    Examples
    --------
    Install a plugin archive to `PLUGIN_PATH`::

        installPlugin(r'/path/to/plugin/psychopy_plugin.egg')

    """
    if path is not None:
        # check if path is a directory
        if not os.path.isdir(path):
            raise NotADirectoryError("Value for `path` is not a directory.")

        # construct a path to the plugin
        pathToPlugin = path
        pluginFile = plugin
    else:
        pathToPlugin, pluginFile = os.path.split(plugin)

    fullPathToPlugin = os.path.join(pathToPlugin, pluginFile)

    # check if file exists
    if not os.path.isfile(fullPathToPlugin):
        raise FileNotFoundError("Cannot find file `{}`.".format(
            fullPathToPlugin))

    # validate the package
    result = checksumHash(fullPathToPlugin)
    if checksum is not None:
        if result != checksum.lower():
            raise RuntimeError(
                "Package `{}` failed validation (checksum `{}`).".format(
                    pluginFile, checksum))

    # inspect the file
    dist = pkg_resources.Distribution.from_filename(fullPathToPlugin)

    # make sure the plugin is compatible with the version of Python we are using
    if not python_version().startswith(dist.py_version):
        raise RuntimeError(
            "Cannot install plugin. Not compatible with Python version {} "
            "running PsychoPy.".format(python_version()))

    # check if we are overwriting a file already there
    if not os.path.isfile(os.path.join(PLUGIN_PATH, pluginFile)) or overwrite:
        shutil.copy2(fullPathToPlugin, PLUGIN_PATH)

    return dist.project_name


def uninstallPlugin(plugin):
    """Uninstall a plugin package.

    This function removes a plugin from PsychoPy. Deleting its files from the
    `PLUGIN_PATH` directory.

    Parameters
    ----------
    plugin : str
        Name of the plugin to uninstall.

    Returns
    -------
    bool
        `True` if the plugin was uninstalled. This may be `False` if the
        package corresponding to `plugin` cannot be found.

    """
    # find the matching distribution in plugin directory
    foundPkg = None
    for dist in pkg_resources.find_distributions(PLUGIN_PATH, only=False):
        if dist.project_name == plugin:  # found it
            foundPkg = dist.egg_name()
            break

    # look for a matching package name
    if foundPkg is not None:
        for file in os.listdir(PLUGIN_PATH):
            if file.startswith(foundPkg):
                pkgPath = os.path.join(PLUGIN_PATH, file)
                os.remove(pkgPath)  # delete the package
                logging.info('Uninstalled package `{}`.'.format(pkgPath))
    else:
        logging.warning(
            'Cannot find package corresponding to plugin `{}`.'.format(
                plugin))

    return foundPkg is not None


def listPlugins():
    """Get a list of plugin packages installed on this instance of PsychoPy.

    Returns
    -------
    list
        Names of plugins as strings.

    """
    installed = []
    dists, _ = _plugin_ws_.find_plugins(_plugin_env_)
    for dist in dists:
        installed.append(dist.project_name)

    return installed


def loadPlugins(plugins):
    """Load a plugin to extend PsychoPy's coder API.

    Plugins are packages which extend upon PsychoPy's existing functionality by
    dynamically importing code at runtime. Plugins put new objects into the
    namespaces of a modules (eg. `psychopy.visual`) allowing them to be used
    as if they were part of PsychoPy. Plugins are simply Python packages which
    can either reside in a location defined in `sys.path` or elsewhere.

    This function searches for any installed packages named in `plugins`,
    imports them, and add their attributes to namespace which the plugin module
    defines with the `__extends__` directive.

    Plugins may also be ZIP files (i.e. *.zip or *.egg) and will be imported if
    they reside in one of the `paths`.

    Parameters
    ----------
    plugins : str, list or None
        Name(s) of the plugin package(s) to load. A name can also be given as a
        regular expression for loading multiple packages with similar names. If
        `None`, all packages starting with `psychopy_` installed on the system
        will be loaded. A list of name strings can be given, where they will be
        loaded sequentially.

    Returns
    -------
    dict
        Names and modules of the loaded plugins. No plugins were loaded if the
        dictionary will be empty.

    Warnings
    --------
    Make sure that plugins installed on your system are from reputable sources,
    as they may contain malware! PsychoPy is not responsible for undefined
    behaviour or bugs associated with the use of 3rd party plugins.

    Examples
    --------
    Load all installed packages into the namespace of `psychopy.visual` prefixed
    with `psychopy_visual_`::

        import psychopy.visual as visual
        loadPlugins('psychopy_visual_.+')

    You can load multiple, specific plugins using a list for `plugins`. Note
    that the second string in this example will match the first too, but it will
    be ignored the second time::

        loadPlugins(['psychopy_hardware_box', 'psychopy_visual_.+'])

    Check if a plugin has been loaded::

        hasPlugin = if 'my_plugin' in loadPlugins('my_plugin')
        if not hasPlugin:
            print('Unable to load plugin!')

    Prevent the `psychopy_visual_bad` plugin from being loaded, but load
    everything else::

        plugins.loadPlugins('psychopy_visual_.+', ignore=['psychopy_visual_bad'])

    """
    # search all potential plugins if `None` is specified
    if isinstance(plugins, str):
        plugins = [plugins]

    searchPaths = [PLUGIN_PATH]

    # find all plugins installed on the system
    workingSet = pkg_resources.WorkingSet(searchPaths)
    env = pkg_resources.Environment(searchPaths)
    distributions, errors = workingSet.find_plugins(env)

    # iter over specified plugins
    for plugin in plugins:
        # look for a matching distribution pointing to the plugin
        entryPoints = {}
        for dist in distributions:
            if dist.project_name == plugin:
                # check if compatible
                if not python_version().startswith(dist.py_version):
                    raise RuntimeError(
                        "Cannot load plugin. Not compatible with Python "
                        "version {} running PsychoPy.".format(python_version()))

                # load all the entry points
                entryPoints.update(dist.get_entry_map())

        # go over entry points, looking for objects explicitly for psychopy
        for fqn, attrs in entryPoints.items():
            if not fqn.startswith('psychopy'):
                continue

            # forbid plugins from modifying this module
            if fqn.startswith('psychopy.plugins') or \
                    (fqn == 'psychopy' and 'plugins' in attrs):
                raise RuntimeError(
                    "Plugins declaring entry points into the "
                    "`psychopy.plugins` module is forbidden.")

            targObj = _objectFromFQN(fqn)
            for attr, ep in attrs.items():
                setattr(targObj, attr, ep.load())


def _objectFromFQN(fqn):
    """Get an object within PsychoPy's namespace using a fully-qualified name
    (FQN). This function will only retrieve an object if the root name of the
    FQN is `psychopy`.

    Parameters
    ----------
    fqn : str
        Fully-qualified name to the object (eg. `psychopy.visual.Window`).

    Returns
    -------
    obj
        Object referred to by the FQN within PsychoPy's namespace. Can be a
        module, unbound class or method, function or variable.

    """
    if not fqn.startswith('psychopy'):
        raise NameError('Base name must be `psychopy`.')

    # get the object the fqn refers to
    objref = sys.modules['psychopy']  # base module
    for attr in fqn.split(".")[1:]:
        objref = getattr(objref, attr)

    return objref


def _patchAttrs(obj, exp, attrs):
    """Assign attributes in the target module or unbound class with objects
    defined in a plugin module.

    Parameters
    ----------
    obj : ModuleType or ClassType
        Object to assign attributes to.
    exp : ModuleType
        Plugin module exporting the objects.
    attrs : str or list of str
        Name(s) of objects to assign. Can be a single string or a list of
        strings.

    """
    # deal with modules and classes
    if inspect.ismodule(obj) or inspect.isclass(obj):
        # modules and class can have their attributes assigned objects directly
        if isinstance(attrs, str):
            # Ensure that we are not wholesale replacing an existing module. We
            # want plugins to be explicit about what they are changing, so the
            # conflict resolution system doesn't flag the whole module as
            # modified. This makes sure plugins play nice with each other, only
            # making changes to existing code where needed. However, plugins are
            # allowed to add new modules to existing ones.
            attr = getattr(exp, attrs)
            if hasattr(obj, attr.__name__) and inspect.ismodule(attr):
                raise NameError("Plugin attempted to override a builtin "
                                "PsychoPy module.")
            else:
                setattr(obj, attrs, attr)
        elif isinstance(attrs, (list, tuple,)):  # attributes can be given as a list
            for attr in attrs:
                _patchAttrs(obj, exp, attr)  # recursive call on each
        else:
            raise TypeError('Value for `attrs` must be list or string.')
    else:
        raise TypeError('Object `obj` must be module or class type.')


def _findConflicts(module):
    """Check if a plugin module exports an attribute a previous plugin did.

    Parameters
    ----------
    module : ModuleType
        Module which defines an ``__extends__`` statement.

    Returns
    -------
    dict
        Dictionary where keys are fully qualified names of attributes where
        a conflict has been identified, and values are the plugin module which
        originally set the attribute.

    """
    global _plugins_

    foundConflicts = {}
    # iter over previously loaded plugins
    for _, loadedModule in _plugins_.items():
        for qn, attrs in module.__extends__.items():
            if qn not in loadedModule.__extends__.keys():
                continue
            if isinstance(attrs, (list, tuple,)):
                for attr in attrs:
                    if attr in loadedModule.__extends__[qn]:
                        foundConflicts[qn + '.' + attr] = loadedModule
            else:
                if attrs == loadedModule.__extends__[qn]:
                    foundConflicts[qn + '.' + attrs] = loadedModule

    return foundConflicts


def _shutdownPlugins():
    """Call the shutdown routines for all loaded plugins.

    This function calls the ``__shutdown__`` function (if present) for all
    presently loaded plugins. The ``__shutdown__`` function is called
    sequentially for each plugin module in the reverse order they were loaded
    (ie. the last plugin loaded will have it's ``__shutdown__`` function called
    first.

    """
    global _plugins_
    if _plugins_:  # only bother with this if there are any plugins loaded
        for name, module in reversed(list(_plugins_.items())):
            if hasattr(module, '__shutdown__'):
                module.__shutdown()

