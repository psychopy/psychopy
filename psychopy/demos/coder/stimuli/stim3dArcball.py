#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Demo for rotating a 3D stimulus with the mouse using an arcball.

Click and drag on the box to rotate it. The point on the box under the mouse
stays under the mouse as you drag. Dragging outside of the arcball (shown while
dragging) turns the box around the line of sight.

An arcball is a virtual sphere around the object being rotated. When the mouse
button is pressed, a ray is cast from the viewer through the mouse to find the
point on the sphere under the mouse. As the mouse moves, the rotation taking
that point to the one now under the mouse is applied to the orientation the
object had when the drag started.

"""
import os

import numpy as np

from psychopy import core, event
import psychopy.visual as visual
from psychopy.visual import LightSource, BlinnPhongMaterial, BoxStim, SphereStim
import psychopy.tools.gltools as gt
import psychopy.tools.mathtools as mt
import psychopy.tools.viewtools as vt


# open a window to render the shape
win = visual.Window((800, 600), units='norm', allowGUI=True)
win.scrWidthPIX = 800  # set if you don't have a monitor profile

mouse = event.Mouse(win=win)

# box to rotate, with a texture so its orientation is easy to see
boxSize = .5
box = BoxStim(win, size=(boxSize,) * 3, pos=(0, 0, -1))
box.material = BlinnPhongMaterial(
    win, diffuseColor=(1, 1, 1), specularColor=(-.5, -.5, -.5),
    shininess=50.0)
faceTexturePath = os.path.join(os.path.dirname(__file__), 'face.jpg')
box.material.diffuseTexture = gt.createTexImage2dFromFile(faceTexturePath)

# the arcball surrounds the box, its radius reaches the corners of the box
arcballCenter = box.pos.copy()
arcballRadius = np.sqrt(3) * boxSize / 2.

# transparent sphere to show the arcball while dragging
arcballSphere = SphereStim(
    win, radius=arcballRadius, pos=arcballCenter, color=(-.5, -.5, 1),
    opacity=0.2)

# light the scene from the top-left, behind the viewer
win.lights = [
    LightSource(win, pos=(-1., 1., 1.), lightType='directional',
                diffuseColor=(1, 1, 1), specularColor=(1, 1, 1),
                ambientColor=(-1, -1, -1))]
win.ambientLight = (.25, .25, .25)

message = visual.TextStim(
    win, text="Drag the box with the mouse to rotate it\n"
              "'r' to reset, 'escape' to quit",
    pos=(0, -.8), units='norm', height=.06)

# shows the axis and angle of the box's orientation
axisAngleText = visual.TextStim(
    win, text='', pos=(-.95, .95), units='norm', height=.06,
    anchorHoriz='left', anchorVert='top', alignText='left')

dragStart = None  # arcball vector and box orientation when dragging started

while True:
    keys = event.getKeys(['escape', 'r'])
    if 'escape' in keys:
        break
    if 'r' in keys:
        box.thePose.ori = (0., 0., 0., 1.)

    # set the projection, must be done every frame prior to drawing 3D stimuli
    win.setPerspectiveView()

    if mouse.getPressed()[0]:
        # ray from the viewer through the mouse, the perspective view must be
        # set when getting this
        rayOrig, rayDir = win.getMouseRay()
        vec = vt.getArcballVector(
            rayOrig, rayDir, arcballCenter, arcballRadius)

        if dragStart is None:  # just pressed, remember where we started
            dragStart = (vec, box.thePose.ori.copy())
        else:
            # rotate the box from where it was when dragging started by the
            # rotation taking the start point on the arcball to the current
            # one
            startVec, startOri = dragStart
            dragRotation = mt.alignTo(startVec, vec)
            box.thePose.ori = mt.multQuat(dragRotation, startOri)
    else:
        dragStart = None

    # show the box's orientation as axis-angle
    axis, angle = box.getOriAxisAngle()
    axisAngleText.text = (
        "Axis: ({:.2f}, {:.2f}, {:.2f})\n"
        "Angle: {:.1f}°".format(*axis, angle))

    win.useLights = True
    box.draw()
    if dragStart is not None:
        arcballSphere.draw()  # transparent, so draw last
    win.useLights = False

    win.resetEyeTransform()  # reset the transformation to draw 2D stimuli
    message.draw()
    axisAngleText.draw()

    win.flip()

win.close()
core.quit()
