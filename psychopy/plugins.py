#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
"""Utilities for loading plugins into PsychoPy."""

import sys
import pkgutil
import importlib
import re
import types


def loadPlugins(module, plugin=None, ignore=None):
    """Load a plugin to extend PsychoPy's coder API.

    This function searches for any installed packages named `plugin`, imports
    them, and add their attributes to namespace of `module`. Only attributes
    defined explicitly `__all__` in the found packages will be assigned
    attributes. Therefore, any packages that wish to extend the PsychoPy API
    must have an `__all__` statement. Note that `module` should be imported
    prior to attempting to load a plugin.

    Parameters
    ----------
    module : str or ModuleType
        Import path or object of the module you wish to install the plugin (eg.
        'psychopy.visual').
    plugin : str or None
        Name of the plugin package to load. A name can also be given as a
        regular expression for loading multiple packages with similar names. If
        `None`, the `plugin` name will be derived from the `module` name and
        all packages prefixed with the name will be loaded. For instance,
        a if 'psychopy.visual' is given, all packages installed on the system
        with names starting with 'psychopy_visual_' will be loaded.
    ignore : list or None
        List of plugin names to ignore. This prevents certain plugins installed
        on the system from being loaded if they match the pattern specified by
        `plugin`. If `None`, all plugins will be loaded.

    Returns
    -------
    list
        Names of the plugins loaded. No plugins were loaded if the list is
        empty.

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
        loadPlugins('psychopy.visual', 'psychopy_visual_.+')

    You can also use the `__name__` attribute of the module, or the module object
    itself::

        import psychopy.visual as visual
        loadPlugins(visual.__name__, 'psychopy_visual_.+')

        # module object
        loadPlugins(visual, 'psychopy_visual_.+')

    If plugins follow the standard naming convention, you can load all plugins
    installed on the system for a given `module` without specifying `plugin`::

        import psychopy.visual as visual
        loadPlugins(visual.__name__)
        # or ..
        loadPlugins(visual)

    Check if a plugin has been loaded::

        hasPlugin = if 'my_plugin' in loadPlugins(__name__, 'my_plugin')
        if not hasPlugin:
            print('Unable to load plugin!')

    Prevent the `psychopy_visual_bad` plugin from being loaded, but load
    everything else::

        plugins.loadPlugins(visual.__name__, ignore=['psychopy_visual_bad'])

    """
    if isinstance(module, str):
        try:
            this_module = sys.modules[module]
        except KeyError:
            raise ModuleNotFoundError(
                'Cannot find module `{}`. Has it been imported yet?'.format(
                    module))
    elif isinstance(module, types.ModuleType):
        if module.__name__ in sys.modules.keys():
            this_module = module
        else:
            raise ModuleNotFoundError(
                'Cannot find module `{}` in current namespace. Has it been '
                'imported yet?'.format(
                    module))
    else:
        raise ValueError('Object specified to `module` must be type `str` or '
                         '`Module`.')

    # derive the plugin search string if not given
    if plugin is None:
        plugin = ''
        for i in this_module.__name__.split('.'):
            plugin += i + '_'
        plugin += '.+'

    # iterate over packages
    loaded = []
    for finder, name, ispkg in pkgutil.iter_modules():
        if re.search(plugin, name):
            if ignore is not None and name in ignore:
                continue

            imp = importlib.import_module(name)  # import the module

            # get module level attributes exposed by __all__
            attrs = sys.modules[imp.__name__].__all__

            # create handles to those attributes in the module
            for attr in attrs:
                setattr(this_module, attr, getattr(imp, attr))

            loaded.append(name)

    return loaded
