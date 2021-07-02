# Author: Dominic Keehan
# Part 4 Project, RJMCMC for Microlensing
# [functions]

import MulensModel as mm 
import math
import random
import matplotlib.pyplot as plt
from numpy.lib.function_base import cov
import numpy as np
from numpy.core.numeric import Inf
from scipy.stats import truncnorm, lognorm, norm, loguniform, uniform, multivariate_normal
import copy


class uniDist(object):
    '''
    Create an instance of a uniform distribution.
    --------------------------------------------
    left: the lower bound for values
    right: the upper bound for values 
    '''
    def __init__(self, left, right):
        self.lb = left
        self.rb = right
        self.dist = uniform(left, right)

    def inBounds(self, x):
        if self.lb <= x <= self.rb: return 1
        else: return 0

    def logPDF(self, x):
        return self.dist.logpdf(x)



class logUniDist(object):
    '''
    Create an instance of a log uniform distribution. 
    I.e., the log of the data is uniformly distributed
    --------------------------------------------
    left: the lower bound for values in true units
    right: the upper bound for values in true units
    '''
    def __init__(self, left, right):
        self.lb = left
        self.rb = right
        self.dist = loguniform(left, right)

    def inBounds(self, x):
        if self.lb <= x <= self.rb: return 1
        else: return 0

    def logPDF(self, x):
        return self.dist.logpdf(x)



class truncatedLogNormDist(object):
    '''
    Create an instance of a truncated log normal distribution. 
    I.e., the log of the data is normally distributed, and the 
    distribution is restricted to a certain range
    --------------------------------------------
    left: the lower bound for values in true units
    right: the upper bound for values in true units
    mu: the mean of the underlying normal distriubtion in true units
    sd: the standard deviation of the underlying normal distribution in true units
    '''
    def __init__(self, left, right, mu, sd):
        self.lb = left
        self.rb = right
        self.dist = lognorm(scale = np.exp(np.log(mu)), s = (np.log(sd))) # (Scipy takes specefic shape parameters)

        # Probability that is otherwise truncated to zero, distributed uniformly into the valid range
        self.truncation = (self.dist.cdf(left) + 1 - self.dist.cdf(right)) / (right - left)

    def inBounds(self, x):
        if self.lb <= x <= self.rb: return 1
        else: return 0

    def logPDF(self, x):
        if self.lb <= x <= self.rb: return np.log(self.dist.pdf(x) + self.truncation)
        else: return -Inf



def AdaptiveMCMC(m, data, theta, priors, covariance, burns, iterations):
    '''
    Performs Adaptive MCMC as described in Haario et al “An adaptive Metropolis algorithm”,
    in the context of microlensing events.
    --------------------------------------------
    m: the index of the microlensing model to use (1 or 2, single or binary)
    data: the data of the microlensing event to analyse, as a mulensModel data object
    theta: the parameter values in the associated model space to initiliase from
    priors: an array of prior distribution objects for the lensing parameters, in the order of entries in theta
    covariance: the covariance to initialise with when proposing a gaussian move. 
                Can be the diagonal entries only or a complete matrix
    burns: how many iterations to perform before beginning to adapt the covaraince matrix
    iterations: how many further iterations to perform while adapting the covaraicne matrix

    Returns:
    covariance: the final covaraince reached 
    states: the list of parameter states visited
    c: a list of values for each iteration, 1 if the move was accepted, 0 otherwise
    '''

    if burns <= 0: #
        raise ValueError("Not enough iterations to safely establish an empirical covariance matrix")
    
    # initialise
    d = len(theta)

    I = np.identity(d)
    s = 2.4**2 / d # Arbitrary(ish), good value from Haario et al
    eps = 1e-12 # Needs to be smaller than the scale of parameter values

    c = np.zeros((iterations + burns))

    states = np.zeros((d, iterations + burns))
    states[:, 0] = theta

    means = np.zeros((d, iterations + burns))
    means[:, 0] = theta


    pi = logLikelihood(m, data, unscale(m, theta), priors)
    for i in range(1, burns): # warm up walk to establish an empirical covariance
        # propose a new state and calculate the resulting likelihood and prior ratio
        proposed = GaussianProposal(theta, covariance)
        piProposed = logLikelihood(m, data, unscale(m, proposed), priors)
        priorRatio = np.exp(PriorRatio(m, m, unscale(m, theta), unscale(m, proposed), priors))

        if random.random() < priorRatio * np.exp(piProposed - pi): # metropolis acceptance using log rules
            theta = proposed
            pi = piProposed
            c[i] = 1

        else: c[i] = 0
        
        states[:, i] = theta#unscale(m, theta)
        means[:, i] = (means[:, i-1]*i + theta)/(i + 1) # recursive mean (offsets indices starting at zero by one)

    # initiliase empirical covaraince
    covariance = s*np.cov(states[:, 0:burns]) + s*eps*I
    
    t = burns # global index

    for i in range(iterations): # adaptive walk
        # propose a new state and calculate the resulting likelihood and prior ratio
        proposed = GaussianProposal(theta, covariance)
        piProposed = logLikelihood(m, data, unscale(m, proposed), priors)
        priorRatio = np.exp(PriorRatio(m, m, unscale(m, theta), unscale(m, proposed), priors))

        if random.random() < priorRatio * np.exp(piProposed - pi): # metropolis acceptance using log rules
            theta = proposed
            pi = piProposed
            c[t]=1

        else: c[t]=0
 
        states[:, t] = theta#unscale(m, theta)
        means[:, t] = (means[:, t-1]*t + theta)/(t + 1) # recursive mean (offsets indices starting at zero by one)
        
        # update step (recursive covariance)
        covariance = (t - 1)/t * covariance + s/t * (t*means[:, t - 1]*np.transpose(means[:, t - 1]) - (t + 1)*means[:, t]*np.transpose(means[:, t]) + states[:, t]*np.transpose(states[:, t])) + eps*I

        t += 1

    # performance diagnostic
    print(f"Adaptive Acc: {(np.sum(c) / (iterations + burns)):.4f}, Model: {m}")

    return covariance, states, means, c



def GaussianProposal(theta, covariance):
    '''
    Takes a single step in a guassian walk process
    ----------------------------------------------
    theta: the parameter values to step from
    covariance: the covariance with which to initialise the multivariate 
                guassian to propose from. Can be the diagonal entries only 
                or a complete matrix

    Returns: a new point in parameter space
    '''
    return multivariate_normal.rvs(mean = theta, cov = covariance)



def RJCenteredProposal(m, mProp, theta, covariance, centers):
    '''
    Proposes a new point to jump to when doing RJMCMC using centreing points,
    in the context of single and binary microlensing events.
    --------------------------------------------
    m: the index of the microlensing model to jump from (1 or 2, single or binary)
    mProp: the index of the microlensing model to jump to
    theta: the parameter values in the associated model space to jump from
    covariance: the covariance to jump with if doing an intra-model jump. 
                Can be the diagonal entries only or a complete matrix
    centers: an array of the parameter values to use as centreing points for each model,
             in the order [single, binary]

    Returns: a new point in the parameter space a jump was proposed too
    '''
    
    if m == mProp: return GaussianProposal(theta, covariance) # intra-modal move
    
    else: # inter-model move
        l = (theta - centers[m-1]) / centers[m-1] # relative distance from the initial model's centre

        if mProp == 1:
            return l[0:3] * centers[mProp-1] + centers[mProp-1]
        
        if mProp == 2: 

            #r = random.random()
            #u = np.multiply(r, [0.001, 0.00059, 1.238, 223.7])+np.multiply((1-r), [0.00099, 0.0009, 1.2, 223.5])#multivariate_normal.rvs(mean=center[mProp-1][3:], cov=covProp[3:] * np.average(l)) #center[mProp-1][3:] * np.average(l)#SurrogatePosterior[mProp].rvs #THIS FUNCTION MIGHT NOT BE DIFFERENTIABLE, JACOBIAN TROUBLES?
            #u = np.append((center[mProp-1][3:6] + center[mProp-1][3:6] * np.average(l)), center[mProp-1][6])

            u = centers[mProp-1][3:] + centers[mProp-1][3:] * np.average(l)# * random.random() # semi-randomly sample the non shared parameters
            thetaProp=np.concatenate(((l * centers[mProp-1][0:3]+centers[mProp-1][0:3]), u))

            return thetaProp



def D(m):
    '''
    Helper function. Maps the model index to the associated 
    dimensionality in the context of microlensing.
    --------------------------------------------
    if m == 1: return 3
    elif m == 2: return 7
    else: return 0 
    '''

    D = [0, 3, 7]
    return D[m]



def unscale(m, theta): ############make this into a class
    '''
    Helper function. Maps the model index to the associated 
    dimensionality in the context of microlensing.
    --------------------------------------------
    if m == 1: return 3
    elif m == 2: return 7
    else: return 0 
    '''

    thetaT=copy.deepcopy(theta)

    if m == 1:
        return thetaT
    
    if m == 2:
        thetaT[4] = np.exp(theta[4])
        return thetaT

    return 0


def PriorRatio(m,mProp,theta,thetaProp,priors):
    '''
    Calculates the ratio of the product of the priors of the proposed point to the
    initial point, in log units.
    --------------------------------------------
    m: the index of the microlensing model to jump from (1 or 2, single or binary)
    mProp: the index of the microlensing model to jump to
    theta: the parameter values in the associated model space to jump from
    thetaProp: the parameter values in the associated model space to jump to
    priors: an array of prior distribution objects for the lensing parameters, in the order of entries in theta
    '''
    
    productNumerator = 0.
    productDenomenator = 0.

    #print(theta, 99)
    #thetaT = unscale(m, theta)
    #thetaTProp = unscale(mProp, thetaProp)
    #print(thetaT, 99)

    for parameter in range(D(mProp)): # cycle through each parameter and associated prior
        productNumerator += (priors[parameter].logPDF(thetaProp[parameter])) # product using log rules

    for parameter in range(D(m)): # cycle through each parameter and associated prior
        #print(np.exp(priors[parameter].logPDF(theta[parameter])), parameter, m)
        productDenomenator += (priors[parameter].logPDF(theta[parameter])) # product using log rules
    
    #print(productNumerator, productDenomenator)
    
    return productNumerator - productDenomenator # ratio using log rules


'''
def PriorBounds(m, theta, priors):
    
    Check if a position in parameter space is within the bounds of the priors
    --------------------------------------------
    m: the index of the microlensing model to jump from (1 or 2, single or binary)
    mProp: the index of the microlensing model to jump to
    theta: the parameter values in the associated model space to jump from
    thetaProp: the parameter values in the associated model space to jump to
    priors: an array of prior distribution objects for the lensing parameters, in the order of entries in theta
    
    for parameter in range(D(m)): 
        if not priors[parameter].inBounds(theta[parameter]): return 0
        productDenomenator += (priors[parameter].logPDF(theta[parameter]))

    if m==1:

        t_0, u_0, t_E = theta

        if (u_0<0 or u_0>2):
            return 0

        if (t_0<0 or t_0>72):
            return 0

        if (t_E<1 or t_E>100):
            return 0
    
    elif m==2:
        t_0, u_0, t_E, rho, q, s, alpha = theta

        if (s<0.2 or s>5):
            return 0

        if (q<10e-6 or q>1):
            return 0

        if (rho<10**-4 or rho> 10**-2 ):
            return 0

        if (alpha<0 or alpha>360):
            return 0

        if (u_0<0 or u_0>2):
            return 0

        if (t_0<0 or t_0>72):
            return 0

        if (t_E<1 or t_E>100):
            return 0
    
    return 1
'''


def logLikelihood(m, Data, theta, priors):
    '''
    Calculate the log likelihood that a lightcurve represents observed lightcurve data, upto linear proportionality

    Note: When used in the ratio for a metropolis hastings step, linear proportionality is sufficient as the shared
    linear coeffiecnt will be present in the numerator and denominator and get cancelled.
    --------------------------------------------
    m: the index of the microlensing model (1 or 2, single or binary)
    data: the data of the microlensing event to analyse, as a mulensModel data object
    theta: the parameter values in the associated model space to jump from
    priors: an array of prior distribution objects for the lensing parameters, in the order of entries in theta
    '''

    #if PriorBounds(m, theta, priors)==0: return -Inf
    #thetaT = unscale(m, theta)

    # check if parameter is not in prior bounds, and ensure it is not accepted if so
    for parameter in range(D(m)):
        if not priors[parameter].inBounds(theta[parameter]): return -Inf

    if m==1:
        try: # for when moves are out of bounds of model valididty
            Model = mm.Model(dict(zip(['t_0', 'u_0', 't_E'], theta)))
            Model.set_magnification_methods([0., 'point_source', 72.])
            Event = mm.Event(datasets=Data, model=Model)

        except: # if a point is uncomputable, return true probability zero
            return -Inf

        return -Event.get_chi2()/2 # exponentially linearly proportional to likelihood


    if m==2:
        try: # check if parameter is not in prior bounds, and ensure it is not accepted if so
            Model = mm.Model(dict(zip(['t_0', 'u_0', 't_E', 'rho', 'q', 's', 'alpha'], theta)))
            Model.set_magnification_methods([0., 'VBBL', 72.]) #?
            Event = mm.Event(datasets=Data, model=Model)

        except: # if a point is uncomputable, return true probability zero
            return -Inf
        
        return -Event.get_chi2()/2 # exponentially linearly proportional to likelihood



'''
def RJAuxiliaryProposal(m,m_prop,theta,covp,priors,params):
    #??????
    if (m==1 and m_prop==1):
        theta_prop = multivariate_normal.rvs(mean=theta, cov=covp[0:3,0:3])
        return theta_prop
    elif (m==2 and m_prop==2):
        theta_prop = multivariate_normal.rvs(mean=theta, cov=covp)
        return theta_prop
    elif (m==1 and m_prop==2):
        theta = np.append(theta,np.zeros(np.shape(theta)))
        theta_prop = multivariate_normal.rvs(mean=theta, cov=covp)
        return theta_prop
    elif (m==2 and m_prop==1):
        theta_prop = multivariate_normal.rvs(mean=theta[0:3], cov=covp[0:3,0:3])
        return theta_prop



def Posterior(m,t,y,theta,cov,priors):
    
    product=Likelihood(m,t,y,theta,cov)
    for p in range(D): product*=priors[p].pdf(theta[p])
    
    return product



def PosteriorRatio(t,y,m,m_prop,theta,theta_prop,cov,priors):
    return Posterior(m_prop,t,y,theta_prop,cov,priors)/Posterior(m,t,y,theta,cov,priors)



def ProposalRatio(m,m_prop,theta,thetaProp,priors):
    #??????????

    productNum=1.
    productDen=1.
    for p in range(DProp-1, D): productNum*=priors[p].pdf(thetaProp[p])
    for p in range(D-1, Dprop): productDen*=priors[p].pdf(theta[p])

    # If Auxiliary proposal, need?

    #   elif(m_prop==1 and m==1):
    #    return priors['phi'].pdf(theta_prop[3])*priors['q'].pdf(theta_prop[4])*priors['d'].pdf(theta_prop[5])/priors['phi'].pdf(theta[3])*priors['q'].pdf(theta[4])*priors['d'].pdf(theta[5])

    return productNum/productDen
'''