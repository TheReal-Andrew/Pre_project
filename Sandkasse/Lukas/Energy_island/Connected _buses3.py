#%% Import
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 10:44:50 2022

@author: Lukas & Anders
"""

import pypsa
from pypsa.linopt import get_dual, get_var
import os
import sys
import numpy as np
import pandas as pd
import island_lib as il #Library with data and calculation functions 
import island_plt as ip #Library with plotting functions.
from ttictoc import tic, toc 
#from Plotting import plot_map

#%% ### ---- Options ---- ###
should_export = False # Export the network to hdf5?
should_solve = True  #Solve the system or not?
should_plot = False   #Produce plots or not? Also activates solving the system
n_points = 2000      #Number of datapoints over the year to use. Max 8760

#%% Load Data

# Load Data price and load data
cprice, cload = il.get_load_and_price(2030)

cprice = cprice[:n_points]
cload  = cload[:n_points]

# Load wind CF
cf_wind_df1 = pd.read_csv(r'data/Wind/wind_test.csv',index_col = [0], sep=",")
cf_wind_df = cf_wind_df1[:n_points]

#Load link info
link_cost_url = 'https://github.com/PyPSA/technology-data/blob/master/inputs/manual_input.csv?raw=true'
link_cost     = pd.read_csv(link_cost_url)
link_inv      = float(link_cost.loc[link_cost['parameter'].str.startswith('investment') & link_cost['technology'].str.startswith('HVDC submarine'), "value"])
link_life     = float(link_cost.loc[link_cost['parameter'].str.startswith('lifetime') & link_cost['technology'].str.startswith('HVDC submarine'), "value"])
link_FOM      = float(link_cost.loc[link_cost['parameter'].str.startswith('FOM') & link_cost['technology'].str.startswith('HVDC submarine'), "value"])

#%% Set up network & bus info -------------------------------------

n = pypsa.Network()       #Create network
t = pd.date_range('2030-01-01 00:00', '2030-12-31 23:00', freq = 'H')
t = t[:n_points]
n.set_snapshots(t)  #Set snapshots of network to the timesteps

#Create dataframe with info on buses. Names, x (Longitude) and y (Latitude) 
bus_df = pd.DataFrame(
    np.array([                                #Create numpy array with bus info
    ["Island",          "EI",   6.68, 56.52, 0], #Energy Island
    ["Denmark",         "DK",   8.12, 56.37, 80], #Assumed Thorsminde
    ["Norway",          "NO",   8.02, 58.16, 300], #Assumed Kristiansand
    ["Germany",         "DE",   8.58, 53.54, 300], #Assumed Bremerhaven
    ["Netherlands",     "NL",   6.84, 53.44, 300], #Assumed Eemshaven
    ["Belgium",         "BE",   3.20, 51.32, 600], #Assumed Zeebrugge
    ["United Kingdom",  "GB",  -1.45, 55.01, 550], #Assumed North Shield
    ]), 
    columns = ["Country", "Abbreviation", "X", "Y", "Distance"]   #Give columns titles
    )

#%% Add buses -----------------------------------------------------
#Adding busses from bus_info to network
for i in range(bus_df.shape[0]):    #i becomes integers
    n.add(                    #Add component
        "Bus",                      #Component type
        bus_df.Country[i],          #Component name
        x = bus_df.X[i],            #Longitude (for plotting)
        y = bus_df.Y[i],            #Latitude (for plotting)
        carrier = "AC",             #Carrier type
        )

#%% Add links -----------------------------------------------------

#List of link destionations from buses
link_destinations = n.buses.index.values

# for i in link_destinations[1:]:     #i becomes each string in the array
#     dist       = float(bus_df.loc[bus_df["Country"] == i]["Distance"]) #Get distance
#     link_ccost = il.get_annuity(0.07, link_life)*link_inv*dist + link_inv*dist*link_FOM
    
#     n.add(                          #Add component
#         "Link",                     #Component type
#         "Island_to_" + i,           #Component name
#         bus0      = "Island",       #Start Bus
#         bus1      = i,              #End Bus
#         carrier   = "AC",           #Define carrier type
#         p_min_pu  = -1,             #Make links bi-directional
#         p_nom     = 0,              #Power capacity of link [MW]
#         p_nom_max = 10000,
#         p_nom_extendable = True,    #Extendable links
#         capital_cost  = link_ccost,
#         marginal_cost = 0.01,
#         )

for i in ["Denmark", "Germany"]:     #i becomes each string in the array
    dist       = float(bus_df.loc[bus_df["Country"] == i]["Distance"]) #Get distance
    link_ccost = il.get_annuity(0.07, link_life)*link_inv*dist + link_inv*dist*link_FOM
    
    n.add(                          #Add component
        "Link",                     #Component type
        "Island_to_" + i,           #Component name
        bus0      = "Island",       #Start Bus
        bus1      = i,              #End Bus
        carrier   = "AC",           #Define carrier type
        p_min_pu  = -1,             #Make links bi-directional
        p_nom     = 0,              #Power capacity of link [MW]
        p_nom_max = 10000,
        p_nom_extendable = True,    #Extendable links
        capital_cost  = link_ccost,
        marginal_cost = 0.01,
        )

#%% Add Generators -------------------------------------------------

#Add wind turbine
n.add(
    "Generator",          #Component type
    "Wind",               #Component name
    bus = "Island",       #Bus on which component is
    p_nom = 10000,         #Nominal power [MW]
    p_max_pu = cf_wind_df['electricity'].values,  #time-series of power coefficients
    carrier = "Wind",
    marginal_cost = 2.7,  #Cost per MW from this source 
    )

#Add generators to each country bus with varying marginal costs
for i in range(1, bus_df.shape[0]):
    n.add(
        "Generator",
        "Gen_" + bus_df.Country[i],
        bus   = bus_df.Country[i],
        p_nom = 0, 
        p_nom_extendable = True,     #Make sure country can always deliver to price
        capital_cost = 0,            #Same as above
        marginal_cost = cprice[bus_df.Abbreviation[i]].values,
        carrier = "AC",
        )


#%% Add store
n.add(
    "Store",          #Component type
    "Store1",         #Component name
    bus = "Island",   #Bus on which component is
    e_nom = 3000,     #Store capacity
    e_initial = 0,    #Initially stored energy
    e_cyclic = True,  #Set store to always end and start at same energy
    carrier = "Battery",
    )

#%% Add Loads ------------------------------------------------------

# Add country loads
for i in range(1, bus_df.shape[0]): 
    n.add(
        "Load",
        "Load_" + bus_df.Country[i],
        bus   = bus_df.Country[i],
        p_set = cload[bus_df.Abbreviation[i]].values, 
        carrier = "AC"
        )

# Add datacenter load on Island
n.add(
    "Load",
    "Datacenter Load",
    bus = "Island",
    p_set = 4000,
    carrier = "AC",
    )

#%% Extra Functionality

def area_use(n, snapshots):
    vars_p = get_var()

#%% Export network

if should_export:
    filename = "/connected_buses3.nc"
    export_path = os.getcwd() + filename
    n.export_to_netcdf(export_path)
else:
    pass

#%% Solver

if should_solve or should_plot:
    tic() #Start timer
    n.lopf(
        pyomo = False,
#       solver_name = 'gurobi',
        keep_shadowprices = True,
        keep_references = True
        ) #Solve dynamic system
    
    print("Solving time: " + str(toc()) ) #Print 
    
    #Normalize
    opt_prices = get_dual(n, "Bus", "marginal_price")
    opt_prices2 = il.remove_outliers(opt_prices, opt_prices.columns, 5)
else:
    pass

#%% Plotting
if should_plot:
    ip.plot_geomap(n)                  #Plot geographic map with links and buses
    ip.plot_loads_generators(n)        #Plot dynamic results
    
    ip.plot_powerflow(n)               #Plot powerflow on links
    
    ip.plot_corr_matrix(
        n.generators_t.p,
        "Generator correlation") #Correlation matrix of generators
    ip.plot_corr_matrix(
        opt_prices2,
        "Price correlation", vmin = -1)
    ip.plot_corr_matrix(
        n.links_t.p0,
        "Powerflow correlation")
    
    ip.plot_bus_prices(opt_prices2)
    ip.plot_price_diff(opt_prices2)
else:
    pass

