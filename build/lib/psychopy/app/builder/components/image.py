# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * #to get the template visual component
from os import path
from psychopy.app.builder.components import getInitVals

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'image.png')
tooltip = 'Image: present images (bmp, jpg, tif...)'

class ImageComponent(VisualComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, exp, parentName, name='image', image='', mask='None', interpolate='linear',
                units='from exp settings', color='$[1,1,1]', colorSpace='rgb',
                pos=[0,0], size=[0.5,0.5], ori=0, texRes='128',
                flipVert=False, flipHoriz=False,
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim=''):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self,exp,parentName,name=name, units=units,
                    color=color, colorSpace=colorSpace,
                    pos=pos, size=size, ori=ori,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type='Image'
        self.url="http://www.psychopy.org/builder/components/image.html"
        self.exp.requirePsychopyLibs(['visual'])
        #params
        self.params['color'].categ = "Advanced" #was set by BaseVisual but for this stim it's advanced
        self.params['colorSpace'].categ = "Advanced"
        self.params['image']=Param(image, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="The image to be displayed - a filename, including path",
            label="Image")
        self.params['mask']=Param(mask, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="An image to define the alpha mask through which the image is seen - gauss, circle, None or a filename (including path)",
            label="Mask", categ="Advanced")
        self.params['texture resolution']=Param(texRes, valType='code', allowedVals=['32','64','128','256','512'],
            updates='constant', allowedUpdates=[],
            hint="Resolution of the mask if one is used.",
            label="Texture resolution", categ="Advanced")
        self.params['interpolate']=Param(mask, valType='str', allowedVals=['linear','nearest'],
            updates='constant', allowedUpdates=[],
            hint="How should the image be interpolated if/when rescaled",
            label="Interpolate", categ="Advanced")
        self.params['flipVert']=Param(flipVert, valType='bool',
            updates='constant', allowedUpdates=[],
            hint="Should the image be flipped vertically (top to bottom)?",
            label="Flip vertically")
        self.params['flipHoriz']=Param(flipVert, valType='bool',
            updates='constant', allowedUpdates=[],
            hint="Should the image be flipped horizontally (left to right)?",
            label="Flip horizontally")

    def writeInitCode(self,buff):
        #do we need units code?
        if self.params['units'].val=='from exp settings': unitsStr=""
        else: unitsStr="units=%(units)s, " %self.params
        inits = getInitVals(self.params)#replaces variable params with defaults
        buff.writeIndented("%s = visual.ImageStim(win=win, name='%s',%s\n" %(inits['name'],inits['name'],unitsStr))
        buff.writeIndented("    image=%(image)s, mask=%(mask)s,\n" %(inits))
        buff.writeIndented("    ori=%(ori)s, pos=%(pos)s, size=%(size)s,\n" %(inits) )
        buff.writeIndented("    color=%(color)s, colorSpace=%(colorSpace)s, opacity=%(opacity)s,\n" %(inits) )
        buff.writeIndented("    flipHoriz=%(flipHoriz)s, flipVert=%(flipVert)s,\n" %(inits) )
        buff.writeIndented("    texRes=%(texture resolution)s" %(inits))# no newline - start optional parameters
        if self.params['interpolate'].val=='linear':
            buff.write(", interpolate=True")
        else: buff.write(", interpolate=False")
        depth = -self.getPosInRoutine()
        buff.write(", depth=%.1f)\n" %depth)#finish with newline

