#!/usr/bin/env python

"""coder demo for using http upload"""
__author__ = 'Jeremy R. Gray'

from psychopy.contrib.http import post

# edit info to reflect your set-up:
info = {
    'host': 'scanlab.psych.yale.edu', # your server; IP address is fine
    'selector': 'http://scanlab.psych.yale.edu/psychopy_org/up.php', # your path to up.php on server
    'filename': __file__} # path to file on your local machine to be uploaded; __file__ is this script

status = post.upload(**info) # do the upload
print status

# several kinds of error are possible. if you just run this demo you'll probably get this one:
if status.startswith('403'):
    print '? maybe your local IP address (see http://whatip.com) is blocked by "%s"' % info['host']
# email me your IP address (jrgray@gmail.com) and I'll enable it for testing purposes
# also see http://scanlab.psych.yale.edu/psychopy_org/send.php