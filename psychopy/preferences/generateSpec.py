#!/usr/bin/env python
# -*- coding: utf-8 -*-

# generate .spec files for all OS's based on differences from baseNoArch.spec
# copies & tweaks baseNoArch.spec -> write out as platform specific .spec file

from __future__ import absolute_import, print_function

import os
from psychopy.core import PY3

if PY3:
    write_mode = 'w'
else:
    write_mode = 'wb'


startPath = os.getcwd()
if os.path.split(__file__)[0]:
    os.chdir(os.path.split(__file__)[0])

# load the base prefs common to all platforms as a single string:
baseSpec = open('baseNoArch.spec').read()
warning = '''\n\n# !! This file is auto-generated and will be overwritten!!
    # Edit baseNoArch.spec (all platforms) or generateSpec.py
    # (platform-specific) instead.'''.replace('    ', '')

# Darwin:
darwinSpec = baseSpec.replace('psychopy prefs for ALL PLATFORMS',
                              'psychopy prefs for Darwin.' + warning)
darwinSpec = darwinSpec.replace("list('portaudio')",
                                "list('coreaudio', 'portaudio')")
darwinSpec = darwinSpec.replace("allowModuleImports = boolean(default='True')",
                                '')
darwinSpec = darwinSpec.replace("default='Helvetica'",
                                "default='Monaco'")
# no parallel port on a mac but user might create for other platform:
macDevPorts = "'0x0378', '0x03BC', '/dev/parport0', '/dev/parport1'"
darwinSpec = darwinSpec.replace("'0x0378', '0x03BC'",
                                macDevPorts)
# Note: Darwin key-binding prefs should be given as Ctrl+Key here,
# displayed in menus and prefs as Cmd+Key to user
with open('Darwin.spec', write_mode) as f:
    f.write(darwinSpec)

# Linux and FreeBSD:
linuxSpec = baseSpec.replace('psychopy prefs for ALL PLATFORMS',
                             'psychopy prefs for Linux.' + warning)
linuxSpec = linuxSpec.replace('integer(6,24, default=14)',
                              'integer(6,24, default=12)')
linuxSpec = linuxSpec.replace("default='Helvetica'",
                              "default='Ubuntu Mono, DejaVu Sans Mono'")
linuxSpec = linuxSpec.replace("allowModuleImports = boolean(default='True')",
                              '')
linuxSpec = linuxSpec.replace("'0x0378', '0x03BC'",  # parallel ports
                              "'/dev/parport0', '/dev/parport1'")
with open('Linux.spec', write_mode) as f:
    f.write(linuxSpec)

freeBSDSpec = linuxSpec.replace('psychopy prefs for Linux.',
                                'psychopy prefs for FreeBSD.')
freeBSDSpec = freeBSDSpec.replace("default='Ubuntu Mono, DejaVu Sans Mono'",
                                  "default='Palatino Linotype'")
with open('FreeBSD.spec', write_mode) as f:
    f.write(freeBSDSpec)

# Windows:
winSpec = baseSpec.replace('psychopy prefs for ALL PLATFORMS',
                           'psychopy prefs for Windows.' + warning)
winSpec = winSpec.replace("list('portaudio')",
                          "list('Primary Sound','ASIO','Audigy')")
winSpec = winSpec.replace("default='Helvetica'",
                          "default='Lucida Console'")
winSpec = winSpec.replace('integer(6,24, default=14)',
                          'integer(6,24, default=10)')
winSpec = winSpec.replace('Ctrl+Q',
                          'Alt+F4')
with open('Windows.spec', write_mode) as f:
    f.write(winSpec)

os.chdir(startPath)
