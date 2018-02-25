#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from builtins import object
__author__ = 'Sol'

from psychopy import visual
import numpy as np

class AnalogMeter(object):
    """
    Displays an analog gauge style graphic (think fuel gauge, etc, but very
    simple). A label can be displayed below the gauge, and the gauge value
    can be displayed as part of the gauge background itself.

    The graphics are created using several standard PsychoPy stim types
    together.
    """
    def __init__(self, win, dial_color=[1, 1, 1],
                 arrow_color=[-0.8, -0.8, -0.8],
                 size=0.25, pos=(-0.5, 0.0), title='Analog Gauge'):
        self.w, self.h = win.size[0], win.size[1]
        px = self.w / 2 * pos[0]
        py = self.h / 2 * pos[1]

        self.dial_bkgd_inner = visual.RadialStim(win=win, tex='None', units='pix',
                                           pos=(px, py), color=dial_color,
                                           size=self.w * size,
                                           angularRes=360,
                                           visibleWedge=[0, 180],
                                           interpolate=True,
                                           ori=-90,
                                           autoLog=False)

        y_offset = self.h * .5 * (size * .08)
        w2 = (self.w/2.0)
        h2 = (self.h/2.0)
        strokew = (size/18.0)
        self.handVerts = np.array([[0.0, (size * 0.9) * w2],
                                   [-strokew * h2, strokew * w2],
                                   [0.0, 0.0],
                                   [strokew * h2, strokew * w2]
                                   ])

        self.arrow = visual.ShapeStim(win, units='pix', vertices=self.handVerts,
                                      lineColor=[-1, -1, -1],
                                      fillColor=arrow_color,
                                      lineWidth=2, opacity=0.60,
                                      pos=(px, y_offset + py),
                                      autoLog=False)

        self.text_value = visual.TextBox(window=win,
                                         text=' ',
                                         bold=False,
                                         italic=False,
                                         font_size=18,
                                         font_color=[1, -1, -1, 1],
                                         size=(self.w * size, 40),
                                         pos=(
                                             px,
                                             py + (self.w * size)/4.0 - 20),
                                         units='pix',
                                         grid_horz_justification='center',
                                         grid_vert_justification='center',
                                         )

        self.title = visual.TextBox(window=win,
                                    text=title,
                                    bold=False,
                                    italic=False,
                                    font_size=13,
                                    font_color=[-1, -1, -1],
                                    size=(self.w * size, 25),
                                    #grid_color=[-1,1,-1,1],
                                    #grid_stroke_width=1,
                                    pos=(px, py),
                                    units='pix',
                                    align_vert='top',
                                    grid_horz_justification='center',
                                    grid_vert_justification='center',
                                    )

    def draw(self, value_txt=None):
        self.dial_bkgd_inner.draw()
        self.title.draw()
        if value_txt:
            self.text_value.draw()
        self.arrow.draw()

    def update_gauge(self, percent, value_txt=''):
        arrowPos = ((percent * 360.0)/2.0 - 90.0)
        self.arrow.setOri(arrowPos)
        self.text_value.setText(value_txt)
        self.draw(value_txt)

    def __del__(self):
        self.dial_bkgd_inner=None
        self.title=None
        self.arrow=None

class DigitalLineStateButton(object):
    """
    Displays a button graphic that changes based on it's state. A label can be
    displayed below the button.

    The graphics are created using two standard PsychoPy stim types
    together.
    """
    def __init__(self, win, dline_num, state_high_img, state_low_img,
                 size=None, pos=(0, 0), title='DIN ?', initial_state=False):

        px,py=pos
        self.state = initial_state
        self.line_number=dline_num
        self.on_button = visual.ImageStim(win, size=size, image=state_high_img, units='pix', pos=pos,autoLog=False,name=title)
        self.off_button = visual.ImageStim(win, size=size, image=state_low_img, units='pix', pos=pos,autoLog=False,name=title)

        self.title = visual.TextBox(window=win,
                                    text=title,
                                    bold=False,
                                    italic=False,
                                    font_size=12,
                                    font_color=[-1, -1, -1],
                                    size=(self.on_button.size[0]*1.05, 20),
                                    pos=(px, py-25),
                                    units='pix',
                                    align_vert='top',
                                    grid_horz_justification='center',
                                    grid_vert_justification='center',
        )

    def draw(self):
        if self.state is True:
            self.on_button.draw()
        else:
            self.off_button.draw()
        self.title.draw()

    def enable(self, v):
        if v&(2**self.line_number):
            self.state=True
        else:
            self.state=False
        self.draw()

    def contains(self,v):
        return self.on_button.contains(v)

    def __del__(self):
        self.off_button=None
        self.on_button=None
        self.title=None

