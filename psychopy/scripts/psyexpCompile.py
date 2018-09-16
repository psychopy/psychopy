#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import argparse
import codecs
from psychopy.app.builder import experiment
from psychopy import logging

# parse args for subprocess
parser = argparse.ArgumentParser(description='Compile your python file from here')
parser.add_argument('infile', help='The input (psyexp) file to be compiled')
parser.add_argument('--version', '-v', help='The PsychoPy version to use for compiling the script. e.g. 1.84.1')
parser.add_argument('--outfile', '-o', help='The output (py) file to be generated (defaults to the ')

def compileScript(infile=None, version=None, outfile=None):
    """
    This function will compile either Python or JS PsychoPy script from .psyexp file.
        :param infile: The input (psyexp) file to be compiled
        :param version: The PsychoPy version to use for compiling the script. e.g. 1.84.1.
                        Warning: Cannot set version if module imported. Set version from
                        command line interface only.
        :param outfile: The output (py) file to be generated (defaults to Python script.
    """
    if __name__ != '__main__' and version not in [None, 'None', 'none', '']:
        version = None
        msg = "You cannot set version by calling compileScript() manually. Setting 'version' to None."
        logging.warning(msg)

    # Check infile type
    if isinstance(infile, experiment.Experiment):
        thisExp = infile
    else:
        thisExp = experiment.Experiment()
        thisExp.loadFromXML(infile)
        # Write version to experiment init text
        thisExp.psychopyVersion = version

    # Set output type, either JS or Python
    if outfile.endswith(".js"):
        targetOutput = "PsychoJS"
    else:
        targetOutput = "PsychoPy"

    # Write script
    if targetOutput == "PsychoJS":
        # Write module JS code
        script = thisExp.writeScript(outfile, target=targetOutput, modular=True)
        # Write no module JS code
        outfileNoModule = outfile.replace('.js', 'NoModule.js')  # For no JS module script
        scriptNoModule = thisExp.writeScript(outfileNoModule, target=targetOutput, modular=False)
        # Store scripts in list
        scriptDict = {'outfile': script, 'outfileNoModule': scriptNoModule}
    else:
        script = thisExp.writeScript(outfile, target=targetOutput)
        scriptDict = {'outfile': script}

    # Output script to file
    for scripts in scriptDict:
        with codecs.open(eval(scripts), 'w', 'utf-8') as f:
            f.write(scriptDict[scripts])
        f.close()

if __name__ == "__main__":

    # define args
    args = parser.parse_args()
    if args.outfile is None:
        args.outfile = args.infile.replace(".psyexp", ".py")

    # Set version
    if args.version:
        from psychopy import useVersion
        useVersion(args.version)

    # run PsychoPy with useVersion active
    compileScript(args.infile, args.version, args.outfile)
