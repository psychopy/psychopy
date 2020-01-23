#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
"""Utilities for loading plugins into PsychoPy."""

__all__ = ['loadPlugins', 'createPluginPackage', 'installPlugin',
           'uninstallPlugin', 'getPlugins', 'PLUGIN_PATH']

import sys
import os
import pkgutil
import importlib
import re
import types
import inspect
import collections
import shutil
import zipfile
import pkg_resources
import subprocess
from setuptools import sandbox


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


def createPluginPackage(packagePath,
                        packageName,
                        extends):
    """Create a plugin package template for a PsychoPy module.

    This generates a folder with setup scripts and a base package to get started
    developing a plugin.

    Parameters
    ----------
    packagePath : str
        Path the create the plugin folder.
    packageName : str
        Name of the plugin. The name will be automatically prefixed with
        'psychopy-' if it does not already.
    extends : str or ModuleType
        The PsychoPy module to extend as a fully qualified path or the module
        object itself.

    """
    # make sure we are using the correct naming convention
    name = packageName
    if not packageName.startswith('psychopy-'):
        packageName = 'psychopy-' + packageName

    # create the directory
    packagePath = os.path.join(packagePath, packageName)
    if not os.path.exists(packagePath):
        os.makedirs(packagePath)

    # generate the base package name
    if isinstance(extends, str):
        try:
            this_module = sys.modules[extends]
        except KeyError:
            raise ModuleNotFoundError(
                'Cannot find module `{}`. Has it been imported yet?'.format(
                    extends))
    elif isinstance(extends, types.ModuleType):
        if extends.__name__ in sys.modules.keys():
            this_module = extends
        else:
            raise ModuleNotFoundError(
                'Module `{}` does not appear to be imported yet.'.format(
                    extends.__name__))
    else:
        raise ValueError('Object specified to `extends` must be type `str` or '
                         '`ModuleType`.')

    # derive the plugin search string if not given
    baseName = ''
    for i in this_module.__name__.split('.'):
        baseName += i + '_'
    baseName += name

    # create a the root directory for the plugin
    rootDir = os.path.join(packagePath, baseName)
    if not os.path.exists(rootDir):
        os.makedirs(rootDir)

    # setup script template and other files
    setupScript = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name="{name}",
    version='1.0',  # version number
    description='',  # short description of your plugin
    long_description='',  # long description of your plugin
    author='',  # author name
    author_email='',  # author email
    license='',  # eg. MIT, GPL3, etc.
    packages=["{package}"]
)
    """.format(name=packageName, package=baseName)

    with open(os.path.join(packagePath, 'setup.py'), 'w') as f:
        f.write(setupScript)

    # README file as markdown
    with open(os.path.join(packagePath, 'README.md'), 'w') as f:
        f.write('# {}\nThis is the README file.'.format(packageName))

    # LICENCE file
    with open(os.path.join(packagePath, 'LICENCE.txt'), 'w') as f:
        f.write('Put your licence here.'.format(packageName))

    # create an __init__ template
    packageInit = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version__ = '1.0'
__license__ = ''
__author__ = ''
__author_email__ = ''
__maintainer_email__ = ''
__url__ = ''
__download_url__ = ''

# Mapping for where objects defined in the scope of this module should be placed
# for example `__extends__ = {'psychopy.visual': ["MyStim"]}` where "MyStim" is 
# defined below.
__extends__ = {}  

# put your import statements and object definitions in this space
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

def __load():
    # put code to run when the plugin is loaded here
    return 

def __shutdown():
    # put code to run when PsychoPy quits here
    return

    """

    # LICENCE file
    with open(os.path.join(rootDir, '__init__.py'), 'w') as f:
        f.write(packageInit)


def installPlugin(plugin, path=None, overwrite=True):
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

    Returns
    -------
    list
        Names of modules installed from `package`. You can pass this list to
        `loadPlugins` to enable them in the current PsychoPy session.

    Examples
    --------
    Install a plugin archive to `PLUGIN_PATH`::

        installPlugin(r'/path/to/plugin/psychopy_plugin.zip')

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

    # identify if the file is a plugin
    if not os.path.isfile(fullPathToPlugin):
        raise FileNotFoundError("Cannot find file `{}`.".format(
            fullPathToPlugin))

    # use PIP to install the plugin to the plugin directory
    subprocess.check_call(['python',  '-m', 'pip',  'install',
                           '--target={}'.format(PLUGIN_PATH),
                           '--upgrade' if overwrite else '',
                           fullPathToPlugin])


def uninstallPlugin(plugin):
    """Uninstall a plugin package.

    This function removes a plugin from PsychoPy. Deleting its files from the
    `PLUGIN_PATH` directory.

    """
    # find the matching distribution in plugin directory

    for dist in pkg_resources.find_distributions(PLUGIN_PATH, only=False):
        if dist.project_name == plugin:  # found it
            print(os.path.join(dist.location, dist.egg_name()))


def getPlugins():
    """Get a list of plugin packages installed on PsychoPy.

    Returns
    -------
    list
        Names of plugins current installed on PsychoPy as strings.

    """
    installed = []
    dists, _ = _plugin_ws_.find_plugins(_plugin_env_)
    for dist in dists:
        installed.append(dist.project_name)

    return installed


def loadPlugins(plugins=None, paths=None, ignore=None, conflicts='warn'):
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
    paths : list
        List of paths (`str`) to look for plugins. If `None`, `paths` will be
        set to `sys.paths`.
    ignore : list or None
        List of plugin names to ignore. This prevents certain plugins installed
        on the system from being loaded if they match the pattern specified by
        `plugins`. If `None`, all plugins will be loaded.
    conflicts : str
        Policy for handling conflicts where a plugin tries to export a name
        a previously loaded plugin used. Options are 'silent' where the previous
        object is silently overridden, 'warn' which logs a warning informing
        of the conflict, and 'error' which raise and exception when a conflict
        occurs.

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
    if plugins is None:
        plugins = 'psychopy_.+'

    if isinstance(plugins, str):
        plugins = [plugins]

    if paths is None:
        paths = PLUGIN_PATH

    global _plugins_

    # find all plugins installed on the system
    distributions, errors = _plugin_ws_.find_plugins(_plugin_env_)

    # iter over specified plugins
    for plugin in plugins:
        # look for a matching distribution pointing to the plugin
        entryPoints = {}
        for dist in distributions:
            if dist.project_name == plugin:
                # load all the entry points
                entryPoints.update(dist.get_entry_map())

        # go over entry points, looking for objects explicitly for psychopy
        for fqn, attrs in entryPoints.items():
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

