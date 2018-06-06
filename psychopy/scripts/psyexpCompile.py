#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compiles a Python script (*.py) form a PsychoPy Builder Experiment file (.psyexp)
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

import argparse

parser = argparse.ArgumentParser(description='Compile your python file from here')
parser.add_argument('infile', help='The input (psyexp) file to be compiled')
parser.add_argument('--version', '-v', help='The PsychoPy version to use for compiling the script. e.g. 1.84.1')
parser.add_argument('--outfile', '-o', help='The output (py) file to be generated (defaults to the ')

args = parser.parse_args()
if args.outfile is None:
    args.outfile = args.infile.replace(".psyexp",".py")
print(args)

if args.version:
    from psychopy import useVersion
    useVersion(args.version)

from psychopy.app.builder import experiment

exp = experiment.Experiment(filename=infile)
if args.outfile.endswith(".html"):
    exp.writeScript(args.outfile, target="PsychoJS")
else:
    exp.writeScript(args.outfile, target="PsychoPy")
