# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 11:46:49 2023

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

# F.  -------------------------------------------------------------------------
# Select one target for decarbonization (i.e., one CO2 allowance limit). What 
# is the CO2 price required to achieve that decarbonization level? Search for 
# information on the existing CO2 tax in your country (if any) and discuss 
# your result.

#%% Choose country
country = 'DEU'

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

#%% Set-up of network
network       = pypsa.Network()
hours_in_2015 = pd.date_range('2015-01-01T00:00Z','2015-12-31T23:00Z', freq='H')
network.set_snapshots(hours_in_2015)
network.add("Bus","electricity bus")

#%% Add load to the bus
network.add("Load",
            "load", 
            bus   = "electricity bus", 
            p_set = df_elec[country])
    
#%% Add the different carriers and generators
system_add.carriers(network)
system_add.generators(network,country, network.buses.index[0])

#%% Add storage
system_add.storages(network)

#%% Initialize dataframes for saving
df_red = pd.DataFrame(columns = ['Percent reduction', 'CO2 price'])
df_gen = pd.DataFrame(columns = network.generators.index)
    
#%% Start loop

for p in [1, 0.5, 0.25, 0.2, 0.15, 0.1, 0.05, 0.02, 0]:
    
    # Reset CO2 Constraint if it exists
    try:
        network.remove('GlobalConstraint', 'co2_limit')
    except:
        pass

    # Get CO2 limit from the bus_df, by searching for the country name and getting
    # corresponding CO2_limit
    co2_limit = float(bus_df[bus_df['Abbreviation'].str.contains(country)]['CO2_limit']) #tonCO2 https://www.worldometers.info/co2-emissions/germany-co2-emissions/    
          
    network.add("GlobalConstraint",
                "co2_limit",
                type                = "primary_energy",
                carrier_attribute   = "co2_emissions",
                sense               = "<=",
                constant            = co2_limit*p)

    #%% Solve the system
    network.lopf(network.snapshots, 
                 pyomo=False,
                 solver_name='gurobi',
                 keep_shadowprices = True, #Keep lagrange multipliers (For CO2 price)
                 keep_references   = True,
                 )

    #%% Find CO2 Price and limit
    
    # Constraint info:
    network.global_constraints
    
    # CO2 Price: ----------------------------------------------------
    network.global_constraints.mu
    
    # Alternative way to get CO2 Price: -----------------------------
    network.constraints #See constraints
    
    #Get value of specific constraint lagrange multiplier
    CO2_price = get_dual(network, 'GlobalConstraint', 'mu') # [EUR/tonCO2]
    
    #%% Save
    
    #Save resulting capacities
    sums   = network.generators_t.p.sum()
    df_gen = df_gen.append(sums, ignore_index = True)
    
    # Save reduction and CO2 price
    df_red = df_red.append({'Percent reduction': ((1-p) * 100),
                            'CO2 price': abs(CO2_price.co2_limit)},
                           ignore_index = True)


#%% Plot the technology mix

colors = sa.get_colors(country)

    
#%% Stacked barchart

reductions = ['0%', '50%', '75%', '80%', '85%', '90%', '95%', '98%', '100%']
y1 = df_gen.iloc[:,0]/10**6
y2 = df_gen.iloc[:,1]/10**6
y3 = df_gen.iloc[:,2]/10**6
y4 = df_gen.iloc[:,3]/10**6
y5 = df_gen.iloc[:,4]/10**6

bar_fig = plt.figure( figsize = (10,5))
plt.bar(reductions, y1, color = colors['Onshorewind (' + country + ')'], label = 'Onshorewind')
plt.bar(reductions, y2, bottom = y1 , color = colors['Offshorewind (' + country + ')'], label = 'Offshorewind')
plt.bar(reductions, y3, bottom = y1+y2 , color = colors['Solar_utility (' + country + ')'], label = 'Solar Utility')
plt.bar(reductions, y4, bottom = y1+y2+y3 , color = colors['Solar_rooftop (' + country + ')'], label = 'Solar rooftop')
plt.bar(reductions, y5, bottom = y1+y2+y3+y4 , color = colors['OCGT (' + country + ')'], label = 'OCGT')

plt.xlabel('CO2 Reduction [%]')
plt.ylabel('Produced energy [TWh]')
plt.title('Effect of CO2 reduction on technology mix')    
plt.legend(loc = 'center left', bbox_to_anchor=(1, 0.5))

#%% Plot reduction

fig, ax1 = plt.subplots(figsize = [10,5])

ax1.plot(df_red['Percent reduction'].values, abs(df_red['CO2 price']).values)
ax1.set_xlabel('CO2 reduction [%]')
ax1.set_ylabel('CO2 price [Eur/TonCO2]')
ax1.set_yscale('symlog')
ax1.set_title('CO2 price vs percent reduction \n (symlog scale)')

# Print Latex tables
print(df_red.to_latex())
print(df_gen.to_latex())

#%% Play Sound
pd.options.display.float_format = '{:.2f}'.format
# pd.options.display.float_format = '{:.2E}'.format
# pd.reset_option('display.float_format')

il.its_britney_bitch(r'C:\Users\lukas\Documents\GitHub\NorthSeaEnergyIsland\Data\Sounds')