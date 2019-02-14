#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from builtins import object
import numpy as np
# from scipy import optimize  # DON'T. It's slow and crashes on some machines


class _baseFunctionFit(object):
    """Not needed by most users except as a superclass for developing
    your own functions

    Derived classes must have _eval and _inverse methods with @staticmethods
    """

    def __init__(self, xx, yy, sems=1.0, guess=None, display=1,
                 expectedMin=0.5, optimize_kws=None):
        super(_baseFunctionFit, self).__init__()


        self.xx = np.array(xx)
        self.yy = np.array(yy)
        self.sems = np.array(sems)
        if not hasattr(sems, "__len__"):
            # annoyingly in numpy 1.13 len(numpy.array(1)) gives an error
            self.sems.shape = (1,)  # otherwise we can't get len (in numpy 1.13)
        self.expectedMin = expectedMin
        self.guess = guess
        self.optimize_kws = {}
        if optimize_kws is not None:
            self.optimize_kws = optimize_kws
        # for holding error calculations:
        self.ssq = 0
        self.rms = 0
        self.chi = 0
        # do the calculations:
        self._doFit()

    def _doFit(self):
        """The Fit class that derives this needs to specify its _evalFunction
        """
        # get some useful variables to help choose starting fit vals
        # self.params = optimize.fmin_powell(self._getErr, self.params,
        #    (self.xx,self.yy,self.sems),disp=self.display)
        # self.params = optimize.fmin_bfgs(self._getErr, self.params, None,
        #    (self.xx,self.yy,self.sems),disp=self.display)
        from scipy import optimize
        # don't import optimize at top of script. Slow and not always present!

        global _chance
        _chance = self.expectedMin
        if len(self.sems) == 1:
            sems = None
        else:
            sems = self.sems
        self.params, self.covar = optimize.curve_fit(
            self._eval, self.xx, self.yy, p0=self.guess, sigma=sems, 
            **self.optimize_kws)
        self.ssq = self._getErr(self.params, self.xx, self.yy, 1.0)
        self.chi = self._getErr(self.params, self.xx, self.yy, self.sems)
        self.rms = self.ssq/len(self.xx)

    def _getErr(self, params, xx, yy, sems):
        mod = self.eval(xx, params)
        err = sum((yy - mod)**2 / sems)
        return err

    def eval(self, xx, params=None):
        """Evaluate xx for the current parameters of the model, or for
        arbitrary params if these are given.
        """
        if params is None:
            params = self.params
        global _chance
        _chance = self.expectedMin
        #_eval is a static method - must be done this way because the
        # curve_fit function doesn't want to have any `self` object as
        # first arg
        yy = self._eval(xx, *params)
        return yy

    def inverse(self, yy, params=None):
        """Evaluate yy for the current parameters of the model,
        or for arbitrary params if these are given.
        """
        if params is None:
            # so the user can set params for this particular inv
            params = self.params
        xx = self._inverse(yy, *params)
        return xx


class FitWeibull(_baseFunctionFit):
    """Fit a Weibull function (either 2AFC or YN)
    of the form::

        y = chance + (1.0-chance)*(1-exp( -(xx/alpha)**(beta) ))

    and with inverse::

        x = alpha * (-log((1.0-y)/(1-chance)))**(1.0/beta)

    After fitting the function you can evaluate an array of x-values
    with ``fit.eval(x)``, retrieve the inverse of the function with
    ``fit.inverse(y)`` or retrieve the parameters from ``fit.params``
    (a list with ``[alpha, beta]``)
    """
    # static methods have no `self` and this is important for
    # optimise.curve_fit
    @staticmethod
    def _eval(xx, alpha, beta):
        global _chance
        xx = np.asarray(xx)
        yy = _chance + (1.0 - _chance) * (1 -
                                          np.exp(-(xx/alpha)**beta))
        return yy

    @staticmethod
    def _inverse(yy, alpha, beta):
        global _chance
        xx = alpha * (-np.log((1.0 - yy)/(1 - _chance))) ** (1.0/beta)
        return xx


class FitNakaRushton(_baseFunctionFit):
    """Fit a Naka-Rushton function
    of the form::

        yy = rMin + (rMax-rMin) * xx**n/(xx**n+c50**n)

    After fitting the function you can evaluate an array of x-values
    with ``fit.eval(x)``, retrieve the inverse of the function with
    ``fit.inverse(y)`` or retrieve the parameters from ``fit.params``
    (a list with ``[rMin, rMax, c50, n]``)

    Note that this differs from most of the other functions in
    not using a value for the expected minimum. Rather, it fits this
    as one of the parameters of the model."""
    # static methods have no `self` and this is important for
    # optimise.curve_fit
    @staticmethod
    def _eval(xx, c50, n, rMin, rMax):
        xx = np.asarray(xx)
        if c50 <= 0:
            c50 = 0.001
        if n <= 0:
            n = 0.001
        if rMax <= 0:
            n = 0.001
        if rMin <= 0:
            n = 0.001
        yy = rMin + (rMax - rMin) * (xx**n / (xx**n + c50**n))
        return yy

    @staticmethod
    def _inverse(yy, c50, n, rMin, rMax):
        yScaled = (yy - rMin) / (rMax - rMin)  # remove baseline and scale
        # do we need to shift while fitting?
        yScaled[yScaled < 0] = 0
        xx = (yScaled * c50**n / (1 - yScaled))**(1 / n)
        return xx


class FitLogistic(_baseFunctionFit):
    """Fit a Logistic function (either 2AFC or YN)
    of the form::

        y = chance + (1-chance)/(1+exp((PSE-xx)*JND))

    and with inverse::

        x = PSE - log((1-chance)/(yy-chance) - 1)/JND

    After fitting the function you can evaluate an array of x-values
    with ``fit.eval(x)``, retrieve the inverse of the function with
    ``fit.inverse(y)`` or retrieve the parameters from ``fit.params``
    (a list with ``[PSE, JND]``)
    """
    # static methods have no `self` and this is important for
    # optimise.curve_fit
    @staticmethod
    def _eval(xx, PSE, JND):
        global _chance
        chance = _chance
        xx = np.asarray(xx)
        yy = chance + (1 - chance) / (1 + np.exp((PSE - xx) * JND))
        return yy

    @staticmethod
    def _inverse(yy, PSE, JND):
        global _chance
        yy = np.asarray(yy)
        xx = PSE - np.log((1 - _chance) / (yy - _chance) - 1) / JND
        return xx


class FitCumNormal(_baseFunctionFit):
    """Fit a Cumulative Normal function (aka error function or erf)
    of the form::

        y = chance + (1-chance)*((special.erf((xx-xShift)/(sqrt(2)*sd))+1)*0.5)

    and with inverse::

        x = xShift+sqrt(2)*sd*(erfinv(((yy-chance)/(1-chance)-.5)*2))

    After fitting the function you can evaluate an array of x-values
    with fit.eval(x), retrieve the inverse of the function with
    fit.inverse(y) or retrieve the parameters from fit.params (a list
    with [centre, sd] for the Gaussian distribution forming the cumulative)

    NB: Prior to version 1.74 the parameters had different meaning, relating
    to xShift and slope of the function (similar to 1/sd). Although that is
    more in with the parameters for the Weibull fit, for instance, it is less
    in keeping with standard expectations of normal (Gaussian distributions)
    so in version 1.74.00 the parameters became the [centre,sd] of the normal
    distribution.

    """
    # static methods have no `self` and this is important for
    # optimise.curve_fit
    @staticmethod
    def _eval(xx, xShift, sd):
        from scipy import special
        global _chance
        xx = np.asarray(xx)
        # NB np.special.erf() goes from -1:1
        yy = (_chance + (1 - _chance) *
              ((special.erf((xx - xShift) / (np.sqrt(2) * sd)) + 1) * 0.5))
        return yy

    @staticmethod
    def _inverse(yy, xShift, sd):
        from scipy import special
        global _chance
        yy = np.asarray(yy)
        # xx = (special.erfinv((yy-chance)/(1-chance)*2.0-1)+xShift)/xScale
        # NB: np.special.erfinv() goes from -1:1
        xx = (xShift + np.sqrt(2) * sd *
              special.erfinv(((yy - _chance) / (1 - _chance) - 0.5) * 2))
        return xx

class FitFunction(object):
    """Deprecated: - use the specific functions; FitWeibull, FitLogistic...
    """

    def __init__(self, *args, **kwargs):
        raise DeprecationWarning("FitFunction is now fully DEPRECATED: use"
                                 " FitLogistic, FitWeibull etc instead")
