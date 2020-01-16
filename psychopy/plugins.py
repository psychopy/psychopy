#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
"""Utilities for loading plugins into PsychoPy."""

__all__ = ['loadPlugins', 'createPluginPackage']

import sys
import os
import pkgutil
import importlib
import re
import types
import inspect

# Keep track of objects exported by plugins to warn of or resolve namespace
# conflicts. Keys are PsychoPy module names and values are lists of object
# names.
_exported_objects_ = {}


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
__extends__ = '{extends}'

# objects to put in the namespace of the module __extends__
__all__ = ['MyClass', 'test_function', 'MY_DATA']  

# put your code in this space
# <<<<<<<<<<<<<<<<<<<<<<<<<<< 

class MyClass(object):
    def __init__(self):
        pass

def test_function():
    return 0
    
MY_DATA = 'mydata'

# <<<<<<<<<<<<<<<<<<<<<<<<<<< 

if __name__ == "__main__":
    # make sure that this can only be used as a plugin
    raise ImportError("Can not import module. This package is a plugin and"
                      " needs to be loaded from PsychoPy using" 
                      " `psychopy.loadPlugin`.")

    """.format(extends=extends.__name__)

    # LICENCE file
    with open(os.path.join(rootDir, '__init__.py'), 'w') as f:
        f.write(packageInit)


def loadPlugins(plugins=None, paths=None, ignore=None, conflicts='silent'):
    """Load a plugin to extend PsychoPy's coder API.

    Plugins are packages which extend upon PsychoPy's existing functionality by
    dynamically importing code at runtime. Plugins put new objects into the
    namespaces of a modules (eg. `psychopy.visual`) allowing them to be used
    as if they were part of PsychoPy. Plugins are simply Python packages which
    can either reside in a location defined in `sys.path` or elsewhere.

    This function searches for any installed packages named in `plugins`,
    imports them, and add their attributes to namespace which the package
    defines with the `__extends__` directive in the `__init__.py` file within
    the top-level package. The `__init__.py` must also define an `__all__`
    statement to indicate which objects to import into the namespace of
    `__extends__`.

    Only attributes defined explicitly `__all__` in the found packages will be
    assigned attributes. Therefore, any packages that wish to extend the
    PsychoPy API must have an `__all__` statement. Note that `module` should be
    imported prior to attempting to load a plugin. Plugins will only be loaded
    once per session, where a plugin will be prevented from being imported again
    if its name appears in `plugins` in successive calls to `loadPlugins`. Any
    objects from subsequently loaded modules will override objects within a
    namespace sharing the same names.

    Plugins may also be ZIP files (i.e. *.zip or *.egg) and will be imported if
    they reside in one of the `paths`.

    Parameters
    ----------
    plugins : str, list or None
        Name(s) of the plugin package(s) to load. A name can also be given as a
        regular expression for loading multiple packages with similar names. If
        `None`, the `plugins` name will be derived from the `module` name and
        all packages prefixed with the name will be loaded. For instance,
        if 'psychopy.visual' is given, all packages installed on the system
        with names starting with 'psychopy_visual_' will be loaded. A list of
        name strings can be given, where they will be loaded sequentially.
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

    loaded = {}
    for plugin in plugins:
        # find packages installed packages matching the specified pattern
        foundPackages = []
        for _, name, ispkg in pkgutil.iter_modules(paths):
            if re.search(plugin, name) is not None:
                foundPackages.append(name)

        # go over found packages and start loading them
        for packageName in foundPackages:
            # ignore a package if in `ignore`
            if ignore is not None and packageName in ignore:
                continue
            # don't load a plugin twice if already in namespace
            elif packageName in sys.modules.keys():
                continue

            imp = importlib.import_module(packageName)  # import the plugin code

            # check if the plugin implements __extends__, skip if not
            if not hasattr(imp, '__extends__'):
                del sys.modules[packageName]
                continue

            # ensure what is being extended is part of PsychoPy
            for moduleName in imp.__extends__.keys():
                if not moduleName.startswith('psychopy'):
                    raise NameError(
                        "Plugin attempted to export objects to a module "
                        "not part of PsychoPy!")

            for fqn, attrs in imp.__extends__.items():
                # get the object the fully qualified name points to
                obj = sys.modules['psychopy']  # base module
                for attr in fqn.split(".")[1:]:
                    obj = getattr(obj, attr)

                # assign attributes from the plugin to the target
                for attr in attrs:
                    setattr(obj, attr, getattr(imp, attr))

            loaded[packageName] = imp

    return loaded
