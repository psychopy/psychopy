#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a Circle with a given radius
as a special case of a :class:`~psychopy.visual.Polygon`
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from psychopy.visual.basevisual import (BaseVisualStim,
                                        ContainerMixin, ColorMixin)
from psychopy import visual, event

import psychopy  # so we can get the __path__

from psychopy.visual.shape import BaseShapeStim
from psychopy.visual import surveys


from builtins import range

from psychopy.tools.attributetools import attributeSetter, setAttribute

import numpy

#win = visual.Window(units='height')
#print(win.backend.shadersSupported, win._haveShaders)


class Button(BaseShapeStim):
    
    """
    Creates a button.
    """

    def __init__( self,
                  win,
                  border_thickness = .003,
                  button_text_sz   = 0.03,
                  buttonPos        = (-.5,0),
                  buttonText = "text for button",
                  survey="",
                  type = "surveySubmit",
                  thisExp="",
                  **kwargs):

        #local variables
        button_width = len(buttonText) * .025
        button_x_inner_margin = .02
        button_x_outer_margin = button_x_inner_margin + border_thickness
        button_y_inner_margin = button_text_sz
        button_y_outer_margin = button_text_sz + border_thickness
        button_x_range = (0-button_width/2+buttonPos[0], 0+button_width/2+buttonPos[0])

        self.thisExp = thisExp
        self._dragging = False
        self.survey = survey
        self.type = type  # this needs to be dynamic
        self.mouse = event.Mouse()
        self.button_selected = False
        self.buttonItems = []
        self.button_border = BaseShapeStim(win, fillColor="blue",vertices=((button_x_range[0]-button_x_outer_margin, -button_y_outer_margin + buttonPos[1]),
                                                                           (button_x_range[0]-button_x_outer_margin, button_y_outer_margin + buttonPos[1]),
                                                                           (button_x_range[1]+button_x_outer_margin, button_y_outer_margin + buttonPos[1]),
                                                                           (button_x_range[1]+button_x_outer_margin, -button_y_outer_margin + buttonPos[1]))) #edges=4
        self.button_inner      = BaseShapeStim(win, fillColor="white",vertices=((button_x_range[0]-button_x_inner_margin, -button_y_inner_margin + buttonPos[1]),
                                                                            (button_x_range[0]-button_x_inner_margin, button_y_inner_margin + buttonPos[1]),
                                                                            (button_x_range[1]+button_x_inner_margin, button_y_inner_margin + buttonPos[1]),
                                                                            (button_x_range[1]+button_x_inner_margin, -button_y_inner_margin + buttonPos[1]))) #edges=4
        self.button_inner_text = visual.TextStim(win, text=buttonText, color="blue",pos=buttonPos,height=button_text_sz)

        self.buttonItems.append(self.button_border)
        self.buttonItems.append(self.button_inner)
        self.buttonItems.append(self.button_inner_text)

    def draw(self):
        self.getMouseResponses()

        for item in self.buttonItems:
            item.draw()
        ### This code has been used to change the color when a button is clicked on or hovered over. Been unable to implement without disrupting the form

    def getMouseResponses(self):
        click = bool(self.mouse.getPressed()[0])

        #hover = bool(self.button_border.contains(self.mouse))

        #if hover:
        if (self.button_selected == False):
            if self.button_border.contains(self.mouse):
                self.button_border.color = "blue"
                self.button_inner.color = "blue"
                self.button_inner_text.color = "white"
            else:
                self.button_border.color = "blue"
                self.button_inner.color = "white"
                self.button_inner_text.color = "blue"
        else:
            if self.button_border.contains(self.mouse):
                self.button_border.color = "blue"
                self.button_inner.color = "white"
                self.button_inner_text.color = "blue"
            else:
                self.button_border.color = "blue"
                self.button_inner.color = "blue"
                self.button_inner_text.color = "white"

        if click:
            self._dragging = True
            # Update current but don't set Rating (mouse is still down)
            # Dragging has to start inside a "valid" area (i.e., on the
            # slider), but may continue even if the mouse moves away from
            # the slider, as long as the mouse button is not released.

        else:  # mouse is up - check if it *just* came up
            if self._dragging:
                if self.type == "surveySubmit":
                    surveys.saveScores(self.survey,self.thisExp)

                elif self.type == "surveyItem":
                    print("Will code what to do with you later")


                if self.button_border.contains(self.mouse):
                    self._dragging = False
                    if (self.button_selected == True):
                        self.button_selected = False
                    else:
                        self.button_selected = True

            else:
                # is up and was already up - move along
                return None
