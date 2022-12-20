# -*- coding: utf-8 -*-
"""
Created on Sun Dec 18 13:58:06 2022

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

#%% Import data
k_P2X   = 60  # [m^2/MW] Area use for P2X
mc_P2X  = 10  # [EUR/MW] Gain for system for P2X
cc_P2X  = 100 # [EUR/MW] Capital cost for P2X

k_Data  = 20  # [m^2/MW] Area use for Data
mc_Data = 15  # [EUR/MW] Gain for system for Data
cc_Data = 110 # [EUR/MW] Capital cost for Data

k_Store  = 2.3  # [m^2/MW] Area use for Storage
cc_Store = 0.36 # [EUR/MWh] Capital cost for Storage

mga_slack = 0.01

#%% Import results

# Optimal solutions for v2 and v3
n_1a_opt = pypsa.Network('case 1a - constraint\case_1a_opt.nc')
n_1b_opt = pypsa.Network('case 1b - no constraint\case_1b_opt.nc')

n_1a_MAA = np.load('case 1a - constraint\case_1a_MAA_solutions.npy')
n_1b_MAA = np.load('case 1b - no constraint\case_1b_MAA_solutions.npy')

#%% Pieplot

def make_pie(n, name):
    
    def autopct_format(values, k):
        def my_format(pct):
            total = sum(values)
            val = int(round(pct*total/100.0))
            return '{:.1f}%\n({v:d} m$^2$)'.format(pct, v=val)
        return my_format
    
    P2X_p   = n.generators.loc["P2X"].p_nom_opt
    Data_p  = n.generators.loc["Data"].p_nom_opt
    Store_p = n.stores.loc["Store1"].e_nom_opt
    
    P2X_A   = k_P2X * P2X_p
    Data_A  = k_Data * n.generators.loc["Data"].p_nom_opt
    Store_A = k_Store * n.stores.loc["Store1"].e_nom_opt
    
    total_A = P2X_A + Data_A + Store_A
    print(f" \n Area used on the island: {total_A} \n")
    
    pie_data = [P2X_A, Data_A, Store_A]
    k        = [k_P2X, k_Data, k_Store] 
    labels   =  "P2X", "Data", "Store"
    
    fig, ax = plt.subplots(figsize = (10,5))
    ax.pie(pie_data, labels = labels,
           # autopct = '%1.1f%%',
           autopct = autopct_format(pie_data, k),
           textprops={'fontsize': 10})
    plt.suptitle('Share of area by technology', fontsize = 18)
    plt.title(f'Area used: {total_A:.0f} m$^2$', fontsize = 10)
    plt.legend()
    
    fig.savefig(name, format = 'eps', bbox_inches='tight')
    
make_pie(n_1a_opt, 'pie_1a.eps')

make_pie(n_1b_opt, 'pie_1b.eps')

#%% Plot MAA

def make_hull(solutions, n_optimal, mga_slack, name):
    hull = ConvexHull(solutions)
    
    fig = plt.figure(figsize = (10,5))
    
    x = solutions[:,0]
    y = solutions[:,1]
    
    for simplex in hull.simplices:
        plt.plot(solutions[simplex, 0], solutions[simplex, 1], 'k-')
    
    plt.plot(x, y,
             'o', label = "Near-optimal")
    
    #Plot optimal
    plt.plot(n_optimal.generators.p_nom_opt["P2X"], 
             n_optimal.generators.p_nom_opt["Data"],
              '.', markersize = 20, label = "Optimal")
    plt.xlabel("P2X capacity [MW]")
    plt.ylabel("Data capacity [MW]")
    plt.ylim([325, 575])
    plt.suptitle('MAA Analysis of island without area constraint', fontsize = 22, y = 1)
    plt.title(f'With MGA slack = {mga_slack}', fontsize = 14)
    
    plt.legend(loc = 'center right')
    
    fig.savefig(name, format = 'eps', bbox_inches='tight')
    
make_hull(n_1a_MAA, n_1a_opt, mga_slack, 'MAA_1a.eps')

make_hull(n_1b_MAA, n_1b_opt, mga_slack, 'MAA_1b.eps')

#%% Sound
il.its_britney_bitch(r'C:\Users\lukas\Documents\GitHub\NorthSeaEnergyIsland\Data\Sounds')