"""
This demo shows off the Color class (`psychopy.colors.Color`), allowing object 
colors to be set and accessed in a variety of different color spaces! Just choose
a color space from the slider at the top and type a value into the textbox
"""
from psychopy import visual, colors

# Create window
win = visual.Window(size=(1080, 720), units='height')

# Button to end script
endBtn = visual.ButtonStim(win, "End",
    pos=(0, -0.45), anchor='bottom-center', 
    size=(0.2, 0.1), letterHeight=0.05)
# Color space chooser
spaces = ['named', 'hex', 'rgb', 'rgb1', 'rgb255', 'hsv', 'lms']
spaceCtrl = visual.Slider(win, style="radio",
    ticks=list(range(len(spaces))), granularity=1,
    labels=spaces,
    pos=(0, 0.4), size=(1.2, 0.05), labelHeight=0.02)
spaceCtrl.value = spaces.index('rgb')
# TextBox to type in values to try out
valueCtrl = visual.TextBox2(win, text="#ffffff", font="Courier Prime",
    pos=(-0.3, 0.1), size=(0.5, 0.2), letterHeight=0.05,
    color='white', fillColor='black',
    editable=True)
win.currentEditable = valueCtrl
# Rect to show current colour
colorBox = visual.TextBox2(win, text="", font="Open Sans",
    pos=(-0.3, -0.2), size=(0.5, 0.2), padding=0.05, letterHeight=0.05,
    color='white', borderColor='white', fillColor=None)
# Instructions
instr = (
    "This demo shows how to define colors in PsychoPy - type a value into the "
    "textbox to the left, choose a color space and the box below will appear in "
    "the color and space you have chosen. For more info on the different spaces, "
    "check out the documentation: \n"
    "psychopy.org/general/colours.html"
    )
instrBox = visual.TextBox2(win, text=instr, font="Open Sans",
    pos=(0.3, 0), size=(0.5, 0.5), padding=0.05, letterHeight=0.03,
    color='white', borderColor=None, fillColor=None)


while not endBtn.isClicked:
    # Try to make a fillColor, make it False if failed
    try:
        val = valueCtrl.text
        # If input looks like a number, convert it
        if val.isnumeric():
            val = float(val)
        # If input looks like an array, un-stringify it
        if "," in val:
            val = eval(val)
        # Get color space from radio slider
        space = spaces[int(spaceCtrl.markerPos)]
        col = colors.Color(val, space)
    except:
        col = False
    # Set the color box's fill color, show text "invalid" if color is invalid
    if col:
        colorBox.text = ""
        colorBox.fillColor = col
    else:
        colorBox.text = "invalid color"
        colorBox.fillColor = None
    # Draw stim and flip
    for stim in (valueCtrl, endBtn, colorBox, spaceCtrl, instrBox):
        stim.draw()
    win.flip()