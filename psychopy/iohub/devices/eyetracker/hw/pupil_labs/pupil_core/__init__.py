# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import psychopy.logging as logging
import psyhopy.iohub.util as _util

try:
    from psychopy_eyetracker_pupil_labs.pupil_labs.pupil_core import (
        MonocularEyeSampleEvent, 
        BinocularEyeSampleEvent,
        EyeTracker)
except (ModuleNotFoundError, ImportError, NameError):
    logging.error(
        "Pupil Labs eyetracker support requires the package "
        "'psychopy-eyetracker-pupil-labs' to be installed. Please install this "
        "package and restart the session to enable support.")

# get configuration from plugin
yamlFile = _util.getSupportedConfigSettings(pupil_core)

if __name__ == "__main__":
    pass
