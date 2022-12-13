#%% Info
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 12:17:52 2022

@author: lukas
"""

import pypsa
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import cartopy.crs as ccrs
import pandas as pd
import island_lib as il #Library with data and calculation functions 
import island_plt as ip #Library with plotting functions.
import os

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

#%% Data

cprice, cload = il.get_load_and_price(2030)

cf_wind_df = pd.read_csv(r'Data/Wind/wind_test.csv', sep = ",")

#%% Network

n = pypsa.Network()

t = pd.date_range('2030-01-01 00:00', '2030-12-31 23:00', freq = 'H')
n.set_snapshots(t)

n.madd("Bus",
       ["Island", 'DK', 'BE'],
       )

n.madd("Link",
       ["L1", 'L2'],
       bus0  = ['Island', 'Island'],
       bus1 = ['DK', 'BE'],
       p_nom_extendable = True,
       p_min_pu = -1,
       )

n.add("Generator",
      "Wind1",
      bus = "Island",
      p_nom = 3000,
      p_max_pu = cf_wind_df['electricity'].values)

n.lopf(pyomo = False,
       solver_name = 'gurobi'
       )