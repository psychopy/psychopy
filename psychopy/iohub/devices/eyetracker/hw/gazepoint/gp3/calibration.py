# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from psychopy.iohub.devices.eyetracker.calibration import BaseCalibrationProcedure


class GazepointCalibrationProcedure(BaseCalibrationProcedure):
    def __init__(self, eyetrackerInterface, calibration_args):
        BaseCalibrationProcedure.__init__(self, eyetrackerInterface, calibration_args, allow_escape_in_progress=False)

    def startCalibrationHook(self):
        self._eyetracker._gp3set('CALIBRATE_SHOW', STATE=0)
        self._eyetracker._gp3set('CALIBRATE_START', STATE=0)

        self._eyetracker._gp3set('CALIBRATE_CLEAR')

        self._eyetracker._gp3set('SCREEN_SIZE', X=0, Y=0, WIDTH=self.width, HEIGHT=self.height)
        #print2err("Set GP3 SCREEN_SIZE: ", self._eyetracker._waitForAck('SCREEN_SIZE'))

        # Inform GazePoint of target list to be used
        for p in self.cal_target_list:
            x, y = p
            self._eyetracker._gp3set('CALIBRATE_ADDPOINT', X=x, Y=y)
            self._eyetracker._waitForAck('CALIBRATE_ADDPOINT')

        self._eyetracker._gp3set('CALIBRATE_SHOW', STATE=0)
        self._eyetracker._gp3set('CALIBRATE_START', STATE=1)
