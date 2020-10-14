#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy import visual, core, event
from psychopy.visual.secondorder import EnvelopeGrating
from psychopy.visual.noise import NoiseStim
import numpy as np

win = visual.Window([512, 512], blendMode='add', screen=1, useFBO=True)

# comment in to test life without shaders
# win._haveShaders=False

#Make a noise stimulus to use as a carrier for a 2nd order envelope
noise = NoiseStim(win=win, name='noise',units='pix', 
                  ori=1.0, pos=(1000, 1000), size=(512, 512), sf=1/512, phase=0,
                  color=[1,1,1], colorSpace='rgb', opacity=1, blendmode='add', contrast=1.0,
                  texRes=512,
                  noiseType='binary', noiseElementSize=2, interpolate=0)

# env1 Bottom right:: Unmodulated roataing carrier sf=8 ori=45:: moddepth=0.
# env2 Bottom left:: 100% modulated binary noise, envelope drifitng and rotating envsf=8
# env3 Top right:: 100% modulated sin carrier, envelope and carrier rotate in
#   opposite directions (envelope orientation appears slower than grating below
#   but it you track the orientation its not
# env4 Top Left:: 100% beat, envsf=4 but is beat so lookslike 8. Envelope is
#   drifitng at same speed as env1

env1 = EnvelopeGrating(win, ori=0, units='norm', carrier='sin', envelope='sin',
    mask='gauss', sf=4, envsf=8, size=1, contrast=1.0, moddepth=0.0, envori=0,
    pos=[-.5, -.5], interpolate=0)
env2 = EnvelopeGrating(win, ori=0, units='norm', carrier='sin', envelope='sin',
    mask='gauss', sf=1, envsf=8, size=1, contrast=0.5, moddepth=1.0, envori=0, texRes=512,
    pos=[.5, -.5], interpolate=0)
env3 = EnvelopeGrating(win, ori=0, units='norm', carrier='sin', envelope='sin',
    mask='gauss', sf=24, envsf=4, size=1, contrast=0.5, moddepth=1.0, envori=0,
    pos=[-.5, .5], interpolate=0)
env4 = EnvelopeGrating(win, ori=90, units='norm', carrier='sin', envelope='sin',
    mask='gauss', sf=24, envsf=4, size=1, contrast=0.5, moddepth=1.0, envori=0,
    pos=[0.5, 0.5], beat=True, interpolate=0)

#Set the carrier for env 2 to the texture in noise.
env2.setCarrier(noise.tex)

while not event.getKeys():
    # contMod.phase += 0.01
    env1.ori += 0.1
    env2.envori += 0.1
    env2.envphase += 0.01
    env3.envori += 0.1
    env3.ori -= 0.1
    env4.envphase += 0.01
    env4.phase += 0.01

    # env1.phase += 0.01
    # env1.ori += 0.1
    env1.draw()
    env2.draw()
    env3.draw()
    env4.draw()
    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
