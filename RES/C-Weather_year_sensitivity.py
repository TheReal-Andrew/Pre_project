#%% Import packages
import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import system_add

#%% Choose country
country = 'DEU'

#%% Initialize and start loop
cf = {}     # Dictionary for storing CF data
d  = {}     # Dictionary for storing data
q  = 1      # Initialize dictionary-store counter

for i in range(1979,2017,1):
#%% Set-up of network
    network       = pypsa.Network()
    hours_in_year = pd.date_range('{}-01-01T00:00Z'.format(i),'{}-12-31T23:00Z'.format(i), freq='H')
    hours_in_year = hours_in_year[~((hours_in_year.month == 2) & (hours_in_year.day == 29))]
    network.set_snapshots(hours_in_year)
    network.add("Bus","electricity bus")
    
#%% Load electricity demand data
    df_elec       = pd.read_csv('data/electricity_demand.csv', sep=';', index_col=0) # in MWh
    df_elec.index = pd.to_datetime(hours_in_year) #change index to datatime
    
#%% Add load to the bus
    network.add("Load",
                "load", 
                bus   = "electricity bus", 
                p_set = df_elec[country])
        
#%% Add the different carriers and generators
    system_add.carriers(network)
    system_add.generators(network,country,network.buses.index[0])
    
#%% Solve system
    network.lopf(network.snapshots, 
                 pyomo=False,
                 solver_name='gurobi')
    
#%% Store data capacity and CF data in dictionaries 
    
    for j in list(network.generators.index):
        if q <= len(network.generators.index):
            d[str(j)] = []
            d[str(j)].append(network.generators_t.p[j].sum())
            
            if j == "OCGT" + "(" + country + ")":
                pass
            else:
                cf[str(j)] = []
                cf[str(j)].append(network.generators_t.p_max_pu.mean()[j])

        else:
            d[str(j)].append(network.generators_t.p[j].sum())
            
            if j == "OCGT" + "(" + country + ")":
                pass
            else:
                cf[str(j)].append(network.generators_t.p_max_pu.mean()[j])
                    
        q = q + 1

#%% Ceil floor functions
def my_ceil(a, precision=0):
    return np.true_divide(np.ceil(a * 10**precision), 10**precision)

#%% Plot
fig, ax1 = plt.subplots(dpi = 300)
ax2 = ax1.twinx()

for i in list(network.generators.index):
    ax1.plot(range(1979,2017,1), d[i], label = i)
    
    if i == "OCGT":
        pass
    else:
        ax2.plot(range(1979,2017,1), cf[i], '--', label = "CF " + i)
                
cap_max = round(max(d[max(d, key=d.get)]))

ax1.set_ylim([0,cap_max])
ax2.set_ylim([0,1])

ax1.set_yticks(np.linspace(0,int(my_ceil(2.41,1)*10**(len(str(cap_max))-1)),11))
ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1.get_yticks())))

# ax1.ticklabel_format(useOffset=False, style='plain')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='center left', bbox_to_anchor=(1.17, 0.5))

# plt.legend(loc = 'best')        
plt.title('Interannual variability of weather')     
plt.xlabel('Time [yr]')
ax1.set_ylabel('Installed capacity [MW]')
ax2.set_ylabel('Mean capacity factor [-]')
ax1.grid(True)
