# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import psychopy.logging as logging

try:
    from psychopy_eyetracker_gazepoint.gazepoint.gp3.calibration import (
        GazepointCalibrationProcedure)
except (ModuleNotFoundError, ImportError, NameError):
    logging.error(
        "The Gazepoint eyetracker requires package " 
        "'psychopy-eyetracker-gazepoint' to be installed. Please install this "
        "package and restart the session to enable support.")

if __name__ == "__main__":
    pass
