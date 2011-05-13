#!/usr/bin/env python

# generate .spec files for all OS's based on differences from baseNoArch.spec
# copies & tweaks baseNoArch.spec -> write out as platform specific .spec file

# load the base prefs common to all platforms as a single string:
baseSpec = open('baseNoArch.spec').read()
warning = '\n# !! This file is auto-generated and will be overwritten!!\n#Edit baseNoArch.spec instead.'

# Darwin:
darwinSpec = baseSpec.replace('psychopy prefs for ALL PLATFORMS', 'psychopy prefs for Darwin.' + warning)
darwinSpec = darwinSpec.replace("allowModuleImports = boolean(default='True')", '')
# Note: Darwin key-binding prefs should be given as Ctrl+O here, displayed as Cmd+O to user
f = open('Darwin.spec', 'wb+')
f.write(darwinSpec)
f.close()

# Linux and FreeBSD:
linuxSpec = baseSpec.replace('psychopy prefs for ALL PLATFORMS', 'psychopy prefs for Linux.' + warning)
linuxSpec = linuxSpec.replace('integer(6,24, default=14)','integer(6,24, default=12)')
linuxSpec = linuxSpec.replace("default='Helvetica'", "default='Arial'")
linuxSpec = linuxSpec.replace("default='Monaco'", "default='Courier New'")
linuxSpec = linuxSpec.replace("allowModuleImports = boolean(default='True')", '')
f = open('Linux.spec', 'wb+')
f.write(linuxSpec)
f.close()

freeBSDSpec = linuxSpec.replace('psychopy prefs for Linux.', 'psychopy prefs for FreeBSD.')
f = open('FreeBSD.spec', 'wb+')
f.write(freeBSDSpec)
f.close()

# Windows:
winSpec = baseSpec.replace('psychopy prefs for ALL PLATFORMS', 'psychopy prefs for Windows.'+ warning)
winSpec = winSpec.replace("default='Helvetica'", "default='Arial'")
winSpec = winSpec.replace("default='Monaco'", "default='Courier New'")
winSpec = winSpec.replace('integer(6,24, default=14)','integer(6,24, default=10)')
winSpec = winSpec.replace('Ctrl+Q', 'Alt+F4')
f = open('Windows.spec', 'wb+')
f.write(winSpec)
f.close()