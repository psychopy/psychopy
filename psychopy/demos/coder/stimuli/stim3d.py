#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Demo for 3D stimulus classes.

This demonstrates how to render 3D stimuli, set lighting and adjust materials.

"""
from psychopy import core
import psychopy.visual as visual
from psychopy.visual import LightSource, BlinnPhongMaterial, BoxStim
from psychopy.tools.gltools import createTexImage2dFromFile
from psychopy import event

# open a window to render the shape
win = visual.Window((600, 600), allowGUI=False, monitor='testMonitor')

# setup scene lights
redLight = LightSource(win, pos=(0, 1, 0), diffuseColor=(.5, 0, 0),
                       specularColor=(.5, .5, .5), lightType='directional')
blueLight = LightSource(win, pos=(5, -3, 0), diffuseColor=(0, 0, .5),
                        specularColor=(.5, .5, .5), lightType='point')
greenLight = LightSource(win, pos=(-5, -3, 0), diffuseColor=(0, .5, 0),
                         specularColor=(.5, .5, .5), lightType='point')

# assign the lights to the scene
win.lights = [redLight, blueLight, greenLight]

# create the stimulus object, try other classes like SphereStim and PlaneStim
boxStim = BoxStim(win, size=(.2, .2, .2))

# set the position of the object by editing the associated rigid body pose
boxStim.thePose.pos = (0, 0, -3)

# create a white material and assign it
boxStim.material = BlinnPhongMaterial(win, diffuseColor=(1, 1, 1),
                                      specularColor=(0, 0, 0), shininess=125.0)

# load a diffuse texture
boxStim.material.diffuseTexture = createTexImage2dFromFile('face.jpg')

# set the box 3 meters away from the observer by editing the stimuli's rigid
# body class
boxStim.thePose.pos = (0, 0, -3)

# text to overlay
message = visual.TextStim(
    win, text='Any key to quit', pos=(0, -0.8), units='norm')

angle = 0.0

while not event.getKeys():
    win.setPerspectiveView()  # set the projection, must be done every frame

    win.useLights = True  # enable lighting

    # spin the stimulus by angle
    boxStim.thePose.setOriAxisAngle((0, 1, 1), angle)

    # draw the stimulus
    boxStim.draw()

    win.resetEyeTransform()  # reset the transformation to draw 2D stimuli
    # disable lights for 2D stimuli, or else colors will be modulated
    win.useLights = False
    message.draw()

    win.flip()

    angle += 0.5

win.close()
core.quit()
