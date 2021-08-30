#   Copyright 2015 Joseph J Glavan
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   Please see <http://www.gnu.org/licenses/> for a copy of the GNU General Public License.

__all__ = ['PsiObject']

from numpy import *


class PsiObject():

    """Special class to handle internal array and functions of Psi adaptive psychophysical method (Kontsevich & Tyler, 1999)."""
    
    def __init__(self, x, alpha, beta, xPrecision, aPrecision, bPrecision, delta=0, stepType='lin', TwoAFC=False, prior=None):
        global stats
        from scipy import stats  # takes a while to load so do it lazy

        self._TwoAFC = TwoAFC
        #Save dimensions
        if stepType == 'lin':
            self.x = linspace(x[0], x[1], int(round((x[1]-x[0])/xPrecision)+1), True)
        elif stepType == 'log':
            self.x = logspace(log10(x[0]), log10(x[1]), xPrecision, True)
        else:
            raise RuntimeError('Invalid step type. Unable to initialize PsiObject.')
        self.alpha = linspace(alpha[0], alpha[1], int(round((alpha[1]-alpha[0])/aPrecision)+1), True)
        self.beta = linspace(beta[0], beta[1], int(round((beta[1]-beta[0])/bPrecision)+1), True)
        self.r = array(list(range(2)))
        self.delta = delta
        
        # Change x,a,b,r arrays to matrix computation compatible orthogonal 4D arrays
        # ALWAYS use the order for P(r|lambda,x); i.e. [r,a,b,x]
        self._r = self.r.reshape((self.r.size,1,1,1))
        self._alpha = self.alpha.reshape((1,self.alpha.size,1,1))
        self._beta = self.beta.reshape((1,1,self.beta.size,1))
        self._x = self.x.reshape((1,1,1,self.x.size))
        
        #Create P(lambda)
        if prior is None or prior.shape != (1, len(self.alpha),len(self.beta), 1):
            if prior is not None:
                warnings.warn("Prior has incompatible dimensions. Using uniform (1/N) probabilities.")
            self._probLambda = ndarray(shape=(1,len(self.alpha),len(self.beta),1))
            self._probLambda.fill(1/(len(self.alpha)*len(self.beta)))
        else:
            if prior.shape == (1, len(self.alpha), len(self.beta), 1):
                self._probLambda = prior
            else:
                self._probLambda = prior.reshape(1, len(self.alpha), len(self.beta), 1)
            
        #Create P(r | lambda, x)
        if TwoAFC:
            self._probResponseGivenLambdaX = (1-self._r) + (2*self._r-1) * ((.5 + .5 * stats.norm.cdf(self._x, self._alpha, self._beta)) * (1 - self.delta) + self.delta / 2)
        else: # Yes/No
            self._probResponseGivenLambdaX = (1-self._r) + (2*self._r-1) * (stats.norm.cdf(self._x, self._alpha, self._beta)*(1-self.delta)+self.delta/2)
        
    def update(self, response=None):
        if response is not None:    #response should only be None when Psi is first initialized
            self._probLambda = self._probLambdaGivenXResponse[response,:,:,self.nextIntensityIndex].reshape((1,len(self.alpha),len(self.beta),1))
            
        #Create P(r | x)
        self._probResponseGivenX = sum(self._probResponseGivenLambdaX * self._probLambda, axis=(1,2)).reshape((len(self.r),1,1,len(self.x)))
        
        #Create P(lambda | x, r)
        self._probLambdaGivenXResponse = self._probLambda*self._probResponseGivenLambdaX/self._probResponseGivenX
        
        #Create H(x, r)
        self._entropyXResponse = -1* sum(self._probLambdaGivenXResponse * log10(self._probLambdaGivenXResponse), axis=(1,2)).reshape((len(self.r),1,1,len(self.x)))
        
        #Create E[H(x)]
        self._expectedEntropyX = sum(self._entropyXResponse * self._probResponseGivenX, axis=0).reshape((1,1,1,len(self.x)))
        
        #Generate next intensity
        self.nextIntensityIndex = argmin(self._expectedEntropyX, axis=3)[0][0][0]
        self.nextIntensity = self.x[self.nextIntensityIndex]
        
    def estimateLambda(self):
        return (sum(sum(self._alpha.reshape((len(self.alpha),1))*self._probLambda.squeeze(), axis=1)), sum(sum(self._beta.reshape((1,len(self.beta)))*self._probLambda.squeeze(), axis=1)))
        
    def estimateThreshold(self, thresh, lam):
        if lam is None:
            lamb = self.estimateLambda()
        else:
            lamb = lam
        if self._TwoAFC:
            return stats.norm.ppf((2*thresh-1)/(1-self.delta), lamb[0], lamb[1])
        else:
            return stats.norm.ppf((thresh-self.delta/2)/(1-self.delta), lamb[0], lamb[1])
        
    def savePosterior(self, file):
        save(file, self._probLambda)
