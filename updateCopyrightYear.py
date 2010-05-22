#!/usr/bin/env python

"""looks for 'Copyright (C) <last-year> Jonathan Peirce' in all files in or below the current directory
  ignore .svn, .hg, .git, .pyc, .mp4, ... and so on
to update previous year to the current year, call with sys.argv[1] == 'replace'
  eg in 2008: 'Copyright (C) 2007 Jonathan Peirce'  --> 'Copyright (C) 2008 Jonathan Peirce'
uses perl in-place replacement; maybe there's a pythonic way to do this....
"""

__author__ = 'Jeremy Gray'

import os,sys,time

assert sys.platform == 'darwin' #linux probably fine too
perl = os.popen('perl -V | head -1').read()
assert perl.find('perl5 (revision 5') > -1 # not completely sure what will happen with other perl versions...

newYear = str(time.localtime()[0]) # current year
oldYear = str(int(newYear)-1) # last year; will need to edit this if you skip a year

# do an update (actually replace)? default = no
replace = False
if len(sys.argv)>1 and sys.argv[1] == 'replace':
    replace = True

# for safe find-replace, use a good long unique string. which will have (C), so escape the parens for perl
oldString = 'Copyright \(C\) '+oldYear+' Jonathan Peirce' 
newString = 'Copyright \(C\) '+newYear+' Jonathan Peirce'

#get paths and names of all eligible files (in or below current directory)
files = os.popen('find . | egrep -v ".pyc|/.hg|/.svn|/.git|.dll|.wav|.mp4|.mpg|.ico|.jpg|.png|.DS_Store"').readlines()
files = [f.strip() for f in files]

someFiles = False
tmpFile = '/tmp/tmpUpdateCopyrightYear'
tmp = open(tmpFile, 'w')
# check each file to see if it has the old copyright year:
for file in files: 
    if len(os.popen('grep "Copyright (C) '+oldYear+' Jonathan Peirce" "'+file+'"').read()): # ignore directories etc
        someFiles = True
        print file+': '+"Copyright (C) "+oldYear+" Jonathan Peirce"
        cmd = "perl -pi -e 's/"+oldString+"/"+newString+"/g' '"+file+"'\n"
        tmp.write(cmd) # save the command into a tmp file; python was removing single quotes around strings in os.popen(cmd), blah
tmp.close()

if replace:
    #os.popen('cat '+tmpFile)
    os.popen('source '+tmpFile) # do all of the replacements; commands to do so are in the tmp file
elif someFiles:
    print '\nto update '+oldYear+' to '+newYear+', do:\n  %s replace\n' % sys.argv[0]
else:
    print 'no matching files found for', oldYear
os.unlink(tmpFile)