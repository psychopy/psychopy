#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Thu Oct 03 12:50:46 2013

@author: Sol
"""
from __future__ import absolute_import, division, print_function

from builtins import str
from psychopy import visual
from psychopy.iohub import ioHubExperimentRuntime,EventConstants,module_directory
import math
import numpy as np
import time


class EloTouchScreenDemo(ioHubExperimentRuntime):
    """
    EloTouchScreenDemo illustrates how to use the Elo Serial Touch Screen
    implementation of the ioHub Touch Device. Based on the calibrate_elo and
    validate_elo settings in the experiment_config.yaml file, the demo will
    first perform a calibration / validation routine for the Touch Device
    (if calibrate_elo is True). If calibrate_elo is False, the last Touch
    device calibration done will be used.

    Once the calibration / validation stages have been performed, the demo
    draws a circle stimulus where ever the touch screen is pressed. The demo
    ends when any keyboard is detected.
    """
    def run(self,*args):
        """
        The script written for the demo.
        """
        display=self.devices.display
        kb=self.devices.kb
        touch=self.devices.touch
        self.touch=touch

        # Issue a query on the ID settings and get the reply as a dict of
        # parsed values. See the elo_serial.py in psychopy/iohub/devices/touch/hw/elo
        # to see what are valid query names. In the elo_serial.py a subset of
        # the classes are named Query*, where * is the query name. The query
        # associated with any Query* class can be issued from a psychopy script
        # by calling the following method of the touch device with the * part
        # of the Query class name:
        #
        #   # Issue an ID Query and get the response from the elo device.
        #   query_reply=touch.queryDevice('ID')
        #
        id_dict=touch.queryDevice('ID')
        print("queryDevice('ID'):" + str(id_dict))
        print()

        # getHardwareConfiguration returns the results from the following
        # queries, issued when the elo device interface was created by iohub:
        #
        #   ID
        #   Diagnostics
        #   Owner
        #   Jumper
        #   Report
        #
        hw_conf_dict=touch.getHardwareConfiguration()
        import pprint
        print("hw_conf_dict:")
        pprint.pprint(hw_conf_dict)
        print()

        display_resolution=display.getPixelResolution()
        psychopy_monitor=display.getPsychopyMonitorName()
        unit_type=display.getCoordinateType()
        screen_index=display.getIndex()

        # Create PsychoPy Window and Stim.
        #
        window=visual.Window(display_resolution, monitor=psychopy_monitor,
                            units=unit_type, color=[128,128,128], colorSpace='rgb255',
                            fullscr=True, allowGUI=False, screen=screen_index)
        self.window=window

        self.cal_instruct_stim=visual.TextStim(self.window,
                                        text="",
                                        pos = (0,-display_resolution[1]/2*0.8),
                                        color=[255,255,255],
                                        colorSpace='rgb255',
                                        alignHoriz='center',
                                        alignVert='center',
                                        units='pix',
                                        wrapWidth=display_resolution[0]*0.9)

        self.touch_point_stim=visual.Circle(self.window,pos=(0,0),
                       lineWidth=1,
                       radius=10,
                       name='touch_point_stim',
                       fillColor=[255,0,0],
                       lineColor=[255,255,0],
                       fillColorSpace='rgb255',
                       lineColorSpace='rgb255',
                       opacity=1.0,
                       interpolate=False,
                       edges=64,
                       units=unit_type)

        self.min_touch_stim_radius=15
        self.max_touch_stim_radius=40
        self.touch_contingent_stim=visual.Circle(self.window,pos=(0,0),
                       lineWidth=3,
                       radius=self.min_touch_stim_radius,
                       name='touch_point_stim',
                       fillColor=[0,255,0],
                       lineColor=[255,0,255],
                       fillColorSpace='rgb255',
                       lineColorSpace='rgb255',
                       opacity=.7,
                       interpolate=False,
                       edges=64,
                       units=unit_type)

        # Clear all events from the global and device level event buffers.
        self.hub.clearEvents('all')

        # determine whether calibration has been enabled.
        user_params=self.getUserDefinedParameters()
        #
        if user_params.get('calibrate_elo',False) is True:
            #Calibrate
            self.run_elo_calibration()
            self.hub.clearEvents('all')
            #Validate
            terminate_calibration=False
            while not terminate_calibration and self.run_elo_validation() is False:
                self.run_elo_calibration()
                kb_events=kb.getEvents()
                if kb_events:
                    terminate_calibration=True
                self.hub.clearEvents('all')

            # End demo if calibration has been cancelled.
            if terminate_calibration is True:
                return False

            #Save elo device settings to NVRAM
            self.touch.saveConfiguration()
        else:
            self.touch.restoreConfiguration()

        self.hub.clearEvents('all')

        self.cal_instruct_stim.setText("Move the dot with your finger.\nPess any key to exit.")
        self.cal_instruct_stim.setPos((0,0))
        self.cal_instruct_stim.draw()
        self.touch_contingent_stim.draw()
        window.flip()

        # Constantly get Touch events and update the touch_contingent_stim
        # position with the latest Touch event position. End demo when a
        # key event is received.
        run_demo=True
        while run_demo:
            touch_events=self.touch.getEvents()
            if touch_events:
                te=touch_events[-1]
                rad_range=self.max_touch_stim_radius- self.min_touch_stim_radius
                touch_stim_radius=self.min_touch_stim_radius+(te.pressure/255.0)*rad_range
                self.touch_contingent_stim.pos = (te.x_position, te.y_position)
                self.touch_contingent_stim.radius = touch_stim_radius
                self.cal_instruct_stim.draw()
                self.touch_contingent_stim.draw()
                window.flip()

            kb_events=kb.getEvents(event_type=EventConstants.KEYBOARD_PRESS)
            if kb_events:
                run_demo=False

        # DONE EXP

    def getTouchPoint(self,x,y):
        # Displays a target stim for calibration or validation. Returns
        # the location of the first Touch Release event received.
        self.touch_point_stim.pos=(x,y)
        self.touch_point_stim.draw()
        self.cal_instruct_stim.draw()
        self.window.flip()

        self.hub.clearEvents('all')

        no_touch_release=True
        while no_touch_release:
            touch_events=self.touch.getEvents()
            for te in touch_events:
                if te.type==EventConstants.TOUCH_RELEASE:
                    return te.x_position,te.y_position

            #not self.devices.kb.getEvents(event_type_id=EventConstants.KEYBOARD_PRESS):
            #self.touch_point_stim.draw()
            #self.cal_instruct_stim.draw()
            #self.window.flip()
            time.sleep(0.05)
        self.hub.clearEvents('all')

    def run_elo_calibration(self):
        """
        Performs the Touch device Calibration routine.
        Note that this method will be integrated into the ioHub module
        itself at some point.
        """
        self.touch.initCalibration()

        display_resolution=self.devices.display.getPixelResolution()
        xmin=0
        ymin=0
        xmax=display_resolution[0]
        ymax=display_resolution[1]
        dwidth=xmax
        dheight=ymax

        horz_margin=dwidth*.1
        vert_margin=dheight*.1

        leftx = xmin+horz_margin
        uppery = ymin+vert_margin
        rightx = xmax-horz_margin
        lowery = ymax-vert_margin

        self.cal_instruct_stim.setText("Elo Touch Screen Calibration.\n \
Touch each Point when it is Presented.")

        cal_points=[
                    (leftx-dwidth/2, -(uppery-dheight/2)),
                    (rightx-dwidth/2, -(lowery-dheight/2)),
                    (rightx-dwidth/2, -(uppery-dheight/2))
                    ]

        ts_points=[]

        for x,y in cal_points:
            ts_points.append(self.getTouchPoint(x,y))

        (x1,y1),(x2,y2),(sx,sy)=ts_points

        self.touch.applyCalibrationData(xmin,xmax,ymin,ymax,
                                      x1,y1,x2,y2,sx,sy,
                                      leftx,uppery,rightx,lowery)

        self.cal_instruct_stim.setText('CALIBRATION COMPLETE.\nPRESS ANY KEY TO CONTINUE.')
        self.cal_instruct_stim.setPos((0,0))
        self.cal_instruct_stim.draw()
        self.window.flip()
        self.hub.clearEvents('all')
        kb=self.devices.kb
        while not kb.getEvents(EventConstants.KEYBOARD_PRESS):
           time.sleep(0.05)
        self.hub.clearEvents('all')


    def run_elo_validation(self):
        """
        Performs the Touch device Validation routine.
        Note that this method will be integrated into the ioHub module
        itself at some point.
        """
        display_resolution=self.devices.display.getPixelResolution()
        dwidth=display_resolution[0]
        dheight=display_resolution[1]

        self.cal_instruct_stim.setText("Elo Touch Screen Validation.\n\
Touch each Point when it is Presented.")
        self.cal_instruct_stim.setPos((0,-display_resolution[1]/2*0.8))

        val_points=(
                    (0,0),
                    (-dwidth/2*.8,dheight/2*.8),
                    (dwidth/2*.8,dheight/2*.8),
                    (-dwidth/2*.8,-dheight/2*.8),
                    (dwidth/2*.8,-dheight/2*.8)
                    )

        diffs=[]
        t_points=[]
        for x,y in val_points:
           tx,ty=self.getTouchPoint(x,y)
           t_points.append((tx,ty))
           diffs.append((math.fabs(tx-x),math.fabs(ty-y)))

        vec_diffs=np.zeros(len(diffs),dtype=np.float32)
        for i,(dx,dy) in enumerate(diffs):
            vec_diffs[i]=np.sqrt(dx*dx+dy*dy)

        txt="Validation Results (units error): Min {0}, Max {1}, Average {2}\nPress Any Key to Continue.".format(
        vec_diffs.min(),vec_diffs.max(),vec_diffs.mean())

        val_passed=True
        if vec_diffs.max() > dwidth*.05 or vec_diffs.mean() > dwidth*.025:
            txt+='\nVALIDATION POOR. SHOULD RECALIBRATE.'
            val_passed=False
        else:
            txt+='\nVALIDATION GOOD.'

        self.cal_instruct_stim.setText(txt)
        self.cal_instruct_stim.setPos((0,0))
        self.cal_instruct_stim.draw()
        self.window.flip()
        self.hub.clearEvents('all')
        kb=self.devices.kb
        while not kb.getEvents(EventConstants.KEYBOARD_PRESS):
           time.sleep(.05)

        return val_passed

###############################################################################

import sys

def main(configurationDirectory):
    """
    Creates an instance of the EloTouchScreenDemo class,
    and launches the experiment logic in run().
    """
    runtime=EloTouchScreenDemo(configurationDirectory, "experiment_config.yaml")
    runtime.start(sys.argv)

# run the main function, which starts the experiment runtime
main(module_directory(main))

##########################