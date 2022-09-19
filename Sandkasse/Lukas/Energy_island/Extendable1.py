# -*- coding: utf-8 -*-
"""
Created on Mon Sep 19 09:54:08 2022

@author: lukas
"""

import pandas as pd
import pypsa
import numpy as np

# Load Data
cprice = pd.read_csv('data/market/price_2030.csv', index_col = 0)
cload  = pd.read_csv('data/market/load_2030.csv',  index_col = 0)

#%% Pypsa
network = pypsa.Network()

t = pd.date_range('2019-01-01 00:00', '2019-12-31 23:00', freq = 'H')

network.set_snapshots(t)

# Add buses
network.add("Bus",
            "Bus1",
            )

network.add("Generator",
            "Gen1",
            bus = "Bus1",
            p_nom = 10,
            p_nom_extendable = True,
            capital_cost = 0,
            marginal_cost = cprice["DK"].values
            )

network.add("Load",
            "Load1",
            bus = "Bus1",
            p_set = cload["DK"].values,
            )

#network.lopf()
