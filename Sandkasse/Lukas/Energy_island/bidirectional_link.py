# -*- coding: utf-8 -*-
"""
Created on Wed Nov  2 19:56:42 2022

@author: lukas
"""

import pypsa
import matplotlib as plt
import pandas as pd
from pypsa.linopt import get_var, linexpr, join_exprs, define_constraints, get_dual

n = pypsa.Network()

n.set_snapshots(range(10))

n.add("Bus",
      "Bus0",
      )

n.add("Bus",
      "Bus1",
      )

n.add("Link",
      "0to1",
      bus0 = "Bus0",
      bus1 = "Bus1",
      p_nom = 1000,
      )

n.add("Link",
      "1to0",
      bus0 = "Bus1",
      bus1 = "Bus0",
      p_nom = 1000,
      )

n.add("Load",
      "Load0",
      bus = "Bus0", 
      p_set = 1000,
      )

n.add("Load",
      "Load1",
      bus = "Bus1", 
      p_set = 500,
      )

n.add("Generator",
      "Gen1",
      bus = "Bus1", 
      p_nom = 1000,
      marginal_cost = 0.01,
      )

n.add("Generator",
      "Gen0",
      bus = "Bus0", 
      p_nom = 2000,
      marginal_cost = 1,
      )

def link_campacity(n, snapshots):
    vars_1 = get_var(n, "Link", "p")


n.lopf(pyomo = False,
       keep_references = True,
       keep_shadowprices = True,)