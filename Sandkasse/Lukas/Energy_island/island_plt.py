# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 18:58:40 2022

@author: lukas & anders
"""

def powerflow(network):
    import matplotlib.pyplot as plt
    import numpy as np
    
    fig, axs = plt.subplots(3, 2)  # Set up subplot with 4 plots
    plt.figure(dpi=300)         # Set resolution
    axs = axs.ravel()
    
    colors = ["tab:red", 
              "forestgreen", 
              "gold", 
              "tab:orange", 
              "tab:brown", 
              "tab:blue"]
    
    for i in np.arange(0,6):
        network.links_t.p0.iloc[:,i].plot(
            ax = axs[i],
            figsize = (17,13),
            title = network.links_t.p0.columns[i],
            color = colors[i],
            )
        
    fig.tight_layout()


#%% Makeplots
def makeplots(network, xscale=12, yscale=12, location = "upper left"):
    #This function plots the network loads, produced power, energy in and out
    #of the battery, and the energy level in the battery. 
    #By default, this is plotted in one subplot, but can be plotted in 
    #individual plots by setting subplots=False.
    
    import matplotlib.pyplot as plt
    
    # ---- Create subplots -----------------------------------------
    
    fig, axs = plt.subplots(2)  # Set up subplot with 4 plots
    plt.figure(dpi=600)         # Set resolution
    
    #---- Subplot 1 ----
    network.loads_t.p.plot(              #Plot loads 
        ax = axs[0],                     #Choose axis in subplot
        ylabel = "Consumed power, [MW]", #Set ylabel
        figsize = (xscale,yscale),        #Set scaling
        )
    axs[0].grid(visible = True, which = 'both')
    
    #---- Subplot 2 ----
    network.generators_t.p.plot(      #Plot generated power
        ax=axs[1],                    #Choose axis in subplot
        ylabel="Produced power [MW]", #Set ylabel
        figsize = (xscale,yscale),    #Set scaling
        #grid = True
        )
    axs[1].grid(visible = True, which = 'both')
    
    # #---- Subplot 3 ----
    #     network.stores_t.p.plot(        #Plot energy in and out of battery
    #         ax = axs[2],                #Choose axis in subplot
    #         ylabel="Active power flow [MW]", #Set ylabel
    #         figsize = (xscale,yscale)   #Set scaling
    #         )  
    #     axs[2].grid(visible = True, which = 'both')
            
        
    # #---- Subplot 4 ---
    #     network.stores_t.e.plot(        #Plot stored energy
    #         ax = axs[3],                #Choose axis in subplot
    #         ylabel="Stored power [MW]", #Set ylabel
    #         figsize = (xscale,yscale),   #Set scaling
    #         #grid = True
    #         )   
    #     axs[3].grid(visible = True, which = 'both')
        
    #---- Legend location loop ----
    for i in range(2): #Loop through subplots and change legend location
        axs[i].legend(loc=location) 
