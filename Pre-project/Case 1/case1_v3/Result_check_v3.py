# -*- coding: utf-8 -*-
"""
Created on Sat Dec 17 19:11:59 2022

@author: lukas
"""

#%% Import
import pypsa 
import numpy as np
from pypsa.linopt import get_var, linexpr, join_exprs, define_constraints, get_dual, get_con, write_objective, get_sol, define_variables
from pypsa.descriptors import nominal_attrs
from pypsa.linopf import lookup, network_lopf, ilopf
from pypsa.pf import get_switchable_as_dense as get_as_dense
from pypsa.descriptors import get_extendable_i, get_non_extendable_i
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
from scipy.spatial import ConvexHull
import os
import sys
import island_plt as ip

ip.set_plot_options()

#%% Import network

#import results
n = pypsa.Network('01_case1_v3_res_3.nc')
n_opt = pypsa.Network('case1_v3.nc')
solutions = np.load('case1_v3_MAA_solutions.npy')


#%% Plot
hull = ConvexHull(solutions)

plt.figure()

DK = solutions[:,0]
DE = solutions[:,1]

for simplex in hull.simplices:

    plt.plot(solutions[simplex, 0], solutions[simplex, 1], 'k-')

plt.plot(DK, DE,
         'o', label = "near-optimal")

#Plot optimal
plt.plot(n_opt.generators.p_nom_opt["P2X"], 
         n_opt.generators.p_nom_opt["Data"],
          '.', markersize = 20, label = "optimum")
plt.xlabel("P2X")
plt.ylabel("Data")
