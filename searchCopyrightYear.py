#!/usr/bin/env python

"""looks for lines containing 'Copyright|(C)', <last-year>, and 'Peirce' in all files in or below the current directory
  ignore .svn, .hg, .git, .pyc, .mp4, ... and some others
and writes out an executable file, replaceCopyright<year>, with commands that could be used to update last-year to the current year.

usage steps:
- 'svn update'
- 'svn commit any pending changes'
- 'python psychopy/tests/run.py'
- './searchCopyrightYear.py'
- review the new file, replaceCopyright<Year>.sh, edit as needed
- './replaceCopyrightYear.py' -- this does the replacing
- 'python psychopy/tests/run.py' -- make sure we didn't break anything
- 'svn commit -m "updated copyright year"'

currently will handle:
Copyright (C) 2009 Jonathan Peirce
(C) 2002-2009 Jonathan Peirce
copyright = u'2009, Jonathan Peirce'
PsychoPy2, version %s (c)Jonathan Peirce, 2009, GNU GPL
Copyright (c) 2002-2009, JW Peirce.

relies on: perl -pi -e 's/\Qold\E/new/' <file>
I couldn't figure out a pythonic way to do in-place changes to files
import fileinput # looked promising but a) don't really want to copy every line of every file, and b) doesn't actually work easily...
for line in fileinput.input(file, inplace = 1):
  print line.replace(...).strip() #--> loses initial whitespace
  line.replace(....) #--> adds quote marks around line
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
files = os.popen("find . | sed -e 's/ /\\ /g'" + ' | egrep -v ".pyc|/.hg|/.svn|/.git|.pdf|.dll|.wav|.mp4|.mpg|.ico|.jpg|.gif|.png|.DS_Store"').readlines()
files = [f.strip() for f in files]
print len(files), 'files found, screening each'

badLines = 0 #  ['$/] will mess with perl search-replace; other characters might too
targetFiles = 0 # count of files to be updated
tmpFile = './replaceCopyright'+oldYear+'_'+newYear+'.sh'
try: del files[files.index(tmpFile)]
except: pass
tmp = open(tmpFile, 'w')
tmp.write('#!/bin/sh \n echo Updating...\n')

# check each line of each file:
for file in files: 
    lines = os.popen('grep '+oldYear+' "'+file+'" | grep Peirce | egrep -i "\(c\)|copyright"').readlines()
    for line in lines: #allow multiple lines per file, each gets its own replace command; directories -> ignored
        line = line.strip()
        anchor = '^' # start-of-line anchor makes search-replace more efficient
        if line.find("'") > -1: # capture stuff in between single-quotes, hopefully including the year
            line = line[line.find("'")+1:]
            line = line[:line.find("'")]
            if line.find(oldYear) == -1:
                badLines += 1
                print file+": expected <last-year> somewhere between single-quotes:", line
                continue
            anchor = '' # will not match at the start of the line anymore
        if line.find('$') > -1 or line.find('/') > -1:
            badLines += 1
            print file+": cannot handle '$' or '/' in line:", line
            continue
        newLine = line.replace(oldYear, newYear) # should not contain characters that will mess with perl 's/oldLine/newLine/'
        cmd = "echo "+file+"\n" # helps with debugging, if the perl s/// flails due to a bad character -> you know what file to look at
        cmd += "perl -pi -e 's/"+anchor+"\Q"+line+"\E/"+newLine+"/' '"+file+"'\n" # only match one line, avoid s///g
        tmp.write(cmd) 
        targetFiles += 1
tmp.write('echo Updated %d files.\n' % targetFiles)
tmp.close()

print os.popen('cat '+tmpFile+" | grep 'perl -pi -e'").read() # merely display, do not actually do, all of the replacement commands
os.popen('chmod u+x '+tmpFile) # make executable
if targetFiles:
    print 'If all of the above changes look correct, to make all changes type:\n  '+tmpFile
    print 'If something looks amiss, you can manually edit '+tmpFile+', and then run it.'
    if badLines:
        print "Warning: %d lines were skipped because they had a special character, see output" % badLines
else:
    print 'No matching files found for year', oldYear
    os.unlink(tmpFile)
