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

ip.set_plot_options()

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
network.add("Generator",
            "boiler",
            bus = "heat bus",
            p_nom_extendable = True,
            efficiency = 0.9,
            marginal_cost = 20,
            carrier = "gas"
            )

#% Add storage ---------------------------------------------------------------
system_add.storages(network)

# Add heat storage (Hot water tank)
network.add("Store",
            "heat store",
            bus = "heat bus",
            e_cyclic = True,
            e_nom_extendable = True,
            standing_loss = 0.01,
            # capital_cost = 0 #Need data
            )


#% Add heat pump that converts electricity into heat (Added as link)
network.add("Link",
            "heat pump",
            bus0 = "electricity bus",
            bus1 = "heat bus",
            efficiency = 3,
            # capital_cost = 0,        # Need data
            p_nom_extendable = True
            )

#%% CO2 limit
# Get CO2 limit from the bus_df, by searching for the country name and getting
# corresponding CO2_limit

co2_limit = float(bus_df[bus_df['Abbreviation'].str.contains(country)]['CO2_limit']) #tonCO2 https://www.worldometers.info/co2-emissions/germany-co2-emissions/    
      
network.add("GlobalConstraint",
            "co2_limit",
            type                = "primary_energy",
            carrier_attribute   = "co2_emissions",
            sense               = "<=",
            constant            = co2_limit*0.05)

#%% Solve the system
network.lopf(network.snapshots, 
              pyomo=False,
              solver_name='gurobi',
              keep_shadowprices = True, #Keep lagrange multipliers (For CO2 price)
              keep_references   = True,
              )
    