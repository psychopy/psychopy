#!/usr/bin/env python

"""Illustrates using psychopy.web.upload() to send a file to a configured server

- the file 'filename' is sent "as is" (whether that's cleartext, binary, or encrypted--it's simply uploaded)
- being a demo, this test will try http://www.psychopy.org/test_upload/, which is specially configured to redirect
    to a different server that will run the actual test (= save then delete the file, returning a status code)
- basicAuth is optional. the test server uses it, with the values given, sent in cleartext (not secure).
"""
__author__ = 'Jeremy R. Gray'

from psychopy import logging
from psychopy import web

logging.console.setLevel(logging.DEBUG) # show what's going on

# replace with your selector, filename, basicAuth (optional):
selector = 'http://www.psychopy.org/test_upload/up.php'  #'http://your_host/your_path/up.php'
filename = __file__  # path to file to upload; __file__ is this script--it will upload itself
basicAuth = 'psychopy:open-sourc-ami'  # optional apache basic auth 'user:password'; required for testing / demo

status = web.upload(selector, filename, basicAuth) # do the upload, get return status
#print status # included in the last line of the logging output

