#!/usr/bin/env python
import nose, sys

argv = sys.argv
argv.append('--verbosity=3')
if 'cover' in argv: 
    argv.remove('cover')
    argv.append('--with-coverage')
    argv.append('--with-doctest')
    argv.append('--cover-package=psychopy')

nose.run(argv=argv)
