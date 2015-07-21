#!/usr/bin/env python

# this script replaces hashtags with a sphinx URL string (to the github issues or pull request) 
# written by Jon with regex code by Jeremy

import re
expr = re.compile(r"([ (]#\d{3,4})\b")

def repl(m):
    g = m.group(1)
    return g.replace('#', '`#') +  " <https://github.com/psychopy/psychopy/issues/" + g.strip(' (#') + ">`_"

with open("docs/source/changelog.rst", "r") as doc:
    txt = doc.read()
print "found %i hashtags" %(len(expr.findall(txt)))
newTxt = expr.sub(repl, txt)

with open("docs/source/changelog.rst", "wb") as doc:
    doc.write(newTxt)

#test:
#text = "yes #123\n yes (#4567)\n; none of `#123, #3, #45, #12345 #123a"
#newText = expr.sub(repl, text)
#print newText
