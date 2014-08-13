#!/usr/bin/env python2

"""Illustrates using psychopy.web.upload() to send a file over the internet to a configured server.

- This demo will upload a file to http://upload.psychopy.org/test/up.php.
- The file 'filename' is sent as is, whether that's cleartext, binary, or encrypted. It's simply uploaded.
- A configured server saves the file, and returns a status code. "Configured" means that it has the receiving
    script, up.php, accessible online (in its web space), plus necesssary file permissions. up.php is provided
    as part of psychopy along with notes for a sys-admin, see psychopy/contrib/http/.
- This demo will save and then delete the file, and indicate "demo_no_save". 'too_big' means the file was too large
- basicAuth is optional. The test server uses it with the values given, sent in cleartext (not secure). 
"""
__author__ = 'Jeremy R. Gray'

from psychopy import web

from psychopy import logging
logging.console.setLevel(logging.DEBUG) # show what's going on

#selector = 'http://host/path/to/up.php'
selector = 'http://upload.psychopy.org/test/up.php' # specially configured for testing / demo (no saving)
filename = __file__  # path to file to upload; __file__ is this script--it will upload itself
basicAuth = 'psychopy:open-sourc-ami'  # optional apache basic auth 'user:password'; required for testing / demo

status = web.upload(selector, filename, basicAuth) # do the upload, get return status
