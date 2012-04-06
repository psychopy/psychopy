#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Send a file over the internet via http POST (to a configured server)
    
    upload(fields, host, selector, filename)
    - returns: (status, sha256 hexdigest of file on server, file size in bytes)
    - supports & assumes basic auth (apache)
    - aims to be unicode-compatible; not tested; binary files are fine
    - user, userAgent --> server logs
    - base64-encoded for transmission (reducing the effective file size limit)
    
    For future:
    - support apache Digest authorization
      for auth options see: http://httpd.apache.org/docs/2.2/misc/password_encryptions.html
    - maybe support https? include server certificate instructions (self-signed)
    
    apache Basic auth (sent in clear text). to set up on server, as root:
    # mkdir -p /usr/local/etc/apache
    # htpasswd /usr/local/etc/apache/.htpasswd psychopy # add -c option to create / overwrite
    # chown -R apache:apache /usr/local/etc/apache
    # chmod -R 400 /usr/local/etc/apache
    might need to edit your httpd.conf file to enable auth (& restart apache)
    
    Jeremy Gray, March 2012; includes post_multipart from activestate.com (PSF license)
"""

import os, sys, random, base64
from psychopy.core import shellCall
from psychopy import logging
import hashlib, base64
import httplib, mimetypes
import shutil # for testing
from tempfile import mkdtemp

### post_multipart is from {{{ http://code.activestate.com/recipes/146306/ (r1) ###
def _post_multipart(host, selector, fields, files, encoding='utf-8', timeout=5,
                    userAgent='PSYCHOPY_USERAGENT', user='psychopy', cred='open-sourc-ami'):
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
    
    content_type, body = _encode_multipart_formdata(fields, files)
    conn = httplib.HTTPConnection(host, timeout=timeout)
    headers = {u'User-Agent': userAgent,
               u'Charset': encoding,
               u'Content-Type': content_type,
               }
    # apache basic auth (sent in clear text):
    user_cred = base64.encodestring('%s:%s' % (user, cred)).replace('\n', '')
    if len(user):
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
    

def upload(fields=None, host=None, selector=None, filename=None):
    """Method for posting a file to a configured server, passed through base64.
    
    This method handshakes with up.php, transfer one local file from psychopy to
    another machine, via http.
    """
    if not fields:
        fields = [('name', 'PsychoPy_upload'), ('type', 'file')]
    if not host:
        logging.error('need a host, as DNS name or IP address')
        raise ValueError('need a host name or IP address')
    if not selector:
        logging.error('need a selector, http://<host>/path/to/up.php')
        raise ValueError('need a selector, http://<host>/path/to/up.php')
    if not os.path.isfile(filename):
        logging.error('file not found (%s)' % filename)
        raise ValueError('file not found (%s)' % filename)
    contents = open(filename).read() # base64 encoded in _encode_multipart_formdata()
    file = [('file_1', filename, contents)]

    try:
        status, reason, result = _post_multipart(host, selector, fields, file)
    except TypeError:
        status = 'no return value from _post_multipart(). '
        reason = 'config error?'
        result = status + reason
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
        outcome = '401 Denied: failed auth, or config error'
    elif status == 400:
        outcome = '400 Bad request: failed, possible config error'
    else:
        outcome = str(status) + ' ' + reason
    
    if status > 299 or type(status) == str:
        logging.error(outcome[:100])
    else:
        logging.exp(outcome[:100])
    return outcome

def _test_post():
    def _test_upload(stuff):
        """test assumes a properly configured http server with up.php in your web space
        """
        fields = [('name', 'PsychoPy_upload'), ('type', 'file')]
        host = 'scanlab.psych.yale.edu'
        port = ':80'
        selector = 'http://' + host + port + '/upload_test/up_no_save.php'
    
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
        status = upload(fields, host, selector, tmp_filename)
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
    msg = 'yo!'
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
    """doing a proper unit-test for this module might be problematic (because
    need a configured server), so I expect it to be run manually from command line"""
    logging.console.setLevel(logging.DEBUG)
    _test_post()