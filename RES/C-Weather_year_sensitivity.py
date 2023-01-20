#%% Import packages
import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import system_add
import island_lib as il
import island_plt as ip

#%% Choose country
country = 'DEU'

#%% Initialize and start loop
cf = {}     # Dictionary for storing CF data
d  = {}     # Dictionary for storing data
q  = 1      # Initialize dictionary-store counter

#%% Load electricity demand data
df_elec       = pd.read_csv('data/electricity_demand.csv', sep=';', index_col=0) # in MWh

for i in range(1979,2017,1):
#%% Set-up of network
    network       = pypsa.Network()
    hours_in_year = pd.date_range('{}-01-01T00:00Z'.format(i),'{}-12-31T23:00Z'.format(i), freq='H')
    hours_in_year = hours_in_year[~((hours_in_year.month == 2) & (hours_in_year.day == 29))]
    network.set_snapshots(hours_in_year)
    network.add("Bus","electricity bus")
    df_elec.index = pd.to_datetime(hours_in_year) #change index to datatime
    
#%% Add load to the bus
    network.add("Load",
                "load", 
                bus   = "electricity bus", 
                p_set = df_elec[country]*(1+0.018)**(35))
        
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
            
            if j == "OCGT " + "(" + country + ")":
                pass
            else:
                cf[str(j)] = []
                cf[str(j)].append(network.generators_t.p_max_pu.mean()[j])

        else:
            d[str(j)].append(network.generators_t.p[j].sum())
            
            if j == "OCGT " + "(" + country + ")":
                pass
            else:
                cf[str(j)].append(network.generators_t.p_max_pu.mean()[j])
                    
        q = q + 1

#%% Ceil floor functions
def my_ceil(a, precision=0):
    return np.true_divide(np.ceil(a * 10**precision), 10**precision)

#%% Plot

colors = system_add.get_colors(country)

fig, ax1 = plt.subplots(figsize=(15, 7.5), dpi = 300)
ax2 = ax1.twinx()

for i in list(network.generators.index):
    ax1.plot(range(1979,2017,1), pd.Series(d[i])/10**6, label = i[:-6], color = colors[i], linewidth = 3)
    
    if i == "OCGT " +"(" + country + ")":
        pass
    else:
        ax2.plot(range(1979,2017,1), cf[i], '--', label = "CF " + i[:-6], color = colors[i])
                
cap_max = round(max(d[max(d, key=d.get)])/10**6)

ax1.set_ylim([0,cap_max])
ax2.set_ylim([0,1])

ax1.set_yticks(np.linspace(0,my_ceil(cap_max/10**(len(str(cap_max))-1),1)*10**(len(str(cap_max))-1),11))
ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1.get_yticks())))

# ax1.ticklabel_format(useOffset=False, style='plain')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='center left', bbox_to_anchor=(1.05, 0.5))

# plt.legend(loc = 'best')        
plt.title('Technology mix sensitivity due to interannual weather variability', fontsize = 20)     
ax1.set_xlabel('Time [yr]', fontsize = 15)
ax1.set_ylabel('Total produced energy [TWh]', fontsize = 15)
ax2.set_ylabel('Mean capacity factor [-]', fontsize = 15)
ax1.grid(True)

plt.savefig('graphics/' + str(country) + '_C_weather.pdf', format = 'pdf', bbox_inches='tight') 

#%% Variance

# Set formatting for pandas
pd.options.display.float_format = '{:.2e}'.format

# Convert dict data to dataframe
d_data  = pd.DataFrame.from_dict(d)
cf_data = pd.DataFrame.from_dict(cf) 

# Variance
d_var  = d_data.var()
cf_var = cf_data.var()

# Standard Variation
d_std  = d_data.std()
cf_std = cf_data.std()

# Create dataframe with variance and STD
d_tab  = pd.DataFrame( data = {'Standard Deviation':d_std, 
                               'Variance':d_var})
cf_tab = pd.DataFrame( data = {'Standard Deviation':cf_std, 
                              'Variance':cf_var})

# Remove country from technology titles
d_tab.index = [x[:-6] for x in d_tab.index]
cf_tab.index = [x[:-6] for x in cf_tab.index]

# Print latex code for each table
print('Latex code for d table: \n')
print(d_tab.to_latex())
print(' \n Latex code for cf table: \n')
print(cf_tab.to_latex())

# -- To Reset Pandas formatting: --
# pd.reset_option('display.float_format')

#%% Play Sound
# il.its_britney_bitch(r'C:\Users\lukas\Documents\GitHub\NorthSeaEnergyIsland\Data\Sounds')
