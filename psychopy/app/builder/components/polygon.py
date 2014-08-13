# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * #to get the template visual component
from os import path
from psychopy.app.builder.components import getInitVals

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'polygon.png')
tooltip = 'Polygon: any regular polygon (line, triangle, square...circle)'

class PolygonComponent(VisualComponent):
    """A class for presenting grating stimuli"""
    def __init__(self, exp, parentName, name='polygon', interpolate='linear',
                units='from exp settings',
                lineColor='$[1,1,1]', lineColorSpace='rgb', lineWidth=1,
                fillColor='$[1,1,1]', fillColorSpace='rgb',
                nVertices = 4,
                pos=[0,0], size=[0.5,0.5], ori=0,
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim=''):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self,exp,parentName,name=name, units=units,
                    pos=pos, size=size, ori=ori,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type='Polygon'
        self.url="http://www.psychopy.org/builder/components/shape.html"
        self.exp.requirePsychopyLibs(['visual'])
        self.order=['nVertices']
        #params
        self.params['nVertices']=Param(nVertices, valType='int',
            updates='constant', allowedUpdates=['constant'],
            hint="How many vertices? 2=line, 3=triangle... (90 approximates a circle)",
            label="N Vertices")
        self.params['fillColorSpace']=Param(fillColorSpace, valType='str', allowedVals=['rgb','dkl','lms'],
            updates='constant',
            hint="Choice of color space for the fill color (rgb, dkl, lms)",
            label="Fill color space")
        self.params['fillColor']=Param(fillColor, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Fill color of this shape; Right-click to bring up a color-picker (rgb only)",
            label="Fill color")
        self.params['lineColorSpace']=Param(lineColorSpace, valType='str', allowedVals=['rgb','dkl','lms'],
            updates='constant',
            hint="Choice of color space for the fill color (rgb, dkl, lms)",
            label="Line color space")
        self.params['lineColor']=Param(lineColor, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Line color of this shape; Right-click to bring up a color-picker (rgb only)",
            label="Line color")
        self.params['lineWidth']=Param(lineWidth, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Width of the shape's line (always in pixels - this does NOT use 'units')",
            label="Line width")
        self.params['interpolate']=Param(interpolate, valType='str', allowedVals=['linear','nearest'],
            updates='constant', allowedUpdates=[],
            hint="How should the image be interpolated if/when rescaled",
            label="Interpolate")
        self.params['size']=Param(size, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Size of this stimulus [w,h]. Note that for a line only the first value is used, for triangle and rect the [w,h] is as expected, but for higher-order polygons it represents the [w,h] of the ellipse that the polygon sits on!! ",
            label="Size [w,h]")
        del self.params['color']
        del self.params['colorSpace']

    def writeInitCode(self,buff):
        #do we need units code?
        if self.params['units'].val=='from exp settings': unitsStr=""
        else: unitsStr="units=%(units)s, " %self.params
        inits = getInitVals(self.params)#replaces variable params with defaults
        if self.params['nVertices'].val == '2':
            buff.writeIndented("%s = visual.Line(win=win, name='%s',%s\n" %(inits['name'],inits['name'],unitsStr))
            buff.writeIndented("    start=(-%(size)s[0]/2.0, 0), end=(+%(size)s[0]/2.0, 0),\n" %(inits) )
        elif self.params['nVertices'].val == '3':
            buff.writeIndented("%s = visual.ShapeStim(win=win, name='%s',%s\n" %(inits['name'],inits['name'],unitsStr))
            buff.writeIndented("    vertices = [[-%(size)s[0]/2.0,-%(size)s[1]/2.0], [+%(size)s[0]/2.0,-%(size)s[1]/2.0], [0,%(size)s[1]/2.0]],\n" %(inits) )
        elif self.params['nVertices'].val == '4':
            buff.writeIndented("%s = visual.Rect(win=win, name='%s',%s\n" %(inits['name'],inits['name'],unitsStr))
            buff.writeIndented("    width=%(size)s[0], height=%(size)s[1],\n" %(inits) )
        else:
            buff.writeIndented("%s = visual.Polygon(win=win, name='%s',%s\n" %(inits['name'],inits['name'],unitsStr))
            buff.writeIndented("    edges = %s," % str(inits['nVertices'].val))
            buff.writeIndented(" size=%(size)s,\n" %(inits) )
        buff.writeIndented("    ori=%(ori)s, pos=%(pos)s,\n" %(inits) )
        buff.writeIndented("    lineWidth=%(lineWidth)s, lineColor=%(lineColor)s, lineColorSpace=%(lineColorSpace)s,\n" %(inits) )
        buff.writeIndented("    fillColor=%(fillColor)s, fillColorSpace=%(fillColorSpace)s,\n" %(inits) )
        buff.writeIndented("    opacity=%(opacity)s," %(inits) )
        if self.params['interpolate'].val=='linear':
            buff.write("interpolate=True)\n")
        else: buff.write("interpolate=False)\n")
