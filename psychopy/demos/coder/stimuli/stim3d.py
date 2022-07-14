#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Demo for 3D stimulus classes.

This demonstrates how to render 3D stimuli, set lighting and adjust materials.

"""
from psychopy import core
import psychopy.visual as visual
from psychopy.visual import LightSource, BlinnPhongMaterial, BoxStim, SphereStim
from psychopy.tools.gltools import createTexImage2dFromFile
from psychopy import event

# open a window to render the shape
win = visual.Window((600, 600), monitor='testMonitor')

# create the stimulus object, try other classes like SphereStim and PlaneStim
boxStim = BoxStim(win, size=(.2, .2, .2))

# set the position of the object by editing the associated rigid body pose
boxStim.thePose.pos = (0, 0, -3)

# create a white material and assign it
boxStim.material = BlinnPhongMaterial(
    win, diffuseColor=(1, 1, 1), specularColor=(0, 0, 0), shininess=125.0)

# load a diffuse texture
boxStim.material.diffuseTexture = createTexImage2dFromFile('face.jpg')

# set the box 3 units away from the observer by editing the stimuli's rigid
# body class
boxStim.thePose.pos = (0, 0, -1)

# setup scene lights
redLight = LightSource(
    win,
    pos=(0, 0.5, -1),
    diffuseColor='red',
    specularColor='red',
    lightType='point')
greenLight = LightSource(
    win,
    pos=(-0.5, -0.5, -1),
    diffuseColor='lightgreen',
    specularColor='lightgreen',
    lightType='point')
blueLight = LightSource(
    win,
    pos=(0.5, -0.5, -1),
    diffuseColor='blue',
    specularColor='blue',
    lightType='point')

# assign the lights to the scene
win.lights = [redLight, greenLight, blueLight]

# Draw spheres at the positions of the light sources to show them. Note that the
# spheres themselves are not emitting light, just made to appear so.
redSphere = SphereStim(win, radius=0.1)
redSphere.thePose.pos = redLight.pos
redSphere.material = BlinnPhongMaterial(win, emissionColor='red')

greenSphere = SphereStim(win, radius=0.1)
greenSphere.thePose.pos = greenLight.pos
greenSphere.material = BlinnPhongMaterial(win, emissionColor='green')

blueSphere = SphereStim(win, radius=0.1)
blueSphere.thePose.pos = blueLight.pos
blueSphere.material = BlinnPhongMaterial(win, emissionColor='blue')

# text to overlay
message = visual.TextStim(
    win, text='Any key to quit', pos=(0, -0.8), units='norm')

angle = 0.0  # box angle

while not event.getKeys():
    win.setPerspectiveView()  # set the projection, must be done every frame

    win.useLights = True  # enable lighting

    # spin the stimulus by angle
    boxStim.thePose.setOriAxisAngle((0, 1, 1), angle)

    # draw the stimulus
    boxStim.draw()

    # Disable lights for 2D stimuli and light source shapes, or else colors will
    # be modulated.
    win.useLights = False

    # Disabling lighting will cause these not to appear shaded by other light
    # sources in the scene.
    redSphere.draw()
    greenSphere.draw()
    blueSphere.draw()

    win.resetEyeTransform()  # reset the transformation to draw 2D stimuli

    message.draw()

    win.flip()

    angle += 0.5

win.close()
core.quit()
