#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Demo for the class psychopy.visual.RigidBodyPose class.

This demonstrates how to use rigid body transforms to control the poses of 3D
objects in a scene.

"""

from psychopy import core, event
import psychopy.visual as visual
from psychopy.tools.gltools import getModelViewMatrix
from psychopy.visual.windowwarp import Warper
from psychopy.visual import SphereStim, LightSource, RigidBodyPose, GratingStim
from psychopy.visual.windowbuffer.filters import LensCorrectionFilter
import pyglet.gl as GL

win = visual.Window((800, 800), useFBO=False, allowGUI=True, units='pix',
                    monitor='testMonitor', stereo=False, fullscr=False,
                    color=(0, 0, 0), multiSample=False, samples=1)

win.createBuffer('newBuffer')

filter = LensCorrectionFilter(win, coefK=(5, 1), normalize=True)
#filter.viewPos = (400, 0.0)
# warper = Warper(win,
#                 warp='spherical',
#                 warpfile="",
#                 warpGridsize=128,
#                 eyepoint=[0.5, 0.5],
#                 flipHorizontal=False,
#                 flipVertical=False)

# create a rigid body defining the pivot point of objects in the scene
pivotPose = RigidBodyPose((0, 0, 0))

grating = GratingStim(win, tex="sqr", mask=None, size=(250, 250), sf=0.04, pos=(0.0, 0.0))

# text to display
instr = visual.TextStim(win, text="X", pos=(400, 0))

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
win.syncLights('back', 'newBuffer')
#win.windowBuffers['left'].eyeOffset = -3.
#win.windowBuffers['right'].eyeOffset = 3.
# win.viewOri = 45.0
# win.viewScale = (4, 0.5)

angle = 0.0
while not event.getKeys():
    win.color = (-1, -1, -1)
    win.clearBuffer()
    win.color = (0, 0, 0)
    win.setBuffer('newBuffer')
    #win.windowBuffer.setDefaultView()

    #if win.eye == 'left':
    #    pass
        #win.viewOri = 45.0

    # #win.frontFace = 'cw'
    # # rotate the pivot pose
    # pivotPose.setOriAxisAngle((0, 1, 0), angle)
    # # setup drawing
    # #win.viewOri = 45.0
    # win.setOffAxisView()
    # # sphere for the light source, note this does not actually emit light
    # lightSphere.thePose = pivotPose
    # lightSphere.draw()
    #
    # # call after drawing `lightSphere` since we don't want it being shaded
    # win.useLights = True
    #
    # # multiplying pose puts the first object in the reference frame of the
    # # second
    # sphere1.thePose = spherePose1 * pivotPose
    # sphere2.thePose = spherePose2 * pivotPose
    # sphere3.thePose = spherePose3 * pivotPose
    #
    # sphere1.draw()
    # sphere2.draw()
    # sphere3.draw()
    # #grating.draw()
    #
    # win.useLights = False

    # reset transform to draw text correctly
    #win.getWindowBuffer('back').viewPos = (150, 0)
    #win.setBuffer('back', clear=False)
    #win.setDefaultView()

    #print(win.viewMatrix)
    #win.useLights = False
    instr.pos = (400, 300)
    instr.draw()
    instr.pos = (-400, 300)
    instr.draw()
    grating.draw()

    #grating.ori = 45.0
    #win.getWindowBuffer('back').viewOri = 45.0
    ##win.windowBuffer.setDefaultView()
    #grating.ori = 0.0
    #grating.draw()
    win.setReadBuffer('newBuffer')
    win.setDrawBuffer('back')
    filter.apply()
    #filter.viewOri = angle


    win.flip()
    angle += 0.5

win.close()
core.quit()