# Author: Dominic Keehan
# Part 4 Project, RJMCMC for Microlensing

import MulensModel as mm
import source
import autocorrelation_functions as acf
import plot_functions as pltf
import random
import numpy as np
import matplotlib.pyplot as plt
import NN_interfaceing as NN
from copy import deepcopy

import time



def P_m2(event_params):

    #-----------
    ## INPUTS ##
    #-----------

    adapt_MH_warm_up = 5 #25 # mcmc steps without adaption
    adapt_MH = 995 #475 # mcmc steps with adaption
    initial_n = 1 #5 # times to repeat mcmc optimisation of centers to try to get better estimate
    iterations = 1000 # rjmcmc steps

    truncate = False # automatically truncate burn in period based on autocorrelation of m

    n_epochs = 720
    epochs = np.linspace(0, 72, n_epochs + 1)[:n_epochs]
    use_NN = True
    sn_base = 23 #(230-23)/2 + 23 # np.random.uniform(23.0, 230.0) # lower means noisier

    #---------------
    ## END INPUTS ##
    #---------------

    ## INITIALISATION ##

    data = source.synthetic_binary(event_params, n_epochs, sn_base)

    # SET PRIORS
    # priors in truth space informative priors (Zhang et al)
    t0_pi = source.Uniform(0, 72)
    u0_pi = source.Uniform(0, 2)
    tE_pi = source.Truncated_Log_Normal(1, 100, 10**1.15, 10**0.45)
    q_pi = source.Log_Uniform(10e-6, 1)
    s_pi = source.Log_Uniform(0.2, 5)
    alpha_pi = source.Uniform(0, 360)
    priors = [t0_pi, u0_pi, tE_pi, q_pi, s_pi, alpha_pi]


    # GET CENTERS
    if use_NN == True:

        # centreing points for inter-model jumps
        single_center = source.State(truth = NN.get_model_centers(NN.get_posteriors(0), data.flux))
        fin_rho = NN.get_model_centers(NN.get_posteriors(1), data.flux)
        binary_center = source.State(truth = np.array([fin_rho[0], fin_rho[1], fin_rho[2], fin_rho[4], fin_rho[5], fin_rho[6]]))

    else: # use known values for centers 

        binary_center = source.State(truth = np.array(event_params.truth))
        single_center = source.State(truth = np.array(event_params.truth[:3]))

    #single_center = source.State(truth = NN.get_model_centers(NN.get_posteriors(0), data.flux))

    # MODEL COVARIANCES
    # initial covariances (diagonal)
    covariance_scale = 0.001 # reduce diagonals by a multiple
    single_covariance = np.zeros((3, 3))
    np.fill_diagonal(single_covariance, np.multiply(covariance_scale, [1, 0.1, 1]))
    binary_covariance = np.zeros((6, 6))
    np.fill_diagonal(binary_covariance, np.multiply(covariance_scale, [1, 0.1, 1, 0.1, 0.1, 10]))

    # MODELS
    single_Model = source.Model(0, 3, single_center, priors, single_covariance, data, source.single_log_likelihood)
    binary_Model = source.Model(1, 6, binary_center, priors, binary_covariance, data, source.binary_log_likelihood)
    Models = [single_Model, binary_Model]

    start_time = (time.time())
    joint_model_chain = source.adapt_RJMH(Models, adapt_MH_warm_up, adapt_MH, initial_n, iterations, user_feedback=True)

    P_m2 = binary_Model.sampled.n/joint_model_chain.n

    return P_m2




theta = [36, 0.1, 61.5, 0.01, 0.2, 25]
n = 1
s_pi = source.Log_Uniform(0.2, 5)
s_range = np.linspace(0.5, 3.0, n)
density_s = []
P_m2_s =[]

for i in range(n):
    s = s_range[i]
    theta_s = deepcopy(theta)
    theta_s[4] = s
    event_params = source.State(truth = theta_s)

    P_m2_s.append(P_m2(event_params))

    density_s.append(np.exp(s_pi.log_pdf(s)))

    pltf.amplification(1, event_params, [0, 72], label = 's='+str(s), color = plt.cm.autumn(i/n))
    single_projection = source.State(truth = event_params.truth[:3])
    pltf.amplification(0, single_projection, [0, 72], label = 'single, s='+str(s), color = plt.cm.winter(i/n))

plt.legend()
plt.xlabel('Time [days]')
plt.ylabel('Magnification')
plt.tight_layout()
plt.savefig('Plots/EPm2.png')
plt.clf()

print(P_m2_s)
print(density_s)
EPM2 = sum([a*b for a,b in zip(P_m2_s, density_s)])/sum(density_s)
sdEPM2 = sum([(a-EPM2)**2*b for a,b in zip(P_m2_s, density_s)])/sum(density_s)**0.5
print(EPM2)
print(sdEPM2)

