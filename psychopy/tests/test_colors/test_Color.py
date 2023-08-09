from psychopy import colors, visual, event, logging


def test_readable():
    """
    Test method of Color which returns readable pairing for the given color.

    Currently no validation - just making sure the method runs without error.
    Commented out sections are for local use when previewing the colors to
    confirm, anecdotally, that they're readable.
    """
    # win = visual.Window(size=(100, 100))
    # text = visual.TextBox2(
    #     win,
    #     text="a",
    #     units="norm",
    #     size=(2, 2),
    #     letterHeight=1,
    #     fillColor=None
    # )

    cases = [
        {'val': (0, 0.00, 1.00, 0.50), 'space': "hsva"}
    ]
    # also test all named colors
    for name in colors.colorNames:
        cases.append(
            {'val': name, 'space': "named"}
        )

    for case in cases:
        # create color object
        col = colors.Color(case['val'], space=case['space'])
        # get its contrasting color
        contr = col.getReadable()
        # # for local use: preview the color pairing on some text
        # win.color = col
        # text.color = contr
        # while not event.getKeys():
        #     text.draw()
        #     win.flip()
