"""
Created on Tue Sep  6 10:44:50 2022

@author: Lukas & Anders
"""

import sys
sys.path.append("../../")
from Modules import island_lib as il #Library with plotting functions.
from Modules import island_plt as ip #Library with plotting functions.
import pypsa
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import pandas as pd
import os

n_points = 8760

# Load power-price and consumer-load data
cprice, cload = il.get_load_and_price(2030)

# cprice = cprice[:n_points]
# cload  = cload[:n_points]

# Load wind capacity factor (CF)
cf_wind_df = pd.read_csv(r'../../Data/Wind/wind_formatted.csv', sep = ",")

#Load technology data
tech_cost = pd.read_csv('https://github.com/PyPSA/technology-data/blob/master/inputs/manual_input.csv?raw=true')
tech_inv  = tech_cost.loc[tech_cost['parameter'].str.startswith('investment') & tech_cost['technology'].str.startswith('HVDC submarine')]
tech_life = tech_cost.loc[tech_cost['parameter'].str.startswith('lifetime') & tech_cost['technology'].str.startswith('HVDC submarine')]
tech_FOM  = tech_cost.loc[tech_cost['parameter'].str.startswith('FOM') & tech_cost['technology'].str.startswith('HVDC submarine')]

#%% Set up network with chosen timesteps
network = pypsa.Network()                   
t = pd.date_range('2030-01-01 00:00', '2030-12-31 23:00', freq = 'H')
network.set_snapshots(t)  #Set snapshots of network to the timesteps

#Create dataframe with info on buses. Names, x (Longitude) and y (Latitude) 
bus_df = pd.DataFrame(
    np.array([                          #Create numpy array with bus info
    ["Island",  "EI",   6.68, 56.52],   #Energy Island
    ["Denmark", "DK",   8.12, 56.37],   #Assumed Thorsminde
    ["Belgium", "BE",   3.20, 51.32]]), #Assumed Zeebrugge 
    columns = ["Country",               #Give columns titles
               "Abbreviation", 
               "X", 
               "Y"])

#%% Add buses -----------------------------------------------------
#Adding busses from bus_info to network
for i in range(bus_df.shape[0]):    #i becomes integers
    network.add(                    #Add component
        "Bus",                      #Component type
        bus_df.Country[i],          #Component name
        x = bus_df.X[i],            #Longitude (for plotting)
        y = bus_df.Y[i])            #Latitude (for plotting)

#%% Add links -----------------------------------------------------

#List of link destionations from buses
link_destinations = network.buses.index.values

DR = 1.2
j = 0
for i in link_destinations[1:]:         #i becomes each string in the array
    j = j + 1
    network.add(                        #Add component
        "Link",                         #Component type
        "Island_to_" + i,               #Component name
        bus0             = "Island",    #Start Bus
        bus1             = i,           #End Bus
        carrier          = "DC" + str(j),        #Define carrier type
        p_min_pu         = -1,          #Make links bi-directional
        p_nom            = 0,           #Power capacity of link
        p_nom_extendable = True,        #Extendable links
        capital_cost     = il.get_annuity(0.07, float(tech_life.value))    #Annuity factor
                            * float(tech_inv.value)                        #Investment cost [EUR/MW/km] 
                            * DR
                            * il.earth_distance(float(bus_df.X.loc[0]),  
                                                float(bus_df.X.loc[j]), 
                                                float(bus_df.Y.loc[0]), 
                                                float(bus_df.Y.loc[j])))

#%% Add Generators -------------------------------------------------

#Add wind turbine
network.add(
    "Generator",                        #Component type
    "Wind",                             #Component name
    bus           = "Island",           #Bus on which component is
    p_nom         = 3000,               #Nominal power [MW]
    p_max_pu      = cf_wind_df['electricity'].values, #Time-series of power coefficients
    carrier       = "Wind",             #Carrier type (AC,DC,Wind,Solar,etc.)
    marginal_cost = 20)                 #Cost per MW from this source 
    
#%% Add Generators -------------------------------------------------

#Add generators to each country bus with varying marginal costs
for i in range(1, bus_df.shape[0]):
    network.add(
        "Generator",
        "Gen_" + bus_df.Country[i],
        bus              = bus_df.Country[i],
        p_nom            = 0, 
        p_nom_extendable = True,         #Make sure country can always deliver to price
        capital_cost     = 0,            #Same as above
        marginal_cost    = cprice[bus_df.Abbreviation[i]].values
        )

#%% Add Loads ------------------------------------------------------

# Add loads to each country bus
for i in range(1, bus_df.shape[0]): #i becomes integers
    network.add(
        "Load",
        "Load_" + bus_df.Country[i],
        bus     = bus_df.Country[i],
        p_set   = cload[bus_df.Abbreviation[i]].values)       
   
#%% Save network

filename = '/case2_setup.nc'
export_path = os.getcwd() + filename
network.export_to_netcdf(export_path)

#%% Plotting -------------------------------------------------------

# Geographical map
plt.rc("figure", figsize=(15, 15))    #Set plot resolution

network.plot(
    color_geomap = True,              #Coloring on oceans
    boundaries = [-3, 12, 59, 50.5],  #Boundaries of the plot as [x1,x2,y1,y2]
    projection=ccrs.EqualEarth()      #Choose cartopy.crs projection
    )

#%% Solver
network.lopf(pyomo = False,
             solver_name = 'gurobi')

#%%
fig_PF, ax_PF = plt.subplots(1, 2, figsize=(16*2,9), dpi=300)

ax_PF[0].plot(network.links_t.p0.iloc[:,0])
ax_PF[1].plot(network.links_t.p0.iloc[:,1])

#%%
# ip.plot_powerflow(network) #Plot dynamic results

#%% Plotting
# plt.plot(figsize = (16*2,9))
# plt.figure(dpi=300)         # Set resolution

# network.links_t.p0.iloc[:,1].plot(
#     figsize = (16*2,9),
#     label = "Island to DK",)

# network.links_t.p0.iloc[:,2].plot(
#     figsize = (16*2,9),
#     label = "Island to BE",)

# plt.legend()
# plt.ylabel("Power flow [MW]")
# plt.title("Power flow from Island to countries")
# print('Done')

#%%
il.play_sound()