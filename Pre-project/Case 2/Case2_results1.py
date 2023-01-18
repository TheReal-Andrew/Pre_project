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

#%%
n_res0 = pypsa.Network('case_2di_res_0.nc')
n_res1 = pypsa.Network('case_2di_res_1.nc')
n_res2 = pypsa.Network('case_2di_res_2.nc')
n_res3 = pypsa.Network('case_2di_res_3.nc')
n_res4 = pypsa.Network('case_2di_res_4.nc')
n_res5 = pypsa.Network('case_2di_res_5.nc')
n_res6 = pypsa.Network('case_2di_res_6.nc')
n_res7 = pypsa.Network('case_2di_res_7.nc')
n_res8 = pypsa.Network('case_2di_res_8.nc')
n_res9 = pypsa.Network('case_2di_res_9.nc')
n_res10 = pypsa.Network('case_2di_res_10.nc')
n_res11 = pypsa.Network('case_2di_res_11.nc')
n_res12 = pypsa.Network('case_2di_res_12.nc')

#%%
for i in [n_res0, n_res1, n_res2, n_res3, n_res4, n_res5, n_res6, n_res7, n_res8, n_res9, n_res10, n_res11, n_res12]:
    print(i.links.p_nom_opt)

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

make_hull2(di_MAA_1, di_MAA_10, di_opt, 'di_case_z.pdf', 'MAA analysis of directional links - Zoomed',
           ylim = [-200, 500], xlim = [-50, 500])

#%% Table



data = {'Direct'  : [di_opt.objective,
                     di_opt.links.p_nom_opt['Island_to_Denmark'],
                     di_opt.links.p_nom_opt['Island_to_Belgium']],
        'Bidirect': [bi_opt.objective,
                     bi_opt.links.p_nom_opt['Island_to_Denmark'],
                     bi_opt.links.p_nom_opt['Island_to_Belgium']],
        }

cost_c = ((data['Bidirect'][0] - data['Direct'][0])/data['Direct'][0]) * 100
DK_c   = ((data['Bidirect'][1] - data['Direct'][1])/data['Direct'][1]) * 100
BE_c   = ((data['Bidirect'][2] - data['Direct'][2])/data['Direct'][2]) * 100

data['Change [%]'] = [cost_c, DK_c, BE_c]

pd.options.display.float_format = '{:.2f}'.format

table = pd.DataFrame(
    data    = data,
    index   = ['System Cost [€]', 'DK Link Capacity [MW]',
               'BE Link Capacity [MW]',
               # 'Change [\%]',
               ],
    )