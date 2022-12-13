#%% Info
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 22 14:40:56 2022

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


#%% Control

n_hrs = 8760

#%% Build network and import

#Build network
n = pypsa.Network()
t = pd.date_range('2030-01-01 00:00', '2030-12-31 23:00', freq = 'H')[:n_hrs]
n.set_snapshots(t)

#Import data
cf_wind_df = pd.read_csv(r'Data/Wind/wind_test.csv',index_col = [0], sep=",")[:n_hrs]

#%% Add components

#Add bus for the island
n.add("Bus", "Island")

# #Add wind generator
n.add("Generator",
      "Wind",
      bus = "Island",
      carrier = "wind",
      p_nom = 3000,
      p_max_pu = cf_wind_df['electricity'].values,
      marginal_cost = 10,
      )

n.add("Generator",
      "Coal1",
      bus = "Island",
      carrier = "Coal",
      p_nom_extendable = True,
      marginal_cost = 30,
      )

#Dummy load
n.add("Load",
      "DummyLoad",
      bus = "Island",
      p_set = 1000,
      )

# Store
n.add("Store",
      "Store1",
      bus = "Island",
      e_cyclic = True,
      e_nom_extendable = True,
      e_nom_max = 10000,
      standing_loss = 0.1,
      # marginal_cost = 5, #System Cost
      )

#Add "loads" in the form of negative generators
n.add("Generator",
      "P2X",
      bus = "Island",
      p_nom_extendable = True,
      p_nom_max = 10000,
      p_max_pu = 0,
      p_min_pu = -1,
      marginal_cost = 15, #System Gain
      )

n.add("Generator",
      "Data",
      bus = "Island",
      p_nom_extendable = True,
      p_nom_max = 10000,
      p_max_pu = -1,
      p_min_pu = -1,
      marginal_cost = 16, #System Gain
      )

#%% Extra functionality
def area_constraint(n, snapshots):
    vars_gen   = get_var(n, 'Generator', 'p_nom')
    vars_store = get_var(n, 'Store', 'e_nom')
    
    k1 = 20 # P2X   [m^2/MW]
    k2 = 19 # Data  [m^2/MW]
    k3 = 21 # Store [m^2/MW]
    
    lhs = linexpr((k1, vars_gen["P2X"]), 
                  (k2, vars_gen["Data"]), 
                  (k3, vars_store))
    
    rhs = 10000 #[m^2]
    
    define_constraints(n, lhs, '=', rhs, 'Generator', 'Area_Use')

def extra_functionalities(n, snapshots):
    area_constraint(n, snapshots)

#%% Solve
n.lopf(pyomo = False,
       solver_name = 'gurobi',
       keep_shadowprices = True,
       keep_references = True,
       extra_functionality = extra_functionalities,
       )

#%% Plot area use
k1 = 20 #[m^2/MW] For P2X
k2 = 19 #[m^2/MW] For Data
k3 = 21 #[m^2/MW] For Storage

P2X_A   = k1 * n.generators.loc["P2X"].p_nom_opt
Data_A  = k2 * n.generators.loc["Data"].p_nom_opt
Store_A = k3 * n.stores.loc["Store1"].e_nom_opt

plt.bar('Area use', P2X_A, label = "P2X")
plt.bar('Area use', Data_A, bottom = P2X_A, label = "Data")
plt.bar('Area use', Store_A, bottom = P2X_A+Data_A, label = "Storage")

plt.ylabel('m^2')
plt.legend()


