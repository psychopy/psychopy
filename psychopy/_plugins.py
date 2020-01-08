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


def load_api_plugins(module, plugin='psychopy_.+'):
    """Load a plugin to extend PsychoPy's coder API.

    This function searches for any installed packages starting with `plugin`,
    imports them, and add their attributes to namespace of `module`. Only
    attributes defined explicitly `__all__` in the found packages will be
    assigned attributes. Therefore, any packages that wish to extend the
    PsychoPy API must have an `__all__` statement. Note that `module` should
    be imported prior to attempting to loading a plugin.

    Parameters
    ----------
    module : str
        Import path of the module you wish to install the plugin (eg.
        psychopy.visual).
    plugin : str or None
        Name of the plugin package to load. A name can also be given as a
        regular expression for loading multiple packages with similar names. If
        `None`, the `plugin` name will be derived from the `module` name and
        all packages prefixed with the name will be loaded. For instance,
        a if 'psychopy.visual' is given, all packages installed on the system
        starting with names starting with 'psychopy_visual_' will be loaded.

    Returns
    -------
    list
        Names of the plugins loaded. No plugins were loaded if the list is
        empty.

    Warnings
    --------
    Make sure that plugins installed on your system are from reputable sources,
    as they may contain malware!

    Examples
    --------
    Load all installed packages into the namespace of `psychopy.visual` prefixed
    with `psychopy_visual_`::

        load_api_plugins('psychopy.visual', 'psychopy_visual_.+')

    This can be called from the `__init__.py` of a package/module directory by
    using the `__name__` attribute::

        load_api_plugins(__name__, 'psychopy_something_.+')

    Load all plugins on the system with names similar to `module`::

        # if __name__ == 'psychopy.visual', all packages starting with
        # `psychopy_visual_` will be loaded.
        load_api_plugins(__name__)

    """
    try:
        this_module = sys.modules[module]
    except KeyError:
        raise ModuleNotFoundError(
            'Cannot find module `{}`. Has it been imported yet?'.format(module))

    # generate a plugin name
    if plugin is None:
        plugin = ''
        for i in module.split('.'):
            plugin += i + '_'
        plugin += '.+'

    # iterate over packages
    loaded = []
    for finder, name, ispkg in pkgutil.iter_modules():
        if re.search(plugin, name):
            imp = importlib.import_module(name)  # import the module

            # get module level attributes exposed by __all__
            attrs = sys.modules[imp.__name__].__all__

            # create handles to those attributes in the module
            for attr in attrs:
                setattr(this_module, attr, getattr(imp, attr))

            loaded.append(name)

    return loaded

