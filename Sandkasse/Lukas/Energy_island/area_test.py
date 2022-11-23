#%% Info
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 22 14:40:56 2022

@author: lukas
"""

#%% Import
import pypsa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from pypsa.linopt import get_var, get_dual, linexpr, join_exprs, define_constraints

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

#Add wind generator
n.add("Generator",
      "Wind",
      bus = "Island",
      carrier = "wind",
      p_nom = 3000,
      p_max_pu = cf_wind_df['electricity'].values,
      marginal_cost = 2.7,
      )

n.add("Generator",
      "Coal1",
      bus = "Island",
      carrier = "Coal",
      p_nom_extendable = True,
      marginal_cost = 10,
      )

#Dummy load
n.add("Load",
      "DummyLoad",
      bus = "Island",
      p_set = 1000,
      )

# #Dummy store
# n.add("Store",
#       "DummyStore",
#       bus = "Island",
#       e_nom_extendable = True,
#       e_nom_max = 10000
#       )

#Add "loads" in the form of negative generators
n.add("Generator",
      "P2X",
      bus = "Island",
      p_nom_extendable = True,
      p_max_pu = 0,
      p_min_pu = -1,
      marginal_cost = 30,
      )

n.add("Generator",
      "Data",
      bus = "Island",
      p_nom_extendable = True,
      p_max_pu = 0,
      p_min_pu = -1,
      marginal_cost = 10,
      )

#%% Extra functionality
def area_constraint(n, snapshots):
    vars_gen = get_var(n, 'Generator', 'p_nom')
    
    k1 = 10
    k2 = 15
    
    lhs = linexpr((k1, vars_gen["P2X"]), (k2, vars_gen["Data"]))
    
    rhs = 10000
    
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

#%%



