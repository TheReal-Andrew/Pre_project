#%% Import packages
import pypsa
from pypsa.linopt import get_var, linexpr, join_exprs, define_constraints
import pandas as pd
import matplotlib.pyplot as plt
import system_add2
import numpy as np
import datetime
import matplotlib.colors as mcolors
import matplotlib.ticker as ticker

country = 'DEU'
allowance = 0.05 # [%] of 1990 CO2 levels
co2_e     = 0.19 # [TonCO2/MWh]
half      = 0.5

#%% Choose country

# Dataframe with country data. All emission data from https://www.worldometers.info/co2-emissions/
# CO2 Limit is the CO2 emission in 1990.

co2_dict = system_add2.get_co2(full = True)

if country == 'DNK':
    bus_df = pd.DataFrame(
        np.array([                          #Create numpy array with bus info
        ["Denmark","DNK", co2_dict['DNK']*half],
        ["Sweden", "SWE", co2_dict['SWE']*half],
        ["Norway", "NOR", co2_dict['NOR']*half],
        ],
        ),  
        columns = ["Country","Abbreviation","CO2_limit"])
else:
    bus_df = pd.DataFrame(
        np.array([                          #Create numpy array with bus info
        ["Germany","DEU", co2_dict['DEU']*half],   
        ["Denmark","DNK", co2_dict['DNK']*half],   
        ["France", "FRA", co2_dict['FRA']*half],
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
network.allow = allowance
network.co2_e = co2_e
hours_in_2015 = pd.date_range('2015-01-01T00:00Z','2015-12-31T23:00Z', freq='H')
network.set_snapshots(hours_in_2015)

network.bus_df = bus_df # Add bus_df as dataframe in the network

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
  
cc_hvac = system_add2.annuity(tech_life,0.07)*tech_inv*(1+tech_FOM)

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
        p_set   = df_elec[bus_df.Abbreviation[i]]*(1+0.018)**(35))       
    
#%% Add the different carriers and generators
system_add2.carriers(network)
    
for i in range(bus_df.shape[0]):
    system_add2.generators(network,bus_df['Abbreviation'][i],network.buses.index[i])
    system_add2.storages(network,bus_df['Abbreviation'][i],network.buses.index[i])
#%% Add storage
# system_add.storages(network)

#%% Add CO2 constraint

#%% 
def CO2(network, snapshots):
    var_gen  = get_var(network, 'Generator', 'p')
    
    CO2_e = network.co2_e # [TonCO2/MWh]
    red   = network.allow # CO2 Allowance in percent of 1990 levels
    
    lhs_DNK = linexpr((CO2_e, var_gen['OCGT (' + network.bus_df.Abbreviation[0] + ')'])).sum()
    rhs_DNK = float(network.bus_df.CO2_limit[0]) * red
    
    lhs_DEU = linexpr((CO2_e, var_gen['OCGT (' + network.bus_df.Abbreviation[1] + ')'])).sum()
    rhs_DEU = float(network.bus_df.CO2_limit[1]) * red
    
    lhs_FRA = linexpr((CO2_e, var_gen['OCGT (' + network.bus_df.Abbreviation[2] + ')'])).sum()
    rhs_FRA = float(network.bus_df.CO2_limit[2]) * red
    
    define_constraints(network, lhs_DNK, '<=', rhs_DNK, 'Generator', 'DNK_CO2')
    define_constraints(network, lhs_DEU, '<=', rhs_DEU, 'Generator', 'DEU_CO2')
    define_constraints(network, lhs_FRA, '<=', rhs_FRA, 'Generator', 'FRA_CO2')
    
def extra_functionality(network, snapshots):
    CO2(network, snapshots)

#%% Solve the system
network.lopf(
    # network.snapshots, 
             pyomo               = False,
             solver_name         = 'gurobi',
             extra_functionality = extra_functionality,
             keep_shadowprices   = True,
             keep_references     = True,
             )

#%% Plot the technology mix


fig1 = plt.figure('Figure 1')
fig1, ax = plt.subplots(nrows=1, ncols=3, figsize=(20, 20), dpi = 300)

# colors = list(mcolors.TABLEAU_COLORS.keys())

q = 0 # Country counter
for j in list(bus_df['Abbreviation']):
    sizes  = []
    labels = []
    l      = []
    
    for i in range(5):
        gen = (network.generators.loc[network.generators['bus'].str.endswith('('+j+')')] & network.generators.loc[network.generators.index.str.endswith('('+j+')')]).index[i]
        cap = network.generators.loc[network.generators.index.str.endswith('('+j+')')].index[i]
        
        colors = system_add2.get_colors(j)
        
        if network.generators_t.p[gen].sum() > 0:
            sizes = sizes + [network.generators_t.p[gen].sum()]
            l       = l + [gen]
            labels1 = gen[:-6]
            # labels2 = "Produced: "+str(round(network.generators_t.p[gen].sum()/10**6)) + " TWh"
            # labels3 = "Capacity: " + str(round(network.generators.p_nom_opt[cap]/10**3)) + " GW"
            labels  = labels + [labels1] #
        else:
            pass
    
    ax[q].pie(sizes, autopct='%.1f%%', # labels = labels
              colors = [colors[v] for v in l], textprops={'fontsize': 15})
    
    cols = [col for col in network.generators_t.p.columns if j in col]
    gen_val = round(network.generators_t.p[cols].sum().sum()/10**6, 2)
    
    ax[q].set_title(j + " demand: " + str(round(df_elec[j].sum()/10**6,2)) + " TWh,\nproduced: " + str(gen_val) + " TWh,\nstorage = " + str(round(network.stores.e_nom_opt[q]/10**3)) +' GW', fontsize = 20)
    q = q + 1

c = ['lightskyblue',    # Onshorewind
     'tab:blue',        # Offshorewind
     'orange',         # Solar utility 
     'gold',           # Solar rooftop
     'tab:purple',     # OCGT
     'tab:red',        # Boiler
     'darkorange',     # Heat pump
          ]    

ax[1].text(-1.8,0,'Link capacity:\n' + str(round(network.links.p_nom_opt[0]/10**3)) + ' GW', fontsize = 15, multialignment="center")
ax[2].text(-1.8,0,'Link capacity:\n' + str(round(network.links.p_nom_opt[1]/10**3)) + ' GW', fontsize = 15, multialignment="center")
colors = ['lightskyblue','tab:blue','orange','tab:purple']
patches, texts = plt.pie(sizes, colors=colors)
ax[1].legend(patches, labels[:], loc="lower center", ncol = 2, fontsize = 15)
fig1.tight_layout()    
plt.savefig('graphics/' + str(country) + '_G_mix.pdf', format = 'pdf', bbox_inches='tight') 

print('\n')
print(network.links.p_nom_opt.to_latex())

#%%
mean_DK7 = network.links_t.p0.iloc[:,0].resample('D').mean()/10**3
mean_BE7 = network.links_t.p0.iloc[:,1].resample('D').mean()/10**3

fig_PF, ax_PF = plt.subplots(2, 1, figsize=(14,7.5), dpi=300)

plt.sca(ax_PF[0])
plt.xticks(fontsize=15, rotation = 45) 
plt.yticks(fontsize=15)
ax_PF[0].plot(network.links_t.p0.iloc[:,0]/10**3,
              label='Hourly',
              color = 'tab:red',)
ax_PF[0].plot(mean_DK7, color='k',
              linewidth = 2,
              label = 'Daily')
# ax_PF[0].set_xlabel('Time [hr]', fontsize = 15)
ax_PF[0].set_ylabel('Powerflow [GW]', fontsize = 15)
ax_PF[0].get_xaxis().set_visible(False)
ax_PF[0].set_xlim([datetime.date(2015, 1, 1), datetime.date(2015,12,31)])
ax_PF[0].set_ylim([-125,125])
ax_PF[0].set_title('Powerflow from '+ bus_df['Country'][0] + ' to ' + bus_df['Country'][1],
                    fontsize = 25)
# ax_PF[0].set_ylim(-100,3000)
ax_PF[0].legend(loc="upper right",
                fontsize = 15)

ax_PF[0].text(1.01, 1, 
               str(round((network.links_t.p0.iloc[:,0]/10**3).describe(),1).reset_index().to_string(header=None, index=None)),
               ha='left', va='top', 
               transform=ax_PF[0].transAxes,
               fontsize = 14)
ax_PF[0].axhline(y=0, color='k', linestyle='--')
ax_PF[0].grid()

ax_PF[0].yaxis.set_major_locator(ticker.MultipleLocator(25))
ax_PF[0].yaxis.set_minor_locator(ticker.MultipleLocator(5))

plt.tight_layout()

plt.sca(ax_PF[1])
plt.xticks(fontsize=15, rotation = 45)
plt.yticks(fontsize=15)
ax_PF[1].plot(network.links_t.p0.iloc[:,1]/10**3,
              color = 'tab:blue',
              label = 'Hourly')
ax_PF[1].plot(mean_BE7, color='k', 
               linewidth = 2,
               label = 'Daily')
ax_PF[1].set_xlabel('Time [hr]', fontsize = 15)
ax_PF[1].set_ylabel('Powerflow [GW]', fontsize = 15)
ax_PF[1].set_xlim([datetime.date(2015, 1, 1), datetime.date(2015,12,31)])
ax_PF[1].set_ylim([-125,125])
ax_PF[1].set_title('Powerflow from '+ bus_df['Country'][0] + ' to ' + bus_df['Country'][2],
                    fontsize = 25)
# ax_PF[1].set_ylim(-100,3000)
ax_PF[1].legend(loc="upper right",
                fontsize = 15)

ax_PF[1].text(1.01, 1, 
               str(round((network.links_t.p0.iloc[:,1]/10**3).describe(),1).reset_index().to_string(header=None, index=None)), 
               ha='left', va='top', 
               transform=ax_PF[1].transAxes,
               fontsize = 14)

ax_PF[0].get_shared_x_axes().join(ax_PF[0], ax_PF[1])
ax_PF[1].axhline(y=0, color='k', linestyle='--')
ax_PF[1].grid()

# ax_PF[1].xaxis.set_major_locator(ticker.MultipleLocator())
ax_PF[1].xaxis.set_minor_locator(ticker.MultipleLocator(7))
ax_PF[1].yaxis.set_major_locator(ticker.MultipleLocator(25))
ax_PF[1].yaxis.set_minor_locator(ticker.MultipleLocator(5))

plt.tight_layout()

plt.savefig('graphics/' + str(country) + '_G_data.pdf', format = 'pdf', bbox_inches='tight') 