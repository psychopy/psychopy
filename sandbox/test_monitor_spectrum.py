import monitors

myPR650 = monitors.Photometer(1)
myPR650.measure()
spec = myPR650.getLastSpectrum()
