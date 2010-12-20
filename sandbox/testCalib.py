from psychopy import calib
import matplotlib.matlab as mat

myMonitor = calib.Monitor('iiyama514')

#run a calibration series
lumsPRE = calib.getLumSeriesPR650(1,8)
gamCalc = calib.GammaCalculator(lums=lumsPRE)
print "monitor gamma=%.2f" %(gamCalc.gammaVal)
myMonitor['gamma'] = gamCalc.gammaVal
myMonitor.save()

#set the gamma value and test again
lumsPOST = calib.getLumSeriesPR650(1,8,myMonitor['gamma'])
mat.plot(calib.DACrange(len(lumsPRE)),lumsPRE,'bo-')
mat.plot(calib.DACrange(len(lumsPOST)),lumsPOST,'ro-')
mat.ylabel('cd/m^2')
mat.show()
