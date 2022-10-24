#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Tools for working with packages.
"""

__all__ = ['getInstalledPackages']

import pkg_resources


def getInstalledPackages():
    """Get a dictionary of installed packages on the system with metadata.

    Returns
    -------
    dict
        Mapping where keys (`str`) are found package names and values are
        metadata. Metadata are mappings where keys (`str`) are field names and
        values (`Any`) are data related to each field.

    """
    toReturn = dict()

    # get the list of packages installed on the system
    installedPackages = pkg_resources.working_set
    if not installedPackages:
        return toReturn

    # get packages and metadata
    for pkg in installedPackages:
        pkg = pkg_resources.get_distribution(pkg.key)
        metadata = pkg.get_metadata(pkg.PKG_INFO)
        toReturn[pkg.key] = metadata

    return toReturn


if __name__ == "__main__":
    pass
