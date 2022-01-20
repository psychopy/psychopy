#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""utility for creating a .csv file from a .psydat file

edit the file name, then run the script
"""

import os
from psychopy.tools.filetools import fromFile

# EDIT THE NEXT LINE to be your .psydat file, with the correct path:
name = 'fileName.psydat'

file_psydat = os.path.abspath(name)
print("psydat: {0}".format(file_psydat))

# read in the experiment session from the psydat file:
exp = fromFile(file_psydat)

# write out the data in .csv format (comma-separated tabular text):
if file_psydat.endswith('.psydat'):
    file_csv = file_psydat[:-7]
else:
    file_csv = file_psydat
file_csv += '.csv'
exp.saveAsWideText(file_csv)

print('-> csv: {0}'.format(os.path.abspath(file_csv)))
