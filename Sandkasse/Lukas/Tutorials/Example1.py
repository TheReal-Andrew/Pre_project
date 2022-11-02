# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 13:21:36 2022

@author: lukas
"""

import pypsa
import matplotlib as plt

n = pypsa.examples.ac_dc_meshed(from_master = True)

plt.rc("figure", figsize = (10,10)) 
n.plot()

n.add(
      "Generator",
      "Frankfurt Wind 2",
      bus = "Frankfurt",
      capital_cost = 120,
      carrier = "Wind",
      p_nom_extendable = True,
      )

n.buses.loc[["Frankfurt", "Manchester"], "nom_min_wind"] = 2000
n.buses.loc[["Frankfurt"], "nom_max_wind"] = 2200

n.lopf(pyomo = False)

print(n.generators.p_nom_opt)