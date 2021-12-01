#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""looks for lines containing 'Copyright|(C)', <last-year>, and 'Peirce'
in all files in or below the current directory
and writes out an executable file, replaceCopyright<year>, with commands that
could be used to update last-year to the current year.

usage steps:
- run tests
- ./searchCopyrightYear.py
- review the new file, replaceCopyright<Year>.sh, edit as needed
- ./replaceCopyrightYear.sh -- this does the replacing
- run tests again -- make sure we didn't break anything
- commit

relies on: perl -pi -e 's/\\Qold\\E/new/' <file>
I couldn't figure out a pythonic way to do in-place changes to files
import fileinput # looked promising but a) don't really want to copy every line
of every file, and b) doesn't actually work easily...
for line in fileinput.input(file, inplace = 1):
  print line.replace(...).strip() #--> loses initial whitespace
  line.replace(....) #--> adds quote marks around line
"""
__author__ = 'Jeremy Gray'

import os, sys, time, glob

from psychopy import core

assert (sys.platform == 'darwin' or sys.platform.startswith('linux')), "This script must be run on a unix-based platform"
perlVersion = core.shellCall('perl -V').splitlines()[0]
assert perlVersion.find('perl5') > -1 # not completely sure what will happen with other perl versions...

newYear = str(time.localtime()[0]) # current year
oldYear = str(int(newYear)-1) # last year; will need to set manually if you miss a year

print("copyright %s -> %s: searching for files" % (oldYear, newYear))

#find relevant files:
files = []
toSearch = ['.txt', '.py', 'md1', '.rst', '.ps1', '.nsi', ]
excludeFolders = set(['build', 'dist', '.git'])
for root, dirs, tmpfiles in os.walk('.', topdown=True):
    dirs[:] = [d for d in dirs if d not in excludeFolders]
    for f in tmpfiles:
        file = root+'/'+f
        main, ext = os.path.splitext(file)
        # if ext in ['.html','.orig','.pickle','.doctree','.pyc','.pdf','.dll',
        #            '.pyw', '.mov', '.wav','.mp4','.mpg','.ico','.jpg','.gif',
        #            '.png','.DS_Store','.xlsx', '.icns','.svg',
        #            '.so','.mo','.h5','ttf','.dat']:
        #     continue
        if ext in toSearch:
            files.append(file)
print(len(files), 'files found, screening each')

badLines = 0 #  ['$/] will mess with perl search-replace; other characters might too
targetFiles = 0 # count of files to be updated
tmpFile = './replaceCopyright'+oldYear+'_'+newYear+'.sh'
try:
    del files[files.index(tmpFile)]
except:
    pass
tmp = open(tmpFile, 'w')
tmp.write('#!/bin/sh \necho Updating...\n')

# check each line of each relevant file:
for file in files:
    if os.path.isdir(file) or file.endswith(sys.argv[0]):
        continue
    try:
        contents = open(file, 'r').readlines()
    except UnicodeDecodeError:
        print("Couldn't read file '{}'".format(file))
    lines = [line for line in contents if \
             line.find("Peirce") > -1 and \
             line.find(oldYear) > -1 and \
             (line.lower().find("(c)") > -1 or line.lower().find("copyright") > -1)
             ]
    for i,line in enumerate(lines): #allow multiple lines per file, each gets its own replace command
        #print i+1, file
        line = line.strip()
        #print line
        if line.find("'") > -1: # capture stuff in between single-quotes, hopefully including the year
            line = line[line.find("'")+1:]
            line = line[:line.find("'")]
            if line.find(oldYear) == -1:
                badLines += 1
                print(file+": expected <last-year> somewhere between single-quotes:", line)
                continue # skip the line
        if '$' in line:
            badLines += 1
            print(file+": cannot handle '$' in line:", line)
            continue
        sep = '/'  # perl search-replace separator
        if sep in line:
            sep = '|'  # try this one instead
            if sep in line:
                badLines += 1
                print(file+": cannot handle '"+sep+"' in line:", line)
                continue
        newLine = line.replace(oldYear, newYear) # should not contain characters that will mess with perl 's/oldLine/newLine/'
        cmd = "echo "+file+"\n  " # helps with debugging, if the perl s/// flails due to a bad character -> you know what file to look at
        cmd += "perl -pi -e 's"+sep+r"\Q"+line+r"\E"+sep+newLine+sep+"' '"+file+"'\n" # only match one line, avoid s///g
        tmp.write(cmd)
        targetFiles += 1
tmp.write('echo Updated %d files.\n' % targetFiles)
tmp.close()

core.shellCall('chmod u+x '+tmpFile) # make executable
if targetFiles:
    print('To make %d changes, inspect then run:\n  '%targetFiles, tmpFile)
    print('If something looks amiss, you can manually edit then run it.')
    if badLines:
        print("Warning: %d lines were skipped" % badLines)
else:
    print('No matching files found for year', oldYear)
    os.unlink(tmpFile)
