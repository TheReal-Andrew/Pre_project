#%% Import
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 10:44:50 2022

@author: Lukas & Anders
"""

import pypsa
from pypsa.linopt import get_dual

import numpy as np
import pandas as pd
import island_lib as il #Library with data and calculation functions 
import island_plt as ip #Library with plotting functions.
from ttictoc import tic, toc 


n_points = 1000

# Load Data price and load data
cprice, cload = il.get_load_and_price(2030)

cprice = cprice[:n_points]
cload  = cload[:n_points]

# Load wind CF
cf_wind_df1 = pd.read_csv(r'Data/Wind/wind_test.csv',index_col = [0], sep=",")
cf_wind_df = cf_wind_df1[:n_points]

#Load link info
link_cost_url = 'https://github.com/PyPSA/technology-data/blob/master/inputs/manual_input.csv?raw=true'
link_cost     = pd.read_csv(link_cost_url)
link_inv      = link_cost.loc[link_cost['parameter'].str.startswith('investment') & link_cost['technology'].str.startswith('HVDC submarine')]
link_life     = link_cost.loc[link_cost['parameter'].str.startswith('lifetime') & link_cost['technology'].str.startswith('HVDC submarine')]
link_FOM      = link_cost.loc[link_cost['parameter'].str.startswith('FOM') & link_cost['technology'].str.startswith('HVDC submarine')]
#%% Set up network & bus info -------------------------------------

network = pypsa.Network()       #Create network
#t = pd.date_range('2019-01-01 00:00', '2019-12-31 23:00', freq = 'H')
t = np.arange(0, len(cprice))
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
        bus0      = "Island",       #Start Bus
        bus1      = i,              #End Bus
        carrier   = "DC",           #Define carrier type
        p_min_pu  = -1,             #Make links bi-directional
        p_nom     = 2000,           #Power capacity of link [MW]
        p_nom_max = 2000,
        p_nom_extendable = True,    #Extendable links
        capital_cost = link_inv.loc[link_inv['year'] == 2030].value,     
        marginal_cost = link_inv.loc[link_inv['year'] == 2030].value*0.02,
        )

#%% Add Generators -------------------------------------------------

#Add wind turbine
network.add(
    "Generator",          #Component type
    "Wind",               #Component name
    bus = "Island",       #Bus on which component is
    p_nom = 10000,         #Nominal power [MW]
    p_max_pu = cf_wind_df['electricity'].values,         #time-series of power coefficients
    carrier = "Wind",
    marginal_cost = 0.01   #Cost per MW from this source 
    )

#%% Add Generators -------------------------------------------------

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
    e_nom = 3000,     #Store capacity
    e_initial = 0,    #Initially stored energy
    e_cyclic = True,  #Set store to always end and start at same energy
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
    p_set = 4000,
    )

#%% Solver

tic() #Start timer

network.lopf(
    pyomo = False,
    keep_shadowprices = ["Bus"]) #Solve dynamic system

print("Solving time: " + str(toc()) ) #Print 

#Normalize
opt_prices = get_dual(network, "Bus", "marginal_price")
opt_prices2 = il.remove_outliers(opt_prices, opt_prices.columns, 5)

#%% Plotting
ip.plot_geomap(network)                  #Plot geographic map with links and buses
ip.plot_loads_generators(network)        #Plot dynamic results

ip.plot_powerflow(network)               #Plot powerflow on links

ip.plot_corr_matrix(
    network.generators_t.p,
    "Generator correlation") #Correlation matrix of generators
ip.plot_corr_matrix(
    opt_prices2,
    "Price correlation", vmin = -1)
ip.plot_corr_matrix(
    network.links_t.p0,
    "Powerflow correlation")

ip.plot_bus_prices(opt_prices2)
ip.plot_price_diff(opt_prices2)
    
#%%   
# data2 = il.remove_outliers(opt_prices, opt_prices.columns, 3)
# fig = plt.figure()
# plt.hist(data2["Denmark"].values, 50)

ip.plot_bus_prices(opt_prices)
