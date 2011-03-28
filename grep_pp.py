#!/usr/bin/env python

# grep for psychopy project

import sys, os

cmd = "find . | sed -e 's/ /\\\\ /g' | egrep -v '/build/|/windlls/|/.git/|/.hg/|/.svn/|.pyc|.pdf|.wav|.mp4|.mpg|.ico|.jpg|.gif|.png|.DS_Store' | xargs grep -n " + ' '.join(sys.argv[1:])
print cmd
print os.popen(cmd).read()
