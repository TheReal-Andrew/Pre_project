# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 18:58:40 2022

@author: lukas & anders
"""

#%% Geographical plot
def geomap(network, bounds = [-3, 12, 59, 50.5], size = (15,15)):
    #Plots geographical map with buses and links shown
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    
    plt.rc("figure", figsize = size)   #Set plot resolution

    network.plot(
        color_geomap = True,            #Coloring on oceans
        boundaries = bounds,            #Boundaries of the plot as [x1,x2,y1,y2]
        projection=ccrs.EqualEarth()    #Choose cartopy.crs projection
        )

#%% Powerflow plot
def powerflow(network, size = (17,13)):
    #Plots power flow from island to country buses.
    import matplotlib.pyplot as plt
    import numpy as np
    
    fig, axs = plt.subplots(3, 2)  # Set up subplot with 4 plots
    plt.figure(dpi=300)            # Set resolution
    axs = axs.ravel()
    
    colors = {"DK":"tab:red", 
              "NO":"forestgreen", 
              "DE":"gold", 
              "NE":"tab:orange", 
              "BE":"tab:brown", 
              "GB":"tab:blue"}
    
    for i in np.arange(0,6):
        network.links_t.p0.iloc[:,i].plot(
            ax = axs[i],
            figsize = size,
            title = network.links_t.p0.columns[i],
            color = colors[list(colors)[i]],
            )
        
    fig.tight_layout()


#%% Power consumption and power production plots
def loads_generators(network, size = (12, 12), location = "upper left"):
    #Plots all power consumption and power generation over time.
    import matplotlib.pyplot as plt
    
    fig, axs = plt.subplots(2)  # Set up subplot
    plt.figure(dpi=600)         # Set resolution
    
    #---- Subplot 1 ----
    network.loads_t.p.plot(              #Plot loads 
        ax = axs[0],                     #Choose axis in subplot
        ylabel = "Consumed power, [MW]", #Set ylabel
        figsize = size,                  #Set scaling
        grid = True,
        )
    
    #---- Subplot 2 ----
    network.generators_t.p.plot(      #Plot generated power
        ax      = axs[1],                    #Choose axis in subplot
        ylabel  = "Produced power [MW]", #Set ylabel
        figsize = size,               #Set scaling
        grid = True,
        )
        
    #---- Legend location loop ----
    for i in range(len(axs)): #Loop through subplots and change legend location
        axs[i].legend(loc=location) 

#%% Correlation Matrix

def corr_matrix(data, title='', fsize = 20, size = (15,15)):
    import matplotlib.pyplot as plt
    import numpy as np
    
    #Get column names as list
    columns = data.columns.tolist()
    
    #Create figure
    fig = plt.figure(figsize = size)
    axes = fig.add_subplot(111)
    
    #Use matshow to visually represent correlation matrix values
    axes.matshow(data.corr())
    
    #Change ticks to be titles instead of numbers
    axes.set_xticklabels([''] + columns)
    axes.set_yticklabels([''] + columns)
    
    #Set and format title
    axes.set_title(title,
                   fontweight = "bold",
                   fontsize = fsize)
    
    #Add correlation values in each cell
    for (i, j), z in np.ndenumerate(data.corr()):
        axes.text(j, i, '{:0.1f}'.format(z), ha='center', va='center',
            bbox=dict(boxstyle='square', facecolor='white', edgecolor='0.3'))

    fig.tight_layout()
    
    
    
    
    
    
    
    
    
    
    
    
    