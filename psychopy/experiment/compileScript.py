#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Python script to compile a psyexp->python file optionally with a specific version

Usage: python compileScript <psyexp_file> [--version]
"""

if __name__ != "__main__":
    print("DO NOT TRY TO IMPORT THIS, USE IT ONLY AS A SCRIPT.\n"
          "Importing will break the functionality of the "
           "useVersion() code and lead to unpredictable behaviour.")
import os
import sys
import codecs

# probably we should do this better with the argparse module
psyexpFile = sys.argv[1]  # 0 will be compileScript.py
if len(sys.argv)>2:
    version = sys.argv[2]
else:
    version = None

if version:
    import psychopy
    psychopy.useVersion(version)

if version is None or version>="1.90":
    from psychopy import experiment
else:
    from psychopy.app.builder import experiment

thisExp = experiment.Experiment()
thisExp.loadFromXML(psyexpFile)
script = thisExp.writeScript(psyexpFile, target="PsychoPy")

fileBase, ext = os.path.splitext(psyexpFile)
f = codecs.open(fileBase+".py", 'w', 'utf-8')
f.write(script.getvalue())
f.close()
