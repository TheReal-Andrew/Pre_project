# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 09:22:53 2022

@author: lukas
"""

#%% Import
import pypsa
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import plotly.io as pio

from makeplots1 import makeplots

#%% Set up network

n_steps   = np.arange(0, 40)   #Define number of timesteps

network = pypsa.Network()       #Create PyPSA network

#Add bus
network.add("Bus",              #Component Type
            "My Bus",           #Component name
            )

network.set_snapshots( #Set up snapshots of unitless time 
    n_steps          
    ) 

#%% Prepare wind and load series

sin_wind = (np.sin(n_steps) + 1)/2

cos_load = ((np.cos(n_steps) + 1)/2)*20

#%% Add generators

#Add wind turbine
network.add(
    "Generator",          #Component type
    "Wind (0.1)",         #Component name
    bus = "My Bus",       #Bus on which component is
    p_nom = 50,           #Nominal power [MW]
    p_max_pu = sin_wind,  #time-series of power coefficients
    marginal_cost = 0.1   #Cost per MW from this source 
    )

#Add coal plant with high cost per MWH and high nominal power
network.add(
    "Generator",
    "Coal (1)",
    bus = "My Bus", 
    p_nom = 12,
    marginal_cost = 1
    )

#Add coal plant with low cost per MWH and medium nominal power
network.add(
    "Generator",
    "Coal2 (0.5)",
    bus = "My Bus", 
    p_nom = 20,
    marginal_cost = 0.2
    )

#%% Add loads
   
#Add dynamic load
network.add(
    "Load",            #Component type
    "Load1",           #Component name
    bus = "My Bus",    #Bus on which component is
    p_set = cos_load   #Time-series of load [MW]
    )

#%% Add stores
    
#Add store
network.add(
    "Store",          #Component type
    "Store1",         #Component name
    bus = "My Bus",   #Bus on which component is
    e_nom = 10,       #Store capacity
    e_initial = 10    #Initially stored energy
    )

#%% Solve system

network.lopf() #Solve dynamic system
        
makeplots(network) #Plot dynamic results