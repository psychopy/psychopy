#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Library for working with internet connections"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import pathlib
import sys
import socket
import re
from psychopy import logging
from psychopy import prefs

import urllib.request
import urllib.error
import urllib.parse

# default 20s from prefs, min 2s
TIMEOUT = max(prefs.connections['timeout'], 2.0)
socket.setdefaulttimeout(TIMEOUT)

# global proxies
proxies = None  # if this is populated then it has been set up already


class NoInternetAccessError(Exception):
    """An internet connection is required but not available
    """
# global haveInternet
haveInternet = None  # gets set True or False when you check


def haveInternetAccess(forceCheck=False):
    """Detect active internet connection or fail quickly.

    If forceCheck is False, will rely on a cached value if possible.
    """
    global haveInternet
    if forceCheck or haveInternet is None:
        # try to connect to a high-availability site
        sites = ["http://www.google.com/", "http://www.opendns.com/"]
        for wait in [0.3, 0.7]:  # try to be quick first
            for site in sites:
                try:
                    urllib.request.urlopen(site, timeout=wait)
                    haveInternet = True  # cache
                    return True  # one success is good enough
                except Exception:  # urllib.error.URLError:
                    #  socket.timeout() can also happen
                    pass
        else:
            haveInternet = False
    return haveInternet


def requireInternetAccess(forceCheck=False):
    """Checks for access to the internet, raise error if no access.
    """
    if not haveInternetAccess(forceCheck=forceCheck):
        msg = 'Internet access required but not detected.'
        logging.error(msg)
        raise NoInternetAccessError(msg)
    return True


def tryProxy(handler, URL=None):
    """
    Test whether we can connect to a URL with the current proxy settings.

    `handler` can be typically `web.proxies`, if `web.setupProxy()` has been
    run.

    :Returns:

        - True (success)
        - a `urllib.error.URLError` (which can be interrogated with `.reason`)
        - a `urllib.error.HTTPError` (which can be interrogated with `.code`)

    """
    if URL is None:
        URL = 'http://www.google.com'  # hopefully google isn't down!
    req = urllib.request.Request(URL)
    opener = urllib.request.build_opener(handler)
    try:
        opener.open(req, timeout=2).read(5)  # open and read a few characters
        return True
    except urllib.error.HTTPError as err:
        return err
    except urllib.error.URLError as err:
        return err


def getPacFiles():
    """Return a list of possible auto proxy .pac files being used,
    based on the system registry (win32) or system preferences (OSX).
    """
    pacFiles = []
    if sys.platform == 'win32':
        try:
            import _winreg as winreg  # used from python 2.0-2.6
        except ImportError:
            import winreg  # used from python 2.7 onwards
        net = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings")
        nSubs, nVals, lastMod = winreg.QueryInfoKey(net)
        subkeys = {}
        for i in range(nVals):
            thisName, thisVal, thisType = winreg.EnumValue(net, i)
            subkeys[thisName] = thisVal
        if ('AutoConfigURL' in list(subkeys.keys()) and
                len(subkeys['AutoConfigURL']) > 0):
            pacFiles.append(subkeys['AutoConfigURL'])
    elif sys.platform == 'darwin':
        import plistlib
        prefs_loc = pathlib.Path('/Library/Preferences/SystemConfiguration/preferences.plist')
        if prefs_loc.exists():
            with open(prefs_loc, 'rb') as fp :
                sysPrefs = plistlib.loads(fp.read())
        networks = sysPrefs['NetworkServices']
        # loop through each possible network (e.g. Ethernet, Airport...)
        for network in list(networks.items()):
            netKey, network = network  # the first part is a long identifier
            if 'ProxyAutoConfigURLString' in network['Proxies']:
                pacFiles.append(network['Proxies']['ProxyAutoConfigURLString'])
    return list(set(pacFiles))  # remove redundant ones


def getWpadFiles():
    """Return possible pac file locations from the standard set of .wpad
    locations

    NB this method only uses the DNS method to search, not DHCP queries, and
    so may not find all possible .pac locations.

    See http://en.wikipedia.org/wiki/Web_Proxy_Autodiscovery_Protocol
    """
    # pacURLs.append("http://webproxy."+domain+"/wpad.dat")
    # for me finds a file that starts: function FindProxyForURL(url,host)
    # dynamcially chooses a proxy based on the requested url and host; how to
    # parse?

    domainParts = socket.gethostname().split('.')
    pacURLs = []
    for ii in range(len(domainParts)):
        domain = '.'.join(domainParts[ii:])
        pacURLs.append("http://wpad." + domain + "/wpad.dat")
    return list(set(pacURLs))  # remove redundant ones


def proxyFromPacFiles(pacURLs=None, URL=None, log=True):
    """Attempts to locate and setup a valid proxy server from pac file URLs

    :Parameters:

        - pacURLs : list

            List of locations (URLs) to look for a pac file. This might
            come from :func:`~psychopy.web.getPacFiles` or
            :func:`~psychopy.web.getWpadFiles`.

        - URL : string

            The URL to use when testing the potential proxies within the files

    :Returns:

        - A urllib.request.ProxyHandler if successful (and this will have
          been added as an opener to the urllib)
        - False if no proxy was found in the files that allowed successful
          connection
    """

    if pacURLs == None:  # if given none try to find some
        pacURLs = getPacFiles()
    if pacURLs == []:  # if still empty search for wpad files
        pacURLs = getWpadFiles()
        # for each file search for valid urls and test them as proxies
    for thisPacURL in pacURLs:
        if log:
            msg = 'proxyFromPacFiles is searching file:\n  %s'
            logging.debug(msg % thisPacURL)
        try:
            response = urllib.request.urlopen(thisPacURL, timeout=2)
        except urllib.error.URLError:
            if log:
                logging.debug("Failed to find PAC URL '%s' " % thisPacURL)
            continue
        pacStr = response.read().decode('utf-8')
        # find the candidate PROXY strings (valid URLS), numeric and
        # non-numeric:
        pattern = r"PROXY\s([^\s;,:]+:[0-9]{1,5})[^0-9]"
        possProxies = re.findall(pattern, pacStr + '\n')
        for thisPoss in possProxies:
            proxUrl = 'http://' + thisPoss
            handler = urllib.request.ProxyHandler({'http': proxUrl})
            if tryProxy(handler) == True:
                if log:
                    logging.debug('successfully loaded: %s' % proxUrl)
                opener = urllib.request.build_opener(handler)
                urllib.request.install_opener(opener)
                return handler
    return False


def setupProxy(log=True):
    """Set up the urllib proxy if possible.

    The function will use the following methods in order to try and
    determine proxies:

    #. standard urllib.request.urlopen (which will use any
       statically-defined http-proxy settings)
    #. previous stored proxy address (in prefs)
    #. proxy.pac files if these have been added to system settings
    #. auto-detect proxy settings (WPAD technology)

    .. note:
        This can take time, as each failed attempt to set up a proxy
        involves trying to load a URL and timing out. Best
        to do in a separate thread.

    Returns
    _________
        True (success) or False (failure)

    """
    global proxies
    # try doing nothing
    proxies = urllib.request.ProxyHandler(urllib.request.getproxies())
    if tryProxy(proxies) is True:
        if log:
            logging.debug("Using standard urllib (static proxy or "
                          "no proxy required)")
        # this will now be used globally for ALL urllib opening
        urllib.request.install_opener(urllib.request.build_opener(proxies))
        return 1

    # try doing what we did last time
    if len(prefs.connections['proxy']) > 0:
        proxConnPref = {'http': prefs.connections['proxy']}
        proxies = urllib.request.ProxyHandler(proxConnPref)
        if tryProxy(proxies) is True:
            if log:
                msg = 'Using %s (from prefs)'
                logging.debug(msg % prefs.connections['proxy'])
            # this will now be used globally for ALL urllib opening
            opener = urllib.request.build_opener(proxies)
            urllib.request.install_opener(opener)
            return 1
        else:
            if log:
                logging.debug("Found a previous proxy but it didn't work")

    # try finding/using a proxy.pac file
    pacURLs = getPacFiles()
    if log:
        logging.debug("Found proxy PAC files: %s" % pacURLs)
    proxies = proxyFromPacFiles(pacURLs)  # installs opener, if successful
    if (proxies and
            hasattr(proxies, 'proxies') and
            len(proxies.proxies['http']) > 0):
        # save that proxy for future
        prefs.connections['proxy'] = proxies.proxies['http']
        prefs.saveUserPrefs()
        if log:
            msg = 'Using %s (from proxy PAC file)'
            logging.debug(msg % prefs.connections['proxy'])
        return 1

    # try finding/using 'auto-detect proxy'
    pacURLs = getWpadFiles()
    proxies = proxyFromPacFiles(pacURLs)  # installs opener, if successful
    if (proxies and
            hasattr(proxies, 'proxies') and
            len(proxies.proxies['http']) > 0):
        # save that proxy for future
        prefs.connections['proxy'] = proxies.proxies['http']
        prefs.saveUserPrefs()
        if log:
            msg = 'Using %s (from proxy auto-detect)'
            logging.debug(msg % prefs.connections['proxy'])
        return 1

    proxies = 0
    return 0
