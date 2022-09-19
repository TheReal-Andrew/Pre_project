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
                     "Biofuels & Waste",        #0
                     "Coal",                    #1
                     "Hydro",                   #2
                     "Natural Gas",             #3
                     "Oil",                     #4
                     "Wind, Solar, etc",        #5
                
                     "Electricity Production",  #6
                     
                     #Final Energy
                     "Refined PC.",             #7
                     "Natural Gas",             #8
                     "Coal, Coke",              #9
                     "Electricity",             #10
                     "Other",                   #11
                     
                     "Energetic Services",      #12
                     
                     #Sector
                     "Agriculture",             #13
                     "Commerical & Co.",        #14
                     "Industry",                #15
                     "Residential",             #16
                     "Transport",               #17       
                    ],
            'x': [x[0], x[0], x[0], x[0], x[0], x[0], x[0], x[0], x[1], x[2], x[2], x[2], x[2], x[2], x[2], x[3], x[4], x[4], x[4]],
            'y': [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        },
    link = dict(
        source = [ 0,  0,  1,  2,  3,  3,  4,  4,  5,  6,  6,  7,  7,  8,  9, 10, 11, 12, 13, 14, 15, 15, 15],
        target = [11,  8,  8,  8,  8,  9,  8, 10,  8,  8, 13,  8, 14, 12, 15, 15, 15, 15, 15, 15, 16, 17, 18],
        value  = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 80, 10, 10, 10, 80, 10, 10, 30, 50, 50]  
        )
    )])

fig.update_layout(title_text="Basic Sankey Diagram", font_size=10)
fig.show()

fig