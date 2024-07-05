#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
"""Utilities for extending PsychoPy with plugins."""

__all__ = [
    'loadPlugin',
    'listPlugins',
    'installPlugin',
    'computeChecksum',
    'startUpPlugins',
    'pluginMetadata',
    'pluginEntryPoints',
    'scanPlugins',
    'requirePlugin',
    'isPluginLoaded',
    'isStartUpPlugin',
    'activatePlugins',
    'discoverModuleClasses',
    'getBundleInstallTarget',
    'refreshBundlePaths'
]

import os
import sys
import inspect
import collections
import hashlib
import importlib, importlib.metadata
from psychopy import logging
from psychopy.preferences import prefs

# Configure the environment to use our custom site-packages location for
# user-installed packages (i.e. plugins). This value remains `None` if the user
# is in a vitual environment or has disabled the custom site-packages location
# via command line.
USER_PACKAGES_PATH = None

# check if we're in a virtual environment or not
inVM = hasattr(sys, 'real_prefix') or sys.prefix != sys.base_prefix

    # add the plugins folder to the path
    # if USER_PACKAGES_PATH not in sys.path:
    #     sys.path.insert(0, USER_PACKAGES_PATH)  # add to path
    if not site.ENABLE_USER_SITE or USER_PACKAGES_PATH not in sys.path:
        site.addsitedir(USER_PACKAGES_PATH)

# Keep track of plugins that have been loaded. Keys are plugin names and values
# are their entry point mappings.
_loaded_plugins_ = collections.OrderedDict()  # Py2 compatibility

# Entry points for all plugins installed on the system, this is populated by
# calling `scanPlugins`. We are caching entry points to avoid having to rescan
# packages for them.
_installed_plugins_ = collections.OrderedDict()

# Keep track of plugins that failed to load here
_failed_plugins_ = []


# ------------------------------------------------------------------------------
# Functions
#

def getEntryPointGroup(group, subgroups=False):
    """
    Get all entry points which target a specific group.

    Parameters
    ----------
    group : str
        Group to look for (e.g. "psychopy.experiment.components" for plugin Components)
    subgroups : bool
        If True, then will also look for subgroups (e.g. "psychopy.experiment" will also return
        entry points for "psychopy.experiment.components")

    Returns
    -------
    list[importlib.metadata.Entrypoint]
        List of EntryPoint objects for the given group
    """
    # start off with no entry points or sections
    entryPoints = []

    if subgroups:
        # if searching subgroups, iterate through entry point groups
        for thisGroup, eps in importlib.metadata.entry_points().items():
            # get entry points within matching group
            if thisGroup.startswith(group):
                # add to list of all entry points
                entryPoints += eps
    else:
        # otherwise, just get the requested group
        entryPoints += importlib.metadata.entry_points().get(group, [])

    return entryPoints


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


def getBundleInstallTarget(projectName):
    """Get the path to a bundle given a package name.

    This returns the installation path for a bundle with the specified project
    name. This is used to either generate installation target directories.

    Parameters
    ----------
    projectName : str
        Project name for the main package within the bundle.

    Returns
    -------
    str
        Path to the bundle with a given project name. Project name is converted
        to a 'safe name'.

    """
    return os.path.join(
        prefs.paths['packages'], projectName)


def refreshBundlePaths():
    """Find package bundles within the PsychoPy user plugin directory.

    This finds subdirectories inside the PsychoPy user package directory
    containing distributions, then add them to the search path for packages.

    These are referred to as 'bundles' since each subdirectory contains the
    plugin package code and all extra dependencies related to it. This allows
    plugins to be uninstalled cleanly along with all their supporting libraries.
    A directory is considered a bundle if it contains a package at the top-level
    whose project name matches the name of the directory. If not, the directory
    will not be appended to `sys.path`.

    This is called implicitly when :func:`scanPlugins()` is called.

    Returns
    -------
    list
        List of bundle names found in the plugin directory which have been
        added to `sys.path`.

    """
    pluginBaseDir = prefs.paths['packages']  # directory packages are in

    foundBundles = []
    pluginTopLevelDirs = os.listdir(pluginBaseDir)
    for pluginDir in pluginTopLevelDirs:
        fullPath = os.path.join(pluginBaseDir, pluginDir)
        allDists = importlib.metadata.distributions(path=pluginDir)
        if not allDists:  # no packages found, move on
            continue

        # does the sud-directory contain an appropriately named distribution?
        validDist = False
        for dist in allDists:
            if sys.version.startswith("3.8"):
                distName = dist.metadata['name']
            else:
                distName = dist.name
            validDist = validDist or distName == pluginDir
        if not validDist:
            continue

        # add to path if the subdir has a valid distribution in it
        if fullPath not in sys.path:
            sys.path.append(fullPath)  # add to path

        foundBundles.append(pluginDir)

    # refresh package index since the working set is now stale
    scanPlugins()

    return foundBundles


def getPluginConfigPath(plugin):
    """Get the path to the configuration file for a plugin.

    This function returns the path to folder alloted to a plugin for storing
    configuration files. This is useful for plugins that require user settings
    to be stored in a file.

    Parameters
    ----------
    plugin : str
        Name of the plugin package to get the configuration file for.

    Returns
    -------
    str
        Path to the configuration file for the plugin.

    """
    # check if the plugin is installed first
    if plugin not in _installed_plugins_:
        raise ValueError("Plugin `{}` is not installed.".format(plugin))
    
    # get the config directory
    import pathlib
    configDir = pathlib.Path(prefs.paths['configs']) / 'plugins' / plugin
    configDir.mkdir(parents=True, exist_ok=True)

    return configDir


def installPlugin(package, local=True, upgrade=False, forceReinstall=False,
                  noDeps=False):
    """Install a plugin package.

    Parameters
    ----------
    package : str
        Name or path to distribution of the plugin package to install.
    local : bool
        If `True`, install the package locally to the PsychoPy user plugin 
        directory.
    upgrade : bool
        Upgrade the specified package to the newest available version.
    forceReinstall : bool
        If `True`, the package and all it's dependencies will be reinstalled if
        they are present in the current distribution.
    noDeps : bool
        Don't install dependencies if `True`.

    """
    # determine where to install the package
    installWhere = USER_PACKAGES_PATH if local else None
    import psychopy.tools.pkgtools as pkgtools
    pkgtools.installPackage(
        package, 
        target=installWhere,
        upgrade=upgrade,
        forceReinstall=forceReinstall,
        noDeps=noDeps)


def scanPlugins():
    """Scan the system for installed plugins.

    This function scans installed packages for the current Python environment
    and looks for ones that specify PsychoPy sub-module entry points in their
    metadata. Afterwards, you can call :func:`listPlugins()` to list them and
    `loadPlugin()` to load them into the current session. This function is
    called automatically when PsychoPy starts, so you do not need to call this
    unless packages have been added since the session began.

    Returns
    -------
    int
        Number of plugins found during the scan. Calling `listPlugins()` will
        return the names of the found plugins.

    """
    global _installed_plugins_
    _installed_plugins_ = {}  # clear the cache
    # iterate through installed packages
    for dist in importlib.metadata.distributions(path=sys.path + [USER_PACKAGES_PATH]):
        # map all entry points
        for ep in dist.entry_points:
            # skip entry points which don't target PsychoPy
            if not ep.group.startswith("psychopy"):
                continue
            # make sure we have an entry for this distribution
            if sys.version.startswith("3.8"):
                distName = dist.metadata['name']
            else:
                distName = dist.name
            if distName not in _installed_plugins_:
                _installed_plugins_[distName] = {}
            # make sure we have an entry for this group
            if ep.group not in _installed_plugins_[distName]:
                _installed_plugins_[distName][ep.group] = {}
            # map entry point
            _installed_plugins_[distName][ep.group][ep.name] = ep
    
    return len(_installed_plugins_)


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
        return list(_installed_plugins_.keys())


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


def loadPluginBuilderElements(plugin):
    """
    Load entry points from plugin which are relevant to Builder, e.g.
    Component/Routine extensions for listing available hardware backends.

    Parameters
    ----------
    plugin : str
        Name of the plugin package to load. This usually refers to the package
        or project name.

    Returns
    -------
    bool
        `True` if successful, `False` if failed.
    """
    # if plugin has already failed to load once, don't try again
    if plugin in _failed_plugins_:
        return False
    # get entry points for plugin
    ep = pluginEntryPoints(plugin)
    # define modules in which entry points are relevant to Builder
    modules = (
        "psychopy.experiment.routines",
        "psychopy.experiment.components",
    )
    # get any points pointing to these modules
    relevantPoints = []
    for mod in modules:
        pts = ep.get(mod, {})
        relevantPoints += list(pts.values())
    # import all relevant classes
    for point in relevantPoints:
        try:
            ep.load()
            return True
        except:
            # if import failed for any reason, log error and mark failure
            logging.error(
                f"Failed to load {point.value}.{point.name} from plugin {plugin}."
            )
            _failed_plugins_.append(plugin)
            return False


def loadPlugin(plugin):
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
    function.

    This function is robust, simply returning `True` or `False` whether a
    plugin has been fully loaded or not. If a plugin fails to load, the reason
    for it will be written to the log as a warning or error, and the application
    will continue running. This may be undesirable in some cases, since features
    the plugin provides may be needed at some point and would lead to undefined
    behavior if not present. If you want to halt the application if a plugin
    fails to load, consider using :func:`requirePlugin` to assert that a plugin
    is loaded before continuing.

    It is advised that you use this function only when using PsychoPy as a
    library. If using the Builder or Coder GUI, it is recommended that you use
    the plugin dialog to enable plugins for PsychoPy sessions spawned by the
    experiment runner. However, you can still use this function if you want to
    load additional plugins for a given experiment, having their effects
    isolated from the main application and other experiments.

    Parameters
    ----------
    plugin : str
        Name of the plugin package to load. This usually refers to the package
        or project name.

    Returns
    -------
    bool
        `True` if the plugin has valid entry points and was loaded successfully.
        Also returns `True` if the plugin was already loaded by a previous
        `loadPlugin` call this session, this function will have no effect in
        this case. `False` is returned if the plugin defines no entry points
        specific to PsychoPy or crashed during import (an error is logged).

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

    You can use the value returned from `loadPlugin` to determine if the plugin
    is installed and supported by the platform::

        hasPlugin = loadPlugin('psychopy-hardware-box')
        if hasPlugin:
            # initialize objects which require the plugin here ...

    Loading all plugins installed on the system::

        scanPlugins()  # call first to find all plugins

        for plugin in listPlugins('all'):
            result = loadPlugin(plugin)
            if not result:
                print(f"Failed to load plugin {plugin}.")

    """
    global _loaded_plugins_, _failed_plugins_

    if isPluginLoaded(plugin):
        logging.info('Plugin `{}` already loaded. Skipping.'.format(plugin))
        return True  # already loaded, return True

    try:
        entryMap = _installed_plugins_[plugin]
    except KeyError:
        logging.warning(
            'Package `{}` does not appear to be a valid plugin. '
            'Skipping.'.format(plugin))
        if plugin not in _failed_plugins_:
            _failed_plugins_.append(plugin)

        return False

    if not any([i.startswith('psychopy') for i in entryMap.keys()]):
        logging.warning(
            'Specified package `{}` defines no entry points for PsychoPy. '
            'Skipping.'.format(plugin))

        if plugin not in _failed_plugins_:
            _failed_plugins_.append(plugin)

        return False  # can't do anything more here, so return

    # go over entry points, looking for objects explicitly for psychopy
    validEntryPoints = collections.OrderedDict()  # entry points to assign
    for fqn, attrs in entryMap.items():
        if not fqn.startswith('psychopy'):
            continue

        # forbid plugins from modifying this module
        if fqn.startswith('psychopy.plugins') or \
                (fqn == 'psychopy' and 'plugins' in attrs):
            logging.error(
                "Plugin `{}` declares entry points into the `psychopy.plugins` "
                "module which is forbidden. Skipping.".format(plugin))

            if plugin not in _failed_plugins_:
                _failed_plugins_.append(plugin)

            return False

        # Get the object the fully-qualified name points to the group which the
        # plugin wants to modify.
        targObj = resolveObjectFromName(fqn, error=False)
        if targObj is None:
            logging.error(
                "Plugin `{}` specified entry point group `{}` that does not "
                "exist or is unreachable.".format(plugin, fqn))

            if plugin not in _failed_plugins_:
                _failed_plugins_.append(plugin)

            return False

        validEntryPoints[fqn] = []

        # Import modules assigned to entry points and load those entry points.
        # We don't assign anything to PsychoPy's namespace until we are sure
        # that the entry points are valid. This prevents plugins from being
        # partially loaded which can cause all sorts of undefined behaviour.
        for attr, ep in attrs.items():
            try:
                # parse the module name from the entry point value
                module_name, _ = ep.value.split(':', 1)
                module_name = module_name.split(".")[0]
            except ValueError:
                logging.error(
                    "Plugin `{}` entry point `{}` is not formatted correctly. "
                    "Skipping.".format(plugin, ep))

                if plugin not in _failed_plugins_:
                    _failed_plugins_.append(plugin)

                return False

            # Load the module the entry point belongs to, this happens
            # anyways when .load() is called, but we get to access it before
            # we start binding. If the module has already been loaded, don't
            # do this again.
            if module_name not in sys.modules:
                # Do stuff before loading entry points here, any executable code
                # in the module will run to configure it.
                try:
                    imp = importlib.import_module(module_name)
                except (ModuleNotFoundError, ImportError):
                    importSuccess = False
                    logging.error(
                        "Plugin `{}` entry point requires module `{}`, but it "
                        "cannot be imported.".format(plugin, module_name))
                except:
                    importSuccess = False
                    logging.error(
                        "Plugin `{}` entry point requires module `{}`, but an "
                        "error occurred while loading it.".format(
                            plugin, module_name))
                else:
                    importSuccess = True

                if not importSuccess:  # if we failed to import
                    if plugin not in _failed_plugins_:
                        _failed_plugins_.append(plugin)

                    return False

            # Ensure that we are not wholesale replacing an existing module.
            # We want plugins to be explicit about what they are changing.
            # This makes sure plugins play nice with each other, only
            # making changes to existing code where needed. However, plugins
            # are allowed to add new modules to the namespaces of existing
            # ones.
            if hasattr(targObj, attr):
                # handle what to do if an attribute exists already here ...
                if inspect.ismodule(getattr(targObj, attr)):
                    logging.warning(
                        "Plugin `{}` attempted to override module `{}`.".format(
                            plugin, fqn + '.' + attr))

                    # if plugin not in _failed_plugins_:
                    #     _failed_plugins_.append(plugin)
                    #
                    # return False
            try:
                ep = ep.load()  # load the entry point

                # Raise a warning if the plugin is being loaded from a zip file.
                if '.zip' in inspect.getfile(ep):
                    logging.warning(
                        "Plugin `{}` is being loaded from a zip file. This may "
                        "cause issues with the plugin's functionality.".format(plugin))

            except ImportError as e:
                logging.error(
                    "Failed to load entry point `{}` of plugin `{}`. "
                    "(`{}: {}`) "
                    "Skipping.".format(str(ep), plugin, e.name, e.msg))

                if plugin not in _failed_plugins_:
                    _failed_plugins_.append(plugin)

                return False
            except Exception:  # catch everything else
                logging.error(
                    "Failed to load entry point `{}` of plugin `{}` for unknown"
                    " reasons. Skipping.".format(str(ep), plugin))

                if plugin not in _failed_plugins_:
                    _failed_plugins_.append(plugin)

                return False

            # If we get here, the entry point is valid and we can safely add it
            # to PsychoPy's namespace.
            validEntryPoints[fqn].append((targObj, attr, ep))

    # Assign entry points that have been successfully loaded. We defer
    # assignment until all entry points are deemed valid to prevent plugins
    # from being partially loaded.
    for fqn, vals in validEntryPoints.items():
        for targObj, attr, ep in vals:
            # add the object to the module or unbound class
            setattr(targObj, attr, ep)
            logging.debug(
                "Assigning the entry point `{}` to `{}`.".format(
                    ep.__name__, fqn + '.' + attr))

            # --- handle special cases ---
            # Note - We're going to handle special cases here for now, but
            # this will eventually be handled by special functions in the 
            # target modules (e.g. `getAllPhotometers()` in 
            # `psychopy.hardware.photometer`) which can detect the loaded 
            # attribute inside the module and add it to a collection.

            if fqn == 'psychopy.visual.backends':  # if window backend
                _registerWindowBackend(attr, ep)
            elif fqn == 'psychopy.experiment.components':  # if component
                _registerBuilderComponent(ep)
            elif fqn == 'psychopy.experiment.routine':  # if component
                _registerBuilderStandaloneRoutine(ep)
            elif fqn == 'psychopy.hardware.photometer':  # photometer
                _registerPhotometer(ep)

    # Retain information about the plugin's entry points, we will use this for
    # conflict resolution.
    _loaded_plugins_[plugin] = entryMap

    # If we made it here on a previously failed plugin, it was likely fixed and
    # can be removed from the list.
    if plugin not in _failed_plugins_:
        try:
            _failed_plugins_.remove(plugin)
        except ValueError:
            pass

    return True


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
        raise RuntimeError('Required plugin `{}` has not been loaded.'.format(
            plugin))


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
    scanPlugins()
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

    pkg = importlib.metadata.distribution(plugin)
    metadict = dict(pkg.metadata)

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


def activatePlugins(which='all'):
    """Activate plugins.

    Calling this routine will load all startup plugins into the current process.

    Warnings
    --------
    This should only be called outside of PsychoPy sub-packages as plugins may
    import them, causing a circular import condition.

    """
    if not scanPlugins():
        logging.info(
            'Calling `psychopy.plugins.activatePlugins()`, but no plugins have '
            'been found in active distributions.')
        return  # nop if no plugins

    # load each plugin and apply any changes to Builder
    for plugin in listPlugins(which):
        loadPlugin(plugin)
        loadPluginBuilderElements(plugin)


# Keep track of currently installed window backends. When a window is loaded,
# its `winType` is looked up here and the matching backend is loaded. Plugins
# which define entry points into this module will update `winTypes` if they
# define subclasses of `BaseBackend` that have valid names.
_winTypes = {
    'pyglet': '.pygletbackend.PygletBackend',
    'glfw': '.glfwbackend.GLFWBackend',  # moved to plugin
    'pygame': '.pygamebackend.PygameBackend'
}


def getWindowBackends():
    # Return winTypes array from backend object
    return _winTypes


def discoverModuleClasses(nameSpace, classType, includeUnbound=True):
    """Discover classes and sub-classes matching a specific type within a
    namespace.

    This function is used to scan a namespace for references to specific classes
    and sub-classes. Classes may be either bound or unbound. This is useful for
    scanning namespaces for plugins which have loaded their entry points into
    them at runtime.

    Parameters
    ----------
    nameSpace : str or ModuleType
        Fully-qualified path to the namespace, or the reference itself. If the
        specified module hasn't been loaded, it will be after calling this.
    classType : Any
        Which type of classes to get. Any value that `isinstance` or
        `issubclass` expects as its second argument is valid.
    includeUnbound : bool
        Include unbound classes in the search. If `False` only bound objects are
        returned. The default is `True`.

    Returns
    -------
    dict
        Mapping of names and associated classes.

    Examples
    --------
    Get references to all visual stimuli classes. Since they all are derived
    from `psychopy.visual.basevisual.BaseVisualStim`, we can specify that as
    the type to search for::

        import psychopy.plugins as plugins
        import psychopy.visual as visual

        foundClasses = plugins.discoverModuleClasses(
            visual,   # base module to search
            visual.basevisual.BaseVisualStim,  # type to search for
            includeUnbound=True  # get unbound classes too
        )

    The resulting dictionary referenced by `foundClasses` will look like::

        foundClasses = {
           'BaseShapeStim': <class 'psychopy.visual.shape.BaseShapeStim'>,
           'BaseVisualStim': <class 'psychopy.visual.basevisual.BaseVisualStim'>
           # ~~~ snip ~~~
           'TextStim': <class 'psychopy.visual.text.TextStim'>,
           'VlcMovieStim': <class 'psychopy.visual.vlcmoviestim.VlcMovieStim'>
        }

    To search for classes more broadly, pass `object` as the type to search
    for::

        foundClasses = plugins.discoverModuleClasses(visual, object)

    """
    if isinstance(nameSpace, str):
        module = resolveObjectFromName(
            nameSpace,
            resolve=(nameSpace not in sys.modules),
            error=False)  # catch error below
    elif inspect.ismodule(nameSpace):
        module = nameSpace
    else:
        raise TypeError(
            'Invalid type for parameter `nameSpace`. Must be `str` or '
            '`ModuleType`')

    if module is None:
        raise ImportError("Cannot resolve namespace `{}`".format(nameSpace))

    foundClasses = {}

    if includeUnbound:  # get unbound classes in a module
        for name, attr in inspect.getmembers(module):
            if inspect.isclass(attr) and issubclass(attr, classType):
                foundClasses[name] = attr

    # now get bound objects, overwrites unbound names if they show up
    for name in dir(module):
        attr = getattr(module, name)
        if inspect.isclass(attr) and issubclass(attr, classType):
            foundClasses[name] = attr

    return foundClasses


# ------------------------------------------------------------------------------
# Registration functions
#
# These functions are called to perform additional operations when a plugin is
# loaded. Most plugins that specify an entry point elsewhere will not need to
# use these functions to appear in the application.
#

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
    ep : ModuleType or ClassType
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
    ep : ClassType
        Class defining the component.

    """
    # get reference to the backend class
    fqn = 'psychopy.experiment.components'
    compPkg = resolveObjectFromName(
        fqn, resolve=(fqn not in sys.modules), error=False)

    if compPkg is None:
        logging.error("Failed to resolve name `{}`.".format(fqn))
        return

    if hasattr(compPkg, 'addComponent'):
        compPkg.addComponent(ep)
    else:
        raise AttributeError(
            "Cannot find function `addComponent()` in namespace "
            "`{}`".format(fqn))


def _registerBuilderStandaloneRoutine(ep):
    """Register a PsychoPy builder standalone routine module.

    This function is called by :func:`loadPlugin` when encountering an entry
    point group for :mod:`psychopy.experiment.routine`.

    This function is called by :func:`loadPlugin`, it should not be used for any
    other purpose.

    Parameters
    ----------
    ep : ClassType
        Class defining the standalone routine.

    """
    # get reference to the backend class
    fqn = 'psychopy.experiment.routines'
    routinePkg = resolveObjectFromName(
        fqn, resolve=(fqn not in sys.modules), error=False)

    if routinePkg is None:
        logging.error("Failed to resolve name `{}`.".format(fqn))
        return

    if hasattr(routinePkg, 'addStandaloneRoutine'):
        routinePkg.addStandaloneRoutine(ep)
    else:
        raise AttributeError(
            "Cannot find function `addStandaloneRoutine()` in namespace "
            "`{}`".format(fqn))


def _registerPhotometer(ep):
    """Register a photometer class.

    This is called when the plugin specifies an entry point into
    :class:`~psychopy.hardware.photometers`.

    Parameters
    ----------
    ep : ModuleType or ClassType
        Entry point which defines an object serving as the interface for the
        photometer.

    """
    # get reference to the backend class
    fqn = 'psychopy.hardware.photometer'
    photPkg = resolveObjectFromName(
        fqn, resolve=(fqn not in sys.modules), error=False)

    if photPkg is None:
        logging.error("Failed to resolve name `{}`.".format(fqn))
        return

    if hasattr(photPkg, 'addPhotometer'):
        photPkg.addPhotometer(ep)
    else:
        raise AttributeError(
            "Cannot find function `addPhotometer()` in namespace "
            "`{}`".format(fqn))


if __name__ == "__main__":
    pass
