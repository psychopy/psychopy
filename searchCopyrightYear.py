#!/usr/bin/env python

"""looks for lines containing 'Copyright|(C)', <last-year>, and 'Peirce' in all files in or below the current directory
  ignore .svn, .hg, .git, .pyc, .mp4, ... and some others
and writes out a file with commands to update previous year to the current year
  eg in 2008: 'Copyright (C) 2007 Jonathan Peirce'  --> 'Copyright (C) 2008 Jonathan Peirce'
this program by itself never makes any changes, just generates a file that will do so if you source it.

eg, finds:
Copyright (C) 2009 Jonathan Peirce
(C) 2002-2009 Jonathan Peirce
copyright = u'2009, Jonathan Peirce'
PsychoPy2, version %s (c)Jonathan Peirce, 2009, GNU GPL
Copyright (c) 2002-2009, JW Peirce.

uses perl -pi -e ...; I couldn't figure out a pythonic way to do in-place changes to files
import fileinput
for line in fileinput.input(file, inplace = 1):
  print line.replace(...).strip() --> loses initial whitespace
  line.replace(....) --> adds quote marks around line
"""

__author__ = 'Jeremy Gray'

import os,sys,time

assert sys.platform == 'darwin' or sys.platform.startswith('linux')
perl = os.popen('perl -V | head -1').read()
assert perl.find('perl5') > -1 # not completely sure what will happen with other perl versions...

newYear = str(time.localtime()[0]) # current year
oldYear = str(int(newYear)-1) # last year; will need to set manually if you miss a year

print "Checking all lines of all files for copyright <year> info..."

#get paths and names of eligible files (in or below current directory)
files = os.popen('find . | egrep -v ".pyc|/.hg|/.svn|/.git|.pdf|.dll|.wav|.mp4|.mpg|.ico|.jpg|.png|.DS_Store"').readlines()
files = [f.strip() for f in files]
try: del files[files.index(sys.argv[0])]
except: pass # not in the list

someFiles = False # found any at all to be updated?
tmpFile = './replaceCopyrightYear.tmp'
try: del files[files.index(tmpFile)]
except: pass
tmp = open(tmpFile, 'w')

# check each line of each file:
for file in files: 
    lines = os.popen('grep '+oldYear+' "'+file+'" | grep Peirce | egrep -i "\(c\)|copyright"').readlines()
    for line in [i.strip() for i in lines]: #allow multiple lines per file, ignore directories etc
        anchor = '^' # start-of-line anchor makes search-replace much more efficient
        if line.find("'") > -1: # capture stuff in between single-quotes
            line = line[line.find("'")+1:]
            line = line[:line.find("'")]
            anchor = ''
        newLine = line.replace(oldYear, newYear)
        someFiles = True
        #print file+': '+line+' --> '+newLine
        cmd = "perl -pi -e 's/"+anchor+"\Q"+line+"\E/\Q"+newLine+"\E/' '"+file+"'\n" # 'source' fails if there are single quotes in the line...
        tmp.write(cmd) # save the command into a tmp file
tmp.close()

print os.popen('cat '+tmpFile).read() # merely display, do not actually do, all of the replacement commands
if someFiles:
    print '\nIf all of the above changes look correct, to make all changes type:\n  source '+tmpFile
    print 'If something looks amiss, you can edit '+tmpFile+', and then source it.'
else:
    print 'No matching files found for', oldYear
    os.unlink(tmpFile)
