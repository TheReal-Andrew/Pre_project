# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 14:17:09 2022

@author: lukas
"""

import plotly.io as pio
pio.renderers.default='browser'

import plotly.graph_objects as go
import numpy as np

#%% Set up

#Columns
ncols = 5

#X values
x = np.linspace(0.1, 1, ncols) #Create array of x spaces

#%% Plotting
fig = go.Figure(
    data = [go.Sankey(
        arrangement = "snap",
        valuesuffix = " TWh",
        node = {
            'pad': 5,
            'thickness': 40,
            'line': {'color': "Black", 
                     'width': 1},
            'label': [#Primary Energy
                     "Crude Oil",               #0
                     "Natural Gas",             #1
                     "Solar",                   #2
                     "Wind",                    #3
                     "Other Renewable Energy",  #4
                     "Waste",                   #5
                     "Renewable Energy Import", #6
                     "Coal Import",             #7
                
                     "Electricity Production",  #8
                     
                     #Final Energy
                     "Oil",                     #9
                     "Natural Gas",             #10
                     "Coal, Coke",              #11
                     "Waste",                   #12
                     "Renewable Energy",        #13
                     "Electricity",             #14
                     "Other",                   #15
                     
                     "Energetic Services",      #16
                     
                     #Sector
                     "Agriculture",             #17
                     "Industry",
                     "Commerical & Public",     #18
                     "Households",              #19     
                    ],
            # 'x': [x[0], x[0], x[0], x[0], x[0], x[0], x[0], x[0], x[1], x[2], x[2], x[2], x[2], x[2], x[2], x[3], x[4], x[4], x[4]],
            # 'y': [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        },
    link = dict(
        source = [ 0,       0,    1,     1,    2, 3,],
        target = [ 8,       9,    8,    10,    8, 8,],
        value  = [947, 150422, 3576, 46287, 4252, 58789,]  
        )
    )])

fig.update_layout(title_text="Basic Sankey Diagram", font_size=10)
fig.show()

fig