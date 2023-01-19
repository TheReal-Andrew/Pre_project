#%% Import packages
import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import system_add
import island_lib as ip

# D.  -------------------------------------------------------------------------
# Add some storage technology/ies and investigate how they behave and what are
# their impact on the optimal system configuration.

#%% Choose country
country = 'DNK'

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

#%% Solve the system
network.lopf(network.snapshots, 
             pyomo=False,
             solver_name='gurobi')

#%% Store the two weeks in January and July
d = {}
for i in list(network.generators.index):
    
    d[str(i) + "_jan"] = network.generators_t.p[i].loc['2015-01-01 00:00:00':'2015-01-8 00:00:00']
    d[str(i) + "_jul"] = network.generators_t.p[i].loc['2015-07-01 00:00:00':'2015-07-8 00:00:00']
    
#%% Plot the dispatch for the two weeks
fig1 = plt.figure('Figure 1')
fig1, ax = plt.subplots(nrows=2, ncols=1, sharex=False, sharey=True, figsize=(15, 7.5), dpi = 300)

for i in list(network.generators.index):
    ax[0].plot(d[str(i) + "_jan"], label = str(i))
    ax[1].plot(d[str(i) + "_jul"], label = str(i))

for i in range(2):
    ax[i].xaxis.set_major_formatter(mdates.DateFormatter('%b-%d'))
    ax[i].grid(visible = True, which = 'both')
    ax[i].legend(loc = 'best')

ax[0].set_xlim([datetime.date(2015, 1, 1), datetime.date(2015, 1, 8)])
ax[1].set_xlim([datetime.date(2015, 7, 1), datetime.date(2015, 7, 8)])

ax[0].set_title('Denmark in January and July without C02 constraint')
fig1.text(0.5,0.05,'Time [Hour]', ha='center')
fig1.text(0.08,0.5,'Power [MW]', va='center', rotation='vertical')

plt.savefig('graphics/' + str(country) + '_D_dispatch.pdf', format = 'pdf', bbox_inches='tight') 
    
#%% Plot the technology mix

colors = system_add.get_colors(country)

fig2    = plt.figure('Figure 2', dpi = 300, figsize=(7.5, 7.5))
sizes   = []
labels  = []
l       = []

for i in list(network.generators.index):
    if network.generators_t.p[i].sum() > 0:
        sizes = sizes + [network.generators_t.p[i].sum()]
        l = l + [i]
        labels = labels + [i[:-6] + "\n" + str(round(network.generators_t.p[i].sum()/10**6,2)) + " TWh"]
    else:
        pass

plt.pie(sizes, labels = labels, autopct='%.1f%%',
        colors = [colors[v] for v in l])

plt.savefig('graphics/' + str(country) + '_D_mix.pdf', format = 'pdf', bbox_inches='tight') 

