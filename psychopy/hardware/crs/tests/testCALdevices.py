
from pycrsltd import colorcal
import numpy
import sys
    
try:
    from psychopy import log
    log.console.setLevel(log.DEBUG)
except:
    import logging as log
    
def testMinolta2Float():
    assert colorcal._minolta2float(50347)== -0.0347
    assert colorcal._minolta2float(10630)==  1.0630
    assert numpy.alltrue(colorcal._minolta2float([10635, 50631]) == numpy.array([ 1.0635, -0.0631]))
    
def testColorCAL(port):
    cal = colorcal.ColorCAL()#using default ports (COM3, /dev/cu.usbmodem0001 or /dev/ttyACM0)
    assert cal.OK#connected and received 'OK00' to cal.getInfo()
    
    print 'Got ColorCAL serial#:%s firmware:%s_%s' %(cal.serialNum, cal.firm, cal.firmBuild)
    #get help
    helpMsg = cal.sendMessage('?')
    print 'Help info:'
    for line in helpMsg[1:]: #the 1st 3 lines are just saying OK00
        print '\t', line.rstrip().lstrip() #remove whitespace from left and right
     
    #perform calibration to zero
    ok = cal.calibrateZero()
    print 'calibZeroSuccess=',ok
    log.flush()
    assert ok
    
    #take a measurement
    ok, x, y, z = cal.measure()
    xyz=numpy.array([x,y,z])
    print 'MES: ok=%s %s' %(ok, xyz)
    assert ok#make sure that the first value returned was True
    log.flush()
    
if __name__ == "__main__":
    testColorCAL(port=defaultPort)
    testMinolta2Float()
    print 'done'