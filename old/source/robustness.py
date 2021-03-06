"""Analyse the robustness of the ARJMH algorithm.

Calculates the expected marginalised binary model probability of some ambiguous 
light curves.
"""

import sampling
import light_curve_simulation
import distributions
import autocorrelation as acf
import plotting as pltf
import random
import numpy as np
import matplotlib.pyplot as plt
import surrogate_posteriors
from copy import deepcopy

import time




def P_m2(event_params, single_centre, binary_centre, sn_base, n_epochs):
    """Calculate the marginalised binary model probability of a specific light curve.

    Args:
        event_params: [list] Single lens model parameters.
        sn_base: [float] Signal to noise baseline of data.
        n_epochs: [int] Number of observations.

    Returns:
        P_m2: [float] Marginalised binary model probability.
    """


    """User Settings"""

    # Warm up parameters.
    fixed_warm_up_iterations = 25#25
    adaptive_warm_up_iterations = 975#975
    warm_up_repititions = 2#2

    # Algorithm parameters.
    iterations = 10000#20000

    # Output parameters.
    truncate = False # Truncate a burn in period based on IACT.
    user_feedback = True

    """Sampling Process"""

    # Informative priors in true space (Zhang et al).
    t0_pi = distributions.Uniform(0, 72)
    u0_pi = distributions.Uniform(0, 2)
    tE_pi = distributions.Truncated_Log_Normal(1, 100, 10**1.15, 10**0.45)
    q_pi = distributions.Log_Uniform(10e-6, 1)
    s_pi = distributions.Log_Uniform(0.2, 5)
    alpha_pi = distributions.Uniform(0, 360)
    priors = [t0_pi, u0_pi, tE_pi, q_pi, s_pi, alpha_pi]



    # Generate synthetic light curve. Could otherwise use f.Read_Light_Curve(file_name).
    data = light_curve_simulation.synthetic_single(event_params, n_epochs, sn_base)

    # Initial diagonal covariances.
    covariance_scale = 0.001 # Reduce values by scalar
    single_covariance = np.zeros((3, 3))
    np.fill_diagonal(single_covariance, np.multiply(covariance_scale, [1, 0.1, 1]))
    binary_covariance = np.zeros((6, 6))
    np.fill_diagonal(binary_covariance, np.multiply(covariance_scale, [1, 0.1, 1, 0.1, 0.1, 10]))

    # Models.
    single_Model = sampling.Model(0, 3, single_centre, priors, single_covariance, data, light_curve_simulation.single_log_likelihood)
    binary_Model = sampling.Model(1, 6, binary_centre, priors, binary_covariance, data, light_curve_simulation.binary_log_likelihood)
    Models = [single_Model, binary_Model]

    # Run algorithm.
    start_time = (time.time())
    random.seed(42)
    joint_model_chain, total_acc, inter_model_history = sampling.ARJMH(Models, iterations, adaptive_warm_up_iterations, fixed_warm_up_iterations, warm_up_repititions, user_feedback)
    duration = (time.time() - start_time)/60
    print(duration, ' minutes')
    single_Model, binary_Model = Models

    P_m2 = np.sum(joint_model_chain.model_indices)/joint_model_chain.n

    return P_m2


if __name__ == "__main__":
    """Expectation Process
    
    This runs in two stages, first calculating the centre for every light curve
    and writing this to a file, then reading that file to calculate each expectation.
    """

    n = 5 # Number of samples in expectation.
    global_i = 0

    # Parameter range to vary.
    theta = [36, 1.0, 5.5]
    tE_pi = distributions.Truncated_Log_Normal(1, 100, 10**1.15, 10**0.45)
    tE_range = np.linspace(2, 10, n)
    n_epochs = [720, 360, 72]  # Cadence to calculate expectations at.
    sn_bases = [23, 126.5, 230]  # Noise to calculate expectations at.
    
    write_surrogate_centers = False

    if write_surrogate_centers == True:
        single_centres = np.zeros((n*3*3,3))
        binary_centres = np.zeros((n*3*3,6))
        with open("results/robustness-centers.npy", "wb") as centre_file:
                for sn_base in sn_bases:
                    for i in range(n): # Samples in expectation.
                        tE = tE_range[i]

                        # Create new light curve.                
                        theta_tE = deepcopy(theta)
                        theta_tE[2] = tE
                        event_params = sampling.State(truth = theta_tE)

                        # Generate synthetic light curve for SP. Could otherwise use f.Read_Light_Curve(file_name).
                        sp_data = light_curve_simulation.synthetic_single(event_params, 720, sn_base)

                        # Get initial centre points.
                        single_centre = surrogate_posteriors.maximise_posterior(surrogate_posteriors.posterior(0), sp_data.flux)
                        for sn_i in range(3):
                            single_centres[global_i+sn_i*n][:] = single_centre

                        fin_rho = surrogate_posteriors.maximise_posterior(surrogate_posteriors.posterior(1), sp_data.flux)
                        # Remove finite source size parameter from neural network.
                        binary_centre = np.array([fin_rho[0], fin_rho[1], fin_rho[2], fin_rho[4], fin_rho[5], fin_rho[6]])
                        for sn_i in range(3):
                            binary_centres[global_i+sn_i*n][:] = binary_centre

                        global_i += 1
                    global_i += (3-1)*n

                np.save(centre_file, single_centres)
                np.save(centre_file, binary_centres)

    global_i = 0

    with open("results/robustness-centers.npy", "rb") as centre_file:
        single_centres = np.load(centre_file)
        binary_centres = np.load(centre_file)

    #print(single_centres)

    if write_surrogate_centers == False:
        with open("results/robustness-run.txt", "w") as out_file:
                    for sn_base in sn_bases:
                        for n_epoch in n_epochs:
                            
                            # Initialise for current expectation.
                            prior_density = []
                            binary_probability =[]

                            for i in range(n): # Samples in expectation.
                                tE = tE_range[i]
                                prior_density.append(np.exp(tE_pi.log_pdf(tE)))

                                # Create new light curve and run ARJMH.                
                                theta_tE = deepcopy(theta)
                                theta_tE[2] = tE
                                event_params = sampling.State(truth = theta_tE)

                                single_centre = sampling.State(truth=single_centres[global_i])
                                binary_centre = sampling.State(truth=binary_centres[global_i])

                                binary_probability.append(P_m2(event_params, single_centre, binary_centre, sn_base, n_epoch))

                                # Prior density weighted expectation and standard deviation. 
                                EPM2 = sum([a*b for a,b in zip(binary_probability, prior_density)])/sum(prior_density)
                                sdEPM2 = (sum([(a-EPM2)**2*b for a,b in zip(binary_probability, prior_density)])/sum(prior_density))**0.5

                                global_i += 1
                            
                            # Store expectation.
                            out_file.write("n_epochs: "+str(n_epoch)+" sn_base: "+str(sn_base)+" E: "+str(EPM2)+" sd+-: "+str(sdEPM2)+"\n")
