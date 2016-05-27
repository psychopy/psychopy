#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Example of performing an eye tracker accuracy validation using ioHub
and the ValidationProcedure utility class.

* Change the et_interface_name variable below to specify the iohub eye tracker
  interface be used. 
* Change the eye tracker configuration by updating the 
  iohub_config[et_interface_name] dict. 
"""
from __future__ import division, print_function, absolute_import

import time

from psychopy import visual
from psychopy.iohub.client import launchHubServer
from psychopy.iohub.constants import EventConstants
from visualUtil import TimeTrigger, DeviceEventTrigger
from targetpositionsequence import TargetStim
from targetpositionsequence import PositionGrid
from targetpositionsequence import ValidationProcedure

exp_code = 'targetdisplay'
sess_code = 'S_{0}'.format(long(time.mktime(time.localtime())))

# Create ioHub Server config settings....
iohub_config = dict()
iohub_config['experiment_code'] = exp_code
iohub_config['session_code'] = sess_code

# Add an eye tracker device; an eyelink system in this example.
# A different tracker could be used by changing the et_interface_name and
# iohub_config[et_interface_name] config.
et_interface_name = 'eyetracker.hw.sr_research.eyelink.EyeTracker'
iohub_config[et_interface_name] = {'name': 'tracker',
                                   'simulation_mode': True,
                                   'model_name': 'EYELINK 1000 DESKTOP',
                                   'runtime_settings': {'sampling_rate': 500,
                                                        'track_eyes': 'BINOCULAR'
                                                        }
                                   }

# Start ioHub event monitoring process....
io = launchHubServer(**iohub_config)

# Get the keyboard and mouse devices for future access.
keyboard = io.devices.keyboard
mouse = io.devices.mouse
tracker = io.devices.tracker
experiment = io.devices.experiment

# Create a default PsychoPy Window
win = visual.Window(io.devices.display.getPixelResolution(), fullscr=True,
                    allowGUI=False)

# Create a TargetStim instance
target = TargetStim(win,
                    radius=16,               # 16 pix outer radius.
                    fillcolor=[.5, .5, .5],  # 75% white fill color.
                    edgecolor=[-1, -1, -1],  # Fully black outer edge
                    edgewidth=3,             # with a 3 pixel width.
                    dotcolor=[1, -1, -1],    # Full red center dot
                    dotradius=3,             # with radius of 3 pixels.
                    units='pix',             # Size & pos units are in pix.
                    colorspace='rgb'         # Colors are in 'rgb' space,
                                             # each with a (-1.0, 1.0) range
                    )

# Create a PositionGrid instance that will hold the locations to display the
# target at. The example lists all possible keyword arguments that are
# supported. Any set to None are ignored during position grid creation.
positions = PositionGrid(winSize=win.size,  # width, height of window used.
                         shape=3,  # Create a grid with 3 cols * 3 rows.
                         posCount=None,
                         leftMargin=None,
                         rightMargin=None,
                         topMargin=None,
                         bottomMargin=None,
                         scale=0.85,  # Equally space the 3x3 grid across 85%
                                      # of the window width and height.
                         posList=None,
                         noiseStd=None,
                         firstposindex=4,  # Use the center position grid
                                           # location as the first point in
                                           # the position order.
                         repeatfirstpos=True  # Redisplay first target position
                                              # as the last target position.
                         )

# randomize the grid position presentation order (not including
# the first position).
positions.randomize()

# Specifiy the Triggers to use to move from target point to point during
# the validation sequence....

# Use DeviceEventTrigger to create a keyboard char event trigger
#     which will fire when the space key is pressed.
kb_trigger = DeviceEventTrigger(io.getDevice('keyboard'),
                                event_type=EventConstants.KEYBOARD_RELEASE,
                                event_attribute_conditions={'key': ' '},
                                repeat_count=0)

# Creating a list of Trigger instances. The first one that
#     fires will cause the start of the next target position
#     presentation.
multi_trigger = (TimeTrigger(start_time=None, delay=1.5), kb_trigger)


# run eyetracker calibration
r = tracker.runSetupProcedure()

# define a dict containing any animation params to be used
targ_anim_param = dict(velocity=None,  # 800.0,
                       expandedscale=None,  # 2.0,
                       expansionduration=None,  # 0.1,
                       contractionduration=None)  # 0.1

# Create a validation procedure
vin_txt = 'Validation procedure is now going to be performed.'
validation_proc = ValidationProcedure(win, target, positions,
                                      target_animation_params=targ_anim_param,
                                      background=None,
                                      triggers=kb_trigger,#multi_trigger,
                                      storeeventsfor=None,
                                      accuracy_period_start=0.550,
                                      accuracy_period_stop=.150,
                                      show_intro_screen=True,
                                      intro_text=vin_txt,
                                      show_results_screen=True,
                                      results_in_degrees=True)

# Run the validation procedure. The display() method does not return until
# the validation is complete. The calculated validation results, and data
# collected for the analysis, are returned.
results = validation_proc.display()

# The last run validation results can also be retrieved using:
# results = validation_proc.getValidationResults()

io.quit()
