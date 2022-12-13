#%% Info
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 09:44:48 2022

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
import island_lib as il
from scipy.spatial import ConvexHull
import os
import sys

#%% Plotting options
#Set up plot parameters
color_bg      = "0.99"          #Choose background color
color_gridaxe = "0.85"          #Choose grid and spine color
rc = {"axes.edgecolor":color_gridaxe} 
plt.style.use(('ggplot', rc))           #Set style with extra spines
plt.rcParams['figure.dpi'] = 300        #Set resolution
plt.rcParams["figure.figsize"] = (10, 5) #Set figure size
matplotlib.rcParams['font.family'] = ['cmss10']     #Change font to Computer Modern Sans Serif
plt.rcParams['axes.unicode_minus'] = False          #Re-enable minus signs on axes))
plt.rcParams['axes.facecolor']= "0.99"              #Set plot background color
plt.rcParams.update({"axes.grid" : True, "grid.color": color_gridaxe}) #Set grid color
plt.rcParams['axes.grid'] = True

#%% CONTROL ------------------------------------

Should_export = True
Should_solve  = True
Should_pie    = True
n_hrs = 8760

filename = "/case1_v2.nc"

# Area affecting parameters
k_P2X   = 60  # [m^2/MW] Area use for P2X
mc_P2X  = 10  # [EUR/MW] Gain for system for P2X
cc_P2X  = 100 # [EUR/MW] Capital cost for P2X

k_Data  = 20  # [m^2/MW] Area use for Data
mc_Data = 15  # [EUR/MW] Gain for system for Data
cc_Data = 110 # [EUR/MW] Capital cost for Data

k_Store  = 7  # [m^2/MW] Area use for Storage
cc_Store = 80 # [EUR/MW] Capital cost for Storage

cc_Wind = il.get_annuity(0.07, 30) * 1.8e6 # [Euro/MW]

#%%  NETWORK -----------------------------------

#Build network
n = pypsa.Network()
t = pd.date_range('2030-01-01 00:00', '2030-12-31 23:00', freq = 'H')[:n_hrs]
n.set_snapshots(t)

#Import data
cf_wind_df = pd.read_csv(r'Data/Wind/wind_test.csv',index_col = [0], sep=",")[:n_hrs]


####### Components #######

#Add bus for the island
n.add("Bus", "Island")

#Add wind generator
n.add("Generator",
      "Wind",
      bus               = "Island",
      carrier           = "wind",
      p_nom_extendable  = True,
      p_nom_min         = 3000,
      p_nom_ma          = 3000,
      p_max_pu          = cf_wind_df['electricity'].values,
      marginal_cost     = 0,
      capital_cost      = cc_Wind
      )

#Add storage
n.add("Store",
      "Store1",
      bus               = "Island",
      carrier           = "Store1",
      e_nom_extendable  = True,
      e_cyclic          = True,
      e_nom_max         = 1000,
      capital_cost      = cc_Store,
      )

#Add "loads" in the form of negative generators
n.add("Generator",
      "P2X",
      bus               = "Island",
      carrier           = "P2X",
      p_nom_extendable  = True,
      p_max_pu          = 0,
      p_min_pu          = -1,
      marginal_cost     = mc_P2X,
      capital_cost      = cc_P2X,
      )

n.add("Generator",
      "Data",
      bus               = "Island",
      carrier           = "Data",
      p_nom_extendable  = True,
      p_max_pu          = -0.99,
      p_min_pu          = -1,
      marginal_cost     = mc_Data,
      capital_cost      = cc_Data
      )

#%% Extra functionality
def area_constraint(n, snapshots):
    vars_gen   = get_var(n, 'Generator', 'p_nom')
    vars_store = get_var(n, 'Store', 'e_nom')
    
    lhs = linexpr((k_P2X,   vars_gen["P2X"]), 
                  (k_Data,  vars_gen["Data"]), 
                  (k_Store, vars_store))
    
    rhs = 10000 #[m^2]
    
    define_constraints(n, lhs, '=', rhs, 'Generator', 'Area_Use')

def extra_functionalities(n, snapshots):
    area_constraint(n, snapshots)

#%% EXPORT
if Should_export:
    filename = filename
    export_path = os.getcwd() + filename
    n.export_to_netcdf(export_path)
else:
    pass

#%% SOLVE

if Should_solve:
    n.lopf(pyomo = False,
           solver_name = 'gurobi',
           keep_shadowprices = True,
           keep_references = True,
           extra_functionality = extra_functionalities,
           )
else:
    pass

#%% Plot area use

if Should_pie:
    P2X_A   = k_P2X * n.generators.loc["P2X"].p_nom_opt
    Data_A  = k_Data * n.generators.loc["Data"].p_nom_opt
    Store_A = k_Store * n.stores.loc["Store1"].e_nom_opt
    
    pie_data = [P2X_A, Data_A, Store_A]
    labels   =  "P2X", "Data", "Store"

    fig, ax = plt.subplots()
    ax.pie(pie_data, labels = labels, autopct='%1.1f%%')
    ax.set_title('Share of area by technology')
    plt.legend()
else:
    pass