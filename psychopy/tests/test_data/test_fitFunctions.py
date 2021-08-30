"""Tests for psychopy.data.DataHandler"""
import numpy
from scipy import special
from pytest import raises

PLOTTING = False #turn this on to check it all looks right too
if PLOTTING:
    import pylab

from psychopy import data


def cumNorm(xx, sd, thresh, chance=0.5):
    """For a given x value (e.g. contrast) returns the probability (y) of
    the subject responding yes (or 'correctly')
    """
    xx = numpy.asarray(xx)
    y = (special.erf((xx-thresh) / (numpy.sqrt(2) * sd)) + 1) * 0.5  # NB numpy.special.erf() goes from -1:1
#    y = special.erf((xx - thresh)*slope)/2.0+0.5 #cum norm from 0-1
    y = y * (1 - chance) + chance  # scale to be from chance to 1
    return y


#create some data to test
thresh=0.2
sd=0.1
contrasts = numpy.linspace(0.0,0.5,10)
responses = cumNorm(contrasts, sd=sd, thresh=thresh)

def plotFit(fittedResps, thresh, title):
    pylab.figure()
    pylab.plot(contrasts, responses, 'o')
    pylab.plot(contrasts, fittedResps)
    pylab.plot([0,thresh],[0.75,0.75],'--b')#horiz
    pylab.plot([thresh,thresh],[0.,0.75],'--b')#vert
    pylab.title(title)


def test_fitNakaRushton():
    #the data are actually from a cum norm so this should be exact
    fit = data.FitNakaRushton(contrasts, responses)
    assert numpy.allclose([ 0.21105363, 3.19844141, 0.5233062, 1.04135427 ], fit.params,
                          atol=1e-004, rtol=1e-004 )
    modResps = fit.eval(contrasts)
    #check that inverse works too
    invs = fit.inverse(modResps)
    assert numpy.allclose(contrasts,invs)#inverse should match the forwards function
    #plot if needed
    if PLOTTING:
        plotFit(modResps, thresh, 'Naka-Rushton (params=%s)' %(fit.params))


def test_fitCumNorm():
    #the data are actually from a cum norm so this should be exact
    fit = data.FitCumNormal(contrasts, responses, display=0, expectedMin=0.5)
    assert numpy.allclose([thresh,sd], fit.params)
    modResps = fit.eval(contrasts)
    #check that inverse works too
    invs = fit.inverse(responses)
    assert numpy.allclose(contrasts,invs)#inverse should match the forwards function
    #plot if needed
    if PLOTTING:
        plotFit(modResps, thresh, 'CumulativeNormal (thresh=%.2f, params=%s)' %(fit.inverse(0.75), fit.params))

def test_weibull():
    #fit to the fake data
    fit = data.FitWeibull(contrasts, responses, display=0, expectedMin=0.5)
    #check threshold is close (maybe not identical because not same function)
    assert thresh-fit.inverse(0.75)<0.01
    #check that inverse works too
    modResps = fit.eval(contrasts)
    invs = fit.inverse(modResps)
    assert numpy.allclose(contrasts,invs), contrasts-invs#inverse should match the forwards function
    #do a plot to check fits look right
    if PLOTTING:
        plotFit(modResps, thresh, 'Weibull (thresh=%.2f, params=%s)' %(fit.inverse(0.75), fit.params))

def test_logistic():
    #fit to the fake data
    fit = data.FitLogistic(contrasts, responses, display=0, expectedMin=0.5)
    #check threshold is close (maybe not identical because not same function)
    assert thresh-fit.inverse(0.75)<0.001
    #check that inverse works too
    modResps = fit.eval(contrasts)
    invs = fit.inverse(modResps)
    assert numpy.allclose(contrasts,invs), contrasts-invs#inverse should match the forwards function
    #do a plot to check fits look right
    if PLOTTING:
        plotFit(modResps, thresh, 'Logistic (thresh=%.2f, params=%s)' %(fit.inverse(0.75), fit.params))

def teardown():
    if PLOTTING:
        pylab.show()

if __name__=='__main__':
#    test_fitCumNorm()
#    test_weibull()
#    test_logistic()
    test_fitNakaRushton()
    if PLOTTING:
        pylab.show()
