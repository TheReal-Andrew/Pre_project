# -*- coding: utf-8 -*-
"""
Created on Thu Aug 25 11:56:07 2022

@author: lukas
"""

"---- IMPORTS ----"
import pypsa
import numpy as np

"Initialize network"
network = pypsa.Network()

"Add 3 buses"

n_buses = 3
for i in range(n_buses):
    network.add("Bus",
                "Bus nr {}".format(i),
                v_nom = 20.0)
    
"Add connectnig lines between buses"

for i in range(n_buses):
    network.add(
        "Line",
        "Line nr {}".format(i),
        bus0 = "Bus nr {}".format(i),
        bus1 = "Bus nr {}".format((i+1) % n_buses),
        x = 0.1,
        r = 0.01)
    
"Add generator at bus 0"
network.add("Generator",
            "Gen",
            bus = "Bus nr 0",
            p_set = 100, 
            control = "PQ")

"Add load at bus 1"
network.add("Load","Load1", bus = "Bus nr 1", p_set = 100)

"Reactive load fix"
network.loads.q_set = 100

"Newton-Raphson power flow"
network.pf()
