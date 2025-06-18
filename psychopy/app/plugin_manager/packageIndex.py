# get script path
# -*- coding: utf-8 -*-

from psychopy import logging
from psychopy import prefs
import sys
import subprocess as sp
import os
import json
import wx

_packageIndex = None
_isIndexing = True  # Flag to indicate if the package index is being updated


def refreshPackageIndex(fetch=False):
    """Refresh the package index.

    Parameters
    ----------
    fetch : bool, optional
        If True, fetch the latest package index from the remote server
        regardless of whether it is already present on disk. The default is
        False, which means it will only update if the index is not present or is
        outdated.

    """
    global _isIndexing
    _isIndexing = True
    scriptDir = prefs.paths['scripts']

    # Construct the command to run the script
    _cmd = [
        sys.executable, 
        os.path.normpath(os.path.join(scriptDir, 'psychopy-pkgutil.py')),
        '--app-pref-dir', prefs.paths['userPrefsDir'],
        'update']
    _cmd += ['--fetch'] if fetch else []
    
    # Execute the command
    try:
        headerText = ' Updating package index '
        headerText = headerText.center(80, '=')
        print(headerText)

        env = os.environ.copy()
        print(f"Running command: {' '.join(_cmd)}")

        proc = sp.Popen(_cmd, 
                        stdout=sp.PIPE, 
                        stderr=sp.PIPE,
                        env=env,
                        universal_newlines=True)
        _, error = proc.communicate()
        if proc.returncode != 0:
            return
        if error:
            logging.error(f"Error refreshing package index: {error}")
            print(f"Error: {error}")

        logging.info("Package index refreshed successfully.")
    except sp.CalledProcessError as e:
        logging.error(f"Error refreshing package index: {e}")
    except FileNotFoundError:
        logging.error("The script was not found. Please check the script path.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        _isIndexing = False


def isIndexing():
    """Check if the package index is currently being updated.
    
    Returns
    -------
    bool
        True if the package index is being updated, False otherwise. This is to
        check if the package index is currently being refreshed from another 
        thread.
    
    """
    global _isIndexing
    return _isIndexing


def downloadPluginAssets(fetch=False):
    """Download assets for the specified plugin.

    Parameters
    ----------
    fetch : bool, optional
        If True, fetch the plugin assets even if present on disk.
        The default is False.
    
    """
    global _packageIndex
    if _packageIndex is None:
        loadPackageIndex()

    # get all plugin icon URLs
    pluginIconsURLs = []
    for plugin in _packageIndex['available']['plugins']['packages'].values():
        pluginIcon = plugin.get('icon', None)
        if pluginIcon is not None:
            pluginIconsURLs.append(pluginIcon)
    
    # cache directory for the plugin icons
    appPluginCacheDir = os.path.join(
        prefs.paths['userCacheDir'], 'appCache', 'plugins')
    
    # make sure we have a directory to put these files in
    try:
        os.makedirs(appPluginCacheDir, exist_ok=True)
    except OSError as err:
        if err.errno != os.errno.EEXIST:
            logging.error(f"Error creating directory {appPluginCacheDir}: {err}")
            raise
    
    headerText = ' Downloading plugin icons '
    headerText = headerText.center(80, '=')
    print(headerText)
    
    for iconUrl in pluginIconsURLs:
        # get the icon file name from URL
        iconFileName = os.path.basename(iconUrl)
        # get the icon file path
        iconPath = os.path.join(appPluginCacheDir, iconFileName)

        # check if we already have a copy of the icon
        if os.path.exists(iconPath) and not fetch:
            print(f"Plugin icon already exists at {iconPath}")
            continue

        print(f"Downloading plugin icon from {iconUrl} to {iconPath}")

        import requests

        try:
            # Make a GET request to download the file
            response = requests.get(iconUrl, stream=True)
            response.raise_for_status()  # Raise an error for bad responses

            # Open the local file in write-binary mode and save the content
            with open(iconPath, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    wx.YieldIfNeeded()

            print(f"Plugin icon downloaded successfully to {iconPath}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading plugin icon: {e}")
        except IOError as e:
            logging.error(f"Error saving plugin icon: {e}")
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
        loadPackageIndex()
    
    return _packageIndex['installed'] if _packageIndex else {}


def getRemotePackages():
    """Get the list of remote packages from the package index.
    """
    global _packageIndex
    if _packageIndex is None:
        loadPackageIndex()
    
    return _packageIndex['available']['remote']['PyPI'] if _packageIndex else []


def getPluginPackages(asList=True):
    """Get the list of plugin packages from the package index.
    """
    global _packageIndex
    if _packageIndex is None:
        loadPackageIndex()
    
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
    global _packageIndex
    if _packageIndex is None:
        loadPackageIndex()

    if isUserPackageInstalled(packageName):
        state = 'u'
    elif isSystemPackageInstalled(packageName):
        state = 's'
    elif packageName in getRemotePackages():
        state = 'n'
    else:
        state = None

    if state is not None:
        version = None
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
        loadPackageIndex()
    
    # Check if the package is in the system packages list
    return packageName in _packageIndex['installed']['system']['packages'].keys()


def isUserPackageInstalled(packageName):
    """Check if a package is installed in the user directory.

    Returns 
    -------
    bool
        True if the package is installed in the user directory, False otherwise.

    """
    global _packageIndex
    if _packageIndex is None:
        loadPackageIndex()
    
    print(list(_packageIndex['installed']['user']['packages'].keys()))

    # Check if the package is in the user packages list
    return packageName in _packageIndex['installed']['user']['packages'].keys()


def getAvailablePackages():
    """Get the list of available packages from the package index.
    """
    global _packageIndex
    if _packageIndex is None:
        loadPackageIndex()
    
    return _packageIndex['available']['PyPI']['packages'] if _packageIndex else {}


def refreshPackageIndexTask(app=None):
    """
    Run the refreshPackageIndex.py script to update the package index.
    """
    refreshPackageIndex()
    downloadPluginAssets()
    

if __name__ == "__main__":
    pass
