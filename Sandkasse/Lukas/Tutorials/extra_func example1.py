# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 13:39:28 2022

@author: lukas
"""

import pypsa
import matplotlib as plt
import pandas as pd
import os
from pypsa.linopt import get_var, linexpr, join_exprs, define_constraints

n = pypsa.examples.ac_dc_meshed(from_master = True)

# Set gas generators to non-extendable
n.generators.loc[n.generators.carrier == "gas", "p_nom_extendable"] = False

# Add ramp limits to gas generators
n.generators.loc[n.generators.carrier == "gas", "ramp_limit_down"] = 0.2
n.generators.loc[n.generators.carrier == "gas", "ramp_limit_up"] = 0.2

# Add storage in manchester
n.add(
      "StorageUnit",
      "su",
      bus = "Manchester",
      marginal_cost = 10,
      inflow = 50,
      p_nom_extendable = True,
      captial_cost = 10,
      p_nom = 2000,
      efficiency_dispatch = 0.5,
      cyclic_state_of_charge = True,
      state_of_charge_initial = 1000,
      )

n.add(
      "StorageUnit",
      "su2",
      bus = "Manchester",
      marginal_cost = 10,
      p_nom_extendable = True,
      capital_cost = 50,
      p_nom = 2000,
      efficiency_dispatch = 0.5,
      carrier = "gas",
      cyclic_state_of_charge = False,
      state_of_charge_initial = 1000,
      )

n.storage_units_t.state_of_charge_set.loc[n.snapshots[7], "su"] = 100

# Add store
n.add("Bus", "storebus", carrier = "hydro", x = -5, y = 55)

n.madd(
       "Link",
       ["battery_power", "battery_discharge"],
       "",
       bus0 = ["Manchester", "storebus"],
       bus1 = ["storebus", "Manchester"],
       p_nom = 100,
       efficiency = 0.9,
       p_nom_extendable = True,
       p_nom_max = 1000,
       )

n.madd(
       "Store",
       ["store"],
       bus = "storebus",
       e_nom = 2000,
       e_nom_extendable = True,
       margina_cost = 10,
       capital_cost = 10,
       e_nom_max = 5000,
       e_initial = 100,
       e_cyclic = True
       )

# Extra Functionalities

def minimal_state_of_charge(n, snapshots):
    #Get State of Charge variables
    vars_soc = get_var(n, "StorageUnit", "state_of_charge")
    
    #Define left hand side:
    lhs = linexpr((1, vars_soc))
    
    #Define right hand side
    rhs = 50
    
    #Set up the constraint. Use lhs as left hand side, and 50 as right hand side.
    # Set to lhs > rhs, so lhs must be larger than rhs
    define_constraints(n, 
                       lhs, ">", rhs,      # Constraint, lhs and rhs
                       "StorageUnit",      # Name of constraint
                       "soc_lower_bound")
    
def extra_functionalities(n, snapshots):
    minimal_state_of_charge(n, snapshots)
    
    
n.lopf(pyomo = False,
       extra_functionality = extra_functionalities,
       keep_shadowprices = True,
       keep_references = True,
       )
    
    
    
    
    
    
    
    
    
    







