"""
Various useful functions for creating filters and textures (e.g. for PatchStim)
	
"""
# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import numpy    
import Image
from psychopy import log

def makeGrating(res,
		ori=0.0,    #in degrees
		cycles=1.0,
		phase=0.0,    #in degrees
		gratType="sin",
		contr=1.0):
	"""
	A function returning an array containing a luminance grating of the specified params
	"""
	
	ori *= (numpy.pi/180)
	phase *= (numpy.pi/180)
	cycle1D = numpy.arange(0.0,cycles*2.0*numpy.pi,cycles*2.0*numpy.pi/res),
	xrange, yrange = numpy.mgrid[0.0 : cycles*2.0*numpy.pi : cycles*2.0*numpy.pi/res,
								 0.0 : cycles*2.0*numpy.pi : cycles*2.0*numpy.pi/res]
	if gratType is "none":
		res=2
		intensity = numpy.ones((res,res),Float)
	elif gratType is "sin":
		intensity= contr*(numpy.sin( xrange*numpy.sin(ori)+yrange*numpy.cos(ori) + phase))
	elif gratType is "ramp":
		intensity= contr*( xrange*numpy.cos(ori)+yrange*numpy.sin(ori) )/(2*numpy.pi)
	elif gratType is "sqr":#square wave (symmetric duty cycle)
		intensity = numpy.where(onePeriodX>pi, 1, -1)
	elif gratType is "sinXsin":
		intensity = numpy.sin(onePeriodX)*numpy.sin(onePeriodY)
	else:#might be a filename of an image
		try:
			im = Image.open(gratType)
		except:
			log.error( "couldn't find tex...",gratType)
			return
	return intensity
	
def maskMatrix(matrix, shape='circle', radius=1.0, center=[0.0,0.0]):
	"""Make and apply a mask to an input matrix (e.g. a grating)
	
	**Arguments:**

            - **matrix** :  a square numpy array to which the mask should be applied
            - **shape** :  shape of the mask, curently: 'circle','gauss','ramp' (linear gradient from center)
            - **radius** :  scale factor to be applied to the mask (circle with radius of [1,1] will extend just to the edge of the matrix). Radius can asymmetric, e.g. [1.0,2.0] will be wider than it is tall.
	    - **center** :  the centre of the mask in the matrix ([1,1] is top-right corner, [-1,-1] is bottom-left)
	"""
	alphaMask = makeMask(matrix.shape[0],shape,radius, center=[0.0,0.0])
	return matrix*alphaMask

def makeMask(matrixSize, shape='circle', radius=1.0, center=[0.0,0.0]):
	"""
	Returns a matrix to be used as an alpha mask (circle,gauss,ramp)
	
	**Arguments:**

            - **matrixSize** :  number of elements in each dimension of the matrix
            - **shape** :  shape of the mask, curently: 'circle','gauss','ramp' (linear gradient from center)
            - **radius** :  scale factor to be applied to the mask (circle with radius of [1,1] will extend just to the edge of the matrix). Radius can asymmetric, e.g. [1.0,2.0] will be wider than it is tall.
	    - **center** :  the centre of the mask in the matrix ([1,1] is top-right corner, [-1,-1] is bottom-left)
		"""
	rad = makeRadialMatrix(matrixSize, center, radius)
	if shape=='ramp':
		outArray=1-rad
	elif shape=='circle':
		#outArray=numpy.ones(matrixSize,'f')
		outArray=numpy.where(numpy.greater(rad,1.0),0.0,1.0)
	elif shape=='gauss':
		outArray=makeGauss(rad,mean=0.0,sd=0.33333)
	else:
		raise 'err', 'unknown shape'
	return outArray*2-1

def makeRadialMatrix(matrixSize, center=[0.0,0.0], radius=1.0):
	"""Generate a square matrix where each element val is
	its distance from the centre of the matrix
	
	**Arguments:**

            - **matrixSize** :  number of elements in each dimension of the matrix
            - **radius** :  scale factor to be applied to the mask (circle with radius of [1,1] will extend just to the edge of the matrix). Radius can asymmetric, e.g. [1.0,2.0] will be wider than it is tall.
	    - **center** :  the centre of the mask in the matrix ([1,1] is top-right corner, [-1,-1] is bottom-left)
	"""
	if type(radius) in [int, float]: radius = [radius,radius]
	
	yy, xx = numpy.mgrid[0:matrixSize, 0:matrixSize]#NB need to add one step length because
	xx = ((1.0- 2.0/matrixSize*xx)+center[0])/radius[0]
	yy = ((1.0- 2.0/matrixSize*yy)+center[1])/radius[1]
	rad = numpy.sqrt(numpy.power(xx,2) + numpy.power(yy,2))
	return rad

def makeGauss(x, mean=0.0, sd=1.0, gain=1.0, base=0.0):
	"""
	Return the gaussian distribution for a given set of x-vals
		
	**Arguments:**

            - **mean** :  then centre of the distribution
            - **sd** :  the width of the distribution
            - **gain** :  the height of the distribution
	    - **base** :  an offset added to the result
	    
	"""
	simpleGauss = numpy.exp( (-numpy.power(mean-x,2)/(2*sd**2)) )
	return base + gain*( simpleGauss )
	
def getRMScontrast(matrix):
	"""Returns the RMS contrast (the sample standard deviation) of a array"""
	matrix = matrix.flat
	RMScontrast = (sum((matrix-numpy.mean(matrix))**2)/len(matrix))**0.5
	return RMScontrast
	
def conv2d(smaller, larger):
	"""convolve a pair of 2d numpy matrices
	Uses fourier transform method, so faster if larger matrix
	has dimensions of size 2^n
	
	Actually right now the matrices must be the same size (will sort out
	padding issues another day!)
	"""
	smallerFFT = numpy.fft2(smaller)
	largerFFT = numpy.fft2(larger)
	
	invFFT = numpy.ifft(smallerFFT*largerFFT)
	return invFFT.real