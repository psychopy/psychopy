#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Functions and classes related to array handling'''

import numpy


def createXYs(x,y=None):
    """Create an Nx2 array of XY values including all combinations of the
    x and y values provided.

    >>> createXYs(x=[1,2,3],y=[4,5,6])
    array([[1, 4],
       [2, 4],
       [3, 4],
       [1, 5],
       [2, 5],
       [3, 5],
       [1, 6],
       [2, 6],
       [3, 6]])
    >>> createXYs(x=[1,2,3])  #assumes y=x
    array([[1, 1],
       [2, 1],
       [3, 1],
       [1, 2],
       [2, 2],
       [3, 2],
       [1, 3],
       [2, 3],
       [3, 3]])

    """
    if y is None:
        y=x
    xs = numpy.resize(x, len(x)*len(y))# [1,2,3,1,2,3,1,2,3]
    ys = numpy.repeat(y,len(x)) # [1,1,1,2,2,2,3,3,3]
    return numpy.vstack([xs,ys]).transpose()


def extendArr(inArray,newSize):
    """Takes a numpy array and returns it padded with zeros to the necessary size

    >>> extendArr([1,2,3],5)
    array([1, 2, 3, 0, 0])

    """
    if type(inArray) in [tuple,list]:
        inArray=numpy.asarray(inArray)

    newArr = numpy.zeros(newSize,inArray.dtype)
    #create a string to eval (see comment below)
    indString=''
    for thisDim in inArray.shape:
        indString += '0:'+str(thisDim)+','
    indString = indString[0:-1]#remove the final comma

    #e.g.
    #newArr[0:4,0:3]=inArray

    exec("newArr["+indString+"]=inArray")
    return newArr


def makeRadialMatrix(matrixSize):
    """Generate a square matrix where each element val is
    its distance from the centre of the matrix
    """
    oneStep = 2.0/(matrixSize-1)
    xx,yy = numpy.mgrid[0:2+oneStep:oneStep, 0:2+oneStep:oneStep] -1.0 #NB need to add one step length because
    rad = numpy.sqrt(xx**2 + yy**2)
    return rad


def ratioRange(start, nSteps=None, stop=None,
               stepRatio=None, stepdB=None, stepLogUnits=None):
    """Creates a  array where each step is a constant ratio
    rather than a constant addition.

    Specify *start* and any 2 of, *nSteps*, *stop*, *stepRatio*, *stepdB*, *stepLogUnits*

    >>> ratioRange(1,nSteps=4,stop=8)
    array([ 1.,  2.,  4.,  8.])
    >>> ratioRange(1,nSteps=4,stepRatio=2)
    array([ 1.,  2.,  4.,  8.])
    >>> ratioRange(1,stop=8,stepRatio=2)
    array([ 1.,  2.,  4.,  8.])

    """

    if start<=0:
        raise RuntimeError, "Can't calculate ratio ranges on negatives or zero"
    if (stepdB != None): stepRatio= 10.0**(stepdB/20.0) #dB = 20*log10(ratio)
    if (stepLogUnits != None): stepRatio= 10.0**stepLogUnits #logUnit = log10(ratio)

    if (stepRatio!=None) and (nSteps!=None):
        factors = stepRatio**numpy.arange(nSteps,dtype='d')
        output = start*factors

    elif (nSteps!=None) and (stop!=None):
        if stop<=0:
            raise RuntimeError, "Can't calculate ratio ranges on negatives or zero"
        lgStart = numpy.log10(start)
        lgStop = numpy.log10(stop)
        lgStep = (lgStop-lgStart)/(nSteps-1)
        lgArray = numpy.arange(lgStart, lgStop+lgStep, lgStep)
        #if the above is a badly rounded float it may have one extra entry
        if len(lgArray)>nSteps: lgArray=lgArray[:-1]
        output = 10**lgArray

    elif (stepRatio!=None) and (stop!=None):
        thisVal=float(start)
        outList = []
        while thisVal<stop:
            outList.append(thisVal)
            thisVal *= stepRatio
        output=numpy.asarray(outList)

    return output


def shuffleArray(inArray, shuffleAxis=-1, seed=None):
    """DEPRECATED: use `numpy.random.shuffle`
    """
    #arrAsList = shuffle(list(inArray))
    #return numpy.array(arrAsList)
    if seed is not None:
        numpy.random.seed(seed)

    inArray = numpy.array(inArray, 'O')#convert to array if necess
    rndArray = numpy.random.random(inArray.shape)#create a random array of the same shape
    newIndices =  numpy.argsort(rndArray, shuffleAxis)# and get the arguments that would sort it
    return numpy.take(inArray,newIndices)#return the array with the sorted random indices


def val2array(value, withNone=True, withScalar=True, length=2):
    """Helper function: converts different input to a numpy array.
    Raises informative error messages if input is invalid.

    withNone: True/False. should 'None' be passed?
    withScalar: True/False. is a scalar an accepted input? Will be converted to array of this scalar
    elements: False/2/3. Number of elements input should have or be converted to. Might be False (do not accept arrays or convert to such)"""
    if value is None:
        if withNone:
            return None
        else:
            raise ValueError('Invalid parameter. None is not accepted as value.')
    value = numpy.array(value, float)
    if numpy.product(value.shape)==1:
        if withScalar:
            return numpy.repeat(value, length)  # e.g. 5 becomes array([5.0, 5.0, 5.0]) for length=3
        else:
            raise ValueError('Invalid parameter. Single numbers are not accepted. Should be tuple/list/array of length ' + str(length))
    elif value.shape[-1]==length:
            return numpy.array(value, float)
    else:
        raise ValueError('Invalid parameter. Should be length ' + str(length) + ' but got length ' + str(len(value)))
