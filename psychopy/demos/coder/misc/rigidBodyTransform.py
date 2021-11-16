#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Demo for the class psychopy.visual.RigidBodyPose class.

This demonstrates how to use rigid body transforms to control the poses of 3D
objects in a scene.

"""

from psychopy import core, event
import psychopy.visual as visual
from psychopy.visual import SphereStim, LightSource, RigidBodyPose

win = visual.Window((600, 600), allowGUI=False, monitor='testMonitor')

# create a rigid body defining the pivot point of objects in the scene
pivotPose = RigidBodyPose((0, 0, -5))

# text to display
instr = visual.TextStim(win, text="Any key to quit", pos=(0, -.7))

# create scene light at the pivot point
win.lights = [
    LightSource(win, pos=pivotPose.pos, lightType='point',
                diffuseColor=(0, 0, 0), specularColor=(1, 1, 1))
]

# Create poses for objects in the scene, these need to remain unchanged so we
# define them here and then set the poses of the 3D stimuli. Pose positions
# are relative to the pivot point.
spherePose1 = RigidBodyPose((0.1, -0.1, 0.1))
spherePose2 = RigidBodyPose((-0.1, 0.1, 0.1))
spherePose3 = RigidBodyPose((0.1, -0.1 , -0.1))

# create some sphere stim objects
lightSphere = SphereStim(win, radius=0.05, color='white')
sphere1 = SphereStim(win, radius=0.05, color='red')
sphere2 = SphereStim(win, radius=0.1, color='green')
sphere3 = SphereStim(win, radius=0.075, color='blue')

angle = 0.0
while not event.getKeys():

    # rotate the pivot pose
    pivotPose.setOriAxisAngle((0, 1, 0), angle)

    # setup drawing
    win.setPerspectiveView()

    # sphere for the light source, note this does not actually emit light
    lightSphere.thePose = pivotPose
    lightSphere.draw()

    # call after drawing `lightSphere` since we don't want it being shaded
    win.useLights = True

    # multiplying pose puts the first object in the reference frame of the
    # second
    sphere1.thePose = spherePose1 * pivotPose
    sphere2.thePose = spherePose2 * pivotPose
    sphere3.thePose = spherePose3 * pivotPose

    sphere1.draw()
    sphere2.draw()
    sphere3.draw()

    # reset transform to draw text correctly
    win.resetEyeTransform()

    instr.draw()

    win.flip()
    angle += 0.5

win.close()
core.quit()