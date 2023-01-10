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
    'installPackage',
    'uninstallPackage',
    'getInstalledPackages',
    'getPackageMetadata',
    'getPypiInfo',
    'isInstalled',
]


import subprocess as sp
from psychopy.preferences import prefs
from psychopy.localization import _translate
import pkg_resources
import sys
import os
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


def installPackage(package, target=None, upgrade=False, forceReinstall=False,
                   noDeps=False):
    """Install a package using the default package management system.

    This is intended to be used only by PsychoPy itself for installing plugins
    and packages through the builtin package manager.

    Parameters
    ----------
    package : str
        Package name (e.g., `'psychopy-connect'`, `'scipy'`, etc.) with version
        if needed. You may also specify URLs to Git repositories and such.
    target : str or None
        Location to install packages to. This defaults to the 'packages' folder
        in the user PsychoPy folder if `None`.
    upgrade : bool
        Upgrade the specified package to the newest available version.
    forceReinstall : bool
        If `True`, the package and all it's dependencies will be reinstalled if
        they are present in the current distribution.
    noDeps : bool
        Don't install dependencies if `True`.

    Returns
    -------
    bool
        `True` if the package installed without errors. If `False`, check
        'stderr' for more information. The package may still have installed
        correctly, but it doesn't work.

    """
    if target is None:
        target = prefs.paths['packages']

    # check the directory exists before installing
    if not os.path.exists(target):
        raise NotADirectoryError(
            'Cannot install package "{}" to "{}", directory does not '
            'exist.'.format(package, target))

    # construct the pip command and execute as a subprocess
    cmd = [sys.executable, "-m", "pip", "install", package, "--target", target]

    # optional args
    if upgrade:
        cmd.append('--upgrade')
    if forceReinstall:
        cmd.append('--force-reinstall')
    if noDeps:
        cmd.append('--no-deps')

    cmd.append('--no-input')  # do not prompt, we cannot accept input
    cmd.append('--no-color')  # no color for console, not supported

    # run command in subprocess
    output = sp.Popen(
        cmd,
        stdout=sp.PIPE,
        stderr=sp.PIPE,
        shell=False,
        universal_newlines=True)
    stdout, stderr = output.communicate()  # blocks until process exits

    sys.stdout.write(stdout)
    sys.stderr.write(stderr)

    if stderr:   # any error, return False
        return False

    return True


def uninstallPackage(package):
    """Uninstall a package from the current distribution.

    Parameters
    ----------
    package : str
        Package name (e.g., `'psychopy-connect'`, `'scipy'`, etc.) with version
        if needed. You may also specify URLs to Git repositories and such.

    Returns
    -------
    bool
        `True` if the package removed without errors. If `False`, check 'stderr'
        for more information. The package may still have uninstalled correctly,
        but some other issues may have arose during the process.

    Notes
    -----
    * The `--yes` flag is appened to the pip command. No confirmation will be
      requested if the package already exists.

    """
    # construct the pip command and execute as a subprocess
    cmd = [sys.executable, "-m", "pip", "uninstall", package, "--yes"]

    cmd.append('--no-input')  # cancels out `--yes`?
    cmd.append('--no-color')  # no color for console, not supported

    # run command in subprocess
    output = sp.Popen(
        cmd,
        stdout=sp.PIPE,
        stderr=sp.PIPE,
        shell=False,
        universal_newlines=True)
    stdout, stderr = output.communicate()  # blocks until process exits

    sys.stdout.write(stdout)
    sys.stderr.write(stderr)

    if stderr:   # any error, return False
        return False

    return True


def isInstalled(packageName):
    """Check if a package is presently installed and reachable.

    Returns
    -------
    bool
        `True` if the specified package is installed.

    """
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

