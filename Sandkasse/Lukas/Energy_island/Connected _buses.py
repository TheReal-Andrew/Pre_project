# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 10:44:50 2022

@author: lukas
"""

import pypsa
import numpy as np
import matplotlib as plt
import cartopy.crs as ccrs

#%% Set up network & bus info -------------------------------------

network = pypsa.Network()

#Info on buses. Names, x (Longitude) and y (Latitude) 
bus_info = np.array([
    ["Island",       6.68, 56.52], #
    ["Thorsminde",   8.12, 56.37], #
    ["Norway",       8.02, 58.16], #Assumed Kristiansand
    ["Germany",      8.58, 53.54], #Assumed Bremerhaven
    ["Netherlands",  6.84, 53.44], #Assumed Eemshaven
    ["Belgium",      3.20, 51.32], #Assumed Zeebrugge
    ["Britain",     -1.45, 55.01], #Assumed North Shield
    ])

#%% Add buses -----------------------------------------------------
#Adding busses from bus_info to network
for i in range(bus_info.shape[0]): #i becomes integers
    network.add(            #Add component
        "Bus",              #Component type
        bus_info[i][0],     #Component name
        x = bus_info[i][1], #Longitude (for plotting)
        y = bus_info[i][2], #Latitude (for plotting)
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
        p_nom = 30          #Power capacity of link
        )

#%% Plotting -------------------------------------------------------

# Geographical map
plt.rc("figure", figsize=(15, 15))  #Set plot resolution

network.plot(
    color_geomap = True,              #Coloring on oceans
    boundaries = [-3, 12, 59, 50.5],  #Boundaries of the plot as [x1,x2,y1,y2]
    projection=ccrs.EqualEarth()      #Choose cartopy.crs projection
    )