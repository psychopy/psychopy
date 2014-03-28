from psychopy import core, visual
from psychopy.iohub import launchHubServer, EventConstants
from psychopy.iohub import TimeTrigger, DeviceEventTrigger
from psychopy.iohub import TargetStim, PositionGrid, TargetPosSequenceStim
import time

exp_code = 'targetdisplay'
sess_code = 'S_{0}'.format(long(time.mktime(time.localtime())))

# Start ioHub event monitoring process
iohub_config = {
    #"eyetracker.hw.tobii.EyeTracker":{},
    "experiment_code": exp_code,
    "session_code": sess_code
}
io = launchHubServer(**iohub_config)

# Get the keyboard and mouse devices for future access.
keyboard = io.devices.keyboard
mouse = io.devices.mouse

# Create a default PsychoPy Window, (800,600)
win = visual.Window()

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
)                            # for r,g,b.

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

# The following are several example trigger values for the triggers kwarg.
# Use only one of them when setting the triggers argument of
# TargetPosSequenceStim.

# Ex: Using DeviceEventTrigger to create a keyboard char event trigger
#     which will fire when the space key is pressed.
kb_trigger = DeviceEventTrigger(io.getDevice('keyboard'),
                                event_type=EventConstants.KEYBOARD_CHAR,
                                event_attribute_conditions={'key': ' '},
                                repeat_count=0)
# Ex: Using TimeTrigger which will fire 0.5 sec after the last update
#     ( flip() ) was made to draw the target as the correct target
#     position.
time_trigger = TimeTrigger(start_time=None, delay=0.5)
# Ex: Using a string to create a keyboard char event trigger
#     which will fire when a key matching the string value is pressed.
kb_trigger_str = ' '
# Ex: Using a float which will result in a TimeTrigger being created
# with a 0.5 sec duration.
time_trigger_float = 0.5
# Ex: Creating a list of Trigger instances. The first one that
#     fires will cause the start of the next target position
#     presentation.
multi_trigger = (TimeTrigger(start_time=None, delay=2.0), kb_trigger)
# Ex: Using a list of strings to create a list of keyboard char
#     based event triggers. First matching key press will cause the
#     start of the next target position presentation.
multi_kb_str_triggers = [' ', 'ESCAPE', 'ENTER']

# Create the TargetPosSequenceStim instance; used to control the sequential
# presentation of the target at each of the grid positions.
targetsequence = TargetPosSequenceStim(target,
                                       positions,
                                       background=None,
                                       triggers=time_trigger_float,
                                       storeeventsfor=[keyboard, mouse])

# Start displaying the target sequence. See the TargetPosSequenceStim.display
# documentation (code comments) for a description of each kwarg passed to
# the display method.
targetsequence.display(velocity=400.0,
                       expandedscale=2.0,
                       expansionduration=0.33,
                       contractionduration=0.5
                       )
print
print 'Events were collected for %d target grid positions.'%(len(positions))
print

io.quit()