# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 10:44:50 2022

@author: lukas
"""

import pypsa
import numpy as np
import matplotlib as plt
import cartopy.crs as ccrs
import pandas as pd
from makeplots1 import makeplots

#%% Set up network & bus info -------------------------------------

network = pypsa.Network()       #Create network
n_steps = np.arange(0, 100)     #Define number of timesteps
network.set_snapshots(n_steps)  #Set snapshots of network to the timesteps

#Create dataframe with info on buses. Names, x (Longitude) and y (Latitude) 
bus_df = pd.DataFrame(
    np.array([                     # Create numpy array with bus info
    ["Island",       6.68, 56.52], #
    ["Thorsminde",   8.12, 56.37], #
    ["Norway",       8.02, 58.16], #Assumed Kristiansand
    ["Germany",      8.58, 53.54], #Assumed Bremerhaven
    ["Netherlands",  6.84, 53.44], #Assumed Eemshaven
    ["Belgium",      3.20, 51.32], #Assumed Zeebrugge
    ["Britain",     -1.45, 55.01], #Assumed North Shield
    ]), 
    columns = ["Name", "x", "y"]   # Give columns titles
    )

#%% Add buses -----------------------------------------------------
#Adding busses from bus_info to network
for i in range(bus_df.shape[0]): #i becomes integers
    network.add(            #Add component
        "Bus",              #Component type
        bus_df.Name[i],     #Component name
        x = bus_df.x[i], #Longitude (for plotting)
        y = bus_df.y[i], #Latitude (for plotting)
        )

#%% Add links -----------------------------------------------------

#List of link destionations from buses
link_destinations = network.buses.index.values

for i in link_destinations: #i becomes each string in the array
    network.add(            #Add component
        "Link",             #Component type
        "Island to " + i,   #Component name
        bus0 = "Island",    #Start Bus
        bus1 = i,           #End Bus
        p_nom = 200         #Power capacity of link
        )

#%% Add Generators -------------------------------------------------

# Prepare wind and load series
sin_wind = (np.sin(n_steps) + 1)/2
#cos_load = ((np.cos(n_steps/4) + 1)/2)

#Add wind turbine
network.add(
    "Generator",          #Component type
    "Wind",               #Component name
    bus = "Island",       #Bus on which component is
    p_nom = 2000,         #Nominal power [MW]
    p_max_pu = sin_wind,  #time-series of power coefficients
    marginal_cost = 0.1   #Cost per MW from this source 
    )

#%% Add stores
network.add(
    "Store",          #Component type
    "Store1",         #Component name
    bus = "Island",   #Bus on which component is
    e_nom = 2000,       #Store capacity
    e_initial = 0,    #Initially stored energy
    e_cyclic = True   #Set store to always end and start at same energy
    )


#%% Add Loads ------------------------------------------------------

for i in range(1, bus_df.shape[0]-1):
    network.add(
        "Load",
        "Load " + bus_df.Name[i],
        bus   = bus_df.Name[i],
        p_set = ((np.cos(n_steps/(2+0.2*i)) + 1)/2)*(50*(1+i*0.4)), 
        )

#%% Plotting -------------------------------------------------------

# Geographical map
plt.rc("figure", figsize=(15, 15))  #Set plot resolution

network.plot(
    color_geomap = True,              #Coloring on oceans
    boundaries = [-3, 12, 59, 50.5],  #Boundaries of the plot as [x1,x2,y1,y2]
    projection=ccrs.EqualEarth()      #Choose cartopy.crs projection
    )

network.lopf() #Solve dynamic system

makeplots(network) #Plot dynamic results