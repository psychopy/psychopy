from _visual import VisualComponent, Param, PreviewParam
from os import path
from psychopy.app.builder.components import getInitVals
from psychopy import visual
import numpy

thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'shapes.png')
tooltip = 'Basic shapes: rectangle, ellipse and arrow'


class BasicShapeComponent(VisualComponent):
    """A class for presenting simple shapes"""
    PREVIEW_STIMULUS = visual.ShapeStim
    
    @staticmethod
    def ellipse_vertices():
        a = numpy.linspace(0, 2 * numpy.math.pi, 60)
        b = numpy.array((numpy.cos(a) / 2, numpy.sin(a) / 2)).transpose()
        return b.tolist()
    
    @staticmethod
    def shape_to_vertices(shape):
        shape = shape.val
        if shape == 'ellipse':
            return BasicShapeComponent.ellipse_vertices()
        elif shape == 'rectangle':
            print "B"
            return ((-0.5, 0.5), (-0.5, -0.5), (0.5, -0.5), (0.5, 0.5))
        else:
            return ((-0.5, 0.5), (-0.5, -0.5), (0.5, -0.5))
    
    def __init__(self, exp, parentName, name='shape', units='from exp settings', color='$[1,1,1]', colorSpace='rgb',
                pos=[0, 0], size=[0.5, 0.5], ori=0, startType='time (s)', startVal='', stopType='duration (s)',
                stopVal='', startEstim='', durationEstim='', shape='ellipse'):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self,exp,parentName,name=name, units=units,
                    color=color, colorSpace=colorSpace,
                    pos=pos, size=size, ori=ori,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type='Shape'
        self.exp.requirePsychopyLibs(['visual'])
        self.order=[]
        #params
        self.params['shape']=Param(shape, valType='str', allowedVals=['ellipse', 'rectangle', 'arrow'],
            updates='constant', allowedUpdates=[], label="shape")

    def writeInitCode(self, buff):
        kwargs = getInitVals(self.params) #replaces variable params with defaults
        kwargs['units'] = '\'\'' if self.params['units'].val == 'from exp settings' else self.params['units']
        kwargs.update(self.SHAPE_PARAMS[self.params['shape'].val])
        buff.writeIndented("%(name)s = visual.ShapeStim(win=win, name='%(name)s',units=%(units)s,\n" % kwargs)
        buff.writeIndented("    ori=%(ori)s, pos=%(pos)s, size=%(size)s, fillColor=%(color)s,\n" % kwargs)
        buff.writeIndented("    opacity=%(opacity)s, vertices=%(vertices)s, lineColor=None)\n" % kwargs)
    
    '''def getStimulus(self, window):
        vertices = self.SHAPE_PARAMS[self.params["shape"].val]['vertices']
        return visual.ShapeStim(
                window, units="norm", pos=eval(self.params["pos"].val), size=eval(self.params["size"].val),
                ori=eval(str(self.params["ori"])), fillColor=eval(str(self.params["color"])), vertices=vertices,
                lineColor=None)'''


BasicShapeComponent.SHAPE_PARAMS = {
    'ellipse': {
        'vertices': BasicShapeComponent.ellipse_vertices(),
    },
    'rectangle': {
        'vertices': ((-0.5, 0.5), (-0.5, -0.5), (0.5, -0.5), (0.5, 0.5)),
    },
    'arrow': {
        'vertices': ((-0.5, 0), (0, 0.5)),
    }
}

BasicShapeComponent.PREVIEW_PARAMS = {
    "size": PreviewParam("size", "eval"),
    "color": PreviewParam("fillColor", "interpret"),
    "colorSpace": PreviewParam("fillColorSpace", "verbatim"),
    'shape': PreviewParam('vertices', BasicShapeComponent.shape_to_vertices)
}
