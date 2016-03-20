# TODO: Retest because of changes

from psychopy import visual
from psychopy.iohub.client import launchHubServer
from psychopy.iohub.constants import EventConstants
from psychopy.iohub.util.visualUtil import TimeTrigger, DeviceEventTrigger
from psychopy.iohub.util.targetpositionsequence import TargetStim
from psychopy.iohub.util.targetpositionsequence import PositionGrid
from psychopy.iohub.util.targetpositionsequence import ValidationProcedure
import time

exp_code = 'targetdisplay'
sess_code = 'S_{0}'.format(long(time.mktime(time.localtime())))

# Start ioHub event monitoring process
iohub_config = {
    "eyetracker.hw.tobii_eyex.EyeTracker":{'name':'tracker'},
    "experiment_code": exp_code,
    "session_code": sess_code
}

io = launchHubServer(**iohub_config)

# Get the keyboard and mouse devices for future access.
keyboard = io.devices.keyboard
mouse = io.devices.mouse
tracker = io.devices.tracker
experiment = io.devices.experiment

# Create a default PsychoPy Window
win = visual.Window((1280,1024))

# Create a TargetStim instance
target = TargetStim(
        win,
        radius=16,               # 16 pix outer radius.
        fillcolor=[.5, .5, .5],  # 75% white fill color.
        edgecolor=[-1, -1, -1],  # Fully black outer edge
        edgewidth=3,             # with a 3 pixel width.
        dotcolor=[1, -1, -1],    # Full red center dot
        dotradius=3,             # with radius of 3 pixels.
        units='pix',             # Size & position units are in pix.
        colorspace='rgb'         # colors are in 'rgb' space (-1.0 - 1.0) range
    )                            # forevents r,g,b.

# Create a PositionGrid instance that will hold the locations to display the
# target at. The example lists all possible keyword arguments that are
# supported. Any set to None are ignored during position grid creation.
positions = PositionGrid(
        winSize=win.size,   # width, height of window used for display.
        shape=3,            # Create a grid with 3 cols and 3 rows (9 points).
        posCount=None,
        leftMargin=None,
        rightMargin=None,
        topMargin=None,
        bottomMargin=None,
        scale=0.85,         # Equally space the 3x3 grid across 85% of the
                            # window width and height, centered.
        posList=None,
        noiseStd=None,
        firstposindex=4,    # Use the center position grid location as the
                            # first point in the position order.
        repeatfirstpos=True # As the last target position to display, use the
    )                       # value of the first target position.

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
r=tracker.runSetupProcedure()

# define a dict containing any animation params to be used

targ_anim_param = dict(
                    velocity=None,#800.0,
                    expandedscale=None,#2.0,
                    expansionduration=None,#0.1,
                    contractionduration=None,#0.1
                    )
                        
# Run a validation procedure 
validation_proc=ValidationProcedure(win,
                                    target,
                                    positions,
                                    target_animation_params=targ_anim_param,
                                    background=None,
                                    triggers=multi_trigger,
                                    storeeventsfor=None,
                                    accuracy_period_start=0.550,
                                    accuracy_period_stop=.150,
                                    show_intro_screen=True,
                                    intro_text="Validation procedure is now going to be performed.",
                                    show_results_screen=True,
                                    results_in_degrees=True
                                    )                        

# Run the validation process. The method does not return until the process
# is complete. Returns the validation calculation results and data collected
# for the analysis.
results = validation_proc.display()

# The last calculated validation results can also be retrieved using
# results = validation_proc.getValidationResults()

io.quit()
