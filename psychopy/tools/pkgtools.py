#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Tools for working with packages within the Python environment.
"""

__all__ = [
    'getUserPackagesPath',
    'getDistributions',
    'addDistribution',
    'installPackage',
    'uninstallPackage',
    'getInstalledPackages',
    'getPackageMetadata',
    'getPypiInfo',
    'isInstalled',
    'refreshPackages'
]


import subprocess as sp
from psychopy.preferences import prefs
from psychopy.localization import _translate
import psychopy.logging as logging
import importlib
import pkg_resources
import sys
import os
import os.path
import requests
import shutil
import site

# On import we want to configure the user site-packages dir and add it to the
# import path. 

# set user site-packages dir
if os.environ.get('PSYCHOPYNOPACKAGES', '0') == '1':
    site.ENABLE_USER_SITE = True
    site.USER_SITE = prefs.paths['userPackages']
    site.USER_BASE = None
    logging.debug(
        'User site-packages dir set to: %s' % site.getusersitepackages())
    
    # add paths from main plugins/packages (installed by plugins manager)
    site.addsitedir(prefs.paths['userPackages'])  # user site-packages
    site.addsitedir(prefs.paths['userInclude'])  # user include
    site.addsitedir(prefs.paths['packages'])  # base package dir

if not site.USER_SITE in sys.path:
    site.addsitedir(site.getusersitepackages()) 

# add packages dir to import path
# if prefs.paths['packages'] not in pkg_resources.working_set.entries:
#     pkg_resources.working_set.add_entry(prefs.paths['packages'])

# cache list of packages to speed up checks
_installedPackageCache = []
_installedPackageNamesCache = []


class PluginStub:
    """
    Class to handle classes which have moved out to plugins.

    Example
    -------
    ```
    class NoiseStim(PluginStub, plugin="psychopy-visionscience", doclink="https://psychopy.github.io/psychopy-visionscience/builder/components/NoiseStimComponent/):
    ```
    """

    def __init_subclass__(cls, plugin, doclink="https://plugins.psychopy.org/directory.html"):
        """
        Subclassing PluginStub will create documentation pointing to the new documentation for the replacement class.
        """
        # store ref to plugin and docs link
        cls.plugin = plugin
        cls.doclink = doclink
        # create doc string point to new location
        cls.__doc__ = (
            "`{mro}` is now located within the `{plugin}` plugin. You can find the documentation for it `here <{doclink}>`_."
        ).format(
            mro=cls.__mro__,
            plugin=plugin,
            doclink=doclink
        )
    
    def __call__(self, *args, **kwargs):
        """
        When initialised, rather than creating an object, will log an error.
        """
        raise NameError(
            "Support for `{mro}` is not available this session. Please install "
            "`{plugin}` and restart the session to enable support."
        ).format(
            mro=type(self).__mro__,
            plugin=self.plugin,
        )


def refreshPackages():
    """Refresh the packaging system.

    This needs to be called after adding and removing packages, or making any
    changes to `sys.path`. Functions `installPackages` and `uninstallPackages`
    calls this everytime.

    Warnings
    --------
    Calling this forces a reload of `pkg_resources`. This can cause side-effects
    for other modules using it!

    """
    global _installedPackageCache
    global _installedPackageNamesCache

    _installedPackageCache.clear()
    _installedPackageNamesCache.clear()

    importlib.reload(pkg_resources)  # reload since package paths might be stale

    # this is like calling `pip freeze` and parsing the output, but faster!
    for pkg in pkg_resources.working_set:
        thisPkg = pkg_resources.get_distribution(pkg.key)
        _installedPackageCache.append(
            (thisPkg.project_name, thisPkg.version))
        _installedPackageNamesCache.append(pkg_resources.safe_name(
            thisPkg.project_name))  # names only


def getUserPackagesPath():
    """Get the path to the user's PsychoPy package directory.

    This is the directory that plugin and extension packages are installed to
    which is added to `sys.path` when `psychopy` is imported.

    Returns
    -------
    str
        Path to user's package directory.

    """
    return prefs.paths['packages']


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
    if distPath not in pkg_resources.working_set.entries:
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
        Location to install packages to directly to. If `None`, the user's
        package directory is set at the prefix and the package is installed
        there. If a `target` is specified, the package top-level directory
        must be added to `sys.path` manually.
    upgrade : bool
        Upgrade the specified package to the newest available version.
    forceReinstall : bool
        If `True`, the package and all it's dependencies will be reinstalled if
        they are present in the current distribution.
    noDeps : bool
        Don't install dependencies if `True`.

    Returns
    -------
    tuple
        `True` if the package installed without errors. If `False`, check
        'stderr' for more information. The package may still have installed
        correctly, but it doesn't work. Second value contains standard output
        and error from the subprocess.

    """
    if target is None:
        target = prefs.paths['packages']

    # check the directory exists before installing
    if not os.path.exists(target):
        raise NotADirectoryError(
            'Cannot install package "{}" to "{}", directory does not '
            'exist.'.format(package, target))

    # construct the pip command and execute as a subprocess
    cmd = [sys.executable, "-m", "pip", "install", package]

    # optional args
    if target is None:  # default to user packages dir
        cmd.append('--prefix')
        cmd.append(prefs.paths['packages'])
    else:
        cmd.append('--target')
        cmd.append(target)
    if upgrade:
        cmd.append('--upgrade')
    if forceReinstall:
        cmd.append('--force-reinstall')
    if noDeps:
        cmd.append('--no-deps')

    cmd.append('--no-input')  # do not prompt, we cannot accept input
    cmd.append('--no-color')  # no color for console, not supported
    cmd.append('--no-warn-conflicts')  # silence non-fatal errors

    # get the environment for the subprocess
    env = os.environ.copy()

    # run command in subprocess
    output = sp.Popen(
        cmd,
        stdout=sp.PIPE,
        stderr=sp.PIPE,
        shell=False,
        universal_newlines=True,
        env=env)
    stdout, stderr = output.communicate()  # blocks until process exits

    sys.stdout.write(stdout)
    sys.stderr.write(stderr)

    refreshPackages()

    # Return True if installed, False if not
    retcode = isInstalled(package)
    # Return the return code and a dict of information from the console
    return retcode, {"cmd": cmd, "stdout": stdout, "stderr": stderr}


def _getUserPackageTopLevels():
    """Get the top-level directories listed in package metadata installed to
    the user's PsychoPy directory.

    Returns
    -------
    dict
        Mapping of project names and top-level packages associated with it which
        are present in the user's PsychoPy packages directory.

    """
    # get all directories
    userPackageDir = getUserPackagesPath()
    userPackageDirs = os.listdir(userPackageDir)

    foundTopLevelDirs = dict()
    for foundDir in userPackageDirs:
        if not  foundDir.endswith('.dist-info'):
            continue

        topLevelPath = os.path.join(userPackageDir, foundDir, 'top_level.txt')
        if not os.path.isfile(topLevelPath):
            continue  # file not present

        with open(topLevelPath, 'r') as tl:
            packageTopLevelDirs = []
            for line in tl.readlines():
                line = line.strip()
                pkgDir = os.path.join(userPackageDir, line)
                if not os.path.isdir(pkgDir):
                    continue

                packageTopLevelDirs.append(pkgDir)

        foundTopLevelDirs[foundDir] = packageTopLevelDirs

    return foundTopLevelDirs


def _isUserPackage(package):
    """Determine if the specified package in installed to the user's PsychoPy
    package directory.

    Parameters
    ----------
    package : str
        Project name of the package (e.g. `psychopy-crs`) to check.

    Returns
    -------
    bool
        `True` if the package is present in the user's PsychoPy directory.

    """
    userPackagePath = getUserPackagesPath()
    for pkg in pkg_resources.working_set:
        if pkg_resources.safe_name(package) == pkg.key:
            thisPkg = pkg_resources.get_distribution(pkg.key)
            if thisPkg.location == userPackagePath:
                return True

    return False


def _uninstallUserPackage(package):
    """Uninstall packages in PsychoPy package directory.

    This function will remove packages from the user's PsychoPy directory since
    we can't do so using 'pip', yet. This reads the metadata associated with
    the package and attempts to remove the packages.

    Parameters
    ----------
    package : str
        Project name of the package (e.g. `psychopy-crs`) to uninstall.

    Returns
    -------
    bool
        `True` if the package has been uninstalled successfully. Second value
        contains standard output and error from the subprocess.

    """
    # todo - check if we imported the package and warn that we're uninstalling
    #        something we're actively using.
    # string to use as stdout
    stdout = ""
    # take note of this function being run as if it was a command
    cmd = f"python psychopy.tools.pkgtools._uninstallUserPackage(package)"

    userPackagePath = getUserPackagesPath()

    msg = 'Attempting to uninstall user package `{}` from `{}`.'.format(
        package, userPackagePath)
    logging.info(msg)
    stdout += msg + "\n"

    # figure out he name of the metadata directory
    pkgName = pkg_resources.safe_name(package)
    thisPkg = pkg_resources.get_distribution(pkgName)

    # build path to metadata based on project name
    pathHead = pkg_resources.to_filename(thisPkg.project_name) + '-'
    metaDir = pathHead + thisPkg.version
    metaDir += '' if thisPkg.py_version is None else '.' + thisPkg.py_version
    metaDir += '.dist-info'

    # check if that directory exists
    metaPath = os.path.join(userPackagePath, metaDir)
    if not os.path.isdir(metaPath):
        return False, {
            "cmd": cmd,
            "stdout": stdout,
            "stderr": "No package metadata found at {metaPath}"}

    # Get the top-levels for all packages in the user's PsychoPy directory, this
    # is intended to safely remove packages without deleting common directories
    # like `bin` which some packages insist on putting in there.
    allTopLevelPackages = _getUserPackageTopLevels()

    # get the top-levels associated with the package we want to uninstall
    pkgTopLevelDirs = allTopLevelPackages[metaDir].copy()
    del allTopLevelPackages[metaDir]  # remove from mapping

    # Check which top-level directories are safe to remove if they are not used
    # by other packages.
    toRemove = []
    for pkgTopLevel in pkgTopLevelDirs:
        safeToRemove = True
        for otherPkg, otherTopLevels in allTopLevelPackages.items():
            if pkgTopLevel in otherTopLevels:
                # check if another version of this package is sharing the dir
                if otherPkg.startswith(pathHead):
                    msg = (
                        'Found metadata for an older version of package `{}` in '
                        '`{}`. This will also be removed.'
                    ).format(pkgName, otherPkg)
                    logging.warning(msg)
                    stdout += msg + "\n"
                    toRemove.append(otherPkg)
                else:
                    # unrelated package
                    msg = (
                        'Found matching top-level directory `{}` in metadata '
                        'for `{}`. Can not safely remove this directory since '
                        'another package appears to use it.'
                    ).format(pkgTopLevel, otherPkg)
                    logging.warning(msg)
                    stdout += msg + "\n"
                    safeToRemove = False
                    break

        if safeToRemove:
            toRemove.append(pkgTopLevel)

    # delete modules from the paths we found
    for rmDir in toRemove:
        if os.path.isfile(rmDir):
            msg = (
                'Removing file `{}` from user package directory.'
            ).format(rmDir)
            logging.info(msg)
            stdout += msg + "\n"
            os.remove(rmDir)
        elif os.path.isdir(rmDir):
            msg = (
                'Removing directory `{}` from user package '
                'directory.'
            ).format(rmDir)
            logging.info(msg)
            stdout += msg + "\n"
            shutil.rmtree(rmDir)

    # cleanup by also deleting the metadata path
    shutil.rmtree(metaPath)

    msg = 'Uninstalled package `{}`.'.format(package)
    logging.info(msg)
    stdout += msg + "\n"

    # Return the return code and a dict of information from the console
    return True, {
        "cmd": cmd,
        "stdout": stdout,
        "stderr": ""}


def uninstallPackage(package):
    """Uninstall a package from the current distribution.

    Parameters
    ----------
    package : str
        Package name (e.g., `'psychopy-connect'`, `'scipy'`, etc.) with version
        if needed. You may also specify URLs to Git repositories and such.

    Returns
    -------
    tuple
        `True` if the package removed without errors. If `False`, check 'stderr'
        for more information. The package may still have uninstalled correctly,
        but some other issues may have arose during the process.

    Notes
    -----
    * The `--yes` flag is appended to the pip command. No confirmation will be
      requested if the package already exists.

    """
    if _isUserPackage(package):  # delete 'manually' if in package dir
        return (_uninstallUserPackage(package),
                {"cmd": '', "stdout": '', "stderr": ''})
    else:  # use the following if in the main package dir
        # construct the pip command and execute as a subprocess
        cmd = [sys.executable, "-m", "pip", "uninstall", package, "--yes",
               '--no-input', '--no-color']

        # setup the environment to use the user's site-packages
        env = os.environ.copy()

        # run command in subprocess
        output = sp.Popen(
            cmd,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            shell=False,
            env=env,
            universal_newlines=True)
        stdout, stderr = output.communicate()  # blocks until process exits

        sys.stdout.write(stdout)
        sys.stderr.write(stderr)

        # if any error, return code should be False
        retcode = bool(stderr)

    # Return the return code and a dict of information from the console
    return retcode, {"cmd": cmd, "stdout": stdout, "stderr": stderr}


def getInstallState(package):
    """
    Get a code indicating the installed state of a given package.

    Returns
    -------
    str
        "s": Installed to system environment
        "u": Installed to user space
        "n": Not installed
    str or None
        Version number installed, or None if not installed
    """
    # If given None, return None
    if package is None:
        return None, None

    if isInstalled(package):
        # If installed, get version from metadata
        metadata = getPackageMetadata(package)
        version = metadata.get('Version', None)
        # Determine whether installed to system or user
        if _isUserPackage(package):
            state = "u"
        else:
            state = "s"
    else:
        # If not installed, we know the state and version
        state = "n"
        version = None

    return state, version


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


def isInstalled(packageName):
    """Check if a package is presently installed and reachable.

    Returns
    -------
    bool
        `True` if the specified package is installed.

    """
    # installed packages are given as keys in the resulting dicts
    return pkg_resources.safe_name(packageName) in _installedPackageNamesCache


def getPackageMetadata(packageName):
    """Get the metadata for a specified package.

    Parameters
    ----------
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
        import wx
        dlg = wx.MessageDialog(None, message=_translate(
            "Could not get info for package {}. Reason:\n"
            "\n"
            "{}"
        ).format(packageName,err), style=wx.ICON_ERROR)
        if not silence:
            dlg.ShowModal()
        return

    if 'info' not in data:
        # handle case where the data cannot be retrived
        return {
            'name': packageName,
            'author': 'Unknown',
            'authorEmail': 'Unknown',
            'license': 'Unknown',
            'summary': '',
            'desc': 'Failed to get package info from PyPI.',
            'releases': [],
        }
    else:
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
    pass
