"""
This demo shows off the piloting mode setting. Using a function in the `core` 
module, you can figure out whether the script was run with the "--pilot" flag, 
which is supplied if you click the Run button while the pilot/run toggle is set 
to pilot (the run button will be orange).

See below for some examples of behaviour you may wish to change according to 
piloting mode.
"""

from psychopy import core, visual, logging
from psychopy.hardware import keyboard

# work out from system args whether we are running in pilot mode
PILOTING = core.setPilotModeFromArgs()

# set some variables according to whether or not we're piloting
fullScr = True
pilotingIndicator = False
logLvl = logging.WARNING
modeMsg = "RUNNING"
tryMsg = "PILOTING"
if PILOTING:
    # it's a good idea to force fullScr False when piloting, to stop yourself 
    # from getting stuck in a full screen experiment if there's an error in 
    # your code
    fullScr = False
    # the piloting indicator is pretty obnoxious, making it super clear when 
    # you're piloting (so you don't accidentally gather data in piloting mode!)
    pilotingIndicator = True
    # there will be a lot of EXPERIMENT level logging messages, which can get 
    # annoying - but when you're piloting, you're more likely to want this 
    # level of detail for debugging!
    logLvl = logging.INFO
    # in this demo, we're showing some text which varies according to piloting 
    # mode - these variables is what varies it
    modeMsg = "PILOTING"
    tryMsg = "RUNNING"
    
# set logging level
logging.console.setLevel(logLvl)

# make window
win = visual.Window(fullscr=fullScr)

# set piloting indicator
if pilotingIndicator:
    win.showPilotingIndicator()

# make a textbox with a differing message according to mode
txtbox = visual.TextBox2(
    win, text=(
        f"If you're reading this, you're in {modeMsg} mode! Toggle the "
        f"pilot/run switch and run again to try {tryMsg}"
    ),
    alignment="center"
)

# make a Keyboard
kb = keyboard.Keyboard()

# start a frame loop until user presses esc
while not kb.getKeys("escape"):
    txtbox.draw()
    win.flip()