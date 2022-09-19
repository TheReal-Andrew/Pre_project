# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 09:22:58 2022

@author: lukas
"""


import pypsa
import numpy as np
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
plt.rc("figure", figsize=(12, 12))

from makeplots1 import makeplots

#%% Set up network

network = pypsa.Network() #Create PyPSA network

ntimesteps = 5           #Define number of timesteps
network.set_snapshots(    #Set up snapshots of unitless time
    range(ntimesteps)
    ) 

#%% Add buses

network.add(    #Add component
    "Bus",      #Component type
    "Island",   #Component name
    x = 6.68,   #Longitude (for plotting)
    y = 56.52   #Latitude (for plotting)
    )  

network.add(
    "Bus",
    "Thorsminde",
    x = 8.12,
    y = 56.37
    )

#%% Add links

network.add(
    "Link",
    "Link1",
    bus0 = "Island",
    bus1 = "Thorsminde",
    p_nom = 30
    )


#%% Add generators

#Add wind turbine
network.add(
    "Generator",                          #Component type
    "Wind (0.1)",                         #Component name
    bus = "Island",                       #Bus on which component is
    p_nom = 30,                           #Nominal power [MW]
    p_max_pu = [1, 0.2, 0.8, 0.9, 0.3], #time-series of power coefficients
    marginal_cost = 0.1                   #Cost per MW from this source 
    )

#%% Add loads

network.add(
    "Load",
    "Load1",
    bus = "Thorsminde",
    p_set = [0, 2, 4, 1, 2]
    )

#%% Add Store

#Add store
network.add(
    "Store",        #Component type
    "Store1",       #Component name
    bus = "Island", #Bus on which component is
    e_nom = 50,      #Store capacity
    e_initial = 0   #Initially stored energy
    )


#%% Solving

network.lopf()

#%% Plotting

network.plot(
    margin = 1,
    color_geomap = True,
    boundaries = [-2, 13, 61, 50],
    projection=ccrs.EqualEarth()
    )

makeplots(network)

