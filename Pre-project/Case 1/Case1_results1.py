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

n_1a_MAA_10 = np.load('case 1a - constraint\case_1a_MAA_solutions_10pct.npy')
n_1b_MAA_10 = np.load('case 1b - no constraint\case_1b_MAA_solutions_10pct.npy')

#%% Pieplot

def make_pie(n, name, title, area1, area2):

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
    
    pie_data = [P2X_A, Data_A, Store_A]
    k        = [k_P2X, k_Data, k_Store] 
    labels   =  "P2X", "Data", "Store"
    
    fig, ax = plt.subplots(figsize = (6,6))
    ax.pie(pie_data, 
           # labels = labels,
           # autopct = '%1.1f%%',
           autopct = autopct_format(pie_data, k),
           textprops={'fontsize': 10},
           startangle=90)
    # fig.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    ax.axis('equal')
    ax.margins(0, 0)
    plt.suptitle(title, fontsize = 18)
    plt.title(area1 + '\n' +f'Area used: {total_A:.0f} m$^2$     ' + area2,
              fontsize = 10,
               pad = 6)
    plt.legend(labels = labels)
    
    fig.savefig(name, format = 'pdf', bbox_inches='tight')
    
make_pie(n_1a_opt, 'pie_1a.pdf', 
         title = '1a - Share of area by technology',
         area1 = 'With area constraint', 
         area2 = 'Max area: 120000 m$^2$')

make_pie(n_1b_opt, 'pie_1b.pdf', 
         title = '1b - Share of area by technology',
         area1 = 'Without area constraint', 
         area2 = 'Max area: No limit')

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
    plt.plot(n_optimal.generators.p_nom_opt["P2X"], 
             n_optimal.generators.p_nom_opt["Data"],
              '.', markersize = 20, label = "Optimal",
              color = 'tab:blue')
    plt.xlabel("P2X capacity [MW]")
    plt.ylabel("Data capacity [MW]")
    plt.ylim(ylim)
    plt.xlim(xlim)
    plt.suptitle(title, fontsize = 22, y = 1)
    plt.title('Near-feasible space, with mga slack of 0.1 and 0.01', fontsize = 14)
    plt.legend(loc = loc)
    
    fig.savefig(name, format = 'pdf', bbox_inches='tight')
    
make_hull2(n_1a_MAA, n_1a_MAA_10, n_1a_opt, 'MAA_1a_1_10.pdf', 
           title = '1a - MAA analysis with area constraint', loc = 'lower center',
           ylim = [None, 600], 
            # xlim = [800, 3000],
           )

make_hull2(n_1b_MAA, n_1b_MAA_10, n_1b_opt, 'MAA_1b_1_10.pdf',
           title = '1b - MAA analysis without area constraint', loc = 'lower center',
           ylim = [None, 600],
            # xlim = [800, 3000],
           )

make_hull2(n_1a_MAA, n_1a_MAA_10, n_1a_opt, 'MAA_1a_z.pdf', 
           title = '1a - MAA Zoomed', loc = 'lower center',
           ylim = [None, 600], 
            xlim = [800, 3000],
           )

make_hull2(n_1b_MAA, n_1b_MAA_10, n_1b_opt, 'MAA_1b_z.pdf',
           title = '1b - MAA Zoomed', loc = 'lower center',
           ylim = [None, 600],
            xlim = [800, 3000],
           )

#%% Table

n1 = n_1a_opt
P2X_p_1a   = n1.generators.loc["P2X"].p_nom_opt
Data_p_1a  = n1.generators.loc["Data"].p_nom_opt
Store_p_1a = n1.stores.loc["Store1"].e_nom_opt

P2X_A_1a   = k_P2X * P2X_p_1a
Data_A_1a  = k_Data * n1.generators.loc["Data"].p_nom_opt
Store_A_1a = k_Store * n1.stores.loc["Store1"].e_nom_opt

total_A_1a = P2X_A_1a + Data_A_1a + Store_A_1a
n1_cost    = n1.objective

n2 = n_1b_opt
P2X_p_1b   = n2.generators.loc["P2X"].p_nom_opt
Data_p_1b  = n2.generators.loc["Data"].p_nom_opt
Store_p_1b = n2.stores.loc["Store1"].e_nom_opt

P2X_A_1b   = k_P2X * P2X_p_1b
Data_A_1b  = k_Data * n2.generators.loc["Data"].p_nom_opt
Store_A_1b = k_Store * n2.stores.loc["Store1"].e_nom_opt

total_A_1b = P2X_A_1b + Data_A_1b + Store_A_1b
n2_cost    = n2.objective


total_c   = ((total_A_1b - total_A_1a)/total_A_1b) * 100
P2X_A_c   = ((P2X_A_1b - P2X_A_1a)/P2X_A_1b) * 100
Data_A_c  = ((Data_A_1b - Data_A_1a)/Data_A_1b) * 100
Store_A_c = ((Store_A_1b - Store_A_1a)/Store_A_1b) * 100
cost_c    = ((n2_cost - n1_cost)/n2_cost) * 100

# total_c   = ((total_A_1a - total_A_1b)/total_A_1a) * 100
# P2X_A_c   = ((P2X_A_1a - P2X_A_1b)/P2X_A_1a) * 100
# Data_A_c  = ((Data_A_1a - Data_A_1b)/Data_A_1a) * 100
# Store_A_c = ((Store_A_1a - Store_A_1b)/Store_A_1a) * 100
# cost_c    = ((n1_cost - n2_cost)/n1_cost) * 100

data = np.array([[total_A_1b, n2_cost, P2X_A_1b, Data_A_1b, Store_A_1b], 
                 [total_A_1a, n1_cost, P2X_A_1a, Data_A_1a, Store_A_1a],
                 [total_c   , cost_c , P2X_A_c , Data_A_c , Store_A_c]])


pd.options.display.float_format = '{:.2f}'.format

table = pd.DataFrame(
    data    = data,
    columns = ['Total Area [m2]', 'System cost [Euro]', 'P2X Area [m2]', 'Data Area [m2]', 'Store Area [m2]'],
    index   = ['Case 1b', 'Case 1a', 'Change [\%]'],
    )

pd.reset_option('display.float_format')

#%% Sound
il.its_britney_bitch(r'C:\Users\lukas\Documents\GitHub\NorthSeaEnergyIsland\Data\Sounds')