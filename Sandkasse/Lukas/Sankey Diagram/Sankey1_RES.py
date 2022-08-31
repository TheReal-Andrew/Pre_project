# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 14:17:09 2022

@author: lukas
"""

import plotly.io as pio
pio.renderers.default='browser'

import plotly.graph_objects as go
import numpy as np

fig = go.Figure(
    data = [go.Sankey(
        node = dict(
            pad = 5,
            thickness = 10,
            line = dict(color = "Black",width = 0.5),
            label = [#Primary Energy
                     "Coal",                   #0
                     "Nuclear",                #1
                     "Wind",                   #2
                     "Crude Oil",              #3
                     "Natural gas",            #4
                     "Hydro",                  #5
                     "Traditional Fuels",      #6
                     "Other",                  #7
                
                     "Electricity Production", #8
                     
                     #Final Energy
                     "Refined PC.",            #9
                     "Natural Gas",            #10
                     "Coal, Coke",             #11
                     "Electricity",            #12
                     "Traditional Fuels",      #13
                     "Other"                   #14
                    ], 
        ),
    link = dict(
        source = [ 0,  0,  1,  2,  3,  3,  4,  4,  5,  6,  6,  7,  7,  8],
        target = [11,  8,  8,  8,  8,  9,  8, 10,  8,  8, 13,  8, 14, 12],
        value  = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 80]  
        )
    )])

fig.update_layout(title_text="Basic Sankey Diagram", font_size=10)
fig.show()

fig