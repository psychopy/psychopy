#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
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
]


import subprocess as sp
from psychopy.preferences import prefs
from psychopy.localization import _translate
from psychopy.app.themes import icons, handlers
import psychopy.logging as logging
import pkg_resources
import sys
import os
import os.path
import requests
import shutil
import wx


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


class InstallErrorDlg(wx.Dialog, handlers.ThemeMixin):
    """
    Dialog to display when something fails to install, contains info on what
    command was tried and what output was received.
    """
    def __init__(self, label, caption=_translate("PIP error"), cmd="", stdout="", stderr=""):
        from psychopy.app.themes import fonts
        # Initialise
        wx.Dialog.__init__(
            self, None,
            size=(480, 620),
            title=caption,
            style=wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.CAPTION
        )
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Create title sizer
        self.title = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.title, border=6, flag=wx.ALL | wx.EXPAND)
        # Create icon
        self.icon = wx.StaticBitmap(
            self, size=(32, 32),
            bitmap=icons.ButtonIcon(stem="stop", size=32).bitmap
        )
        self.title.Add(self.icon, border=6, flag=wx.ALL | wx.EXPAND)
        # Create title
        self.titleLbl = wx.StaticText(self, label=label)
        self.titleLbl.SetFont(fonts.appTheme['h3'].obj)
        self.title.Add(self.titleLbl, proportion=1, border=6, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        # Show what we tried
        self.inLbl = wx.StaticText(self, label=_translate("We tried:"))
        self.sizer.Add(self.inLbl, border=6, flag=wx.ALL | wx.EXPAND)
        self.inCtrl = wx.TextCtrl(self, value=cmd, style=wx.TE_READONLY)
        self.inCtrl.SetBackgroundColour("white")
        self.inCtrl.SetFont(fonts.appTheme['code'].obj)
        self.sizer.Add(self.inCtrl, border=6, flag=wx.ALL | wx.EXPAND)
        # Show what we got
        self.outLbl = wx.StaticText(self, label=_translate("We got:"))
        self.sizer.Add(self.outLbl, border=6, flag=wx.ALL | wx.EXPAND)
        self.outCtrl = wx.TextCtrl(self, value=f"{stdout}\n{stderr}",
                                   size=(-1, 620), style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.outCtrl.SetFont(fonts.appTheme['code'].obj)
        self.sizer.Add(self.outCtrl, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)

        # Make buttons
        self.btns = self.CreateStdDialogButtonSizer(flags=wx.OK)
        self.border.Add(self.btns, border=6, flag=wx.ALIGN_RIGHT | wx.ALL)

        self.Layout()
        self._applyAppTheme()

    def ShowModal(self):
        # Make error noise
        wx.Bell()
        # Show as normal
        wx.Dialog.ShowModal(self)


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
        `True` if the package has been uninstalled successfully.

    """
    # todo - check if we imported the package and warn that we're uninstalling
    #        something we're actively using.
    userPackagePath = getUserPackagesPath()

    logging.info('Attempting to uninstall user package `{}` from `{}`.'.format(
        package, userPackagePath))

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
        return False

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
                    logging.warning(
                        'Found metadata for an older version of package '
                        '`{}` in `{}`. This will also be removed.'.format(
                            pkgName, otherPkg))
                    toRemove.append(otherPkg)
                else:
                    # unrelated package
                    logging.warning(
                        'Found matching top-level directory `{}` in metadata '
                        'for `{}`. Can not safely remove this directory since '
                        'another package appears to use it.'.format(
                            pkgTopLevel, otherPkg))
                    safeToRemove = False
                    break

        if safeToRemove:
            toRemove.append(pkgTopLevel)

    # delete modules from the paths we found
    for rmDir in toRemove:
        if os.path.isfile(rmDir):
            logging.info(
                'Removing file `{}` from user package directory.'.format(
                    rmDir))
            os.remove(rmDir)
        elif os.path.isdir(rmDir):
            logging.info(
                'Removing directory `{}` from user package '
                'directory.'.format(rmDir))
            shutil.rmtree(rmDir)

    # cleanup by also deleting the metadata path
    shutil.rmtree(metaPath)

    logging.info('Uninstalled package `{}`.'.format(package))

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
    * The `--yes` flag is appended to the pip command. No confirmation will be
      requested if the package already exists.

    """
    if _isUserPackage(package):  # delete 'manually' if in package dir
        return _uninstallUserPackage(package)
    else:  # use the following if in the main package dir
        # construct the pip command and execute as a subprocess
        cmd = [sys.executable, "-m", "pip", "uninstall", package, "--yes",
               '--no-input', '--no-color']
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

    # Handle errors
    if output.returncode != 0:
        # Display output if error
        cmd = "\n>> " + " ".join(cmd) + "\n"
        dlg = InstallErrorDlg(
            cmd=cmd,
            stdout=stdout,
            stderr=stderr,
            label=_translate("Package {} could not be installed.").format(package)
        )
    else:
        # Display success message if success
        dlg = wx.MessageDialog(
            parent=None,
            caption=_translate("Package installed"),
            message=_translate("Package {} successfully installed!").format(package),
            style=wx.ICON_INFORMATION
        )
    dlg.ShowModal()

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

    # Handle errors
    if output.returncode != 0:
        # Display output if error
        cmd = "\n>> " + " ".join(cmd) + "\n"
        dlg = InstallErrorDlg(
            cmd=cmd,
            stdout=stdout,
            stderr=stderr,
            label=_translate("Package {} could not be uninstalled.").format(package)
        )
    else:
        # Display success message if success
        dlg = wx.MessageDialog(
            parent=None,
            caption=_translate("Package installed"),
            message=_translate("Package {} successfully uninstalled!").format(package),
            style=wx.ICON_INFORMATION
        )
    dlg.ShowModal()


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
    pass
