#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Python script to compile a psyexp->python file optionally with a specific version

Usage: python -m psychopy.scripts.psyexpCompile <infile> -v <version> -o <outfile>
"""

if __name__ != "__main__":
    print("DO NOT TRY TO IMPORT THIS, USE IT ONLY AS A SCRIPT.\n"
          "Importing will break the functionality of the "
          "useVersion() code and lead to unpredictable behaviour.")

import os
import argparse
import codecs

parser = argparse.ArgumentParser(description='Compile your python file from here')
parser.add_argument('infile', help='The input (psyexp) file to be compiled')
parser.add_argument('--version', '-v', help='The PsychoPy version to use for compiling the script. e.g. 1.84.1')
parser.add_argument('--outfile', '-o', help='The output (py) file to be generated (defaults to the ')

args = parser.parse_args()
if args.outfile is None:
    args.outfile = args.infile.replace(".psyexp",".py")

# Set version
if args.version:
    from psychopy import useVersion
    useVersion(args.version)
# Import requested version of experiment
from psychopy.app.builder import experiment
# Set experiment object according to version
thisExp = experiment.Experiment()
thisExp.loadFromXML(args.infile)
# Write version to experiment init text
thisExp.psychopyVersion = args.version
# Set output type, either JS or Python
if args.outfile.endswith(".js"):
    targetOutput = "PsychoJS"
else:
    targetOutput = "PsychoPy"

# Write script
script = thisExp.writeScript(args.outfile, target=targetOutput)
args.outfile.replace('.py', targetOutput[-2:].lower())
# Output script to file
f = codecs.open(args.outfile, 'w', 'utf-8')
f.write(script.getvalue())
f.close()
