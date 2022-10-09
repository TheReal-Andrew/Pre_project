# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 11:39:45 2022

@author: lukas
"""

import pypsa
import numpy as np
import matplotlib as plt
import cartopy.crs as ccrs
import pandas as pd

network = pypsa.Network()       #Create network

network.add(
    "Bus",
    "Generator Bus",
    )

network.add(
    "Bus",
    "H2 Bus"
    )

network.add(
    "Link",
    "Converter Link",
    bus0 = "Generator Bus",
    bus1 = "H2 Bus",
    efficiency = 0.8,
    p_nom = 2000,
    )

network.add(
    "Generator",
    "Gen1",
    bus = "Generator Bus",
    p_nom = 1000,
    )

network.add(
    "Store",
    "H2 store",
    bus = "H2 Bus",
    e_nom = 2000,
    )

network.add(
    "Load",
    "Generator Load",
    p_set = 
    )