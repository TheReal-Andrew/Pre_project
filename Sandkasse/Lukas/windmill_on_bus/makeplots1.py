# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 18:58:40 2022

@author: lukas
"""
import numpy as np
import matplotlib.pyplot as plt

def makeplots(network,subplots=True, aspect_ratio=0.2,xscale=6,yscale=12,location = "upper left"):
    #This function plots the network loads, produced power, energy in and out
    #of the battery, and the energy level in the battery. 
    #By default, this is plotted in one subplot, but can be plotted in 
    #individual plots by setting subplots=False.
    
    #%% create subplots
    if subplots == True:
        
        fig, axs = plt.subplots(4)  # Set up subplot with 4 plots
        plt.figure(dpi=300)         # Set resolution
        
    #---- Subplot 1 ----------------------------
        network.loads_t.p.plot(              #Plot loads 
            ax = axs[0],                     #Choose axis in subplot
            ylabel = "Consumed power, [MW]", #Set ylabel
            figsize = (xscale,yscale),        #Set scaling
            )
        axs[0].grid(visible = True, which = 'both')
        
    #---- Subplot 2 ----------------------------
        network.generators_t.p.plot(      #Plot generated power
            ax=axs[1],                    #Choose axis in subplot
            ylabel="Produced power [MW]", #Set ylabel
            figsize = (xscale,yscale),    #Set scaling
            #grid = True
            )
        axs[1].grid(visible = True, which = 'both')
    
    #---- Subplot 3 ----------------------------
        network.stores_t.p.plot(        #Plot energy in and out of battery
            ax = axs[2],                #Choose axis in subplot
            ylabel="Active power flow [MW]", #Set ylabel
            figsize = (xscale,yscale)   #Set scaling
            )  
        axs[2].grid(visible = True, which = 'both')
            
        
    #---- Subplot 4 ----------------------------
        network.stores_t.e.plot(        #Plot stored energy
            ax = axs[3],                #Choose axis in subplot
            ylabel="Stored power [MW]", #Set ylabel
            figsize = (xscale,yscale),   #Set scaling
            #grid = True
            )   
        axs[3].grid(visible = True, which = 'both')
        
    #---- Legend location loop -----------------
        for i in range(4): #Loop through subplots and change legend location
            axs[i].legend(loc=location) 
    
    #%% Create individual plots
    else: 
    #---- Plot 1 ----------------------------
        plot1 = network.loads_t.p.plot(       #Plot loads 
            ylabel = "Consumed power, [MW]",  #Set ylabel
            figsize = (yscale,xscale),        #Set scaling
            )    
        plot1.legend(loc=location)            #Set legend location

    #---- Plot 2 ----------------------------
        plot2 = network.generators_t.p.plot(  #Plot generated power
            ylabel="Produced power [MW]",
            figsize = (yscale,xscale)
            ) 
        plot2.legend(loc=location)
        
    #---- Plot 3 ----------------------------
        plot3 = network.stores_t.p.plot(      #Plot energy in and out of battery
            ylabel="Active power [MW]",
            figsize = (yscale,xscale)
            )
        plot3.legend(loc=location)
        
    #---- Plot 4 ----------------------------
        plot4 = network.stores_t.e.plot(      #Plot stored power
            ylabel="Stored power [MW]",
            figsize = (yscale,xscale)
            )   
        plot4.legend(loc=location)
        