#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Tools for working with packages within the Python environment.
"""

__all__ = [
    'getDistributions',
    'addDistribution',
    'getInstalledPackages',
    'getPackageMetadata',
    'getPypiInfo',
    'isInstalled',
]

from psychopy.localization import _translate
import pkg_resources
import requests
import wx


def getDistributions():
    """Get a list of active distributions in the current environment.

    Returns
    -------
    list
        List of paths where active distributions are located. These paths
        refer to locations where packages containing importable modules and
        plugins can be found.

    """
    toReturn = list()
    toReturn.extend(pkg_resources.working_set.entries)  # copy

    return toReturn


def addDistribution(distPath):
    """Add a distribution to the current environment.

    This function can be used to add a distribution to the present environment
    which contains Python packages that have importable modules or plugins.

    Parameters
    ----------
    distPath : str
        Path to distribution. May be either a path for a directory or archive
        file (e.g. ZIP).

    """
    pkg_resources.working_set.add_entry(distPath)


def isInstalled(packageName):
    return packageName in dict(getInstalledPackages())


def getInstalledPackages():
    """Get a list of installed packages and their versions.

    Returns
    -------
    list
        List of installed packages and their versions i.e. `('PsychoPy',
        '2021.3.1')`.

    """
    # this is like calling `pip freeze` and parsing the output, but faster!
    installedPackages = []
    for pkg in pkg_resources.working_set:
        thisPkg = pkg_resources.get_distribution(pkg.key)
        installedPackages.append(
            (thisPkg.project_name, thisPkg.version))

    return installedPackages


def getPackageMetadata(packageName):
    """Get the metadata for a specified package.

    Paramters
    ---------
    packageName : str
        Project name of package to get metadata from.

    Returns
    -------
    dict or None
        Dictionary of metadata fields. If `None` is returned, the package isn't
        present in the current distribution.

    """
    import email.parser

    try:
        dist = pkg_resources.get_distribution(packageName)
    except pkg_resources.DistributionNotFound:
        return  # do nothing

    metadata = dist.get_metadata(dist.PKG_INFO)

    # parse the metadata using
    metadict = dict()
    for key, val in email.message_from_string(metadata).raw_items():
        metadict[key] = val

    return metadict


def getPypiInfo(packageName, silence=False):
    try:
        data = requests.get(
            f"https://pypi.python.org/pypi/{packageName}/json"
        ).json()
    except (requests.ConnectionError, requests.JSONDecodeError) as err:
        dlg = wx.MessageDialog(None, message=_translate(
            f"Could not get info for package {packageName}. Reason:\n"
            f"\n"
            f"{err}"
        ), style=wx.ICON_ERROR)
        if not silence:
            dlg.ShowModal()
        return

    return {
        'name': data['info'].get('Name', packageName),
        'author': data['info'].get('author', 'Unknown'),
        'authorEmail': data['info'].get('author_email', 'Unknown'),
        'license': data['info'].get('license', 'Unknown'),
        'summary': data['info'].get('summary', ''),
        'desc': data['info'].get('description', ''),
        'releases': list(data['releases']),
    }


if __name__ == "__main__":
    getPackageMetadata('sdfdsfasdf')

