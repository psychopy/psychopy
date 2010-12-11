import monitors

nPoints = 3
stimSize = 0.8
useBits = False
autoMode = 'auto'

#run the calibration itself
lum_levels=monitors.DACrange(nPoints)
pr650 = monitors.findPR650()
lumsPRE = monitors.getLumSeriesPR650(photometer=pr650,
                                     lum_levels=nPoints,
                                     useBits=useBits,
                                     autoMode=autoMode,
                                     stimSize=stimSize,
                                     gamma=[3.5,3.5,2.2])