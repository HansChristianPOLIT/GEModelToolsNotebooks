
import numpy as np
from EconModel import EconModelClass
from GEModelTools import GEModelClass

from grids import create_grids
from household_problem import solve_hh_ss, solve_hh_path
from steady_state import find_ss
from transition_path import evaluate_transition_path

class HANKModelClass(EconModelClass,GEModelClass):
    
    #########
    # setup #
    #########      

    def settings(self):
        """ fundamental settings """

        # a. namespaces
        self.namespaces = ['par','sol','sim','ss','path','jac_hh']
        
        # b. other attributes (to save them)
        self.other_attrs = ['grids_hh','pols_hh','inputs_hh','inputs_exo','inputs_endo','targets','varlist_hh','varlist','jac']

        # household
        self.grids_hh = ['a'] # grids
        self.pols_hh = ['a'] # policy functions

        self.inputs_hh = ['r','w'] # inputs to household problem
        self.outputs_hh = ['a','c'] # output of household problem

        self.varlist_hh = ['a','m','c','Va'] # variables in household problem

        # GE
        self.inputs_exo = ['Z'] # exogenous inputs
        self.inputs_endo = ['K'] # endogenous inputs

        self.targets = ['clearing_A'] # targets
        
        self.varlist = [ # all variables
            'Z',
            'Y',
            'A_hh',
            'A',
            'K',
            'L',
            'C_hh',
            'C',
            'clearing_A',
            'clearing_C',
            'rk',
            'r',
            'w',
        ]

        # c. savefolder
        self.savefolder = 'saved'
        
        # d. list not-floats for safe type inference
        self.not_floats = ['Nbeta']

    def setup(self):
        """ set baseline parameters """

        par = self.par

        # a. macros
        pass

        # b. preferences
        par.sigma = 2.0 # CRRA coefficient
        par.beta_mean = 0.9875 # discount factor, mean, range is [mean-width,mean+width]
        par.beta_delta = 0.00000 # discount factor, width, range is [mean-width,mean+width]
        par.Nbeta = 1 # discount factor, number of states

        # c. income parameters
        par.rho_z = 0.95 # AR(1) parameter

        par.sigma_z = 0.30*(1.0-par.rho_z**2.0)**0.5 # std. of persistent shock
        par.Nz = 7 # number of productivity states

        # d. production and investment
        par.alpha = 0.36 # cobb-douglas
        par.delta = 0.032 # depreciation

        # e. calibration
        par.r_ss_target = 0.01 # target for real interest rate
        par.w_ss_target = 1.0 # target for real wage

        # h. grids         
        par.a_max = 500.0 # maximum point in grid for a
        par.Na = 300 # number of grid points

        # i. shocks
        par.jump_Z = -0.01 # initial jump in %
        par.rho_Z = 0.8

        # j. misc.
        par.transition_T = 500 # length of path        
        
        par.max_iter_solve = 50_000 # maximum number of iterations when solving
        par.max_iter_simulate = 50_000 # maximum number of iterations when simulating
        par.max_iter_broyden = 100 # maximum number of iteration when solving eq. system
        
        par.tol_solve = 1e-10 # tolerance when solving
        par.tol_simulate = 1e-10 # tolerance when simulating
        par.tol_broyden = 1e-8 # tolerance when solving eq. system
        
    def allocate(self):
        """ allocate model """

        par = self.par

        # a. grids
        par.beta_grid = np.zeros(par.Nbeta)
        
        # b. solution
        sol_shape = (par.Nbeta,par.Nz,par.Na)
        self.allocate_GE(sol_shape)
