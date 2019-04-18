#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import argparse
import io
from copy import deepcopy

# parse args for subprocess
parser = argparse.ArgumentParser(description='Compile your python file from here')
parser.add_argument('infile', help='The input (psyexp) file to be compiled')
parser.add_argument('--version', '-v', help='The PsychoPy version to use for compiling the script. e.g. 1.84.1')
parser.add_argument('--outfile', '-o', help='The output (py) file to be generated (defaults to the ')


def compileScript(infile=None, version=None, outfile=None):
    """
    This function will compile either Python or JS PsychoPy script from .psyexp file.

    Paramaters
    ----------

    infile: string, experiment.Experiment object
        The input (psyexp) file to be compiled
    version: str
        The PsychoPy version to use for compiling the script. e.g. 1.84.1.
        Warning: Cannot set version if module imported. Set version from
        command line interface only.
    outfile: string
        The output file to be generated (defaults to Python script).
    """

    def _setVersion(version):
        """
        Sets the version to be used for compiling using the useVersion function

        Parameters
        ----------
        version: string
            The version requested
        """

        # Set version
        if version:
            from psychopy import useVersion
            useVersion(version)

        global logging

        from psychopy import logging

        if __name__ != '__main__' and version not in [None, 'None', 'none', '']:
            version = None
            msg = "You cannot set version by calling compileScript() manually. Setting 'version' to None."
            logging.warning(msg)

        return version

    def _getExperiment(infile, version):
        """

        Parameters
        ----------
        infile: string, experiment.Experiment object
            The input (psyexp) file to be compiled
        version: string
            The version requested
        Returns
        -------
        experiment.Experiment
            The experiment object used for generating the experiment script

        """
        # import PsychoPy experiment and write script with useVersion active
        from psychopy.app.builder import experiment
        # Check infile type
        if isinstance(infile, experiment.Experiment):
            thisExp = infile
        else:
            thisExp = experiment.Experiment()
            thisExp.loadFromXML(infile)
            thisExp.psychopyVersion = version

        return thisExp

    def _removeDisabledComponents(exp):
        """
        Drop disabled components, if any.

        Parameters
        ---------
        exp : psychopy.experiment.Experiment
            The experiment from which to remove all components that have been
            marked `disabled`.

        Returns
        -------
        exp : psychopy.experiment.Experiment
            The experiment with the disabled components removed.

        Notes
        -----
        This function leaves the original experiment unchanged as it always
        only works on (and returns) a copy.

        """
        # Leave original experiment unchanged.
        exp = deepcopy(exp)

        for _, routine in list(exp.routines.items()):  # PY2/3 compat
            for component in routine:
                try:
                    if component.params['disabled'].val:
                        routine.removeComponent(component)
                except KeyError:
                    pass

        return exp

    def _setTarget(outfile):
        """

        Parameters
        ----------
        outfile : string
             The output file to be generated (defaults to Python script).
        Returns
        -------
        string
            The Python or JavaScript target type
        """

        # Set output type, either JS or Python
        if outfile.endswith(".js"):
            targetOutput = "PsychoJS"
        else:
            targetOutput = "PsychoPy"

        return targetOutput

    def _makeTarget(thisExp, outfile, targetOutput):
        """
        This function generates the actual scripts for Python and/or JS
        Parameters
        ----------
        thisExp : experiment.Experiment object
            The current experiment created under requested version
        outfile : string
             The output file to be generated (defaults to Python script).
        targetOutput : string
            The Python or JavaScript target type
        """

        # Write script
        if targetOutput == "PsychoJS":
            try:
                # Write module JS code
                script = thisExp.writeScript(outfile, target=targetOutput, modular=True)
                # Write no module JS code
                outfileNoModule = outfile.replace('.js', 'NoModule.js')  # For no JS module script
                scriptNoModule = thisExp.writeScript(outfileNoModule, target=targetOutput, modular=False)
                # Store scripts in list
                scriptDict = {'outfile': script, 'outfileNoModule': scriptNoModule}
            except Exception as err:
                if "writeScript()" in '{}'.format(err):  # the exception comes from this module
                    err = ("You cannot compile JavaScript experiments with this version of PsychoPy. "
                           "Please use version 3.0.0 or higher.")
                logging.error("\t{}".format(err))
                return 0
        else:
            script = thisExp.writeScript(outfile, target=targetOutput)
            scriptDict = {'outfile': script}

        # Output script to file
        for scripts in scriptDict:
            if not type(scriptDict[scripts]) in (str, type(u'')):
                # We have a stringBuffer not plain string/text
                scriptText = scriptDict[scripts].getvalue()
            else:
                # We already have the text
                scriptText = scriptDict[scripts]
            with io.open(eval(scripts), 'w', encoding='utf-8-sig') as f:
                f.write(scriptText)

        return 1

    ###### Write script #####
    version = _setVersion(version)
    thisExp = _getExperiment(infile, version)
    thisExp = _removeDisabledComponents(thisExp)
    targetOutput = _setTarget(outfile)
    _makeTarget(thisExp, outfile, targetOutput)


if __name__ == "__main__":
    # define args
    args = parser.parse_args()
    if args.outfile is None:
        args.outfile = args.infile.replace(".psyexp", ".py")
    compileScript(args.infile, args.version, args.outfile)
