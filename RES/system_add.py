def annuity(n,r):
    
        if r > 0:
            return r/(1. - 1./(1.+r)**n)
        else:
            return 1/n
        
def carriers(network):
    # locals()["co2_emission_" + country] = 0.19
    network.add("Carrier", "gas", co2_emissions = 0.19) # in t_CO2/MWh_th
    network.add("Carrier", "onshorewind")
    network.add("Carrier", "offshorewind")
    network.add("Carrier", "solar_utility")
    network.add("Carrier", "solar_rooftop")
    network.add("Carrier", "hydro_storage")
    network.add("Carrier", "lithium_storage")
        
def storages(network):
    
    capital_cost_hydro = annuity(80,0.07)*2000000*(1+0.1) # in €/MW

    # network.add("Store",
    #       "Hydro_storage",
    #       bus               = "electricity bus",
    #       carrier           = "hydro_storage",
    #       e_nom_extendable  = True,
    #       e_cyclic          = True,
    #       # capital_cost      = capital_cost_hydro, #[EUR/MWh] Capital cost for Storage
    #       capital_cost = 0,
    #       # capital_cost      = 0, #[EUR/MWh] Capital cost for Storage
    #       # marginal_cost     = 40/0.75,
    #       marginal_cost     = 0,
    #       # e_nom_max         = 11022, #https://www.hydropower.org/country-profiles/germany
    #       )
    
    cc_lithium = annuity(15,0.07)*1.288*10**6*(1+0.1)
    
    network.add("Store",
          "Lithium_storage",
          bus                   = "electricity bus",
          carrier               = "lithium_storage",
          e_nom_extendable      = True,
          e_cyclic              = True,
          capital_cost          = cc_lithium, #[EUR/MWh] Capital cost for Storage
           # capital_cost          = 0,
          marginal_cost         = 2.1,
          efficiency_store      = 0.98,
          efficiency_dispatch   = 0.97,
          )

def generators(network,country,bus):
    import pandas as pd
    
    # Load cost data
    tech_cost = pd.read_csv('https://github.com/PyPSA/technology-data/blob/master/inputs/costs_PyPSA.csv?raw=true')
    
    #---------------------------
    # Add onshore wind generator
    df_onshorewind           = pd.read_csv('data/onshore_wind_1979-2017.csv', sep=';', index_col=0)
    df_onshorewind.index     = pd.to_datetime(df_onshorewind.index)
    CF_wind_onshore          = df_onshorewind[country][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]
    
    tech_name = 'onwind'
    tech_inv  = 1000*float(tech_cost.loc[tech_cost['parameter'].str.startswith('investment') & tech_cost['technology'].str.startswith(tech_name)].value)
    tech_life = float(tech_cost.loc[tech_cost['parameter'].str.startswith('lifetime') & tech_cost['technology'].str.startswith(tech_name)].value)
    tech_FOM  = 0.01*float(tech_cost.loc[tech_cost['parameter'].str.startswith('FOM') & tech_cost['technology'].str.startswith(tech_name)].value)
    
    cc_onshorewind = annuity(tech_life,0.07)*tech_inv*(1+tech_FOM) # in €/MW
    # cc_onshorewind = annuity(30,0.07)*910000*(1+0.033) # in €/MW
    
    network.add("Generator", 
                "Onshorewind (" + country +")",
                bus              = bus,
                p_nom_extendable = True,
                carrier          = "onshorewind",
                capital_cost     = cc_onshorewind,
                marginal_cost    = 0,
                p_nom_max        = 115*10**9, #https://www.reuters.com/business/energy/germany-introduce-bill-accelerate-wind-energy-expansion-document-2022-06-07/
                p_max_pu         = CF_wind_onshore,
                # p_nom_max        = max_cap,
                )
    
    #----------------------------
    # Add offshore wind generator
    df_offshorewind           = pd.read_csv('data/offshore_wind_1979-2017.csv', sep=';', index_col=0)
    df_offshorewind.index     = pd.to_datetime(df_offshorewind.index)
    CF_wind_offshore          = df_offshorewind[country][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]
    
    tech_name = 'offwind'
    tech_inv  = 1000*float(tech_cost.loc[tech_cost['parameter'].str.startswith('investment') & tech_cost['technology'].str.endswith(tech_name)].value)
    tech_life = float(tech_cost.loc[tech_cost['parameter'].str.startswith('lifetime') & tech_cost['technology'].str.endswith(tech_name)].value)
    tech_FOM  = 0.01*float(tech_cost.loc[tech_cost['parameter'].str.startswith('FOM') & tech_cost['technology'].str.endswith(tech_name)].value)
   
    cc_offshorewind = annuity(tech_life,0.07)*tech_inv*(1+tech_FOM) # in €/MW
    # cc_offshorewind = annuity(25,0.07)*2506000*(1+0.03) # in €/MW
    
    network.add("Generator",
                "Offshorewind (" + country +")",
                bus              = bus,
                p_nom_extendable = True,
                carrier          = "offshorewind",
                capital_cost     = cc_offshorewind,
                marginal_cost    = 0,
                p_max_pu         = CF_wind_offshore)
    
    #-------------------------------
    # Add utility solar PV generator
    df_solar_utility           = pd.read_csv('data/pv_optimal.csv', sep=';', index_col=0)
    df_solar_utility.index     = pd.to_datetime(df_solar_utility.index)
    CF_solar_utility           = df_solar_utility[country][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]
    
    tech_name = 'solar-utility'
    tech_inv  = 1000*float(tech_cost.loc[tech_cost['parameter'].str.startswith('investment') & tech_cost['technology'].str.startswith(tech_name)].value)
    tech_life = float(tech_cost.loc[tech_cost['parameter'].str.startswith('lifetime') & tech_cost['technology'].str.startswith(tech_name)].value)
    tech_FOM  = 0.01*float(tech_cost.loc[tech_cost['parameter'].str.startswith('FOM') & tech_cost['technology'].str.startswith(tech_name)].value)
    
    cc_solar_utility = annuity(tech_life,0.07)*tech_inv*(1+tech_FOM) # in €/MW
    # cc_solar_utility = annuity(25,0.07)*425000*(1+0.03) # in €/MW
    
    network.add("Generator",
                "Solar_utility (" + country +")",
                bus              = bus,
                p_nom_extendable = True,
                carrier          = "solar_utility",
                capital_cost     = cc_solar_utility,
                marginal_cost    = 0,
                p_max_pu         = CF_solar_utility,
                # p_nom_max        = max_cap,
                )
    
    #-------------------------------
    # Add rooftop solar PV generator
    df_solar_rooftop           = pd.read_csv('data/pv_rooftop.csv', sep=';', index_col=0)
    df_solar_rooftop.index     = pd.to_datetime(df_solar_rooftop.index)
    CF_solar_rooftop           = df_solar_rooftop[country][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]
    
    tech_name = 'solar-rooftop'
    tech_inv  = 1000*float(tech_cost.loc[tech_cost['parameter'].str.startswith('investment') & tech_cost['technology'].str.startswith(tech_name)].value)
    tech_life = float(tech_cost.loc[tech_cost['parameter'].str.startswith('lifetime') & tech_cost['technology'].str.startswith(tech_name)].value)
    tech_FOM  = 0.01*float(tech_cost.loc[tech_cost['parameter'].str.startswith('FOM') & tech_cost['technology'].str.startswith(tech_name)].value)
    
    cc_solar_rooftop = annuity(tech_life,0.07)*tech_inv*(1+tech_FOM) # in €/MW
    # cc_solar_rooftop = annuity(25,0.04)*725000*(1+0.02) # in €/MW
    
    network.add("Generator",
                "Solar_rooftop (" + country +")",
                bus              = bus,
                p_nom_extendable = True,
                carrier          = "solar_rooftop",
                capital_cost     = cc_solar_rooftop,
                marginal_cost    = 0,
                p_max_pu         = CF_solar_rooftop,
                # p_nom_max        = max_cap,
                )
    
    #--------------------------------------------
    # Add OCGT (Open Cycle Gas Turbine) generator
    tech_name = 'OCGT'
    tech_inv  = 1000*float(tech_cost.loc[tech_cost['parameter'].str.startswith('investment') & tech_cost['technology'].str.startswith(tech_name)].value)
    tech_life = float(tech_cost.loc[tech_cost['parameter'].str.startswith('lifetime') & tech_cost['technology'].str.startswith(tech_name)].value)
    tech_FOM  = 0.01*float(tech_cost.loc[tech_cost['parameter'].str.startswith('FOM') & tech_cost['technology'].str.startswith(tech_name)].value)
    
    cc_OCGT = annuity(tech_life,0.07)*tech_inv*(1+tech_FOM) # in €/MW
    # cc_OCGT  = annuity(25,0.07)*560000*(1+0.033) # in €/MW
    
    fuel_cost          = 21.6 # in €/MWh_th
    efficiency         = 0.39
    mc_OCGT = fuel_cost/efficiency # in €/MWh_el
    
    network.add("Generator",
                "OCGT (" + country +")",
                bus              = bus,
                p_nom_extendable = True,
                carrier          = "gas",
                capital_cost     = cc_OCGT,
                marginal_cost    = mc_OCGT,
                # p_nom_max        = max_cap,
                )
    
    #--------------------------------------------
    # Add gas boiler generator
    # cc_gas_boiler   = annuity(20,0.07)*63000*(1+0.015) # in €/MW
    # fuel_cost       = 21.6 # in €/MWh_th
    # efficiency      = 0.9
    # mg_gas_boiler   = fuel_cost/efficiency # in €/MWh_el
    
    # network.add("Generator",
    #             "Gas boiler (" + country +")",
    #             bus              = bus,
    #             p_nom_extendable = True,
    #             carrier          = "gas",
    #             capital_cost     = cc_gas_boiler,
    #             marginal_cost    = mg_gas_boiler)