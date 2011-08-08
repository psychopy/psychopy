#!/bin/sh

find . | sed -e 's/ /\\ /g' | egrep -v ".pyc|/.hg|/.svn|/.git|.pdf|.dll|.wav|.mp4|.mpg|.ico|.jpg|.gif|.png|.DS_Store|/sandbox/|/pyobjc-core|/pyobjc-framework-|/pygame-examples|/pygame-headers|/pygame-SDL|/pygame-docs-|/pygame-platlib-"
