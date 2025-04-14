# -*- coding: utf-8 -*-
#

"""Module to manage packages in PsychoPy.
"""

__version__ = '0.1.0'

import argparse
import os
import time
import requests
import json
import subprocess
import re
import sys

from bs4 import BeautifulSoup
from packaging.version import Version

# get the psychopuy user base from the environment variable
_userBaseEnvVal = os.environ.get('PYTHONUSERBASE', None)
if _userBaseEnvVal is not None:
    PYTHONUSERBASE = _userBaseEnvVal  # user base directory from environment variable
else:
    import site
    PYTHONUSERBASE = site.getuserbase()  # user base directory from site module
    print(f'[notice]: No PYTHONUSERBASE environment variable found. Using '
          f'interpreter default: {PYTHONUSERBASE}')

# root user preferences dir
_userAppPrefDir = os.environ.get('PSYCHOPYUSERPREFDIR', None)
if _userAppPrefDir is not None:
    PSYCHOPYUSERPREFDIR = _userAppPrefDir  # user app preferences dir from environment variable

PYPI_SIMPLE_INDEX_URL = "https://pypi.org/simple/"
PACKAGE_INDEX_FILE = "psychopy_packages.json"

# Storage for package indices
packageCache = None  # initialized later

# time elapsed from the previous update before the index is considered stale
_indexStaleAfter = 28 * 24 * 3600  # every 4 weeks


# ------------------------------------------------------------------------------
# Functions for managing the package index 
#

def setStaleTime(days):
    """Set the amount of time before the package index is considered stale.

    Parameters
    ----------
    days : float or int
        The amount of time elapsed from the previous update before the index is 
        considered stale and in need of an update. If `updatePackageIndex` is 
        called with `fetch=False`, the index will be updated if the last update
        was more than this amount of time ago. The default is 28 days.
    
    """
    global _indexStaleAfter
    _indexStaleAfter = days * 24 * 3600  # hours to seconds
    print('[notice]: Package index stale time set to:', days, 'days')


def getStaleTime():
    """Get the amount of time before the package index cache is considered 
    stale.

    Returns
    -------
    float
        The amount of time elapsed from the previous update before the index is
        considered stale and in need of an update. If `updatePackageIndex` is
        called with `fetch=False`, the index will be updated if the last update
        was more than this amount of time ago. The default is 28 days.
    
    """
    global _indexStaleAfter
    return _indexStaleAfter / (24 * 3600)  # seconds to days


def setUserBase(userBase):
    """Set the user base directory.

    Parameters
    ----------
    userBase : str
        User base directory.

    """
    global PYTHONUSERBASE
    
    # check if the user base directory is valid
    if not os.path.exists(userBase):
        raise ValueError(
            f"[error]: User base directory '{userBase}' does not exist.")
    
    # set the user base directory
    PYTHONUSERBASE = userBase
    print('[notice]: User base directory set to:', PYTHONUSERBASE)


def getUserBase():
    """Get the user base directory.

    Returns
    -------
    str
        User base directory.

    """
    global PYTHONUSERBASE
    return PYTHONUSERBASE


def setLockFile():
    """Set the lock file for the package index.

    This function creates a lock file in the user base directory to prevent
    multiple processes from updating the package index at the same time.

    """
    global PACKAGE_INDEX_FILE
    indexPath = os.path.dirname(os.path.abspath(PACKAGE_INDEX_FILE))
    lockFile = os.path.join(indexPath, 'psychopy_packages.lock')

    print('[notice]: Setting lock file for package index at:', lockFile)
    
    # check if the lock file already exists
    if os.path.exists(lockFile):
        print(f"[error]: Lock file '{lockFile}' already exists.")
        return False
    
    # create the lock file
    with open(lockFile, 'w') as f:
        f.write('Lock file for PsychoPy package index.')
    
    print(f'[notice]: Lock file created at: {lockFile}')
    return True


def freeLockFile():
    """Free the lock file for the package index.

    This function removes the lock file in the user base directory to allow
    other processes to update the package index.

    """
    global PACKAGE_INDEX_FILE
    indexPath = os.path.dirname(os.path.abspath(PACKAGE_INDEX_FILE))
    lockFile = os.path.join(indexPath, 'psychopy_packages.lock')
    
    # check if the lock file exists
    if os.path.exists(lockFile):
        os.remove(lockFile)
        print(f'[notice]: Lock file removed: {lockFile}')
    else:
        print(f"[error]: Lock file '{lockFile}' does not exist.")
        return False
    
    return True


def setPackageIndexFilePath(indexFile):
    """Set the location for the index file.
    """
    global PACKAGE_INDEX_FILE
    PACKAGE_INDEX_FILE = os.path.abspath(indexFile)

    print(f'[notice]: Package index file set to: {PACKAGE_INDEX_FILE}')


def getPackageIndexFilePath():
    """Get the location for the index file.

    Returns
    -------
    str
        The location of the index file.

    """
    global PACKAGE_INDEX_FILE
    return PACKAGE_INDEX_FILE 


def _getRemoteFileSize(url):
    """Get the size of the remote file from its header.
    
    Parameters
    ----------
    url : str
        The URL of the remote file.
    
    Returns
    -------
    int or None
        Size of the file in bytes. If the file does not exist or the size cannot
        be determined, returns -1.

    """
    # check the size of the remote file
    try:
        response = requests.head(url)
        if response.status_code != 200:
            print(f"[error]: Failed to fetch {url}: {response.status_code}")
            return -1
    except requests.RequestException as e:
        print(f"[error]: Failed to fetch {url}: {e}")
        return -1
    
    return int(response.headers.get('Content-Length', -1))


def _fetchPluginIndex(fetch=False):
    """Fetch the official PsychoPy plugin index.

    This function fetches the PsychoPy plugin index from the official URL and
    updates the local package cache. It checks if the remote file has changed
    in size from the last download, or if the local data is stale. If either of
    these cases are true, it downloads the file and updates the local cache.

    Parameters
    ----------
    fetch : bool
        Refresh index even if local cache is up-to-date. Default is False.

    """
    global packageCache
    url = "https://psychopy.org/plugins.json"  # url for plugins
    
    # check if the remote file has changed or local data is stale
    remoteFileSize = _getRemoteFileSize(url)
    if not fetch:
        localFileSize = packageCache['available']['plugins'].get('lastsize', -1)
        lastUpdated = packageCache['available']['plugins'].get('lastupdated', -1)
        indexStale = lastUpdated < time.time() - _indexStaleAfter
        if remoteFileSize == localFileSize and not indexStale:
            print(f'Local PsychoPy plugin index is up-to-date.')
            return
        
    # download the file
    print(f'Fetching PsychoPy plugin index from URL: {url}')
    downloadStartTime = time.time()
    response = requests.get(url)
    if response.status_code != 200:
        print(f"[error]: Failed to fetch {url}: {response.status_code}")
        return
    
    print(f'Completed fetching remote PsychoPy plugin index (took '
          f'{round(time.time() - downloadStartTime, 4)} seconds)')

    # parse the JSON content
    print('Parsing downloaded PsychoPy plugin index...')
    parseStartTime = time.time()
    try:
        pluginIndexJSON = json.loads(response.text)
    except json.JSONDecodeError:
        print(f"[error]: Failed to decode JSON from {url}.")
        return False

    print(f'Completed parsing PsychoPy plugin index (took '
          f'{round(time.time() - parseStartTime, 4)} seconds)')
    print(f'Found {len(pluginIndexJSON)} packages in the remote plugin index.')

    # add fields to the package index
    for pluginInfo in pluginIndexJSON:
        pipName = pluginInfo['pipname']
        packageCache['available']['plugins']['packages'][pipName] = pluginInfo

        # get installed version by looking up local package cache
        packageVersion = packageCache['installed']['user']['packages'].get(pipName, None)
        packageCache['available']['plugins']['packages'][pipName]['version'] = packageVersion

        # get remote versions
        versions = getPackageVersions(pipName)
        packageCache['available']['plugins']['packages'][pipName]['releases'] = versions
    
    packageCache['available']['plugins']['lastupdated'] = time.time()
    packageCache['available']['plugins']['lastsize'] = remoteFileSize


def updatePackageIndex(fetch=True):
    """Update the package index.
    
    Parameters
    ----------
    packageIndex : str
        The package index to update. Default is 'PyPI'.
    fetch : bool
        Whether to fetch a fresh package index from the URL. If False, the 
        locally cached package index will be used if available. If the local
        file is not present and fetch is False, the index will be updated.

    """
    global packageCache

    setLockFile()  # set the lock file to prevent multiple processes from updating

    updateStartTime = time.time()

    # setup package cache structure for JSON file
    packageCache = {
        'installed': {},
        'available': {  # list of installable packages from remote locations
            'remote': {
                'PyPI': {
                    'name': 'Python Package Index (PyPI)',  # human readable name
                    'url': PYPI_SIMPLE_INDEX_URL,  # root index URL
                    'doctype': 'pypi-simple-index-html',  # parser type, future feature
                    'lastupdated': -1.0,
                    'packages': [],
                },
            },
            'plugins': {
                'name': 'PsychoPy Offical Plugin Index',
                'lastupdated': -1,
                'lastsize': -1,  # from header, used to check if updated
                'url': "https://psychopy.org/plugins.json",
                'doctype': 'psychopy-plugin-json',
                'packages': {},
            }
        },
    }

    # check if we have a local index file
    localData = None
    if not os.path.exists(PACKAGE_INDEX_FILE):
        print(f"[notice]: Package index file '{PACKAGE_INDEX_FILE}' not found. "
              f"Creating a new one...")
    else:
        # load the file to get remote repo data
        with open(PACKAGE_INDEX_FILE, 'r') as f:
            print(f"Reading package index from {PACKAGE_INDEX_FILE}...")
            try:
                localData = json.load(f)
            except json.JSONDecodeError:
                print(f"[error]: Failed to decode JSON from {PACKAGE_INDEX_FILE}.")
                sys.exit(1)

        # check if the local file data has valid fields
        if 'available' not in localData:
            print(f"[error]: Package index file '{PACKAGE_INDEX_FILE}' is "
                  f"missing 'available' field.")
            sys.exit(1)

        # store data
        packageCache['available'] = localData['available']
        # we'll check if this data is stale later and update if needed

    # structure of the package index
    localPackages = {   # stores locally installed packages
        'system': {
            'lastupdated': -1.0,
            'sitebase': sys.prefix,  # system base directory
            'packages': {},   # dict of installed packages and other info
        },
        'user': {
            'lastupdated': -1.0,
            'sitebase': PYTHONUSERBASE,  # user base directory
            'packages': {},
        }
    }

    # get all local packages for the index
    for pkgsite in ['system', 'user']:
        pkgList = getInstalledPackages(where=pkgsite)
        print(f'Found {len(pkgList)} packages in "{pkgsite}" site-packages '
              f'location.')
        localPackages[pkgsite]['packages'] = pkgList
        localPackages[pkgsite]['lastupdated'] = time.time()  # set updated time

    packageCache['installed'] = localPackages  # set installed packages

    # update the plugin index
    _fetchPluginIndex(fetch)

    def _fetch(packageIndex):
        """This function fetches and updates the local package index file with 
        data from a remote source.

        """
        url = packageCache['available']['remote'][packageIndex]['url']
        # doctype = packageCache['available']['remote'][packageIndex]['doctype']

        downloadStartTime = time.time()
        print(f'Fetching "{packageIndex}" remote package index from URL: {url} ')
        response = requests.get(url)
        if response.status_code != 200:
            print('')
            print(f"[error]: Failed to fetch {url}: {response.status_code}")
            return False
        print(f'Completed fetching remote package index for "{packageIndex}" '
              f'(took {round(time.time() - downloadStartTime, 4)} seconds)')

        # parse the HTML content
        print(f'Parsing downloaded "{packageIndex}" remote package index...')
        parseStartTime = time.time()
        soup = BeautifulSoup(response.text, 'html.parser')
        packageCache['available']['remote'][packageIndex]['packages'].clear()
        for a in soup.find_all('a', href=True):
            # Check if the link is a package link
            if re.search(r'/simple/[^/]+/', a['href']):
                package_name = a['href'].split('/')[-2]
                packageCache['available']['remote'][packageIndex]['packages'].append(package_name)

        packageCache['available']['remote'][packageIndex]['lastupdated'] = time.time()

        print(f'Completed parsing remote package index for "{packageIndex}" '
              f'(took {round(time.time() - parseStartTime, 4)} seconds)')

        return True

    for remoteIndex in ['PyPI']:
        lastUpdated = packageCache['available']['remote'][remoteIndex]['lastupdated'] 
        isStale = lastUpdated < time.time() - _indexStaleAfter
        if isStale or fetch:
            print(f'[notice]: Remote package index "{remoteIndex}" is stale, updating...')
            _fetch(packageIndex=remoteIndex)
        else:
            # index is not stale, use the cached data
            print(f'[notice]: Remote package index "{remoteIndex}" is not stale, using locally cached data.')
        
        totalPackages = len(
            packageCache['available']['remote'][remoteIndex]['packages'])
        print(f'Found {totalPackages} available packages in "{remoteIndex}" remote index.')
    
    # write out the package index to a file
    with open(PACKAGE_INDEX_FILE, 'w') as f:
        print(f'Writing package index to {PACKAGE_INDEX_FILE}...')
        try:
            json.dump(packageCache, f, indent=4)
        except Exception as e:
            print(f"[error]: Failed to write package index to {PACKAGE_INDEX_FILE}: {e}")
            sys.exit(1)
    
    print(f'Finished updating local package index cache (took '
          f'{round(time.time() - updateStartTime, 4)} seconds)')
    
    freeLockFile()  # free the lock file
        

def getPackageVersions(packageName):
    """Fetches the package versions from the PyPI simple index page.

    Parameters
    ----------
    packageName : str
        The name of the package to fetch versions for.
    
    """
    url = 'https://pypi.org/simple/' + packageName + '/'
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}: {response.status_code}")
    
    # parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    versions = set()
    for a in soup.find_all('a', href=True):
        match = re.search(rf'{packageName}-(\d+\.\d+\.\d+)', a['href'], re.IGNORECASE)
        if match:
            version = match.group(1)
            versions.add(version)

    versions = list(versions)
    versions.sort(key=Version)

    return versions


# ------------------------------------------------------------------------------
# Helper functions to call pip and parse output
#

def _parsePIPListOutput(output, ncols=2):
    """Parse the output of the pip list command.

    Parameters
    ----------
    output : str
        The output of the pip list command.
    ncols : int, optional
        The number of columns in the output. Default is 2.
    
    Returns
    -------
    dict
        A dictionary of installed packages with their versions.

    """
    packages = {}
    for line in output.splitlines():
        if not line:
            break
        if line.startswith('Package'):  # skip heading
            continue
        elif line.startswith('-'):
            continue

        # add the package to the dictionary
        parts = line.split()
        if len(parts) != ncols:
            continue

        packageName = parts[0]
        versionInfo = parts[1:]
        versionCols = len(versionInfo)

        if versionCols == 1:
            packageVersions = versionInfo[0]  # simple case
        else:
            packageVersions = versionInfo

        packages[packageName] = packageVersions

    return packages


def _callPIP(cmd, userBase=None):
    """Call the pip list command and return the output.

    Parameters
    ----------
    cmd : list
        The command to call pip with.
    userBase : str, optional
        User base directory. If not provided, the default user base directory
        will be used.

    Returns
    -------
    str
        The output of the pip list command.

    """
    env = os.environ.copy()

    try:
        _exec = sys.executable
        if userBase is None:
            userBase = PYTHONUSERBASE

        # set the user base directory in the environment
        env['PYTHONUSERBASE'] = userBase
        
        # call pip list command and return output
        _cmd = [_exec, '-m', 'pip'] + cmd
        output = subprocess.check_output(
            _cmd, 
            stderr=subprocess.STDOUT,
            env=env)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to call pip command: {e}")
    except FileNotFoundError as e:
        raise Exception(f"Failed to find pip executable: {e}")
    except Exception as e:
        raise Exception(f"Failed to call pip command: {e}")
    
    return output.decode('utf-8')


# ------------------------------------------------------------------------------
# Functions to get installed and outdated packages
# 

def getInstalledPackages(where='system', userBase=None):
    """Get the installed packages in the local environment.

    Parameters
    ----------
    where : str, optional
        The type of installed packages to return. Can be 'system' or 'user'.
        Default is 'system'.
    userBase : str, optional
        User base directory. If not provided, the default user base directory
        will be used. This is only used if `which` is 'user'.
    
    Returns
    -------
    dict
        A dictionary of installed packages with their versions.

    """
    if where not in ['system', 'user']:
        raise ValueError(
            f"Invalid value for 'where': {where}. Must be 'system' or 'user'.")

    cmd = ['list']
    if where == 'user':
        cmd.append('--user')

    # use pip to get the installed packages
    output = _callPIP(cmd, userBase=userBase)

    # parse the output and return a dictionary of installed packages
    packages = _parsePIPListOutput(output, ncols=2)

    return packages


def getOutdatedPackages(which='system', userBase=None):
    """Get the outdated packages in the local environment.

    Parameters
    ----------
    which : str, optional
        The type of installed packages to return. Can be 'system' or 'user'.
        Default is 'system'.
    userBase : str, optional
        User base directory. If not provided, the default user base directory
        will be used. This is only used if `which` is 'user'.
    
    Returns
    -------
    dict
        A dictionary of outdated packages with their versions.

    """
    if which not in ['system', 'user']:
        raise ValueError(
            f"Invalid value for 'which': {which}. Must be 'system' or 'user'.")

    # use pip to get the outdated packages
    cmd = ['list', '--outdated']
    if which == 'user':
        cmd.append('--user')

    output = _callPIP(cmd, userBase=userBase)
    packages = _parsePIPListOutput(output, ncols=4)

    return packages


def getPluginPackages():
    """Get a list of available PsychoPy plugins.
    """
    pass


# ------------------------------------------------------------------------------
# Functions to install, upgrade, and uninstall packages
#

def installPackage(packageName, where='user', forceReinstall=False, 
                   noCacheDir=False, extraIndexURL=None, userBase=None):
    """Install a package using pip.

    Parameters
    ----------
    packageName : str
        The name of the package to install.
    version : str, optional
        The version of the package to install. If not provided, the latest 
        version will be installed.
    where : str, optional
        Where to install the packages. Can be 'system' or 'user'. Default is 
        'system'.
    forceReinstall : bool, optional
        Whether to force reinstall the package if it is already installed.
        Default is False.
    noCacheDir : bool, optional
        Whether to disable the cache directory. Default is False.
    extraIndexURL : str, optional
        The URL of the package index to use. If not provided, the default
        package index will be used.
    userBase : str, optional
        User base directory. If not provided, the default user base directory
        will be used. This is only used if `where` is 'user'.

    Examples
    --------
    Installing a package to the user base directory:

        installPackage('numpy', where='user')

    Installing a package with a specific version:

        installPackage('numpy==1.21.0', where='user')
    
    """
    if where not in ['system', 'user']:
        raise ValueError(
            f"Invalid value for 'which': {where}. Must be 'system' or 'user'.")
    
    cmd = ['install', packageName]
    
    if where == 'user':
        cmd.append('--user')  # install to user base directory   
    if forceReinstall:
        cmd.append('--force-reinstall')
    if extraIndexURL:
        cmd.append('--extra-index-url')
        cmd.append(extraIndexURL)
    if noCacheDir:
        cmd.append('--no-cache-dir')

    # use pip to install the package
    print(f'Installing {packageName} to "{where}" site-packages...')
    _ = _callPIP(cmd, userBase=userBase)
    print(f'Completed installing {packageName} to "{where}" site-packages.')


def upgradePackage(packageName, strategy='eager', extraIndexURL=None, userBase=None):
    """Upgrade an installed package to the latest version.

    Parameters
    ----------
    packageName : str
        The name of the package to upgrade.
    extraIndexURL : str, optional
        The URL of the package index to use. If not provided, the default
        package index will be used.
    userBase : str, optional
        User base directory. If not provided, the default user base directory
        will be used. This is only used if `which` is 'user'.
    
    """
    # use pip to upgrade the package
    cmd = [
        'install', 
        '--upgrade', 
        packageName]
    
    if extraIndexURL:
        cmd.append('--extra-index-url')
        cmd.append(extraIndexURL)
    if strategy:
        cmd.append('--upgrade-strategy')
        cmd.append(strategy)

    print('Upgrading package:', packageName)

    _ = _callPIP(cmd, userBase=userBase)


def upgradeAllPackages(where='system', strategy='eager', userBase=None):
    """Upgrade all installed packages to the latest version.

    Parameters
    ----------
    where : str, optional
        The type of installed packages to upgrade. Can be 'system' or 'user'.
        Default is 'system'.
    strategy : str, optional
        The upgrade strategy to use. Can be 'eager' or 'only-if-needed'.
        Default is 'eager'.
    userBase : str, optional
        User base directory. If not provided, the default user base directory
        will be used. This is only used if `where` is 'user'.
    
    """
    if where not in ['system', 'user']:
        raise ValueError(
            f"Invalid value for 'where': {where}. Must be 'system' or 'user'.")
    
    # use pip to upgrade all packages
    cmd = ['install', '--upgrade']
    if where == 'user':
        cmd.append('--user')

    # list all packages to upgrade
    outdatedPackages = getOutdatedPackages(which=where, userBase=userBase)

    if not outdatedPackages:
        print('No packages to upgrade.')
        return
    
    print(f'Found {len(outdatedPackages)} packages to upgrade.')
    
    # generate the list of packages to upgrade
    packagesToUpgrade = []
    for packageName, versionInfo in outdatedPackages.items():
        print(f'Package "{packageName}" is outdated, marking for upgrade: {versionInfo[0]} -> {versionInfo[1]}')
        packagesToUpgrade.append(packageName)

    cmd += packagesToUpgrade

    if strategy:
        cmd.append('--upgrade-strategy')
        cmd.append(strategy)
    
    print(f'Upgrading {len(packagesToUpgrade)} packages in {where} site-packages...')
    _ = _callPIP(cmd, userBase=userBase)

    print('Completed upgrading packages.')


def uninstallPackage(packageName, userBase=None):
    """Uninstall a package using pip.

    Parameters
    ----------
    packageName : str
        The name of the package to uninstall.
    userBase : str, optional
        User base directory. If not provided, the default user base directory
        will be used. This is only used if `which` is 'user'.
    
    """
    # use pip to uninstall the package
    cmd = ['uninstall', packageName, '-y']  # always use the -y flag to confirm
    _ = _callPIP(cmd, userBase=userBase)


def getPackageInfo(packageName):
    """Get the package info from the local environment.

    Parameters
    ----------
    packageName : str
        The name of the package to get info for.

    Returns
    -------
    dict
        A dictionary of package info.

    """
    from importlib import metadata

    # get package metadata
    try:
        toReturn = {
            'installed_version': metadata.version(packageName),
            'available_versions': [],
            'metadata': {},
        }

        # get the package metadata
        toReturn['available_versions'] = getPackageVersions(packageName)

        pkgMetadata = metadata.metadata(packageName)
        pkgMetadata = dict(pkgMetadata)
        toReturn['metadata'] = pkgMetadata

        return toReturn
    except ImportError:
        # package not found in local environment
        raise ValueError(
            f"Package '{packageName}' not found in local environment.")
    

# command-line interface

def main():
    """Main function to run the package utility.
    """
    # use argparse 
    desc = f'PsychoPy package managment utility v{__version__} (Copyright 2025 - Open Science Tools Ltd.)'

    parser = argparse.ArgumentParser(
        description=desc,
        prog='psychopy-pkgutil.py',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--user-base', type=str, help='User base directory.')
    parser.add_argument(
        '--index-file', type=str, default=PACKAGE_INDEX_FILE,
        help='Local package index cache file. Default is "psychopy_packages.json"')
    parser.add_argument(
        '--app-pref-dir', type=str, default=None, 
        help='PsychoPy app preferences directory.')
    parser.add_argument(
        '--verbose', action='store_true', help='Enable verbose output.')
    
    # subcommands are 'update', 'list', 'install', 'uninstall', and 'upgrade'
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    # update command
    update_parser = subparsers.add_parser('update', help='Update the package index.')
    update_parser.add_argument(
        '--fetch', action='store_true', help='Fetch a fresh package index.')
    update_parser.add_argument(
        '--stale-after', type=float, default=28.0,
        help='Time in days before the package index is considered stale.')
    
    # list command
    list_parser = subparsers.add_parser('list', help='List installed packages.')
    list_parser.add_argument(
        '--outdated', action='store_true', help='List outdated packages.')
    list_parser.add_argument(
        '--json', action='store_true', help='Output in JSON format.')
    list_parser.add_argument(
        '--user', action='store_true', help='List user packages.')
    list_parser.add_argument(
        '--system', action='store_true', help='List system packages.')
    list_parser.add_argument(
        '--plugins', action='store_true', help='List available PsychoPy plugins.')
    list_parser.add_argument(
        '--all', action='store_true', help='List all packages.')

    # install command
    install_parser = subparsers.add_parser('install', help='Install a package.')
    install_parser.add_argument(
        'package', type=str, help='The name of the package to install.')
    install_parser.add_argument(
        '--user', action='store_true', help='Install to user base directory.')
    install_parser.add_argument(
        '--force', action='store_true', help='Force reinstall the package.')
    install_parser.add_argument(
        '--no-cache', action='store_true', help='Disable the cache directory.')
    install_parser.add_argument(
        '--extra-index-url', type=str, help='The URL of the package index to use.')
    
    # uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall a package.')
    uninstall_parser.add_argument(
        'package', type=str, help='The name of the package to uninstall.')
    
    # upgrade command
    upgrade_parser = subparsers.add_parser('upgrade', help='Upgrade a package.')
    upgrade_parser.add_argument(
        'package', type=str, help='The name of the package to upgrade.')

    # parse the arguments
    args = parser.parse_args()

    # configure paths if root config directory is specified
    if args.app_pref_dir:
        setUserBase(os.path.join(args.app_pref_dir, 'packages'))
        setPackageIndexFilePath(
            os.path.join(
                args.app_pref_dir, 'cache', 'appCache', PACKAGE_INDEX_FILE))
    else:
        if args.user_base:
            setUserBase(args.user_base)
            
        if args.index_file:
            setPackageIndexFilePath(args.index_file)
    
    if args.command == 'update':
        if args.stale_after:
            setStaleTime(args.stale_after)
        updatePackageIndex(fetch=args.fetch)
    elif args.command == 'list':
        if args.outdated:
            packages = getOutdatedPackages()
        else:
            packages = getInstalledPackages()
        
        for packageName, versionInfo in packages.items():
            print(f"{packageName}: {versionInfo}")
    elif args.command == 'install':
        installPackage(
            args.package, 
            where='user' if args.user else 'system', 
            forceReinstall=args.force, 
            noCacheDir=args.no_cache, 
            extraIndexURL=args.extra_index_url, 
            userBase=args.user_base)
    elif args.command == 'uninstall':
        uninstallPackage(args.package, userBase=args.user_base)
    elif args.command == 'upgrade':
        upgradePackage(
            args.package, 
            extraIndexURL=args.extra_index_url, 
            userBase=args.user_base)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    # setStaleTime(0.00001)  # set the index to be stale after 24 hours
    # updatePackageIndex(fetch=True)  # update the package index
    main()