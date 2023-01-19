#%% Import packages
import pypsa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import island_plt as ip
import system_add

ip.set_plot_options()

#%% Choose country
country = 'DNK'
co2     = system_add.get_co2(country)

#%% Initialize and start CO2 loop from 0-100% reduction with 5% steps
d = {}  # Dictionary for storing data
reduction = {}  # Dictionary for storing data
q = 1   # Initialize dictionary-store counter

# reduction_range = np.linspace(0,1,101)  # 01% increments
reduction_range = np.linspace(0.75,1,26)   # 05% incrementse
# reduction_range = np.linspace(0,1,11)   # 10% increments

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
    co2_limit = co2*(1-round(i,1)) #tonCO2 https://www.worldometers.info/co2-emissions/germany-co2-emissions/
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
    
    reduction = reduction
          
#%% Plot the installed capacity wrt. CO2 reduction
# fig = plt.figure(dpi = 300)
# ax1 = fig.add_subplot(1,1,1)

fig     = plt.figure('Figure 3')
fig, ax1 = plt.subplots(1, figsize=(15, 7.5))

for i in list(network.generators.index):
    plt.plot(reduction_range*100, d[i], label = i[:-6])
    plt.legend(loc = 'best')
    
# plt.xticks(np.arange(0,110,10))
# plt.xlim([0,100])   
plt.title('Energy production sensitivity wrt. CO2 reduction from 1990', fontsize = 20)     
plt.xlabel('Reduction in CO2 emissions [%]', fontsize = 15)
plt.ylabel('Installed capacity [MW]', fontsize = 15)
# plt.grid()

plt.savefig('graphics/' + str(country) + '_B_capacity.pdf', format = 'pdf', bbox_inches='tight') 

#%% Bar plots

colors = system_add.get_colors(country)

reductions = ['75','76','77','78','79',
              '80','81','82','83','84','85','86','87','88','89',
              '90','91','92','93','94','95','96','97','98','99','100']

y1 = pd.Series(d[network.generators.index[0]])/10**6
y2 = pd.Series(d[network.generators.index[1]])/10**6
y3 = pd.Series(d[network.generators.index[2]])/10**6
y4 = pd.Series(d[network.generators.index[3]])/10**6
y5 = pd.Series(d[network.generators.index[4]])/10**6

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

plt.savefig('graphics/' + str(country) + '_B_bar.pdf', format = 'pdf', bbox_inches='tight') 