import numpy as np

from consav.grids import equilogspace
from consav.markov import log_rouwenhorst

def prepare_hh_ss(model):
    """ prepare the household block to solve for steady state """

    par = model.par
    ss = model.ss

    ############
    # 1. grids #
    ############
    
    # a. beta
    par.beta_grid[:] = np.linspace(par.beta_mean-par.beta_delta,par.beta_mean+par.beta_delta,par.Nbeta)

    # b. a
    par.a_grid[:] = equilogspace(0.0,ss.w*par.a_max,par.Na)
    
    # c. z
    par.z_grid[:],z_trans,z_ergodic,_,_ = log_rouwenhorst(par.rho_z,par.sigma_psi,par.Nz)

    #############################################
    # 2. transition matrix initial distribution #
    #############################################
    
    for i_beta in range(par.Nbeta):
        ss.z_trans[i_beta,:,:] = z_trans
        ss.Dbeg[i_beta,:,0] = z_ergodic/par.Nbeta
        ss.Dbeg[i_beta,:,1:] = 0.0

    ################################################
    # 3. initial guess for intertemporal variables #
    ################################################

    model.set_hh_initial_guess() # calls .solve_hh_backwards() with ss=True

def find_ss(model,do_print=False):
    """ find the steady state """

    par = model.par
    ss = model.ss

    # a. exogenous and targets
    ss.L = 1.0 # normalization
    ss.r = par.r_ss_target
    ss.w = par.w_ss_target

    assert (1+ss.r)*par.beta_mean < 1.0, '(1+r)*beta < 1, otherwise problems might arise'

    # b. stock and capital stock from household behavior
    model.solve_hh_ss(do_print=do_print) # give us sol.a and sol.c
    model.simulate_hh_ss(do_print=do_print) # give us sim.D, ss.A_hh and ss.C_hh 
    if do_print: print('')

    ss.A = ss.K_lag = ss.K = ss.A_hh
    
    # c. back technology and depreciation rate
    ss.Gamma = ss.w / ((1-par.alpha)*(ss.K/ss.L)**par.alpha)
    ss.rk = par.alpha*ss.Gamma*(ss.K/ss.L)**(par.alpha-1)
    par.delta = ss.rk - ss.r

    # d. produktion and investment
    ss.Y = ss.Gamma*ss.K**par.alpha*ss.L**(1-par.alpha)
    ss.I = par.delta*ss.K

    # e. market clearing
    ss.clearing_A = ss.A-ss.A_hh
    ss.clearing_L = ss.L-ss.L_hh
    ss.clearing_Y = ss.Y-ss.C_hh-ss.I

    # f. print
    if do_print:

        print(f'Implied K = {ss.K:6.3f}')
        print(f'Implied Y = {ss.Y:6.3f}')
        print(f'Implied Gamma = {ss.Gamma:6.3f}')
        print(f'Implied delta = {par.delta:6.3f}') # check is positive
        print(f'Implied K/Y = {ss.K/ss.Y:6.3f}') 
        print(f'Discrepancy in A = {ss.clearing_A:12.8f}') # = 0 by construction
        print(f'Discrepancy in L = {ss.clearing_L:12.8f}') # = 0 by construction
        print(f'Discrepancy in Y = {ss.clearing_Y:12.8f}') # != 0 due to numerical error 
