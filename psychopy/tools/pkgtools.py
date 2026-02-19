#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
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
    'refreshPackages',
    'isUserPackage',
    'isSystemPackage',
    'getInstallState'
]


from pathlib import Path
import subprocess as sp
from psychopy.preferences import prefs
from psychopy.localization import _translate
import psychopy.logging as logging
import importlib, importlib.metadata, importlib.resources
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
    site.USER_SITE = str(prefs.paths['userPackages'])
    site.USER_BASE = None
    logging.debug(
        'User site-packages dir set to: %s' % site.getusersitepackages())

    # add paths from main plugins/packages (installed by plugins manager)
    site.addsitedir(prefs.paths['userPackages'])  # user site-packages
    site.addsitedir(prefs.paths['userInclude'])  # user include
    site.addsitedir(prefs.paths['packages'])  # base package dir

if site.USER_SITE not in sys.path:
    site.addsitedir(site.getusersitepackages())

# cache list of packages to speed up checks
_installedPackageCache = {'system': [], 'user': []}
_installedPackageNamesCache = {'system': [], 'user': []}

# reference the user packages path
USER_PACKAGES_PATH = str(prefs.paths['userPackages'])

_isVenv = hasattr(sys, 'real_prefix') or (
    hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)


def refreshPackages():
    """Refresh the packaging system.

    This needs to be called after adding and removing packages, or making any
    changes to `sys.path`. Functions `installPackages` and `uninstallPackages`
    calls this everytime.
    """
    global _installedPackageCache
    global _installedPackageNamesCache

    def _getPackageInventory(searchPath):
        # iterate through installed packages in the user folder
        searchPath = [searchPath] if isinstance(searchPath, str) else searchPath
        foundPackages = []
        for dist in importlib.metadata.distributions(path=searchPath):
            # get name if in 3.8
            if sys.version_info.major == 3:
                if sys.version_info.minor <= 9:
                    distName = dist.metadata['name']
                else:
                    distName = dist.name
            else:
                raise RuntimeError(
                    "PsychoPy only supports Python 3.8 and above. "
                    "Please upgrade your Python installation.")
            
            foundPackages.append((distName, dist.version))
            
        return foundPackages
    
    # installed packages in the system path
    _installedPackageCache['system'] = _getPackageInventory(sys.path)
    _installedPackageNamesCache['system'] = [
        pkg[0] for pkg in _installedPackageCache['system']]
    
    global _isVenv
    if not _isVenv:
        # if we're not in a venv, also check user packages path
        _installedPackageCache['user'] = _getPackageInventory(USER_PACKAGES_PATH)
        _installedPackageNamesCache['user'] = [
            pkg[0] for pkg in _installedPackageCache['user']]


def getUserPackagesPath():
    """Get the path to the user's PsychoPy package directory.

    This is the directory that plugin and extension packages are installed to
    which is added to `sys.path` when `psychopy` is imported.

    Returns
    -------
    str
        Path to user's package directory.

    """
    return prefs.paths['userPackages']


def getDistributions():
    """Get a list of active distributions in the current environment.

    Returns
    -------
    list
        List of paths where active distributions are located. These paths
        refer to locations where packages containing importable modules and
        plugins can be found.

    """
    logging.error(
        "`pkgtools.getDistributions` is now deprecated as packages are detected via "
        "`importlib.metadata`, which doesn't need a separate working set from the system path. "
        "Please use `sys.path` instead."
    )
    return sys.path


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
    logging.error(
        "`pkgtools.addDistribution` is now deprecated as packages are detected via "
        "`importlib.metadata`, which doesn't need a separate working set from the system path. "
        "Please use `sys.path.append` instead."
    )
    if distPath not in sys.path:
        sys.path.append(distPath)


def installPackage(
    package,
    target=None,
    upgrade=False,
    forceReinstall=False,
    noDeps=False,
    awaited=True,
    outputCallback=None,
    terminateCallback=None,
    extra=None,
):
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
    awaited : bool
        If False, then use an asynchronous install process - this function will return right away
        and the plugin install will happen in a different thread.
    outputCallback : function
        Function to be called when any output text is received from the process performing the
        install. Not used if awaited=True.
    terminateCallback : function
        Function to be called when installation is finished. Not used if awaited=True.
    extra : dict
        Extra information to be supplied to the install thread when installing asynchronously.
        Not used if awaited=True.

    Returns
    -------
    tuple or psychopy.app.jobs.Job
        If `awaited=True`:
            `True` if the package installed without errors. If `False`, check
            'stderr' for more information. The package may still have installed
            correctly, but it doesn't work. Second value contains standard output
            and error from the subprocess.
        If `awaited=False`:
            Returns the job (thread) which is running the install.
    """
    # convert extra to dict
    if extra is None:
        extra = {}
    # assume non-editable
    editable = []
    # handle install from file
    try:
        packagePath = Path(package)
    except:
        pass
    else:
        if packagePath.is_file():
            # if file is a pyproject.toml, use the containing folder
            if packagePath.name == "pyproject.toml":
                packagePath = packagePath.parent
                package = str(packagePath)
        if packagePath.is_dir():
            # if given a folder, add quotation marks and an editable flag
            editable.append("-e")
    # construct the pip command and execute as a subprocess
    cmd = [sys.executable, "-m", "pip", "install", *editable, package]

    # optional args
    if target is None:  # default to user packages dir
        # check if we are in a virtual environment, if so, dont use --user
        if hasattr(sys, 'real_prefix') or (
                hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            # we are in a venv
            logging.warning(
                "You are installing a package inside a virtual environment. "
                "The package will be installed in the user site-packages "
                "directory."
            )
        else:
            cmd.append('--user')
    else:
        # check the directory exists before installing
        if target is not None and not os.path.exists(target):
            raise NotADirectoryError(
                'Cannot install package "{}" to "{}", directory does not '
                'exist.'.format(package, target))

        cmd.append('--target')
        cmd.append(target)
    if upgrade:
        cmd.append('--upgrade')
    if forceReinstall:
        cmd.append('--force-reinstall')
    if noDeps:
        cmd.append('--no-deps')

    cmd.append('--prefer-binary')  # use binary wheels if available
    cmd.append('--no-input')  # do not prompt, we cannot accept input
    cmd.append('--no-color')  # no color for console, not supported
    cmd.append('--no-warn-conflicts')  # silence non-fatal errors
    cmd.append('--disable-pip-version-check')  # do not check for pip updates

    # get the environment for the subprocess
    env = os.environ.copy()

    # if unawaited, try to get jobs handler
    if not awaited:
        try:
            from psychopy.app import jobs
        except ModuleNotFoundError:
            logging.warn(_translate(
                "Could not install package {} asynchronously as psychopy.app.jobs is not found. "
                "Defaulting to synchronous install."
            ).format(package))
            awaited = True
    if awaited:
        # if synchronous, just use regular command line
        proc = sp.Popen(
            cmd,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            shell=False,
            universal_newlines=True,
            env=env
        )
        # run
        stdout, stderr = proc.communicate()
        # print output
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        # refresh packages once done
        refreshPackages()

        return isInstalled(package), {'cmd': cmd, 'stdout': stdout, 'stderr': stderr}
    else:
        # otherwise, use a job (which can provide live feedback)
        proc = jobs.Job(
            parent=None,
            command=cmd,
            inputCallback=outputCallback,
            errorCallback=outputCallback,
            terminateCallback=terminateCallback,
            extra=extra,
        )
        proc.start(env=env)

        return proc


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
        if not foundDir.endswith('.dist-info'):
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


def isSystemPackage(package):
    """Determine if the specified package in installed to the system Python
    directory.

    Parameters
    ----------
    package : str
        Project name of the package (e.g. `psychopy-crs`) to check.

    Returns
    -------
    bool
        `True` if the package is present in the system Python directory.

    """
    return package in _installedPackageNamesCache['system']


def isUserPackage(package):
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
    return package in _installedPackageNamesCache['user']


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
    cmd = "python psychopy.tools.pkgtools._uninstallUserPackage(package)"

    userPackagePath = getUserPackagesPath()

    msg = 'Attempting to uninstall user package `{}` from `{}`.'.format(
        package, userPackagePath)
    logging.info(msg)
    stdout += msg + "\n"

    # get distribution object
    thisPkg = importlib.metadata.distribution(package)
    # iterate through its files
    for file in thisPkg.files:
        # get absolute path (not relative to package dir)
        absPath = thisPkg.locate_file(file)
        # skip pycache
        if absPath.stem == "__pycache__":
            continue
        # delete file
        if absPath.is_file():
            try:
                absPath.unlink()
            except PermissionError as err:
                stdout += _translate(
                    "Could not remove {absPath}, reason: {err}".format(absPath=absPath, err=err)
                )
        # skip pycache
        if absPath.parent.stem == "__pycache__":
            continue
        # delete folder if empty
        if absPath.parent.is_dir() and not [f for f in absPath.parent.glob("*")]:
            # delete file
            try:
                absPath.parent.unlink()
            except PermissionError as err:
                stdout += _translate(
                    "Could not remove {absPath}, reason: {err}".format(absPath=absPath, err=err)
                )

    # log success
    msg = 'Uninstalled package `{}`.'.format(package)
    logging.info(msg)
    stdout += msg + "\n"

    # return the return code and a dict of information from the console
    return True, {
        "cmd": cmd,
        "stdout": stdout,
        "stderr": ""
    }


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
    # if _isUserPackage(package):  # delete 'manually' if in package dir
    #     return (_uninstallUserPackage(package),
    #             {"cmd": '', "stdout": '', "stderr": ''})
    # else:  # use the following if in the main package dir
    
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
        if isUserPackage(package):
            state = "u"
        else:
            state = "s"
    else:
        # If not installed, we know the state and version
        state = "n"
        version = None

    return state, version


def getInstalledPackages(where='both'):
    """Get a list of installed packages and their versions.

    Parameters
    ----------
    where : str
        Location to check for installed packages. Can be one of the following:
        - 'system': Check only the system Python environment.
        - 'user': Check only the user's PsychoPy package directory.
        - 'both': Check both locations (default).

    Returns
    -------
    list
         List of installed packages and their versions i.e. `('PsychoPy',
        '2021.3.1')`.

    """
    global _installedPackageCache

    if _installedPackageCache['system'] == []:
        refreshPackages()

    if where == 'system':
        return _installedPackageCache['system']
    elif where == 'user':
        return _installedPackageCache['user']
    elif where == 'both':  # combined into one list
        return list(set(_installedPackageCache['system']) | set(_installedPackageCache['user']))
    else:
        raise ValueError(
            "Parameter 'where' must be one of 'system', 'user', or 'both'.")


def isInstalled(packageName, where='both'):
    """Check if a package is presently installed and reachable.

    Parameters
    ----------
    packageName : str
        Project name of package to check.
    where : str
        Location to check for the package. Can be one of the following:
        - 'system': Check only the system Python environment.
        - 'user': Check only the user's PsychoPy package directory.
        - 'both': Check both locations (default).

    Returns
    -------
    bool
        `True` if the specified package is installed.

    """
    global _installedPackageNamesCache

    if _installedPackageNamesCache['system'] == []:
        refreshPackages()

    if where == 'system':
        return packageName in _installedPackageNamesCache['system']
    elif where == 'user':
        return packageName in _installedPackageNamesCache['user']
    elif where == 'both':
        return packageName in _installedPackageNamesCache['system'] or \
               packageName in _installedPackageNamesCache['user']
    else:
        raise ValueError(
            "Parameter 'where' must be one of 'system', 'user', or 'both'.")    


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
    try:
        dist = importlib.metadata.distribution(packageName)
    except importlib.metadata.PackageNotFoundError:
        return  # do nothing

    metadict = dict(dist.metadata)

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
        ).format(packageName, err), style=wx.ICON_ERROR)
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
