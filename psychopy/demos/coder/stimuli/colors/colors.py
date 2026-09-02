"""
This demo shows how colors are defined in PsychoPy, and shows how to use the Color class (`psychopy.colors.Color`) to easily convert between them. Just choose a color space from the slider at the top, then type a value into the textbox to see that value as a color.

The contents of this file are in the public domain.
"""

from psychopy import visual, colors, event

# create window
win = visual.Window(
    size=(1080, 720), 
    units='height'
)

# add some instructions
instr = visual.TextBox2(
    win, 
    text=(
        "Choose a color space and type a value into the textbox to see that color in the box to the left.\n"
        "\n"
        "For more info on the different spaces, check out the documentation: \n"
        "psychopy.org/general/colours.html\n"
        "\n"
        "Press ESCAPE to quit."
    ), 
    pos=(0.3, 0), 
    size=(0.5, 0.5)
)
# add a slider to choose color space
spaces = [
    # named colors, these are the same as available in HTML:
    # https://www.w3schools.com/tags/ref_colornames.asp
    "named", 
    # hex values, e.g. #ffffff for white
    'hex', 
    # rgb (red, green and blue) values, ranging from -1 to 1
    'rgb', 
    # rgb values ranging from 0 to 1
    'rgb1', 
    # rgb values ranging from 0 to 255
    'rgb255', 
    # hsv (hue. saturation, value/luminance) values
    'hsv', 
    # lms (long, medium, short) cone values
    'lms'
]
spaceCtrl = visual.Slider(
    win,
    style="radio",
    ticks=None,
    labels=spaces,
    pos=(0, 0.4), 
    size=(1.2, 0.05)
)
spaceCtrl.markerPos = spaceCtrl.labels.index("rgb")
# add an editable textbox for color values
valueCtrl = visual.TextBox2(
    win,
    text="#ffffff",
    font="JetBrains Mono",
    pos=(-0.3, 0.1), 
    size=(0.5, 0.2),
    color='white', 
    fillColor='black',
    editable=True
)
# start off with the ctrl selected
win.currentEditable = valueCtrl
# add a box to show color
colorBox = visual.TextBox2(
    win, 
    text="", 
    pos=(-0.3, -0.2), 
    size=(0.5, 0.2),
    color='white', 
    borderColor='white', 
    fillColor=None
)

# start a frame loop...
while not event.getKeys(["escape"]):
    # process value from value ctrl
    val = valueCtrl.text
    if val.isnumeric():
        val = float(val)
    if "," in val:
        val = eval(val)
    # try to make a fill color from the given values
    try:
        col = colors.Color(
            val,
            space=spaceCtrl.labels[int(spaceCtrl.markerPos)]
        )
        # show the color
        colorBox.text = ""
        colorBox.fillColor = col
    except:
        # if color is invalid, say as much
        colorBox.text = "invalid color"
        colorBox.fillColor = None
    # draw everything
    instr.draw()
    spaceCtrl.draw()
    valueCtrl.draw()
    colorBox.draw()
    # flip the window
    win.flip()