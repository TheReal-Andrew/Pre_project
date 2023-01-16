#%% Import packages
import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import system_add
import numpy as np
import datetime
import matplotlib.colors as mcolors

#%% Choose country
bus_df = pd.DataFrame(
    np.array([                          #Create numpy array with bus info
    ["Germany","DEU", 765922900*0.44],   
    ["Denmark","DNK", 765922900*0.44],   
    ["France","FRA", 765922900*0.44*0.2]],
             ),  
    columns = ["Country","Abbreviation","CO2_limit"])

#%% Load electricity demand data
df_elec       = pd.read_csv('data/electricity_demand.csv', sep=';', index_col=0) # in MWh
df_elec.index = pd.to_datetime(df_elec.index) #change index to datatime

#%% Set-up of network
network       = pypsa.Network()
hours_in_2015 = pd.date_range('2015-01-01T00:00Z','2015-12-31T23:00Z', freq='H')
network.set_snapshots(hours_in_2015)

for i in range(bus_df.shape[0]):    #i becomes integers
    network.add(                    #Add component
        "Bus",                      #Component type
        bus_df.Abbreviation[i] + ' EL',          #Component name
        )            

#%% Set-up busses to the countries

#List of link destionations from buses
tech_cost = pd.read_csv('https://github.com/PyPSA/technology-data/blob/master/inputs/manual_input.csv?raw=true')
tech_name = 'HVAC overhead'
tech_inv  = 1000*float(tech_cost.loc[tech_cost['parameter'].str.startswith('investment') & tech_cost['technology'].str.startswith(tech_name)].value)
tech_life = float(tech_cost.loc[tech_cost['parameter'].str.startswith('lifetime') & tech_cost['technology'].str.startswith(tech_name)].value)
tech_FOM  = 0.01*float(tech_cost.loc[tech_cost['parameter'].str.startswith('FOM') & tech_cost['technology'].str.startswith(tech_name)].value)
  
cc_hvac = system_add.annuity(tech_life,0.07)*tech_inv*(1+tech_FOM)

j = 0
for i in list(bus_df['Country'][1:]):         #i becomes each string in the array
    j = j + 1
    network.add(                        #Add component
        "Link",                         #Component type
        bus_df.Country[0] + " to " + i,               #Component name
        bus0             = bus_df.Abbreviation[0] + ' EL',    #Start Bus
        bus1             = bus_df.Abbreviation[j] + ' EL',           #End Bus
        carrier          = "DC" + str(j),        #Define carrier type
        p_min_pu         = -1,          #Make links bi-directional
        # p_nom            = 0,           #Power capacity of link
        p_nom_extendable = True,        #Extendable links
        capital_cost     = cc_hvac,
        )                        

# Add loads to each country bus
for i in range(bus_df.shape[0]): #i becomes integers
    network.add(
        "Load",
        "Load " + bus_df.Abbreviation[i],
        bus     = bus_df.Abbreviation[i] + ' EL',
        p_set   = df_elec[bus_df.Abbreviation[i]])       
    
#%% Add the different carriers and generators
system_add.carriers(network)
    
for i in range(bus_df.shape[0]):
    system_add.generators(network,bus_df['Abbreviation'][i],network.buses.index[i])

#%% Add storage
system_add.storages(network)

#%% Add CO2 constraint
    
co2_limit = 765922900*0.44*0.15 #tonCO2 https://www.worldometers.info/co2-emissions/germany-co2-emissions/
# co2_limit = 4000000*(1-round(i,1))   
         
network.add("GlobalConstraint",
            "co2_limit",
            type                = "primary_energy",
            carrier_attribute   = "co2_emissions",
            sense               = "<=",
            constant            = co2_limit)

#%% Solve the system
network.lopf(network.snapshots, 
             pyomo              = False,
             solver_name        = 'gurobi',
             keep_shadowprices  = True,
             keep_references    = True,
             )

#%% Plot the technology mix
fig1 = plt.figure('Figure 1')
fig1, ax = plt.subplots(nrows=1, ncols=3, figsize=(20, 7.5), dpi = 300)

colors = list(mcolors.TABLEAU_COLORS.keys())

q = 0
for j in list(bus_df['Abbreviation']):
    sizes = []
    labels = []
    color  = []
    for i in range(5):
        gen = (network.generators.loc[network.generators['bus'].str.endswith('('+j+')')] & network.generators.loc[network.generators.index.str.endswith('('+j+')')]).index[i]
        cap = network.generators.loc[network.generators.index.str.endswith('('+j+')')].index[i]
        
        if network.generators_t.p[gen].sum() > 0:
            sizes = sizes + [network.generators_t.p[gen].sum()]
            labels1 = gen[:-6]
            labels2 = "Produced: "+str(round(network.generators_t.p[gen].sum()/10**6)) + " TWh"
            labels3 = "Capacity: " + str(round(network.generators.p_nom_opt[cap]/10**3)) + " GW"
            labels  = labels + [labels1  + "\n" + labels2 + "\n" + labels3]
            color   = color + [colors[i]]
        else:
            pass
    
    ax[q].pie(sizes, labels = labels, autopct='%.1f%%', colors = color)
    ax[q].set_title(j + " - Energy demand: " + str(round(df_elec[j].sum()/10**6,2)) + " TWh")
    q = q + 1

#%%
mean_DK7 = network.links_t.p0.iloc[:,0].resample('D').mean()
mean_BE7 = network.links_t.p0.iloc[:,1].resample('D').mean()

fig_PF, ax_PF = plt.subplots(2, 1, figsize=(16,9), dpi=300)

plt.sca(ax_PF[0])
plt.xticks(fontsize=15, rotation = 45) 
plt.yticks(fontsize=15)
ax_PF[0].plot(network.links_t.p0.iloc[:,0],
              label='Hourly',
              color = 'tab:red',)
ax_PF[0].plot(mean_DK7, color='k',
              linewidth = 2,
              label = 'Daily')
# ax_PF[0].set_xlabel('Time [hr]', fontsize = 15)
ax_PF[0].set_ylabel('Powerflow [MW]', fontsize = 15)
ax_PF[0].get_xaxis().set_visible(False)
ax_PF[0].set_xlim([datetime.date(2015, 1, 1), datetime.date(2015,12,31)])
ax_PF[0].set_title('Powerflow from Germany to Denmark',
                    fontsize = 25)
# ax_PF[0].set_ylim(-100,3000)
ax_PF[0].legend(loc="upper right",
                fontsize = 15)

ax_PF[0].text(1.01, 1, 
               str(round(network.links_t.p0.iloc[:,0].describe(),1).reset_index().to_string(header=None, index=None)),
               ha='left', va='top', 
               transform=ax_PF[0].transAxes,
               fontsize = 14)
ax_PF[0].axhline(y=0, color='k', linestyle='--')
ax_PF[0].grid()
plt.tight_layout()

plt.sca(ax_PF[1])
plt.xticks(fontsize=15, rotation = 45)
plt.yticks(fontsize=15)
ax_PF[1].plot(network.links_t.p0.iloc[:,1],
              color = 'tab:blue',
              label = 'Hourly')
ax_PF[1].plot(mean_BE7, color='k', 
               linewidth = 2,
               label = 'Daily')
ax_PF[1].set_xlabel('Time [hr]', fontsize = 15)
ax_PF[1].set_ylabel('Powerflow [MW]', fontsize = 15)
ax_PF[1].set_xlim([datetime.date(2015, 1, 1), datetime.date(2015,12,31)])
ax_PF[1].set_title('Powerflow from Germany to France',
                    fontsize = 25)
# ax_PF[1].set_ylim(-100,3000)
ax_PF[1].legend(loc="lower right",
                fontsize = 15)

ax_PF[1].text(1.01, 1, 
               str(round(network.links_t.p0.iloc[:,1].describe(),1).reset_index().to_string(header=None, index=None)), 
               ha='left', va='top', 
               transform=ax_PF[1].transAxes,
               fontsize = 14)

ax_PF[0].get_shared_x_axes().join(ax_PF[0], ax_PF[1])
ax_PF[1].axhline(y=0, color='k', linestyle='--')
ax_PF[1].grid()
plt.tight_layout()
