#%% Import packages
import pypsa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import system_add

#%% Choose country
country = 'DEU'

#%% Initialize and start CO2 loop from 0-100% reduction with 5% steps
d = {}  # Dictionary for storing data
q = 1   # Initialize dictionary-store counter

# reduction_range = np.linspace(0,1,101)  # 01% increments
# reduction_range = np.linspace(0,1,21)   # 05% increments
reduction_range = np.linspace(0,1,11)   # 10% increments

for i in list(reduction_range):
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

#%% Add the different carriers, only gas emits CO2
    system_add.carriers(network)
    system_add.generators(network,country,network.buses.index[0])

#%% Add CO2 constraint
    co2_limit = 765922900*0.44*(1-round(i,1)) #tonCO2 https://www.worldometers.info/co2-emissions/germany-co2-emissions/
    # co2_limit = 4000000*(1-round(i,1))            
    network.add("GlobalConstraint",
                "co2_limit",
                type                = "primary_energy",
                carrier_attribute   = "co2_emissions",
                sense               = "<=",
                constant            = co2_limit)

#%% Solve system
    network.lopf(network.snapshots, 
                 pyomo = False,
                 solver_name = 'gurobi')
    
#%% Store data in dictionary
    for j in list(network.generators.index):
        if q <= len(network.generators.index):
            d[str(j)] = []
            d[str(j)].append(network.generators_t.p[j].sum())
        else:
            d[str(j)].append(network.generators_t.p[j].sum())
        
        q = q + 1
          
#%% Plot the installed capacity wrt. CO2 reduction
fig = plt.figure(dpi = 300)
ax1 = fig.add_subplot(1,1,1)

for i in list(network.generators.index):
    plt.plot(reduction_range*100, d[i], label = i)
    plt.legend(loc = 'best')
    
plt.xticks(np.arange(0,110,10))
plt.xlim([0,100])   
plt.title('Tech. sensitivity wrt. CO2 reduction from 2015')     
plt.xlabel('Reduction in CO2 emissions [%]')
plt.ylabel('Installed capacity [MW]')
plt.grid()
