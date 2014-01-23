#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Library for working with internet connections"""

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import os, sys, time
import hashlib, base64
import httplib, mimetypes
import urllib2, socket, re
from psychopy import logging
from psychopy.constants import PSYCHOPY_USERAGENT
from psychopy import prefs

TIMEOUT = max(prefs.connections['timeout'], 2.0) # default 20s from prefs, min 2s
socket.setdefaulttimeout(TIMEOUT)

global proxies
proxies = None #if this is populated then it has been set up already


class NoInternetAccessError(StandardError):
    """An internet connection is required but not available
    """
global haveInternet
haveInternet = None  # gets set True or False when you check

def haveInternetAccess(forceCheck=False):
    """Detect active internet connection or fail quickly.

    If forceCheck is False, will rely on a cached value if possible.
    """
    global haveInternet
    if forceCheck or haveInternet not in [True, False]:
        # try to connect to a high-availability site
        sites = ["http://www.google.com/", "http://www.opendns.com/"]
        for wait in [0.3, 0.7]:  # try to be quick first
            for site in sites:
                try:
                    urllib2.urlopen(site, timeout=wait)
                    haveInternet = True  # cache
                    return True  # one success is good enough
                except urllib2.URLError:
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

    `handler` can be typically `web.proxies`, if `web.setupProxy()` has been run.

    :Returns:

        - True (success)
        - a `urllib2.URLError` (which can be interrogated with `.reason`)
        - a `urllib2.HTTPError` (which can be interrogated with `.code`)

    """
    if URL is None:
        URL='http://www.google.com'#hopefully google isn't down!
    req = urllib2.Request(URL)
    opener = urllib2.build_opener(handler)
    try:
        opener.open(req, timeout=2).read(5)#open and read a few characters
        return True
    except urllib2.URLError, err:
        return err
    except urllib2.HTTPError, err:
        return err

def getPacFiles():
    """Return a list of possible auto proxy .pac files being used,
    based on the system registry (win32) or system preferences (OSX).
    """
    pacFiles=[]
    if sys.platform=='win32':
        try:
            import _winreg as winreg#used from python 2.0-2.6
        except:
            import winreg#used from python 2.7 onwards
        net = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
        )
        nSubs, nVals, lastMod = winreg.QueryInfoKey(net)
        subkeys={}
        for i in range(nVals):
            thisName, thisVal, thisType=winreg.EnumValue(net,i)
            subkeys[thisName]=thisVal
        if 'AutoConfigURL' in subkeys.keys() and len(subkeys['AutoConfigURL'])>0:
            pacFiles.append(subkeys['AutoConfigURL'])
    elif sys.platform=='darwin':
        import plistlib
        sysPrefs = plistlib.readPlist('/Library/Preferences/SystemConfiguration/preferences.plist')
        networks=sysPrefs['NetworkServices']
        #loop through each possible network (e.g. Ethernet, Airport...)
        for network in networks.items():
            netKey, network=network#the first part is a long identifier
            if 'ProxyAutoConfigURLString' in network['Proxies'].keys():
                pacFiles.append(network['Proxies']['ProxyAutoConfigURLString'])
    return list(set(pacFiles)) # remove redundant ones

def getWpadFiles():
    """
    Return possible pac file locations from the standard set of .wpad locations

    NB this method only uses the DNS method to search, not DHCP queries, and
    so may not find all possible .pac locations.

    See http://en.wikipedia.org/wiki/Web_Proxy_Autodiscovery_Protocol
    """
    #pacURLs.append("http://webproxy."+domain+"/wpad.dat")
    # for me finds a file that starts: function FindProxyForURL(url,host) { ... }
    # dynamcially chooses a proxy based on the requested url and host; how to parse?

    domainParts = socket.gethostname().split('.')
    pacURLs=[]
    for ii in range(len(domainParts)):
        domain = '.'.join(domainParts[ii:])
        pacURLs.append("http://wpad."+domain+"/wpad.dat")
    return list(set(pacURLs)) # remove redundant ones

def proxyFromPacFiles(pacURLs=[], URL=None, log=True):
    """Attempts to locate and setup a valid proxy server from pac file URLs

    :Parameters:

        - pacURLs : list

            List of locations (URLs) to look for a pac file. This might come from
            :func:`~psychopy.web.getPacFiles` or :func:`~psychopy.web.getWpadFiles`.

        - URL : string

            The URL to use when testing the potential proxies within the files

    :Returns:

        - A urllib2.ProxyHandler if successful (and this will have been added as
        an opener to the urllib2.
        - False if no proxy was found in the files that allowed successful connection
    """

    if pacURLs==[]:#if given none try to find some
        pacURLs = getPacFiles()
    if pacURLs==[]:#if still empty search for wpad files
        pacURLs = getWpadFiles()
        #for each file search for valid urls and test them as proxies
    for thisPacURL in pacURLs:
        if log:
            logging.debug('proxyFromPacFiles is searching file:\n  %s' %thisPacURL)
        try:
            response = urllib2.urlopen(thisPacURL, timeout=2)
        except urllib2.URLError:
            if log:
                logging.debug("Failed to find PAC URL '%s' " %thisPacURL)
            continue
        pacStr = response.read()
        #find the candidate PROXY strings (valid URLS), numeric and non-numeric:
        possProxies = re.findall(r"PROXY\s([^\s;,:]+:[0-9]{1,5})[^0-9]", pacStr+'\n')
        for thisPoss in possProxies:
            proxUrl = 'http://' + thisPoss
            handler=urllib2.ProxyHandler({'http':proxUrl})
            if tryProxy(handler)==True:
                if log:
                    logging.debug('successfully loaded: %s' %proxUrl)
                urllib2.install_opener(urllib2.build_opener(handler))
                return handler
    return False

def setupProxy(log=True):
    """Set up the urllib proxy if possible.

     The function will use the following methods in order to try and determine proxies:
        #. standard urllib2.urlopen (which will use any statically-defined http-proxy settings)
        #. previous stored proxy address (in prefs)
        #. proxy.pac files if these have been added to system settings
        #. auto-detect proxy settings (WPAD technology)

     .. note:
        This can take time, as each failed attempt to set up a proxy involves trying to load a URL and timing out. Best
        to do in a separate thread.

    :Returns:

        True (success) or False (failure)
    """
    global proxies
    #try doing nothing
    proxies=urllib2.ProxyHandler(urllib2.getproxies())
    if tryProxy(proxies) is True:
        if log:
            logging.debug("Using standard urllib2 (static proxy or no proxy required)")
        urllib2.install_opener(urllib2.build_opener(proxies))#this will now be used globally for ALL urllib2 opening
        return 1

    #try doing what we did last time
    if len(prefs.connections['proxy'])>0:
        proxies=urllib2.ProxyHandler({'http': prefs.connections['proxy']})
        if tryProxy(proxies) is True:
            if log:
                logging.debug('Using %s (from prefs)' %(prefs.connections['proxy']))
            urllib2.install_opener(urllib2.build_opener(proxies))#this will now be used globally for ALL urllib2 opening
            return 1
        else:
            if log:
                logging.debug("Found a previous proxy but it didn't work")

    #try finding/using a proxy.pac file
    pacURLs=getPacFiles()
    if log:
        logging.debug("Found proxy PAC files: %s" %pacURLs)
    proxies=proxyFromPacFiles(pacURLs) # installs opener, if successful
    if proxies and hasattr(proxies, 'proxies') and len(proxies.proxies['http'])>0:
        #save that proxy for future
        prefs.connections['proxy']=proxies.proxies['http']
        prefs.saveUserPrefs()
        if log:
            logging.debug('Using %s (from proxy PAC file)' %(prefs.connections['proxy']))
        return 1

    #try finding/using 'auto-detect proxy'
    pacURLs=getWpadFiles()
    proxies=proxyFromPacFiles(pacURLs) # installs opener, if successful
    if proxies and hasattr(proxies, 'proxies') and len(proxies.proxies['http'])>0:
        #save that proxy for future
        prefs.connections['proxy']=proxies.proxies['http']
        prefs.saveUserPrefs()
        if log:
            logging.debug('Using %s (from proxy auto-detect)' %(prefs.connections['proxy']))
        return 1

    proxies=0
    return 0

### post_multipart is from {{{ http://code.activestate.com/recipes/146306/ (r1) ###
def _post_multipart(host, selector, fields, files, encoding='utf-8', timeout=TIMEOUT,
                    userAgent=PSYCHOPY_USERAGENT, basicAuth=None, https=False):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    file is a 1-item sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    # as updated for HTTPConnection()
    # as rewritten for any encoding http://www.nerdwho.com/blog/57/enviando-arquivos-e-dados-ao-mesmo-tempo-via-http-post-usando-utf-8/
    # JRG: added timeout, userAgent, basic auth, https

    def _encode_multipart_formdata(fields, files, encoding='utf-8'):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTP instance
        """
        BOUNDARY = u'----------ThIs_Is_tHe_bouNdaRY_$'
        CRLF = u'\r\n'
        L = []

        for (key, value) in fields:
            L.append(u'--' + BOUNDARY)
            L.append(u'Content-Disposition: form-data; name="%s"' % key)
            L.append(u'Content-Type: text/plain;charset=%s' % encoding)
            L.append(u'Content-Transfer-Encoding: 8bit')
            L.append(u'')
            L.append(value)

        for (key, filename, value) in files:
            L.append(u'--' + BOUNDARY)
            L.append(u'Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append(u'Content-Type: %s;charset=%s' % (_get_content_type(filename), encoding))
            L.append(u'Content-Transfer-Encoding: base64')
            L.append(u'')
            L.append(base64.b64encode(value).decode())

        L.append(u'--' + BOUNDARY + u'--')
        L.append(u'')
        body = CRLF.join(L)
        content_type = u'multipart/form-data; boundary=%s' % BOUNDARY

        return content_type, body

    def _get_content_type(filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    # start of _post_multipart main code:
    content_type, body = _encode_multipart_formdata(fields, files)

    # select https -- note there's NO verification of the server’s certificate
    if https is True:
        conn = httplib.HTTPSConnection(host, timeout=timeout)
    else:
        conn = httplib.HTTPConnection(host, timeout=timeout)
    headers = {u'User-Agent': userAgent,
               u'Charset': encoding,
               u'Content-Type': content_type,
               }
    # apache basic auth (sent in clear text, https can help):
    if basicAuth and type(basicAuth) == str:
        user_cred = base64.encodestring(basicAuth).replace('\n', '')
        headers.update({u"Authorization": u"Basic %s" % user_cred})

    try:
        conn.request(u'POST', selector, body, headers)
    except: # ? don't seem to get a proper exception
        return -1, 'connection error (possible timeout after %ss)' % str(timeout), 'timeout or error'

    try:
        result = conn.getresponse()
    except:
        return -1, 'connection error (can be "socket.error: [Errno 54] Connection reset by peer")'
    return result.status, result.reason, result.read()

    ## end of http://code.activestate.com/recipes/146306/ }}}

def upload(selector, filename, basicAuth=None, host=None, https=False, log=True):
    """Upload a local file over the internet to a configured http server.

    This method handshakes with a php script on a remote server to transfer a local
    file to another machine via http (using POST).

    Returns "success" plus a sha256 digest of the file on the server and a byte count.
    If the upload was not successful, an error code is returned (eg, "too_large" if the
    file size exceeds the limit specified server-side in up.php, or "no_file" if there
    was no POST attachment).

    .. note::
        The server that receives the files needs to be configured before uploading
        will work. php files and notes for a sys-admin are included in `psychopy/contrib/http/`.
        In particular, the php script `up.php` needs to be copied to the server's
        web-space, with appropriate permissions and directories, including apache
        basic auth and https (if desired). The maximum size for an upload can be configured within up.php

        A configured test-server is available; see the Coder demo for details
        (upload size is limited to ~1500 characters for the demo).

    **Parameters:**

        `selector` : (required, string)
            a standard URL of the form `http://host/path/to/up.php`, e.g., `http://upload.psychopy.org/test/up.php`

            .. note::
                Limited https support is provided (see below).

        `filename` : (required, string)
            the path to the local file to be transferred. The file can be any format:
            text, utf-8, binary. All files are hex encoded while in transit (increasing
            the effective file size).

            .. note::
                Encryption (*beta*) is available as a separate step. That is,
                first :mod:`~psychopy.contrib.opensslwrap.encrypt()` the file,
                then :mod:`~psychopy.web.upload()` the encrypted file in the same
                way that you would any other file.

        `basicAuth` : (optional)
            apache 'user:password' string for basic authentication. If a `basicAuth`
            value is supplied, it will be sent as the auth credentials (in cleartext);
            using https will encrypt the credentials.
        `host` : (optional)
            The default process is to extract host information from the `selector`. The `host` option
            allows you to specify a host explicitly (i.e., if it differs from the `selector`).
        `https` : (optional)
            If the remote server is configured to use https, passing the parameter
            `https=True` will encrypt the transmission including all data and `basicAuth`
            credentials. It is approximately as secure as using a self-signed X.509 certificate.

            An important caveat is that the authenticity of the certificate returned from the
            server is not checked, and so the certificate could potentially be spoofed
            (see the warning under HTTPSConnection http://docs.python.org/library/httplib.html).
            Overall, using https can still be much more secure than not using it.
            The encryption is good, but that of itself does not eliminate all risk.
            Importantly, it is not as secure as one might expect, given that all major web browsers
            do check certificate authenticity. The idea behind this parameter is to require people
            to explicitly indicate that they want to proceed anyway, in effect saying
            "I know what I am doing and accept the risks (of using un-verified certificates)".

    **Example:**

        See Coder demo / misc / http_upload.py

    Author: Jeremy R. Gray, 2012
    """

    requireInternetAccess()  # needed to upload over http

    fields = [('name', 'PsychoPy_upload'), ('type', 'file')]
    if not selector:
        logging.error('upload: need a selector, http://<host>/path/to/up.php')
        raise ValueError('upload: need a selector, http://<host>/path/to/up.php')
    if not host:
        host = selector.split('/')[2]
        if log:
            logging.info('upload: host extracted from selector = %s' % host)
    if selector.startswith('https'):
        if https is not True:
            logging.error('upload: https not explicitly requested. use https=True to proceed anyway (see API for security caveats).')
            raise ValueError('upload: https not fully supported (see API for caveats and usage), exiting.')
        elif log:
            logging.exp('upload: https requested; note that security is not fully assured (see API)')
    elif https:
        msg = 'upload: to use https, the selector URL must start with "https"'
        logging.error(msg)
        raise ValueError(msg)
    if not os.path.isfile(filename):
        logging.error('upload: file not found (%s)' % filename)
        raise ValueError('upload: file not found (%s)' % filename)
    contents = open(filename).read() # base64 encoded in _encode_multipart_formdata()
    file = [('file_1', filename, contents)]

    # initiate the POST:
    if log:
        logging.exp('upload: uploading file %s to %s' % (os.path.abspath(filename), selector))
    try:
        status, reason, result = _post_multipart(host, selector, fields, file,
                                                 basicAuth=basicAuth, https=https)
    except TypeError:
        status = 'no return value from _post_multipart(). '
        reason = 'config error?'
        result = status + reason
    except urllib2.URLError as ex:
        logging.error('upload: URL Error. (no internet connection?)')
        raise ex

    # process the result:
    if status == 200:
        result_fields = result.split()
        #result = 'status_msg digest' # if using up.php
        if result_fields[0] == 'good_upload':
            outcome = 'success'+' '+result
        else:
            outcome = result # failure code
    elif status == 404:
        outcome = '404 Not_Found: server config error'
    elif status == 403:
        outcome = '403 Forbidden: server config error'
    elif status == 401:
        outcome = '401 Denied: failed apache Basic authorization, or config error'
    elif status == 400:
        outcome = '400 Bad request: failed, possible config error'
    else:
        outcome = str(status) + ' ' + reason

    if status == -1 or status > 299 or type(status) == str:
        logging.error('upload: ' + outcome[:102])
    else:
        if outcome.startswith('success'):
            if log:
                logging.info('upload: ' + outcome[:102])
        else:
            logging.error('upload: ' + outcome[:102])
    return outcome
