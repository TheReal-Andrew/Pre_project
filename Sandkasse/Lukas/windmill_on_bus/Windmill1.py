# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 11:19:27 2022

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

n_timesteps = 4             #Define number of timesteps

network = pypsa.Network()   #Create PyPSA network

#Add bus
network.add("Bus",          #Component Type
            "My Bus",       #Component name
            )

network.set_snapshots(      #Set up snapshots of unitless time
    range(n_timesteps)
    ) 

#%% Add generators

#Add wind turbine
network.add(
    "Generator",                    #Component type
    "Wind (0.1)",                   #Component name
    bus = "My Bus",                 #Bus on which component is
    p_nom = 30,                     #Nominal power [MW]
    p_max_pu = [0.1, 1, 0.4, 0.2],  #time-series of power coefficients
    marginal_cost = 0.1             #Cost per MW from this source 
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
    marginal_cost = 0.5
    )

#%% Add loads
   
#Add dynamic load
network.add(
    "Load",              #Component type
    "Load1",             #Component name
    bus = "My Bus",      #Bus on which component is
    p_set = [15,20,4,20] #Time-series of load [MW]
    )

#%% Add stores
    
#Add store
network.add(
    "Store",        #Component type
    "Store1",       #Component name
    bus = "My Bus", #Bus on which component is
    e_nom = 5,      #Store capacity
    e_initial = 0   #Initially stored energy
    )

#%% Solve system

network.lopf() #Solve dynamic system
        
makeplots(network) #Plot dynamic results


