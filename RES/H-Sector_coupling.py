# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 21:14:43 2023

@author: lukas
"""

#%% Import packages
import pypsa
from pypsa.linopt import get_dual, get_var
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import system_add
import island_lib as il
import island_plt as ip
import system_add as sa

ip.set_plot_options()

allowance = 0.85 # CO2 allowance as percent of 1990 CO2 levels

# F.  -------------------------------------------------------------------------
# Select one target for decarbonization (i.e., one CO2 allowance limit). What 
# is the CO2 price required to achieve that decarbonization level? Search for 
# information on the existing CO2 tax in your country (if any) and discuss 
# your result.

#%% Choose country
country = 'DNK'

# Dataframe with country data. All emission data from https://www.worldometers.info/co2-emissions/
# CO2 Limit is the CO2 emission in 1990.
bus_df = pd.DataFrame(
    np.array([                          #Create numpy array with bus info
    ["Germany","DEU", 1_003_148_970*0.438],   
    ["Denmark","DNK",    53_045_230*0.424],   
    ["France", "FRA",   376_699_660*0.132],
    # ["Sweden", "SWE",    56_677_744*0.177],
    # ["Norway", "NOR",    35_902_816*0.069],
    ],
    ),  
    columns = ["Country","Abbreviation","CO2_limit"])
    
#%% Load electricity demand data
df_elec       = pd.read_csv('data/electricity_demand.csv', sep=';', index_col=0) # in MWh
df_elec.index = pd.to_datetime(df_elec.index) #change index to datatime

df_heat       = pd.read_csv('data/heat_demand.csv', sep=';', index_col=0) # in MWh
df_heat.index = pd.to_datetime(df_heat.index) #change index to datatime

#%% Set-up of network
network       = pypsa.Network()
hours_in_2015 = pd.date_range('2015-01-01T00:00Z','2015-12-31T23:00Z', freq='H')
network.set_snapshots(hours_in_2015)

#% Add Buses-------------------------------------------------------------------
network.add("Bus","electricity bus") 

network.add("Bus","heat bus")

#% Add Loads ------------------------------------------------------------------
network.add("Load",
            "elec load", 
            bus   = "electricity bus", 
            p_set = df_elec[country])

network.add("Load",
            "heat load", 
            bus   = "heat bus", 
            p_set = df_elec[country])
    
#% Add the different carriers and generators ----------------------------------
system_add.carriers(network)
system_add.generators(network,country, network.buses.index[0])

# Add heat carrier
network.add("Carrier", "heat")

# Add gas boiler to provide heat
cc_boiler = sa.annuity(20,0.07)*63000*(1+0.01) # in €/MW
network.add("Generator",
            "Boiler " + '(' + country + ')',
            bus = "heat bus",
            p_nom_extendable = True,
            efficiency = 0.9,
            capital_cost = cc_boiler,
            marginal_cost = 32, # [EUR/MWh], European average gas price for 2015
            carrier = "gas",
            )

#% Add heat pump that converts electricity into heat (Added as link)
cc_hp = sa.annuity(20,0.07)*933000*(1+0.035) # in €/MW
network.add("Link",
            "Heat pump " '(' + country + ')',
            bus0 = "electricity bus",
            bus1 = "heat bus",
            efficiency = 3,
            capital_cost = cc_hp,        # Need data
            marginal_cost = 0, # Assumed due to PyPSA example https://pypsa.readthedocs.io/en/latest/examples/lopf-with-heating.html
            p_nom_extendable = True
            )

#% Add storage ---------------------------------------------------------------
system_add.storages(network)

#%% CO2 limit
# Get CO2 limit from the bus_df, by searching for the country name and getting
# corresponding CO2_limit

co2_limit = float(bus_df[bus_df['Abbreviation'].str.contains(country)]['CO2_limit']) #tonCO2 https://www.worldometers.info/co2-emissions/germany-co2-emissions/    
      
network.add("GlobalConstraint",
            "co2_limit",
            type                = "primary_energy",
            carrier_attribute   = "co2_emissions",
            sense               = "<=",
            constant            = co2_limit*allowance)

#%% Solve the system
network.lopf(network.snapshots, 
              pyomo=False,
              solver_name='gurobi',
              keep_shadowprices = True, #Keep lagrange multipliers (For CO2 price)
              keep_references   = True,
              )

#%% Plot

#Pandas float formatting
# pd.options.display.float_format = '{:.2f}'.format
# pd.options.display.float_format = '{:.2E}'.format
# pd.reset_option('display.float_format')

colors = sa.get_colors(country)

# Plots
fig, ax = plt.subplots(1, 2, figsize = (10,5))

# Electricity
sizes, labels, l = [], [], []
for i in list(network.generators[:5].index):
    if network.generators_t.p.iloc[:,:5][i].sum() > 0:
        sizes = sizes + [network.generators_t.p.iloc[:,:5][i].sum()]
        l = l + [i]
        labels = labels + [i[:-6] + "\n" + str(round(network.generators_t.p.iloc[:,:5][i].sum()/10**6,2)) + " TWh"]
    else:
        pass
ax[0].pie(sizes, labels = labels, autopct='%.1f%%',
          colors = [colors[v] for v in l])
ax[0].set_title('Electricity sector')
# Heating

df_heat = pd.DataFrame( {network.generators.index[5] : [network.generators_t.p.iloc[:,5].sum()] ,
                         network.links.index[0] : [network.links_t.p0.iloc[:,0].sum()] } )

sizes, labels, l = [], [], []
for i in list(df_heat.columns):
    if df_heat[i][0] > 0:
        sizes = sizes + [df_heat[i][0]]
        l = l + [i]
        labels = labels + [i[:-6] + "\n" + str(round(df_heat[i][0]/10**6,2)) + " TWh"]
    else:
        pass
ax[1].pie(sizes, labels = labels, autopct='%.1f%%',
          colors = [colors[v] for v in l])
ax[1].set_title('Heat sector')

plt.savefig('graphics/' + str(country) + '_H_heat.pdf', format = 'pdf', bbox_inches='tight') 

#%% 