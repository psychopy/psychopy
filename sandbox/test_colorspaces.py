#test colorspaces

from psychopy import misc
import scipy
testDKL1 = scipy.asarray([45,90,1.0])

print testDKL1
print misc.dkl2rgb(testDKL1)
#print misc.dkl2rgb(testDKL2)
#print misc.dkl2rgb(testDKL3)
#print misc.dkl2rgb(testDKL4)
