#%% Import
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 10:44:50 2022

@author: Lukas & Anders
"""

import pypsa
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import pandas as pd
import island_lib as il #Library with data and calculation functions 
import island_plt as ip #Library with plotting functions.

# Load Data price and load data
cprice, cload = il.get_load_and_price(2030)

# Load wind CF
cf_wind_df = pd.read_csv(r'Data/Wind/wind_test.csv')

#Load link info
link_cost_url = 'https://github.com/PyPSA/technology-data/blob/master/inputs/manual_input.csv?raw=true'
link_cost     = pd.read_csv(link_cost_url)
link_inv      = link_cost.loc[link_cost['parameter'].str.startswith('investment') & link_cost['technology'].str.startswith('HVDC submarine')]
link_life     = link_cost.loc[link_cost['parameter'].str.startswith('lifetime') & link_cost['technology'].str.startswith('HVDC submarine')]
link_FOM      = link_cost.loc[link_cost['parameter'].str.startswith('FOM') & link_cost['technology'].str.startswith('HVDC submarine')]

#%% Set up network & bus info -------------------------------------

network = pypsa.Network()       #Create network
t = pd.date_range('2019-01-01 00:00', '2019-12-31 23:00', freq = 'H')
network.set_snapshots(t)  #Set snapshots of network to the timesteps

#Create dataframe with info on buses. Names, x (Longitude) and y (Latitude) 
bus_df = pd.DataFrame(
    np.array([                                #Create numpy array with bus info
    ["Island",          "EI",   6.68, 56.52], #Energy Island
    ["Denmark",         "DK",   8.12, 56.37], #Assumed Thorsminde
    ["Norway",          "NO",   8.02, 58.16], #Assumed Kristiansand
    ["Germany",         "DE",   8.58, 53.54], #Assumed Bremerhaven
    ["Netherlands",     "NL",   6.84, 53.44], #Assumed Eemshaven
    ["Belgium",         "BE",   3.20, 51.32], #Assumed Zeebrugge
    ["United Kingdom",  "GB",  -1.45, 55.01], #Assumed North Shield
    ]), 
    columns = ["Country", "Abbreviation", "X", "Y"]   #Give columns titles
    )

#%% Add buses -----------------------------------------------------
#Adding busses from bus_info to network
for i in range(bus_df.shape[0]):    #i becomes integers
    network.add(                    #Add component
        "Bus",                      #Component type
        bus_df.Country[i],          #Component name
        x = bus_df.X[i],            #Longitude (for plotting)
        y = bus_df.Y[i],            #Latitude (for plotting)
        )

#%% Add links -----------------------------------------------------

#List of link destionations from buses
link_destinations = network.buses.index.values

for i in link_destinations[1:]:     #i becomes each string in the array
    network.add(                    #Add component
        "Link",                     #Component type
        "Island_to_" + i,           #Component name
        bus0    = "Island",         #Start Bus
        bus1    = i,                #End Bus
        carrier = "DC",             #Define carrier type
        p_min_pu = -1,              #Make links bi-directional
        p_nom   = 200,              #Power capacity of link
        p_nom_extendable = True,    #Extendable links
        capital_cost = link_inv.loc[link_inv['year'] == 2030].value,         
        )

#%% Add Generators -------------------------------------------------

#Add wind turbine
network.add(
    "Generator",          #Component type
    "Wind",               #Component name
    bus = "Island",       #Bus on which component is
    p_nom = 3000,         #Nominal power [MW]
    p_max_pu = cf_wind_df['CF'],         #time-series of power coefficients
    carrier = "Wind",
    marginal_cost = 0.1   #Cost per MW from this source 
    )

#Add generators to each country bus with varying marginal costs
for i in range(1, bus_df.shape[0]):
    network.add(
        "Generator",
        "Gen_" + bus_df.Country[i],
        bus   = bus_df.Country[i],
        p_nom = 0, 
        p_nom_extendable = True,     #Make sure country can always deliver to price
        capital_cost = 0,            #Same as above
        marginal_cost = cprice[bus_df.Abbreviation[i]].values,
        )


#%% Add stores
network.add(
    "Store",          #Component type
    "Store1",         #Component name
    bus = "Island",   #Bus on which component is
    e_nom = 3000,        #Store capacity
    e_initial = 0,    #Initially stored energy
    e_cyclic = True,  #Set store to always end and start at same energy
    #e_nom_extendable = True, #Allow expansion of capacity
    #e_nom_max = 3000,
    )


#%% Add Loads ------------------------------------------------------

# Add varying cos loads to each country bus
for i in range(1, bus_df.shape[0]): #i becomes integers
    network.add(
        "Load",
        "Load_" + bus_df.Country[i],
        bus   = bus_df.Country[i],
        p_set = cload[bus_df.Abbreviation[i]].values, 
        )

network.add(
    "Load",
    "Datacenter Load",
    bus = "Island",
    p_set = 1000,
    )

#%% Plotting -------------------------------------------------------

# Geographical map
plt.rc("figure", figsize=(15, 15))    #Set plot resolution

network.plot(
    color_geomap = True,              #Coloring on oceans
    boundaries = [-3, 12, 59, 50.5],  #Boundaries of the plot as [x1,x2,y1,y2]
    projection=ccrs.EqualEarth()      #Choose cartopy.crs projection
    )

#%% Solver

#network.lopf(pyomo = False) #Solve dynamic system

ip.makeplots(network) #Plot dynamic results

#%% Plotting
# plt.plot(figsize = (14,7))
# plt.figure(dpi=300)         # Set resolution

network.links_t.p0.iloc[:,1].plot(
    figsize = (14,7),
    label = "Island to DK",)

network.links_t.p0.iloc[:,2].plot(
    figsize = (14,7),
    label = "Island to NO",)

network.links_t.p0.iloc[:,3].plot(
    figsize = (14,7),
    label = "Island to DE",)

plt.legend()
plt.ylabel("Power flow [MW]")
plt.title("Power flow from Island to countries")