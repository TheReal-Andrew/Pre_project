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
        valuesuffix = " PJ",
        node = {
            'pad': 5,
            'thickness': 40,
            'line': {'color': "Black", 
                     'width': 1},
            'label': [#Primary Energy
                     "Oil production",          #0
                     "Oil import",              #1
                     "Coal import",             #2
                     "Natural Gas",             #3
                     "Gas import",              #4
                     "Biofuel & Waste",         #5
                     "Electricity import",      #6
                     "Solar/Tide/Wind",         #7
                
                     "Power Plants",            #8
                     "Oil products",            #9
                     
                     #Final Energy
                     "Oil",                     #10
                     "Natural Gas",             #11
                     "Coal, Coke",              #12
                     "Biofuel & Waste",         #13
                     "Electricity",             #14
                     "Heat",                    #15
                     
                     #Sector
                     "Industry",                #16
                     "Transport",               #17
                     "Other",                   #18
                    ],
            # 'x': [x[0], x[0], x[0], x[0], x[0], x[0], x[0], x[0], x[1], x[2], x[2], x[2], x[2], x[2], x[2], x[3], x[4], x[4], x[4]],
            # 'y': [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        },
    link = dict(
        source = [    0,     1,   9,   9,    2,    3,     5,    6,     7,     8,   8,   14,  15, ],
        target = [    9,     9,   8,  17,    8,    8,     8,   14,     8,    14,  15,   16,  16,],
        value  = [215.7, 252.7, 3.3, 220, 33.5, 29.8, 124.7, 57.5,  63.9, 103.6, 137, 29.9, 3.2,]  
        )
    )])

fig.update_layout(title_text="Basic Sankey Diagram", font_size=10)
fig.show()

fig