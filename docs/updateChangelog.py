#!/usr/bin/env python
# -*- coding: utf-8 -*-

# this script replaces hashtags with a sphinx URL string (to the github issues or pull request)
# written by Jon with regex code by Jeremy

import re
from pathlib import Path
import os

thisFolder = Path(__file__).absolute().parent
rootFolder = thisFolder.parent
input_path = rootFolder / 'psychopy/CHANGELOG.txt'
output_path = thisFolder / 'source/changelog.rst'


def repl_issue(m):
    g = m.group(1)
    return g.replace('#', '`#') +  " <https://github.com/psychopy/psychopy/issues/" + g.strip(' (#') + ">`_"

def repl_commit(m):
    g = m.group(1)
    return g.replace('#', '`commit:')[:18] +  " <https://github.com/psychopy/psychopy/commit/" + g.strip(' (#') + ">`_"

def repl_noncompat(m):
    g = m.group(1)
    g = g.replace('`', "'")
    return g.replace('CHANGE', ':noncompat:`CHANGE') + "`\n"

print(thisFolder)
print(f"looking in {input_path.absolute()} from {os.getcwd()}")
# raw .txt form of changelog:
txt = open(input_path, "rU", encoding='utf8').read()

# programmatic replacements:
hashtag = re.compile(r"([ (]#\d{3,5})\b")
print("found %i issue tags" %(len(hashtag.findall(txt))))
txt_hash = hashtag.sub(repl_issue, txt)

hashtag = re.compile(r"([ (]#[0-9a-f]{6,})\b")
print("found %i commit tags" %(len(hashtag.findall(txt_hash))))
txt_hash = hashtag.sub(repl_commit, txt_hash)

noncompat = re.compile(r"(CHANGE.*)\n")
print("found %i CHANGE" %(len(noncompat.findall(txt_hash))))
txt_hash_noncompat = noncompat.sub(repl_noncompat, txt_hash)

# one-off specific .rst directives:
newRST = txt_hash_noncompat.replace('PsychoPy uses **major.minor.patch** version numbers', """.. raw:: html

    <style> .noncompat {color:red} </style>

.. role:: noncompat

PsychoPy uses **major.minor.patch** version numbers""", 1)

# add note about blue meaning a change?

with open(output_path, "w", encoding='utf8') as doc:
    doc.write(newRST)

print(f"generated {output_path}")

#test:
#text = "yes #123\n yes (#4567)\n; none of `#123, #3, #45, #12345 #123a"
#newText = expr.sub(repl, text)
#print newText
