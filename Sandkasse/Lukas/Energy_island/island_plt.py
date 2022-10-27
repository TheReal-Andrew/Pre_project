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

def corr_matrix(data, title='', fsize = 20, size = (15,15),  vmin = 0 ):
    import seaborn as sn
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np
    matplotlib.rcParams['font.family'] = ['cmss10']
    
    #Show correlation matrix heatmap with 
    corr = data.corr()
    
    mask = np.triu(np.ones_like(corr))
    
    cmap = sn.diverging_palette(10, 130, as_cmap=True)
    ax = sn.heatmap(corr,
               annot=True, mask = mask, square = True, cbar_kws={"shrink": .82},
               linewidth = 1, cmap = cmap, vmin = vmin)
    
    ax.set_title(title, fontsize = 20, fontweight = "bold",)
    
    plt.show()
    
#%% Price diff

def plot_price_diff(opt_prices):
    import matplotlib.pyplot as plt
    import numpy as np
    
    fig, axs = plt.subplots(6, sharey = True)  # Set up subplot
    plt.figure(dpi=600)         # Set resolution
    country_price = opt_prices.iloc[:,1:]
    
    colors = {"DK":"tab:red", 
              "NO":"forestgreen", 
              "DE":"gold", 
              "NE":"tab:orange", 
              "BE":"tab:brown", 
              "GB":"tab:blue"}

    for i in range(len(country_price.columns)):
        diff = country_price.iloc[:,i] - opt_prices.iloc[:,0]
        
        axs[i].plot(diff.values,
                    color = colors[list(colors)[i]])
        axs[i].grid()
        
        axs[i].set_ylabel("Euro per MWh")
        
        axs[i].set_title("Price difference, Island to " +str(country_price.columns[i]))
        
        axs[i].fill_between(np.arange(len(diff)), diff,
                            color = colors[list(colors)[i]],
                            alpha = 0.2)
        
    fig.tight_layout()
    
#%% Bus Prices
def plot_bus_prices(opt_prices):
    import matplotlib.pyplot as plt
    import numpy as np
    
    fig, axs = plt.subplots(7, sharey = True)  # Set up subplot
    plt.figure(dpi=600)         # Set resolution
    
    colors = {"IL":"black",
              "DK":"tab:red", 
              "NO":"forestgreen", 
              "DE":"gold", 
              "NE":"tab:orange", 
              "BE":"tab:brown", 
              "GB":"tab:blue"}
    
    for i in range(len(opt_prices.columns)):
        axs[i].plot(opt_prices.iloc[:,i].values,
                    color = colors[list(colors)[i]])
        #axs[i].set_ylim([None, opt_prices.values.ravel().max()])
        axs[i].grid()
        axs[i].set_ylabel("Euro per MWh")
        axs[i].set_title(str(opt_prices.columns[i]) + " - Electricity price")
        axs[i].fill_between(np.arange(len(opt_prices)),opt_prices.iloc[:,i].values,
                            color = colors[list(colors)[i]],
                            alpha = 0.2)
        
    fig.tight_layout()
    
    
    
    
    
    
    
    
    
    
    
    