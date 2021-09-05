# Author: Dominic Keehan
# Part 4 Project, RJMCMC for Microlensing
# [functions]




import MulensModel as mm 
import math
import random
import numpy as np
from numpy.lib.function_base import append, cov
from numpy.core.numeric import Inf
from scipy.stats import lognorm, loguniform, uniform, multivariate_normal
from copy import deepcopy




class uniDist(object):
    '''
    Create an instance of a uniform distribution.
    --------------------------------------------
    left [scalar]: the lower bound for values
    right [scalar]: the upper bound for values 
    '''
    def __init__(self, left, right):
        self.lb = left
        self.rb = right
        self.dist = uniform(left, right)

    def in_Bounds(self, x):
        if self.lb <= x <= self.rb: return 1
        else: return 0

    def log_PDF(self, x):
        return self.dist.logpdf(x)



class logUniDist(object):
    '''
    Create an instance of a log uniform distribution. 
    I.e., the log of the data is uniformly distributed
    --------------------------------------------
    left [scalar]: the lower bound for values in true units
    right [scalar]: the upper bound for values in true units
    '''
    def __init__(self, left, right):
        self.lb = left
        self.rb = right
        self.dist = loguniform(left, right)

    def in_Bounds(self, x):
        if self.lb <= x <= self.rb: return 1
        else: return 0

    def log_PDF(self, x):
        return self.dist.logpdf(x)



class truncatedLogNormDist(object):
    '''
    Create an instance of a truncated log normal distribution. 
    I.e., the log of the data is normally distributed, and the 
    distribution is restricted to a certain range
    --------------------------------------------
    left [scalar]: the lower bound for values in true units
    right [scalar]: the upper bound for values in true units
    mu [scalar]: the mean of the underlying normal distriubtion in true units
    sd [scalar]: the standard deviation of the underlying normal distribution in true units
    '''
    def __init__(self, left, right, mu, sd):
        self.lb = left
        self.rb = right
        self.dist = lognorm(scale = np.exp(np.log(mu)), s = (np.log(sd))) # (Scipy takes specefic shape parameters)

        # Probability that is otherwise truncated to zero, 
        # distributed uniformly into the valid range (not quite correct but a good aprroximation)
        self.truncation = (self.dist.cdf(left) + 1 - self.dist.cdf(right)) / (right - left)

    def in_Bounds(self, x):
        if self.lb <= x <= self.rb: return 1
        else: return 0

    def log_PDF(self, x):
        if self.lb <= x <= self.rb: return np.log(self.dist.pdf(x) + self.truncation)
        else: return -Inf


class state(object):

    def __init__():

    def value(self):
        return self.scaled

    def true(self):
        return self.unscaled


class chain(object):

    def __init__(self):
        self.n_states = 0
        self.states = []
        self.model_indices = []

    def add_state(self, state, m):
        self.n_states += 1
        self.states.append(state)
        self.average_state
        self.model_indices.append(m)
        return


method ln_():



class model(object):
    '''
    Class that implements explicit RK methods.

    Attributes:
        alpha (numpy array): vector of weights in the Butcher tableau
        beta  (numpy array): vector of nodes in the Butcher tableau
        gamma (numpy array): RK matrix in the Butcher tableau
        n (int): number of derivatives used in explicit RK method
    '''

    def __init__(self, m, D, theta, priors, covariance, ln_likelihood_method):
        self.m = m
        self.D = D
        self.center = theta
        self.priors = priors
        self.model_states = chain()
        self.ln_likelihood_fnc = ln_likelihood_fnc

    def 

    def ln_likelihood(self, theta):
        return self.ln_likelihood_fnc(theta.true())

    def ln_prior_density(self, theta, **kwargs):
        '''
        Calculates the product of the priors for a model and state. Optionally accounts for auxilliary variables.
        ------------------------------------------------------------------------------------------------------
        Inputs:
        theta [array like]: the scaled parameter values in the associated model space to jump from
        
        Optional args:
        v [array like]: the values of the auxiliary variables, stored from the largest model
        max_D [int]: dimensionality of the largest model


        Returns:
        log_prior_product [scalar]: log prior probability density of the state
        '''
        if self.D != len(theta.true()):
            raise ValueError
    
        log_prior_product = 0.

        #cycle through parameters
        for p in range(self.D):

            # product using log rules
            log_prior_product += (self.priors[p].log_PDF(theta.true()[p]))

        if 
            #cycle through auxiliary parameters
            for p in range(self.D, max_D):
                
                # product using log rules
                log_prior_product += (self.priors[p].log_PDF(v.true()[p])) 

        return log_prior_product







## FUNCTIONS ##









def Adapt_MH(m, data, theta, priors, covariance, burns, iterations):
    '''
    Performs Adaptive MCMC as described in Haario et al “An adaptive Metropolis algorithm”,
    in the context of microlensing events.
    --------------------------------------------
    m [int]: the index of the microlensing model to use (0 or 1, single or binary)
    data [muLens data]: the data of the microlensing event to analyse
    theta [array like]: the scaled parameter values in the associated model space to start from
    priors [array like]: an array of prior distribution objects for the lensing parameters,
                         in the order of entries in theta
    covariance [array like]: the covariance to initialise with when proposing a move. 
                             Can be the diagonal entries only or a complete matrix.
                             In the order of theta
    burns [int]: how many iterations to perform before beginning to adapt the covariance matrix
    iterations [int]: how many further iterations to perform while adapting the covariance matrix

    Returns:
    covariance [array like] : final adaptive covariance matrix reached 
    chain_states [array like]: array of scaled states visited
    chain_means [array like]: array of mean scaled states of the chain
    acceptance_history [array like]: array of accepted moves. 1 if the proposal was accepted, 0 otherwise.
    covariance_history [array like]: list of scaled states visited
    best_posterior [scalar]: best posterior density visited
    best_theta [array like]: array of scaled state that produced best_posterior
    '''

    if burns < 25:
        raise ValueError("Not enough iterations to safely establish an empirical covariance matrix")
    
    # initialise
    d = len(theta)

    I = np.identity(d)
    s = 2.4**2 / d # Arbitrary(ish), good value from Haario et al
    eps = 1e-12 # Needs to be smaller than the scale of parameter values


    acceptance_history = np.zeros((iterations + burns))
    acceptance_history[0] = 1 # first state (move) accepted

    chain_states = np.zeros((d, iterations + burns))
    chain_states[:, 0] = theta

    chain_means = np.zeros((d, iterations + burns))
    chain_means[:, 0] = theta
    
    covariance_history = [covariance]


    # initial values
    log_likelihood = Log_Likelihood(m, theta, priors, data)

    best_posterior = np.exp(log_likelihood + Log_Prior_Product(m, theta, priors))
    best_theta = theta


    for i in range(1, burns): # warm up walk to establish an empirical covariance
        # propose a new state and calculate the resulting likelihood and prior ratio
        proposed = Gaussian_Proposal(theta, covariance)
        log_likelihood_proposed = Log_Likelihood(m, proposed, priors, data)
        log_prior_ratio = Log_Prior_Ratio(m, m, theta, proposed, False, priors)

        if random.random() < np.exp(log_prior_ratio + log_likelihood_proposed - log_likelihood): # metropolis acceptance
            theta = proposed
            log_likelihood = log_likelihood_proposed
            acceptance_history[i] = 1 # accept proposal

            # store best state
            posterior_density = np.exp(log_likelihood_proposed + Log_Prior_Product(m, theta, priors))
            if best_posterior < posterior_density: 
                best_posterior = posterior_density
                best_theta = theta

        else: acceptance_history[i] = 0 # reject proposal
        
        # update storage
        chain_states[:, i] = theta
        chain_means[:, i] = (chain_means[:, i-1]*i + theta) / (i+1) # recursive mean
        covariance_history.append(covariance)

    # initilial empirical covaraince
    covariance = s * np.cov(chain_states[:, 0:burns]) + s*eps*I
    covariance_history.append(covariance)

    t = burns # global index

    for i in range(iterations): # adaptive walk

        # user feedback
        cf = i / (iterations-1);
        print(f'Best Score Function: {best_posterior:.4f}, Progress: [{"#"*round(50*cf)+"-"*round(50*(1-cf))}] {100.*cf:.2f}%\r', end='')

        # propose a new state and calculate the resulting likelihood and prior ratio
        proposed = Gaussian_Proposal(theta, covariance)
        log_likelihood_proposed = Log_Likelihood(m, proposed, priors, data)
        log_prior_ratio = np.exp(Log_Prior_Ratio(m, m, theta, proposed, False, priors))

        if random.random() < np.exp(log_prior_ratio + log_likelihood_proposed - log_likelihood): # metropolis acceptance
            theta = proposed
            log_likelihood = log_likelihood_proposed
            acceptance_history[t] = 1 # accept proposal

            # store best state
            posterior_density = np.exp(log_likelihood_proposed + Log_Prior_Product(m, theta, priors))
            if best_posterior < posterior_density:
                best_posterior = posterior_density
                best_theta = theta

        else: acceptance_history[t] = 0 # reject proposal
 
        chain_states[:, t] = theta
        chain_means[:, t] = (chain_means[:, t-1]*t + theta)/(t + 1) # recursive mean
        
        # adapt covraince iteratively
        covariance = (t-1)/t * covariance + s/(t+1) * np.outer(chain_states[:, t] - chain_means[:, t-1], chain_states[:, t] - chain_means[:, t-1]) + s*eps*I/t
        covariance_history.append(covariance)

        #if not check_symmetric(covariance, tol=1e-8):
        #    print('non symm cov')

        t += 1

    # performance
    print(f"\n Model: {m}, Accepted Move Fraction: {(np.sum(acceptance_history) / (iterations+burns)):4f}, Best Score Function: {best_posterior:.4f}")

    return covariance, chain_states, chain_means, acceptance_history, covariance_history, best_posterior, best_theta



def check_symmetric(A, tol = 1e-16):
    return np.all(np.abs(A-A.T) < tol)



def Gaussian_Proposal(theta, covariance):
    '''
    Takes a single step in a guassian walk process
    ----------------------------------------------
    theta [array like]: the scaled parameter values to step from
    covariance [array like]: the covariance with which to center the multivariate 
                guassian to propose from. Can be the diagonal entries only or a complete matrix

    Returns: [array like]: a new point in scaled parameter space
    '''
    return multivariate_normal.rvs(mean = theta, cov = covariance)



def Adaptive_RJ_Metropolis_Hastings_Proposal(m, m_prop, covariances, centers, theta, auxiliary_variables):
    '''
    Proposes a new point to jump to when doing RJMCMC using centreing points,
    in the context of single and binary microlensing events.
    --------------------------------------------
    m [int]: the index of the microlensing model to jump from (0 or 1, single or binary)
    m_prop [int]: the index of the microlensing model to jump to
    covariances [array like]: a list of the covariance for each model [single , binary]
    centers [array like]: a list of the parameter values of the centreing point for each model [single , binary]
    theta [array like]: the scaled parameter values in the associated model space to jump from
    auxilliary_variables [array like]: the stored values of the most recent binary state

    Returns: 
    theta_prop [array like]: a new point in the scaled parameter space a jump was proposed too
    g_ratio [scalar]: ratio of proposal distribution densities
    '''
    
    if m == m_prop: return Gaussian_Proposal(theta, covariances[m_prop]), 1 # intra-model move

    else: # inter-model move

        l = theta - centers[m] # offset from initial model's centre

        if m_prop == 0: # jump to single. Exclude non shared parameters.

            n_shared = D(m_prop)

            theta_prop = centers[m_prop] + l[:n_shared]  # map shared parameters without randomness


            covariance = covariances[m]  
            c_11 = covariance[:n_shared, :n_shared] # covariance matrix of (shared) dependent variables
            c_12 = covariance[:n_shared, n_shared:] # covariances, not variances
            c_21 = covariance[n_shared:, :n_shared] # same as above
            c_22 = covariance[n_shared:, n_shared:] # covariance matrix of independent variables
            c_22_inv = np.linalg.inv(c_22)
            conditioned_covariance = c_11 - c_12.dot(c_22_inv).dot(c_21)
            

            u = Gaussian_Proposal(np.zeros((n_shared)), conditioned_covariance)
            theta_prop = theta_prop + u # add randomness to jump

            #u = Gaussian_Proposal(np.zeros(6), covariances[m])
            #theta_prop = theta[:3]#theta_prop #+ u[:3] # add randomness to jump

            g_ratio = 1 # unity as symmetric forward and reverse jumps

            return theta_prop, g_ratio


        if m_prop == 1: # jump to binary. Include non shared parameters.

            n_shared = D(m)

            v = auxiliary_variables[n_shared:]
            h = l + centers[m_prop][:n_shared]

            theta_prop = np.concatenate((h, v)) # map without randomness


            covariance = covariances[m_prop]  
            c_11 = covariance[:n_shared, :n_shared] # covariance matrix of (shared) dependent variables
            c_12 = covariance[:n_shared, n_shared:] # covariances, not variances
            c_21 = covariance[n_shared:, :n_shared] # same as above
            c_22 = covariance[n_shared:, n_shared:] # covariance matrix of independent variables
            c_22_inv = np.linalg.inv(c_22)
            conditioned_covariance = c_11 - c_12.dot(c_22_inv).dot(c_21)


            u = Gaussian_Proposal(np.zeros((n_shared)), conditioned_covariance)
            theta_prop[:n_shared] = theta_prop[:n_shared] + u # add randomness to jump on shared parameters
            #u = Gaussian_Proposal(np.zeros(6), covariances[m_prop])
            #theta_prop = np.concatenate((theta, v))#theta_prop #+ u[:3] # add randomness to jump


            g_ratio = 1 # unity as symmetric forward and reverse jumps

            return theta_prop, g_ratio

    



def D(m):
    '''
    Helper function. Maps the model index to the associated 
    dimensionality in the context of microlensing.

    m == 0 -> single
    m == 1 -> binary 
    '''

    D = [3, 6]
    return D[m]



def unscale(theta):
    '''
    Helper function. Unscales the scaled parameter values for 
    input to muLensModel
    '''

    theta_unscaled = deepcopy(theta)
    #print(theta)
    if len(theta) == D(0): # no single parameters are scaled
        return theta_unscaled
    
    if len(theta) == D(1):
        theta_unscaled[3] = 10**theta_unscaled[3]
        #theta_unscaled[6] = theta_unscaled[6] * 180 / math.pi

        return theta_unscaled

    return



def scale(theta):
    '''
    Helper function. Scales the unscaled parameter values for 
    jumps through paramter space
    '''

    theta_scaled = deepcopy(theta)
    #print(theta)
    if len(theta) == D(0): # no single parameters are scaled
        return theta_scaled
    
    if len(theta) == D(1):
        theta_scaled[3] = np.log10(theta_scaled[3])
        #theta_scaled[6] = theta_scaled[6] * math.pi /180

        return theta_scaled

    return



def Log_Prior_Ratio(m, m_prop, theta, theta_prop, auxiliary_variables, priors):
    '''
    Calculates the ratio of the product of the priors of the proposed point to the
    initial point, in log units. Accounts for auxilliary variables.
    --------------------------------------------
    m [int]: the index of the microlensing model to jump from (0 or 1, single or binary)
    m_prop [int]: the index of the microlensing model to jump to
    theta [array like]: the scaled parameter values in the associated model space to jump from
    theta_prop [array like]: the scaled parameter values in the associated model space to jump too
    auxiliary_variables [array like / bool]: most recent binary state in scaled space
    priors [array like]: a list of prior distribution objects for the lensing parameters, 
                         in the order of entries in theta, in scaled space

    Returns
    log_prior_ratio [scalar]: log ratio of prior product of poposed and initial states
    '''
    
    log_product_numerator = Log_Prior_Product(m_prop, theta_prop, priors)
    log_product_denomenator = Log_Prior_Product(m, theta, priors)



    if m_prop != m: # adjust ratio with auxiliary variable product density for inter-model jumps
        aux_true_scale = unscale(auxiliary_variables)

        if m_prop < m:
            for parameter in range(D(m_prop), D(m)): # cycle through each auxiliary parameter and associated prior
                log_product_numerator += (priors[parameter].log_PDF(aux_true_scale[parameter])) # product using log rules

        if m < m_prop:
            for parameter in range(D(m), D(m_prop)): # cycle through each auxiliary parameter and associated prior
                log_product_denomenator += (priors[parameter].log_PDF(aux_true_scale[parameter])) # product using log rules


    log_prior_ratio = log_product_numerator - log_product_denomenator # ratio using log rules

    return log_prior_ratio



def Log_Prior_Product(m, theta, priors):
    '''
    Calculates the product of the priors for a model and state. 
    Does not accounts for auxilliary variables.
    --------------------------------------------
    m [int]: the index of the microlensing model to jump from (0 or 1, single or binary)
    theta [array like]: the scaled parameter values in the associated model space to jump from
    priors [array like]: a list of prior distribution objects for the lensing parameters, 
                         in the order of entries in theta, in scaled space

    Returns
    log_prior_ratio [scalar]: log ratio of prior product of poposed and initial states
    '''

    log_prior_product = 0.

    theta_true_scale = unscale(theta)

    for parameter in range(D(m)):
        log_prior_product += (priors[parameter].log_PDF(theta_true_scale[parameter])) # product using log rules

    return log_prior_product



def Log_Likelihood(m, theta, priors, data):
    '''
    Calculate the log likelihood that a lightcurve represents observed lightcurve data
    --------------------------------------------
    m [int]: the index of the microlensing model to jump from (0 or 1, single or binary)
    theta [array like]: the scaled parameter values in the associated model space to jump from
    priors [array like]: a list of prior distribution objects for the lensing parameters, 
                         in the order of entries in theta, in scaled space
    data [muLens data]: the data of the microlensing event to analyse

    Returns
    log_likelihood [scalar]: log likelihood parameters represent lightcuvre with model
    '''

    theta_true_scale = unscale(theta)

    # check if parameter is not in prior bounds, and ensure it is not accepted if so
    for parameter in range(D(m)):
        if not priors[parameter].in_Bounds(theta_true_scale[parameter]): return -Inf

    if m == 0:
        try: # for when moves are out of bounds of model valididty
            model = mm.Model(dict(zip(['t_0', 'u_0', 't_E'], theta_true_scale)))
            model.set_magnification_methods([0., 'point_source', 72.])

            a = model.magnification(data.time) #(model.magnification(data.time) - 1.0) * theta_true_scale[0] + 1.0 # compute parameter lightcurve with fs
            y = data.flux # flux signal
            
            A = np.vstack([a, np.ones(len(a))]).T
            f_s, f_b = np.linalg.lstsq(A, y, rcond = None)[0]
            F = f_s*a + f_b # least square signal
            
            #print(f_s, f_b)

            sd = data.err_flux # error
            chi2 = np.sum((y - F)**2/sd**2)

        except: # if a point is uncomputable, return true probability zero
            return -Inf

        return -chi2/2 # transform chi2 to log likelihood


    if m == 1:
        try: # check if parameter is not in prior bounds, and ensure it is not accepted if so
            model = mm.Model(dict(zip(['t_0', 'u_0', 't_E', 'q', 's', 'alpha'], theta_true_scale)))
            model.set_magnification_methods([0., 'point_source', 72.])

            a = model.magnification(data.time) #(model.magnification(data.time) - 1.0) * theta_true_scale[0] + 1.0  # compute parameter lightcurve with fs
            y = data.flux # signal

            A = np.vstack([a, np.ones(len(a))]).T
            f_s, f_b = np.linalg.lstsq(A, y, rcond = None)[0]
            F = f_s*a + f_b # least square signal

            #print(f_s, f_b)

            sd = data.err_flux # error
            chi2 = np.sum((y - F)**2/sd**2)

        except: # if a point is uncomputable, return true probability zero
            return -Inf
        
        return -chi2/2 # transform chi2 to log likelihood



def Run_Adaptive_RJ_Metropolis_Hastings\
(initial_states, initial_means, n_warmup_iterations, initial_covariances, centers, priors, iterations,  data):
    '''
    Performs Adaptive RJMCMC as described in thesis, in the context of microlensing events.
    --------------------------------------------
    initial_states [array like]: list of the final states in each warmup chain for each model (0 or 1, single or binary)
    initial_means [array like]: list of the means of each parameter in each warmup chain for each model (0 or 1, single or binary)
    n_warmup_iterations [int]: number of states in each warmup chain (0 or 1, single or binary)
    initial_covariances [array like]: list of the covariances as initialised from each warmup chain (0 or 1, single or binary)
    centers [array like]: list of the centreing points for each model (0 or 1, single or binary)
    priors [array like]: an array of prior distribution objects for the lensing parameters, in the order of entries in theta
    iterations [int]: how many iterations to perform
    data [muLens data]: the data of the microlensing event to analyse

    Returns:
    chain_states [array like]: array of scaled states visited
    chain_ms [array like]: array of mean scaled states of the chain
    best_posteriors [array like]: list of best posterior densities visited for each model
    best_thetas [array like]: list of scaled states that produced best_posteriors for each model
    covariances_history [array like]: list of covatainces for each model
    acceptance_history [array like]: list of accepted moves (0 if rejected, 1 if accepted)
    '''

    # initialise values
    ts = [n_warmup_iterations, n_warmup_iterations]
    I = [np.identity(D(0)), np.identity(D(1))] 
    s = [2.4**2 / D(0), 2.4**2 / D(1)] # Arbitrary(ish), good value from Haario et al
    eps = 1e-12 # Needs to be smaller than the scale of parameter values

    m = random.randint(0, 1) # choose initial model

    theta = initial_states[m] # final state in model's warmup chain
    auxiliary_variables = initial_states[1]
    log_likelihood = Log_Likelihood(m, theta, priors, data)

    # initialse storages
    best_posteriors = [-Inf, -Inf]
    best_posteriors[m] = np.exp(log_likelihood + Log_Prior_Product(m, theta, priors))
    best_thetas = [[], []]
    best_thetas[m] = theta

    chain_ms = np.zeros((iterations))
    chain_ms[0] = m
    chain_states = []
    chain_states.append(theta)
    chain_model_means = [initial_means[0], initial_means[1]] 

    intra_jump_acceptance_histories = [[], []]
    intra_jump_acceptance_histories[m].append(1) # first state counts as jump
    inter_jump_acceptance_histories = []

    acceptance_history = np.zeros((iterations))
    acceptance_history[0] = 1

    covariances = initial_covariances
    covariances_history = [[initial_covariances[0]], [initial_covariances[1]]]
    inter_cov_history = [initial_covariances[1]]



    print('Running Adpt-RJMH')
    for i in range(1, iterations): # loop through Adpt-RJMH steps
        
        #diagnostics
        cf = i / (iterations-1);
        print(f'Current: M {m+1} | Progress: [{"#"*round(50*cf)+"-"*round(50*(1-cf))}] {100.*cf:.2f}%\r', end='')

        m_prop = random.randint(0, 1) # since all models are equally likelly, this has no presence in the acceptance step

        #centers = [mean(), ]

        theta_prop, g_ratio = Adaptive_RJ_Metropolis_Hastings_Proposal(m, m_prop, covariances, centers, theta, auxiliary_variables)
        log_prior_ratio = Log_Prior_Ratio(m, m_prop, theta, theta_prop, auxiliary_variables, priors)
        log_likelihood_prop = Log_Likelihood(m_prop, theta_prop, priors, data)


        J = 1 # Jacobian of sampler
        acc_pi = np.exp(log_likelihood_prop - log_likelihood + log_prior_ratio) * g_ratio * J


        if random.random() <= acc_pi: # metropolis acceptance
            acceptance_history[i] = 1 # accept proposal
            
            if m == m_prop: 
                intra_jump_acceptance_histories[m_prop].append(1)
            else:
                inter_jump_acceptance_histories.append(1)
                inter_cov_history.append(covariances[1])

            theta = theta_prop
            m = m_prop
            
            log_likelihood = log_likelihood_prop

            if m_prop == 1: auxiliary_variables = theta_prop

            posterior_density = np.exp(log_likelihood_prop + Log_Prior_Product(m, theta, priors))
            if best_posteriors[m_prop] < posterior_density: # store best states
                best_posteriors[m_prop] = posterior_density
                best_thetas[m_prop] = theta_prop

        elif m == m_prop: 
            intra_jump_acceptance_histories[m_prop].append(0)
            acceptance_history[i] = 0 # reject move
        
        else:
            inter_jump_acceptance_histories.append(0)
            acceptance_history[i] = 0 # reject jump
            inter_cov_history.append(covariances[1])

        chain_states.append(theta)
        chain_ms[i] = m


        t = ts[m]
        
        covariances_history[m].append(covariances[m])
        covariances[m] = (t-1)/t*covariances[m] + s[m]/(t+1) * np.outer(theta-chain_model_means[m], theta-chain_model_means[m]) + s[m]*eps*I[m]/t

        # print('Is Symmetric?', check_symmetric(covariances[m], tol=1e-8))
        
        chain_model_means[m] = (chain_model_means[m]*t + theta) / (t+1)

        ts[m] += 1

    # performance:
    print("\nIterations: "+str(iterations))
    print("Accepted Move Fraction: " + str(np.sum(acceptance_history) / iterations))
    print("P(Singular|y): " + str(1-np.sum(chain_ms) / iterations))
    print("P(Binary|y): " + str(np.sum(chain_ms) / iterations))

    return chain_states, chain_ms, best_thetas, best_posteriors, covariances_history, acceptance_history, inter_jump_acceptance_histories, intra_jump_acceptance_histories, inter_cov_history



def Read_Light_Curve(file_name):
    '''
    Read in an existing lightcurve. Must be between 0 and 72 days, with 720 observations
    --------------------------------------------
    file_name [string]: csv file in three columns in same directory for light curve

    Returns:
    data [muLens data]: data for true light curve
    '''

    with open(file_name) as file:
        array = np.loadtxt(file, delimiter = ",")

    data = mm.MulensData(data_list = [array[:, 0], array[:, 1], array[:, 2]], phot_fmt = 'flux', chi2_fmt = 'flux')

    return data



def Synthetic_Light_Curve(true_theta, light_curve_type, n_epochs, signal_to_noise_baseline):
    '''
    Generate a synthetic lightcurve for some parameters and signal to noise ratio
    --------------------------------------------
    true_theta [array like]: parameters to generate curve from in unscaled space
    light_curve_type [int]: 0 (single) 1 (binary)
    n_epochs [int]: number of data points in curve
    signal_to_noise_baseline [scalar]: 

    Returns:
    data [muLens data]: data for synthetic light curve
    '''

    if light_curve_type == 0:
        model = mm.Model(dict(zip(['t_0', 'u_0', 't_E'], true_theta)))
        model.set_magnification_methods([0., 'point_source', 72.])

    elif light_curve_type == 1:
        model = mm.Model(dict(zip(['t_0', 'u_0', 't_E', 'q', 's', 'alpha'], true_theta)))
        model.set_magnification_methods([0., 'point_source', 72.])

    # exact signal
    epochs = np.linspace(0, 72, n_epochs + 1)[:n_epochs]
    true_signal = model.magnification(epochs) #(model.magnification(epochs) - 1.0) * true_theta[0] + 1.0 # adjust for fs

    np.random.seed(42)

    # simulate noise in gaussian errored flux space
    noise = np.random.normal(0.0, np.sqrt(true_signal) / signal_to_noise_baseline, n_epochs) 
    noise_sd = np.sqrt(true_signal) / signal_to_noise_baseline
    
    signal = true_signal + noise

    data = mm.MulensData(data_list = [epochs, signal, noise_sd], phot_fmt = 'flux', chi2_fmt = 'flux')

    return data



def Loop_Adaptive_Warmup(n, m, data, theta, priors, covariance, adaptive_warmup_iterations, adaptive_iterations):
    '''
    Repeat the adaptive mcmc warmup process used for each model in Adpt-RJMH
    and store the best run for use in Adpt-RJMH
    --------------------------------------------
    n [int]: number of repeats
    m [int]: the index of the microlensing model to use (0 or 1, single or binary)
    data [muLens data]: the data of the microlensing event to analyse
    theta [array like]: the unscaled parameter values in the associated model space to start from
    priors [array like]: an array of prior distribution objects for the lensing parameters, in same order as theta
    covariance [array like]: the covariance to initialise with when proposing a move. 
                             Can be the diagonal entries only or a complete matrix.
                             In the order of theta
    adaptive_warmup_iterations [int]: number of MCMC steps without adapting cov
    adaptive_iterations [int]: remaining number of MCMC steps

    Returns:
    inc_covariance [array like] : final adaptive covariance matrix reached 
    inc_chain_states [array like]: array of scaled states visited
    inc_chain_means [array like]: array of mean scaled states of the chain
    inc_acceptance_history [array like]: array of accepted moves. 1 if the proposal was accepted, 0 otherwise.
    inc_covariance_history [array like]: list of scaled states visited
    inc_best_posterior [scalar]: best posterior density visited
    inc_best_theta [array like]: array of scaled state that produced best_posterior
    '''

    inc_best_posterior = -Inf # initialise incumbent value to always get beaten

    for i in range(n):
        # run MCMC
        covariance, chain_states, chain_means, acceptance_history, covariance_history, best_posterior, best_theta = \
        Adaptive_Metropolis_Hastings(m, data, scale(theta), priors, covariance, adaptive_warmup_iterations, adaptive_iterations)

        # if best posterior density state is better than incumbent, update store
        if inc_best_posterior < best_posterior:
            inc_covariance, inc_chain_states, inc_chain_means, inc_acceptance_history, inc_covariance_history, inc_best_posterior, inc_best_theta = \
                covariance, chain_states, chain_means, acceptance_history, covariance_history, best_posterior, best_theta

    return inc_covariance, inc_chain_states, inc_chain_means, inc_acceptance_history, inc_covariance_history, inc_best_posterior, inc_best_theta
