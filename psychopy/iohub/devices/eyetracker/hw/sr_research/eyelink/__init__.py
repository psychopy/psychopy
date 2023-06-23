# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import psychopy.logging as logging

try:
    from psychopy_eyetracker_sr_research.sr_research.eyelink import (
        EyeTracker, 
        MonocularEyeSampleEvent,
        BinocularEyeSampleEvent, 
        FixationStartEvent,
        FixationEndEvent, 
        SaccadeStartEvent,
        SaccadeEndEvent, 
        BlinkStartEvent,
        BlinkEndEvent)
except (ModuleNotFoundError, ImportError, NameError):
    logging.error(
        "SR Research eyetracker support requires the package "
        "'psychopy-eyetracker-sr-research' to be installed. Please install "
        "this package and restart the session to enable support.")

if __name__ == "__main__":
    pass
