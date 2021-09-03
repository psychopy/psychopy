#!/usr/bin/env python
# -*- coding: utf-8 -*-

# this script replaces hashtags with a sphinx URL string (to the github issues or pull request)
# written by Jon with regex code by Jeremy

import os
from psychopy import experiment, __version__
from pathlib import Path

thisFolder = Path(__file__).parent

nFiles = 0
for root, dirs, files in os.walk(thisFolder.parent/"psychopy/demos/builder"):
    for filename in files:
        if filename.endswith('.psyexp'):

            filepath = os.path.join(root, filename)
            exp = experiment.Experiment()
            exp.loadFromXML(filepath)
            origVersion = exp.psychopyVersion
            exp.psychopyVersion = __version__
            exp.saveToXML(filepath)
            print("switching {} from {} to {}".format(filepath, origVersion, __version__))
