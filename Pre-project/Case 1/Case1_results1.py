# -*- coding: utf-8 -*-
"""
Created on Sun Dec 18 13:58:06 2022

@author: lukas
"""

#%% Import
import pypsa 
import numpy as np
from pypsa.linopt import get_var, linexpr, join_exprs, define_constraints, get_dual, get_con, write_objective, get_sol, define_variables
from pypsa.descriptors import nominal_attrs
from pypsa.linopf import lookup, network_lopf, ilopf
from pypsa.pf import get_switchable_as_dense as get_as_dense
from pypsa.descriptors import get_extendable_i, get_non_extendable_i
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
from scipy.spatial import ConvexHull
import os
import sys
import island_plt as ip

ip.set_plot_options()

#%% Import results

# Optimal solutions for v2 and v3
n_v2_opt = pypsa.Network(r'\case1_v2\case1_v2.nc')
n_v3_opt = pypsa.Network(r'\case1_v3\case1_v3.nc')