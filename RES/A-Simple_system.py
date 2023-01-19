#%% Import packages
import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import system_add
import numpy as np
import matplotlib.ticker as ticker
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

#%% Choose country
country = 'DNK'

#%% Load electricity demand data
df_elec       = pd.read_csv('data/electricity_demand.csv', sep=';', index_col=0)    # [MWh]
df_elec.index = pd.to_datetime(df_elec.index)                                       # Change index to datatime

#%% Set-up of network
network       = pypsa.Network()
hours_in_2015 = pd.date_range('2015-01-01T00:00Z','2015-12-31T23:00Z', freq='H')
network.set_snapshots(hours_in_2015)
network.add("Bus","electricity bus")

#%% Add load to the bus
network.add("Load",
            "load", 
            bus   = "electricity bus", 
            p_set = df_elec[country]*(1+0.018)**(35))

#%% Define max capacity for any given technology
max_cap = df_elec[country].max()
    
#%% Add the different carriers and generators
system_add.carriers(network)
system_add.generators(network,country,network.buses.index[0])

#%% Solve the system
network.lopf(network.snapshots, 
             pyomo=False,
             solver_name='gurobi')

#%% Store the week in January and July data in a dictionary
d = {}
for i in list(network.generators.index):
    
    d[str(i) + "_jan"] = network.generators_t.p[i].loc['2015-01-01 00:00:00':'2015-01-8 00:00:00']
    d[str(i) + "_jul"] = network.generators_t.p[i].loc['2015-07-01 00:00:00':'2015-07-8 00:00:00']
    
#%% Plot the dispatch for the two weeks

colors = system_add.get_colors(country)

fig1 = plt.figure('Figure 1')
fig1, ax = plt.subplots(nrows=2, ncols=1, sharex=False, sharey=True, figsize=(15, 7.5), dpi = 300)

for i in list(network.generators.index):
    ax[0].plot(d[str(i) + "_jan"]/10**3, label = str(i)[:-6],
               color = colors[i])
    ax[1].plot(d[str(i) + "_jul"]/10**3, label = str(i)[:-6],
               color = colors[i])

for i in range(2):
    ax[i].xaxis.set_major_formatter(mdates.DateFormatter('%b-%d'))
    ax[i].grid(visible = True, which = 'both')
    ax[i].plot(df_elec[country]*(1+0.018)**(35)/10**3, label = 'EL demand', linestyle = '--')
    
ax[0].legend(loc = 'best')
ax[0].set_xlim([datetime.date(2015, 1, 1), datetime.date(2015, 1, 8)])
ax[1].set_xlim([datetime.date(2015, 7, 1), datetime.date(2015, 7, 8)])

ax[0].set_title(country +' in January and July without C02 constraint or storage', size = 20)

fig1.supxlabel('Time [Hour]')
fig1.supylabel('Power [GW]')
    
plt.tight_layout()
plt.savefig('graphics/' + str(country) + '_A_dispatch.pdf', format = 'pdf', bbox_inches='tight') 

#%% Plot the technology mix in pie-chart
fig2 = plt.figure('Figure 2')
fig2, ax = plt.subplots(nrows=1, ncols=1, figsize=(7.5, 7.5), dpi = 300)

sizes  = []
labels = []
l      = [] 
for i in list(network.generators.index):
    if network.generators_t.p[i].sum() > 0:
        sizes = sizes + [network.generators_t.p[i].sum()]
        l = l + [i]
        labels = labels + [i[:-6] + "\n" + str(round(network.generators_t.p[i].sum()/10**6,2)) + " TWh"]
    else:
        pass
ax.pie(sizes, labels = labels, autopct='%.1f%%',
       colors = [colors[v] for v in l])
# ax.set_title('Energy produced in ' + country + '\n without CO2 constraint or storage', size = 20)     

plt.tight_layout()    
plt.savefig('graphics/' + str(country) + '_A_pie.pdf', format = 'pdf', bbox_inches='tight') 

#%% Plot duration curve
# Load offshore wind data
df_offshorewind           = pd.read_csv('data/offshore_wind_1979-2017.csv', sep=';', index_col=0)
df_offshorewind.index     = pd.to_datetime(df_offshorewind.index)
CF_wind_offshore          = df_offshorewind[country][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

sort_wind_offshore  = CF_wind_offshore.sort_values(ascending = False)
exceedence_offwind  = np.arange(1,len(sort_wind_offshore)+1)

# Load onshore wind data
df_onshorewind           = pd.read_csv('data/onshore_wind_1979-2017.csv', sep=';', index_col=0)
df_onshorewind.index     = pd.to_datetime(df_onshorewind.index)
CF_wind_onshore          = df_onshorewind[country][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

sort_wind_onshore  = CF_wind_onshore.sort_values(ascending = False)
exceedence_onwind  = np.arange(1,len(sort_wind_onshore)+1)

# Load solar utility data
df_solar_utility            = pd.read_csv('data/pv_optimal.csv', sep=';', index_col=0)
df_solar_utility.index      = pd.to_datetime(df_solar_utility.index)
CF_solar_utility            = df_solar_utility[country][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

sort_solar_utility          = CF_solar_utility.sort_values(ascending = False)
exceedence_solar_utility    = np.arange(1,len(sort_solar_utility)+1)

# Load solar rooftop data
df_solar_rooftop           = pd.read_csv('data/pv_rooftop.csv', sep=';', index_col=0)
df_solar_rooftop.index     = pd.to_datetime(df_solar_rooftop.index)
CF_solar_rooftop           = df_solar_rooftop[country][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]

sort_solar_rooftop          = CF_solar_rooftop.sort_values(ascending = False)
exceedence_solar_rooftop    = np.arange(1,len(sort_solar_rooftop)+1)

# Load OCGT data
CF_OCGT = network.generators_t.p['OCGT ('+country+')']/network.generators.p_nom_opt['OCGT ('+country+')']

sort_OCGT        = CF_OCGT.sort_values(ascending = False)
exceedence_OCGT  = np.arange(1,len(sort_OCGT)+1)

#%%Actual plot

# Creating new figure
fig3     = plt.figure('Figure 3')
fig3, ax = plt.subplots(1, figsize=(15, 7.5))

lw = 3

ax.plot(exceedence_offwind, sort_wind_offshore,
        linewidth = lw, color = colors['Offshorewind (' + country + ')'])
ax.plot(exceedence_onwind, sort_wind_onshore,
        linewidth = lw, color = colors['Onshorewind (' + country + ')'])
ax.plot(exceedence_solar_utility, sort_solar_utility,
        linewidth = lw, color = colors['Solar_utility (' + country + ')'])
ax.plot(exceedence_solar_rooftop, sort_solar_rooftop,
        linewidth = lw, color = colors['Solar_rooftop (' + country + ')'])
ax.plot(exceedence_OCGT, sort_OCGT,
        linewidth = lw, color = colors['OCGT (' + country + ')'])

plt.axvline(x = 8760*0.75, linestyle = '--', color = 'grey')
plt.axvline(x = 8760*0.50, linestyle = '--', color = 'grey')
plt.axvline(x = 8760*0.25, linestyle = '--', color = 'grey')

ax.legend(['Offshore wind','Onshore wind','Solar utility','Solar rooftop','OCGT'])

ax.set_xlabel("Cumulative Time [Hours]", fontsize = 15)
ax.set_ylabel("Capacity Factor [-]", fontsize = 15)

ax.set_ylim([0,1])

ax.set_title('Duration curve for the different technologies', fontsize = 20)
ax.yaxis.set_major_locator(ticker.MultipleLocator(0.05))
ax.xaxis.set_major_locator(ticker.MultipleLocator(500))
ax.set_xlim([0,len(sort_wind_offshore)])
ax.grid(visible = True, which = 'both')

plt.tight_layout() 
plt.savefig('graphics/' + str(country) + '_A_duration.pdf', format = 'pdf', bbox_inches='tight')

#%% Print CF at different durations
DC = pd.DataFrame(columns = ["Technology","25%","50%","75%","100%"])
sort_list = [sort_wind_offshore,
             sort_wind_onshore,
             sort_solar_utility,
             sort_solar_rooftop,
             sort_OCGT]

for i in range(len(sort_list)):
    gen_name = network.generators.index[i]
    DC = DC.append({'Technology': gen_name[:-6],
                    '25%': round(sort_list[i][int(8760*0.25-1)],2),
                    '50%': round(sort_list[i][int(8760*0.50-1)],2),
                    '75%': round(sort_list[i][int(8760*0.75-1)],2),
                    '100%': round(sort_list[i][int(8760*1.00-1)],2)
                    }, ignore_index=True)
pd.options.display.float_format = '{:.2f}'.format
DC2 = DC.copy().reset_index(drop=True)
print(DC2.to_latex())

#%% Print data assumptions
system_add.price_gen(network)
