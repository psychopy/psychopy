#!/usr/bin/env python

"""illustrates using psychopy.contrib.http.post to send a file to a configured server

- the file info['filename'] is sent "as is" (whether that's cleartext, binary, or encrypted--all are simply uploaded)
- being a demo, this test will try http://www.psychopy.org/test_upload/, which is specially configured to redirect
    to a different server that will run the actual test (= save then delete the file, returning a status code)
- basicAuth is optional. the test server uses it, with the values given, sent in cleartext (not secure).
"""
__author__ = 'Jeremy R. Gray'

from psychopy.contrib.http import post

# replace with your selector, filename, basicAuth (optional):
selector = 'http://www.psychopy.org/test_upload/up.php'  #'http://your_host/your_path/up.php'
filename = __file__  # path to file to upload; __file__ is this script--it will upload itself
basicAuth = 'psychopy:open-sourc-ami'  # optional apache basic auth 'user:password'

print 'trying %s' % selector
status = post.upload(selector, filename, basicAuth) # do the upload, get return value
print status

if not status.startswith('success'): # handle your error conditions, e.g., warn that upload failed
    print '''\nFAILED.\na good upload will return something like this (different sha256 and byte count):
success good_upload c5df3bf286b8e3cc9bfccaf1218adf43342b6725c901987bda7989e29c136b45 984'''