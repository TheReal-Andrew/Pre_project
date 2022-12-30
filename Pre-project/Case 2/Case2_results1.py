# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 10:11:25 2022

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
import island_lib as il

ip.set_plot_options()

#%% Import results

# Optimal solutions for v2 and v3
bi_opt    = pypsa.Network('case2_bidirect.nc')
di_opt    = pypsa.Network('case2_direct.nc')

bi_MAA_1  = np.load('case_2bi_MAA_solutions_1pct.npy')
di_MAA_1  = np.load('case_2di_MAA_solutions_1pct.npy')

bi_MAA_10 = np.load('case_2bi_MAA_solutions_10pct.npy')
di_MAA_10 = np.load('case_2di_MAA_solutions_10pct.npy')

#%% MAA hulls in same plot
def make_hull2(sol1, sol10, n_optimal, name, title, loc = 'upper right',
              ylim = [None, None], xlim = [None, None]):
    
    x1, y1 = sol1[:,0], sol1[:,1]
    
    x10, y10 = sol10[:,0], sol10[:,1]
    
    fig = plt.figure(figsize = (10,5))
    
    colors = ['tab:blue', 'tab:red', 'tab:purple']
    
    i = 1
    for sol in [sol1, sol10]:
        hull = ConvexHull(sol)
        for simplex in hull.simplices:
            plt.plot(sol[simplex, 0], sol[simplex, 1], colors[i])
        i += 1
            
    plt.plot(x1, y1, 'o', label = "Near-optimal, mga = 0.01", color = 'tab:red')
    plt.plot(x10, y10, 'o', label = "Near-optimal, mga = 0.1", color = 'tab:purple')
    
    #Plot optimal
    plt.plot(n_optimal.links.p_nom_opt.loc['Island_to_Denmark'], 
             n_optimal.links.p_nom_opt.loc['Island_to_Belgium'],
              '.', markersize = 20, label = "Optimal",
              color = 'tab:blue')
    plt.xlabel("Island to DK link capacity [MW]")
    plt.ylabel("Island to BE link capacity [MW]")
    plt.ylim(ylim)
    plt.xlim(xlim)
    plt.suptitle(title, fontsize = 22, y = 1)
    plt.title('Near-feasible space, with mga slack of 0.1 and 0.01', fontsize = 14)
    plt.legend(loc = loc)
    
    fig.savefig(name, format = 'pdf', bbox_inches='tight')
    
make_hull2(bi_MAA_1, bi_MAA_10, bi_opt, 'bi_case.pdf', 'MAA analysis of bidirectional links',
           ylim = [-1000, 25000], xlim = [-1000, 73000])

make_hull2(di_MAA_1, di_MAA_10, di_opt, 'di_case.pdf', 'MAA analysis of directional links',
           ylim = [-1000, 25000], xlim = [-1000, 73000])