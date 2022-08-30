# -*- coding: utf-8 -*-
"""
Created on Fri Aug 26 09:25:32 2022

@author: lukas
"""

"Import"
import pypsa

"Set up network"
network = pypsa.Network()

#%% Set up buses
nbus = 5
for i in range(nbus):
    network.add("Bus",
                "Bus {}".format(i),
                v_nom = 132)        #Voltage, [KV]
    
#%% Add Lines
for i in range(nbus-1):
    network.add("Line", 
                "Line {}".format(i),            #Line name
                bus0 = "Bus {}".format(i),      #Start bus
                bus1 = "Bus {}".format(i+1),    #End bus
                r = 0.02    ,                   #DC Resistance [Ohm]
                x = 0.3                         #AC Resistance [Ohm]
                )
    
#%% Add Generators
#Slack generator
network.add("Generator", "Slack Gen",
            bus = "Bus 0",
            p_set = 0,
            control = "Slack"
            )

network.add("Generator", "Gen 1",
            bus = "Bus 3",
            p_set = 60,                         #Set power, [MW]
            control = "PV")

#%% Add Loads
network.add("Load","Load 1",
            bus = "Bus 4",
            p_set = 90,       #Set power, [MW]
            q_set = 40        #Reactive power, Mega Volt Ampere Reactive [MVar]
            )

#%% Solve
network.pf()


























