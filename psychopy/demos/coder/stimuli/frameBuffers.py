#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Demo for the class psychopy.visual.RigidBodyPose class.

This demonstrates how to use rigid body transforms to control the poses of 3D
objects in a scene.

"""

from psychopy import core, event
import psychopy.visual as visual
from psychopy.visual import SphereStim, LightSource, RigidBodyPose

win = visual.Window((800, 600), allowGUI=True, monitor='testMonitor', stereo='fuse')

# create a rigid body defining the pivot point of objects in the scene
pivotPose = RigidBodyPose((0, 0, 0))

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
spherePose1 = RigidBodyPose((0.01, -0.01, 0.01))
spherePose2 = RigidBodyPose((-0.01, 0.01, 0.01))
spherePose3 = RigidBodyPose((0.01, -0.01, -0.01))

# create some sphere stim objects
lightSphere = SphereStim(win, radius=0.005, color='white', useShaders=False)
sphere1 = SphereStim(win, radius=0.005, color='red', useShaders=False)
sphere2 = SphereStim(win, radius=0.01, color='green', useShaders=False)
sphere3 = SphereStim(win, radius=0.0075, color='blue', useShaders=False)

#win.createBufferFromRect('left', 'back', (0, 0, 400, 600))
#win.createBufferFromRect('right', 'back', (400, 0, 400, 600))

win.ambientLight = (0, 0, 0)
win.syncLights('back', ('left', 'right'))

angle = 0.0
while not event.getKeys():
    for eye in ('left', 'right'):
        win.setBuffer(eye)
        # rotate the pivot pose
        pivotPose.setOriAxisAngle((0, 1, 0), angle)
        # setup drawing
        win.eyeOffset = -3.2 if eye == 'left' else 3.2
        win.convergeOffset = 0.0

        win.setOffAxisView()
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

        win.useLights = False

    # reset transform to draw text correctly
    win.setBuffer('back', clear=False)
    #win.useLights = False
    win.resetEyeTransform()

    instr.draw()

    win.flip()
    angle += 0.5

win.close()
core.quit()