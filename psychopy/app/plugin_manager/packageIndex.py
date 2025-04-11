# get script path
# -*- coding: utf-8 -*-

from psychopy import logging
from psychopy import prefs
from psychopy import logging
import sys
import subprocess as sp
import os
import json

_packageIndex = None


def refreshPackageIndex(fetch=False):
    """Refresh the package index.
    """
    scriptDir = prefs.paths['scripts']

    # Construct the command to run the script
    _cmd = [
        sys.executable, 
        scriptDir + '/psychopy-pkgutil.py',
        '--app-pref-dir', prefs.paths['userPrefsDir'],
        'update']
    _cmd += ['--fetch'] if fetch else []
    
    # Execute the command
    try:
        env = os.environ.copy()
        output = sp.check_output(
            _cmd, 
            stderr=sp.PIPE,
            env=env)
        
        # Decode the output from bytes to string
        print(output.decode('utf-8'))

        logging.info("Package index refreshed successfully.")
    except sp.CalledProcessError as e:
        logging.error(f"Error refreshing package index: {e}")
    except FileNotFoundError:
        logging.error("The script was not found. Please check the script path.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def loadPackageIndex():
    """Load the package index from the specified file.
    """
    global _packageIndex
    try:
        # Load the package index from the specified file
        packageIndexPath = os.path.join(
            prefs.paths['userPrefsDir'], 'cache', 'appCache', 'psychopy_packages.json')
        with open(packageIndexPath, 'r') as f:
            indexData = f.read()
        _packageIndex = json.loads(indexData)
    except FileNotFoundError:
        logging.error("Package index file not found.")
    except json.JSONDecodeError:
        logging.error("Error decoding package index JSON.")


def freePackageIndex():
    """Free the package index to allow it to be reloaded.
    """
    global _packageIndex
    _packageIndex = None


def getInstalledPackages():
    """Get the list of installed packages from the package index.
    """
    global _packageIndex
    if _packageIndex is None:
        _packageIndex = loadPackageIndex()
    
    return _packageIndex['installed'] if _packageIndex else {}


def getRemotePackages():
    """Get the list of remote packages from the package index.
    """
    global _packageIndex
    if _packageIndex is None:
        _packageIndex = loadPackageIndex()
    
    return _packageIndex['available']['remote']['PyPI'] if _packageIndex else []


def getPluginPackages(asList=True):
    """Get the list of plugin packages from the package index.
    """
    global _packageIndex
    if _packageIndex is None:
        _packageIndex = loadPackageIndex()
    
    if asList:  # legacy
        return list(_packageIndex['available']['plugins']['packages'].values())
    
    return _packageIndex['available']['plugins']['packages'] if _packageIndex else {}


def isPackageInstalled(packageName):
    """Check if a package is installed.

    Returns 
    -------
    tuple
        A tuple containing a boolean indicating if the package is installed,
        and its version if installed.
        If the package is not installed, the version will be None.

    """
    state = isUserPackageInstalled(packageName) or isSystemPackageInstalled(packageName)
    if state:
        version = getInstalledPackages().get(packageName, {}).get('version', None)
    else:
        version = None

    return state, version


def isSystemPackageInstalled(packageName):
    """Check if a package is installed in the system directory.

    Returns 
    -------
    bool
        True if the package is installed in the system directory, False otherwise.

    """
    global _packageIndex
    if _packageIndex is None:
        _packageIndex = loadPackageIndex()
    
    # Check if the package is in the system packages list
    return packageName in _packageIndex['installed']['system']


def isUserPackageInstalled(packageName):
    """Check if a package is installed in the user directory.

    Returns 
    -------
    bool
        True if the package is installed in the user directory, False otherwise.

    """
    global _packageIndex
    if _packageIndex is None:
        _packageIndex = loadPackageIndex()
    
    # Check if the package is in the user packages list
    return packageName in _packageIndex['installed']['user']


def getAvailablePackages():
    """Get the list of available packages from the package index.
    """
    global _packageIndex
    if _packageIndex is None:
        _packageIndex = loadPackageIndex()
    
    return _packageIndex['available']['PyPI']['packages'] if _packageIndex else {}



def refreshPackageIndexTask(app=None):
    """
    Run the refreshPackageIndex.py script to update the package index.
    """
    scriptDir = prefs.paths['scripts']

    # Construct the command to run the script
    command = [
        sys.executable, 
        scriptDir + '/psychopy-pkgutil.py',
        '--app-pref-dir', prefs.paths['userPrefsDir'],
        'update']
    
    logging.debug(f"Executing command: {command}")
    
    # Execute the command
    try:
        env = os.environ.copy()
        output = sp.check_output(
            command, 
            stderr=sp.PIPE,
            env=env)
        
        # Decode the output from bytes to string
        print(output.decode('utf-8'))

        logging.info("Package index refreshed successfully.")
    except sp.CalledProcessError as e:
        logging.error(f"Error refreshing package index: {e}")
    except FileNotFoundError:
        logging.error("The script was not found. Please check the script path.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    

if __name__ == "__main__":
    loadPackageIndex()
    print(getPluginPackages())