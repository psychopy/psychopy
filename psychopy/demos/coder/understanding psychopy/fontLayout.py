"""
This demo produces a handy diagram showing how the metrics of a PsychoPy GLFont object affect the layout of rows in a textbox. A textbox is drawn such that the baseline of the first line is at the vertical coordinate 0, meaning that all other lines and shapes can be laid out relative to this line.
"""


from psychopy import visual, event
from psychopy.visual.textbox2.fontmanager import FontManager

# Create window
win = visual.Window(size=(500, 200), units="pix", color="white")

# Create a list to store objects for easy drawing
drawList = []

# Get a font with consistent proportions that are easy to spot
allFonts = FontManager()
font = allFonts.getFont("Outfit", size=50, lineSpacing=1.3)

# Create a textbox using this font, whose vertical position is such that the baseline of the first line of text is at 0
text = visual.TextBox2(
    win=win, text="My text has an È!\nMy text has an È!", font=font,
    pos=(-50, font.ascender), size=(400, font.height), padding=0,
    color="black", anchor="top center", alignment="top left"
)
drawList += [text]

# Draw the baseline
baseline = visual.Line(win, start=(-250, 0), end=(250, 0), lineColor="green")
baselineLbl = visual.TextBox2(win, "baseline (0)", "Outfit", color="green", letterHeight=12, pos=(160, 8), size=(50, 10), padding=0)
drawList += [baseline, baselineLbl]
# Draw the descent line
descender = visual.Line(win, start=(-250, font.descender), end=(250, font.descender), lineColor="blue")
descenderLbl = visual.TextBox2(win, ".descender", "Outfit", color="blue", letterHeight=12, pos=(160, font.descender + 8), size=(50, 10), padding=0)
drawList += [descender, descenderLbl]
# Draw the ascent line
ascender = visual.Line(win, start=(-250, font.ascender), end=(250, font.ascender), lineColor="orange")
ascenderLbl = visual.TextBox2(win, ".ascender", "Outfit", color="orange", letterHeight=12, pos=(160, font.ascender + 8), size=(50, 10), padding=0)
drawList += [ascender, ascenderLbl]
# Draw the cap height line
capheight = visual.Line(win, start=(-250, font.capheight), end=(250, font.capheight), lineColor="red")
capheightLbl = visual.TextBox2(win, ".capheight", "Outfit", color="red", letterHeight=12, pos=(160, font.capheight + 8), size=(50, 10), padding=0)
drawList += [capheight, capheightLbl]
# Draw the leading line
leading = visual.Line(win, start=(-250, font.leading), end=(250, font.leading), lineColor="purple")
leadingLbl = visual.TextBox2(win, ".leading", "Outfit", color="purple", letterHeight=12, pos=(160, font.leading - 4), size=(50, 10), padding=0)
drawList += [leading, leadingLbl]

# Draw the height box
height = visual.Rect(win, fillColor="orange", pos=(215, (font.ascender + font.leading)/2), size=(20, font.height))
heightLbl = visual.TextStim(win, ".height", "Outfit", color="white", bold=True, pos=(215, (font.ascender + font.leading)/2), height=12, ori=90)
drawList += [height, heightLbl]
# Draw the size box
size = visual.Rect(win, fillColor="red", pos=(240, (font.capheight + font.descender)/2), size=(20, font.size))
sizeLbl = visual.TextStim(win, ".size", "Outfit", color="white", bold=True, pos=(240, (font.capheight + font.descender)/2), height=12, ori=90)
drawList += [size, sizeLbl]
# Draw linegap box
linegap = visual.TextBox2(win, ".linegap", "Outfit", fillColor="purple", color="white", letterHeight=12, pos=(160, (font.descender + font.leading)/2), size=(45, font.linegap), padding=0)
drawList += [linegap]

# Rearrange order
drawList += [drawList.pop(drawList.index(descender))]
drawList += [drawList.pop(drawList.index(height))]
drawList += [drawList.pop(drawList.index(heightLbl))]
drawList += [drawList.pop(drawList.index(leading))]

while not event.getKeys("escape"):
    for obj in drawList:
        obj.draw()
    win.flip()
