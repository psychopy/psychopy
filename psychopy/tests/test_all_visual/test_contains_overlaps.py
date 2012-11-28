
from psychopy import visual, monitors, core
from numpy import sqrt, cos, sin, radians, array
from numpy.linalg import norm

params = [
    {'units':'pix',   'scaleFactor':500.0},
    {'units':'height','scaleFactor':1.0},
    {'units':'norm',  'scaleFactor':2.0},
    {'units':'cm',    'scaleFactor':20.0},
    {'units':'deg',   'scaleFactor':20.0},
]

unitDist = 0.2
sqrt2 = sqrt(2)

points = [
    array((0,0)),
    array((0,unitDist)),
    array((0,unitDist*2)),
    array((unitDist/sqrt2,unitDist/sqrt2)),
    array((unitDist*sqrt2,0)),
    array((unitDist*sqrt2,unitDist*sqrt2))
]

postures = [
    {'ori':  0,'size':(1.0,1.0),'pos':array((0,0))},
    {'ori':  0,'size':(1.0,2.0),'pos':array((0,0))},
    {'ori': 45,'size':(1.0,1.0),'pos':array((0,0))},
    {'ori': 45,'size':(1.0,2.0),'pos':array((0,0))},
    {'ori':  0,'size':(1.0,1.0),'pos':array((unitDist*sqrt2,0))},
    {'ori':  0,'size':(1.0,2.0),'pos':array((unitDist*sqrt2,0))},
    {'ori':-45,'size':(1.0,1.0),'pos':array((unitDist*sqrt2,0))},
    {'ori':-90,'size':(1.0,2.0),'pos':array((unitDist*sqrt2,0))}
]

correctResults = [
    (True, True, False, False, False, False),
    (True, True, True, False, False, False),
    (True, False, False, True, False, False),
    (True, False, False, True, False, True),
    (False, False, False, False, True, False),
    (False, False, False, False, True, True),
    (False, False, False, True, True, False),
    (True, False, False, False, True, False)
]


mon = monitors.Monitor('testMonitor')
mon.setDistance(57)
mon.setWidth(40.0)
mon.setSizePix([1024,768])

def contains_overlaps(testType):
    for param in params:
        vertices = [( 0.05*param['scaleFactor'], 0.24*param['scaleFactor']),
                    ( 0.05*param['scaleFactor'],-0.24*param['scaleFactor']),
                    (-0.05*param['scaleFactor'],-0.24*param['scaleFactor']),
                    (-0.05*param['scaleFactor'], 0.24*param['scaleFactor'])]
        win = visual.Window([512,512], monitor=mon, winType='pyglet', units=param['units'])
        shape = visual.ShapeStim(win, vertices=vertices)
        testPoints = [visual.Circle(win, radius=0.02*param['scaleFactor'], pos=p*param['scaleFactor'],
                                    units=param['units']) for p in points]
        message = visual.TextStim(win, text='test:%s  units:%s'%(testType,param['units']),
                                  pos=(0,-0.4*param['scaleFactor']), height=0.04*param['scaleFactor'])
        
        for i in range(len(postures)):
            shape.setOri(postures[i]['ori'])
            shape.setSize(postures[i]['size'])
            shape.setPos(postures[i]['pos']*param['scaleFactor'])
            shape.draw()
            message.draw()
            for j in range(len(testPoints)):
                if testType == 'contains':
                    res = shape.contains(points[j]*param['scaleFactor'])
                    #test for two parameters
                    assert shape.contains(points[j][0]*param['scaleFactor'],points[j][1]*param['scaleFactor']) == res
                elif testType == 'overlaps':
                    res = shape.overlaps(testPoints[j])
                assert res == correctResults[i][j], \
                    '"%s" returns wrong value: unit=%s, ori=%.1f, size=%s, pos=%s, testpoint=%s, expedted=%s'% \
                    (testType, param['units'], postures[i]['ori'], postures[i]['size'], postures[i]['pos'], points[j], correctResults[i][j])
                if res:
                    testPoints[j].setFillColor('green')
                else:
                    testPoints[j].setFillColor('red')
                testPoints[j].draw()
            win.flip()
            #core.wait(0.2)
        
        win.close()


def test_contains():
    contains_overlaps('contains')
    
def test_overlaps():
    contains_overlaps('overlaps')
    
if __name__=='__main__':
    test_contains_overlaps('contains')
    test_contains_overlaps('overlaps')



