import monitors

mon = monitors.Monitor('3T')#will fetch the most recent saved calibration
nm, power = mon.getSpectra()#i think nm is Nx1, power is Nx3

#nb, i can't remember the way the indices will work for the power
#could be this (if it's a list of lists)
#or could be [0,n], or [n,0] if it's an array
f = open('3Tspectra.csv', 'w') 
for n, this_nm in enumerate(nm):
    f.write('%f,%f,%f,%f\n' %(this_nm, power[0][n], power[1][n], power[2][n]))
f.close()

