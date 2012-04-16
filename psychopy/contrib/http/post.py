#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Send a file over the internet via http POST (to a configured server)
    
    upload(selector, filename, fields, host, basicAuth)
    - returns: (status, sha256 hexdigest of file on server, file size in bytes)
    - supports & assumes basic auth (apache)
    - aims to be unicode-compatible; not tested; binary files are fine
    - user, userAgent --> server logs
    - base64-encoded for transmission (reducing the effective file size limit)
    
    For future:
    - maybe support https? include server certificate instructions (self-signed)
    
    apache 2.2 Basic auth (sent in clear text). to set up on server, as root:
    # mkdir -p /usr/local/etc/apache
    # htpasswd /usr/local/etc/apache/.htpasswd psychopy # add -c option to create / overwrite
    # chown -R apache:apache /usr/local/etc/apache
    # chmod -R 400 /usr/local/etc/apache
    might need to edit your httpd.conf file to enable auth (& restart apache)
    need to allow POST'ing to your server (and the up.php directory in particular)
    
    Jeremy Gray, March 2012; includes post_multipart from activestate.com (PSF license)
"""

import os, sys, random, base64
from psychopy.core import shellCall
from psychopy.constants import PSYCHOPY_USERAGENT
from psychopy import logging
import hashlib, base64
import httplib, mimetypes, urllib2
import shutil # for testing
from tempfile import mkdtemp

# special / magic selector for tests and demos (returns URL to use for actual post):
SELECTOR_FOR_TESTS = 'http://www.psychopy.org/test_upload/up.php'

### post_multipart is from {{{ http://code.activestate.com/recipes/146306/ (r1) ###
def _post_multipart(host, selector, fields, files, encoding='utf-8', timeout=5,
                    userAgent=PSYCHOPY_USERAGENT, basicAuth=None):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    file is a 1-item sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    # as updated for HTTPConnection()
    # as rewritten for any encoding http://www.nerdwho.com/blog/57/enviando-arquivos-e-dados-ao-mesmo-tempo-via-http-post-usando-utf-8/
    # JRG: added timeout, userAgent, basic auth

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
    conn = httplib.HTTPConnection(host, timeout=timeout)
    headers = {u'User-Agent': userAgent,
               u'Charset': encoding,
               u'Content-Type': content_type,
               }
    # apache basic auth (sent in clear text):
    if basicAuth and type(basicAuth) == str:
        user_cred = base64.encodestring(basicAuth).replace('\n', '')
        headers.update({u"Authorization": u"Basic %s" % user_cred})
    try:
        conn.request(u'POST', selector, body, headers)
    except: # ? don't seem to get a proper exception
        return -1, 'connection error; timeout after %ss' % str(timeout), 'timeout or error'
    
    try:
        result = conn.getresponse()
    except:
        return -1, 'connection error (can be "socket.error: [Errno 54] Connection reset by peer")'
    return result.status, result.reason, result.read()

    ## end of http://code.activestate.com/recipes/146306/ }}}
    

def upload(selector, filename, basicAuth=None, host=None):
    """Post a file to a configured http server.
    
    This method handshakes with a php script on a remote server to transfer a local
    file to another machine via http.
    
    .. note::
        The server that receives the files needs to be configured before uploading
        will work. Notes for a sys-admin are included in psychopy/contrib/http/.
        In particular, the php script `up.php` needs to be copied to the server's
        web-space, with appropriate permissions and directories, including apache
        basic auth (if desired).
    
        A test server is available through http://www.psychopy.org/;
        see the Coder demo for details. 
    
    **Parameters:**
    
        `selector` : (required)
            URL, e.g., 'http://<host>/path/to/up.php'
        `filename` : (required)
            path to local file to be transferred. Any format: text, utf-8, binary
        `basicAuth` : (optional)
            apache 'user:password' string for basic authentication. If a basicAuth
            value is supplied, it will be sent as the auth credentials (in cleartext,
            not intended to be secure).
        `host` : (optional)
            typically extracted from `selector`; specify explicitly if its something different
    
    **Example:**
    
        See Coder demo / misc / http_upload.py
    
    Author: Jeremy R. Gray, 2012
    """
    fields = [('name', 'PsychoPy_upload'), ('type', 'file')]
    if not selector:
        logging.error('post: need a selector, http://<host>/path/to/up.php')
        raise ValueError('post: need a selector, http://<host>/path/to/up.php')
    if not host:
        host = selector.split('/')[2]
        logging.info('post: host extracted from selector = %s' % host)
    if not os.path.isfile(filename):
        logging.error('post: file not found (%s)' % filename)
        raise ValueError('post: file not found (%s)' % filename)
    contents = open(filename).read() # base64 encoded in _encode_multipart_formdata()
    file = [('file_1', filename, contents)]

    # handle special case selector: for demo and unit-tests, want to redirect to 
    # up_no_save.php (which itself calls the real up.php, then deletes the file)
    if selector == SELECTOR_FOR_TESTS:
        html = urllib2.urlopen('http://www.psychopy.org/test_upload/')
        data = html.read()
        if not(data.find('http://') > -1 and data.find('up_no_save.php') > -1):
            logging.error('post: TEST / DEMO bad redirect URL ' + data.replace('\n', ' '))
            raise ValueError('unexpected redirection URL value returned from %s' % host)
        selector = data[data.find('http://'): data.find('up_no_save.php')+14]
        host = selector.split('/')[2]
        logging.info('post: TEST / DEMO special-case redirected to %s' % selector)
    
    # initiate the POST:
    logging.exp('post: uploading %s to %s' % (os.path.abspath(filename), selector))
    try:
        status, reason, result = _post_multipart(host, selector, fields, file,
                                                 basicAuth=basicAuth)
    except TypeError:
        status = 'no return value from _post_multipart(). '
        reason = 'config error?'
        result = status + reason
    
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
    
    if status > 299 or type(status) == str:
        logging.error('post: '+outcome[:102])
    else:
        logging.info('post: '+outcome[:102])
    return outcome

def _test_post():
    def _test_upload(stuff):
        """assumes that SELECTOR_FOR_TESTS will return the URL of a configured http server
        """
        selector = SELECTOR_FOR_TESTS
        basicAuth = 'psychopy:open-sourc-ami'
        
        # make a tmp dir just for testing:
        tmp = mkdtemp()
        filename = 'test.txt'
        tmp_filename = os.path.join(tmp, filename)
        f = open(tmp_filename, 'w+')
        f.write(stuff)
        f.close()
        
        # get local sha256 before cleanup:
        digest = hashlib.sha256()
        digest.update(open(tmp_filename).read())
        dgst = digest.hexdigest()
        
        # upload:
        status = upload(selector, tmp_filename, basicAuth)
        shutil.rmtree(tmp) # cleanup; do before asserts
        
        # test
        good_upload = True
        disgest_match = False
        if not status.startswith('success'):
            good_upload = False
        elif status.find(dgst) > -1:
            logging.exp('digests match')
            digest_match = True
        else:
            logging.error('digest mismatch')
        
        logging.flush()
        assert good_upload # remote server FAILED to report success
        assert digest_match # sha256 mismatch local vs remote file
        
        return int(status.split()[3]) # bytes
        
    # test upload: normal text, binary:
    msg = PSYCHOPY_USERAGENT # can be anything
    print 'text:   '
    bytes = _test_upload(msg) #normal text
    assert (bytes == len(msg)) # FAILED to report len() bytes
    
    print 'binary: '
    digest = hashlib.sha256()  # to get binary, 256 bits
    digest.update(msg)
    bytes = _test_upload(digest.digest())
    assert (bytes == 32) # FAILED to report 32 bytes for a 256-bit binary file (= odd if digests match)
    logging.exp('binary-file byte-counts match')

if __name__ == '__main__':
    """do the unit-test for this module"""
    logging.console.setLevel(logging.DEBUG)
    _test_post()