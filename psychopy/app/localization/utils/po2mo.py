#!/usr/bin/env python2

"""Helper script to convert .po files to .mo

No args = convert all files; arg = path/file(s) to convert
expects res_po/message*.po -> res/message*.mo
Needed after editing a po file (new translation) or adding new ones.

Author: Jeremy R. Gray, 2014
"""

import glob, subprocess, os, sys

path = os.path.dirname(__file__)
msgfmt = os.path.join(path, 'msgfmt.py')

if len(sys.argv) > 1:
    poList = sys.argv[1:]
else:
    poList = glob.glob('../res_po/*.po')

for po in poList:
    print po
    mo = po.replace('.po', '.mo').replace('_po', '')
    subprocess.check_output(['python', msgfmt, '-o', mo, po])
