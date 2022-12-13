#%% Info
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 10:25:17 2022

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

#%% Plotting options
#Set up plot parameters
color_bg      = "0.99"          #Choose background color
color_gridaxe = "0.85"          #Choose grid and spine color
rc = {"axes.edgecolor":color_gridaxe} 
plt.style.use(('ggplot', rc))           #Set style with extra spines
plt.rcParams['figure.dpi'] = 300        #Set resolution
plt.rcParams["figure.figsize"] = (10, 5) #Set figure size
matplotlib.rcParams['font.family'] = ['cmss10']     #Change font to Computer Modern Sans Serif
plt.rcParams['axes.unicode_minus'] = False          #Re-enable minus signs on axes))
plt.rcParams['axes.facecolor']= "0.99"              #Set plot background color
plt.rcParams.update({"axes.grid" : True, "grid.color": color_gridaxe}) #Set grid color
plt.rcParams['axes.grid'] = True

#%% Control

Should_solve = True
Should_MGA   = True
Should_MAA   = True
n_snapshots  = 8670
mga_slack    = 0.1

# Area affecting parameters
k_P2X   = 60  # [m^2/MW] Area use for P2X
mc_P2X  = 10  # [EUR/MW] Gain for system for P2X
cc_P2X  = 100 # [EUR/MW] Capital cost for P2X

k_Data  = 20  # [m^2/MW] Area use for Data
mc_Data = 15  # [EUR/MW] Gain for system for Data
cc_Data = 110 # [EUR/MW] Capital cost for Data

k_Store  = 7  # [m^2/MW] Area use for Storage
cc_Store = 80 # [EUR/MW] Capital cost for Storage

#%% Load and copy network

n = pypsa.Network('case1_v2.nc') #Load network from netcdf file

# Reduce snapshots used for faster computing
n.snapshots = n.snapshots[:n_snapshots]
n.snapshot_weightings = n.snapshot_weightings[:n_snapshots] 

n_optimum = n.copy()

#%% Solve optimum network 

# Extra functionality
def area_constraint(n, snapshots):
    vars_gen   = get_var(n, 'Generator', 'p_nom')
    vars_store = get_var(n, 'Store', 'e_nom')
    
    lhs = linexpr((k_P2X, vars_gen["P2X"]), 
                  (k_Data, vars_gen["Data"]), 
                  (k_Store, vars_store))
    
    rhs = 10000 #[m^2]
    
    define_constraints(n, lhs, '=', rhs, 'Generator', 'Area_Use')

def extra_functionalities(n, snapshots):
    area_constraint(n, snapshots)

if Should_solve:
    n_optimum.lopf(pyomo = False,
          solver_name = 'gurobi',
          extra_functionality = extra_functionalities,
          )
    
    print("Network objective value:" + str(n_optimum.objective))
    
    n_objective = n_optimum.objective
else:
    pass

#%% MGA functions
def extra_functionality(n,snapshots,options,direction):
    define_mga_constraint(n,snapshots,options['mga_slack'])
    define_mga_objective(n,snapshots,direction,options)
    area_constraint(n, snapshots)

def assign_carriers(n):
    """
    Author: Fabian Neumann 
    Source: https://github.com/PyPSA/pypsa-eur-mga
    """

    if "Load" in n.carriers.index:
        n.carriers = n.carriers.drop("Load")

    if "carrier" not in n.lines:
        n.lines["carrier"] = "AC"

    if n.links.empty:
        n.links["carrier"] = pd.Series(dtype=str)

    config = {
        "AC": {"color": "rosybrown", "nice_name": "HVAC Line"},
        "DC": {"color": "darkseagreen", "nice_name": "HVDC Link"},
    }
    for c in ["AC", "DC"]:
        if c in n.carriers.index:
            continue
        n.carriers = n.carriers.append(pd.Series(config[c], name=c))

def define_mga_constraint(n, sns, epsilon=None, with_fix=False):
    """
    Author: Fabian Neumann 
    Source: https://github.com/PyPSA/pypsa-eur-mga
    
    Build constraint defining near-optimal feasible space
    Parameters
    ----------
    n : pypsa.Network
    sns : Series|list-like
        snapshots
    epsilon : float, optional
        Allowed added cost compared to least-cost solution, by default None
    with_fix : bool, optional
        Calculation of allowed cost penalty should include cost of non-extendable components, by default None
    """

    if epsilon is None:
        epsilon = float(snakemake.wildcards.epsilon)

    if with_fix is None:
        with_fix = snakemake.config.get("include_non_extendable", True)

    expr = []

    # operation
    for c, attr in lookup.query("marginal_cost").index:
        cost = (
            get_as_dense(n, c, "marginal_cost", sns)
            .loc[:, lambda ds: (ds != 0).all()]
            .mul(n.snapshot_weightings.loc[sns,'objective'], axis=0)
        )
        if cost.empty:
            continue
        expr.append(linexpr((cost, get_var(n, c, attr).loc[sns, cost.columns])).stack())

    # investment
    for c, attr in nominal_attrs.items():
        cost = n.df(c)["capital_cost"][get_extendable_i(n, c)]
        if cost.empty:
            continue
        expr.append(linexpr((cost, get_var(n, c, attr)[cost.index])))

    lhs = pd.concat(expr).sum()

    if with_fix:
        ext_const = objective_constant(n, ext=True, nonext=False)
        nonext_const = objective_constant(n, ext=False, nonext=True)
        rhs = (1 + epsilon) * (n.objective_optimum + ext_const + nonext_const) - nonext_const
    else:
        ext_const = objective_constant(n)
        rhs = (1 + epsilon) * (n.objective_optimum + ext_const)

    define_constraints(n, lhs, "<=", rhs, "GlobalConstraint", "mu_epsilon")

def objective_constant(n, ext=True, nonext=True):
    """
    Author: Fabian Neumann 
    Source: https://github.com/PyPSA/pypsa-eur-mga
    """

    if not (ext or nonext):
        return 0.0

    constant = 0.0
    for c, attr in nominal_attrs.items():
        i = pd.Index([])
        if ext:
            i = i.append(get_extendable_i(n, c))
        if nonext:
            i = i.append(get_non_extendable_i(n, c))
        constant += n.df(c)[attr][i] @ n.df(c).capital_cost[i]

    return constant


def define_mga_objective(n,snapshots,direction,options):
    mga_variables = options['mga_variables']
    expr_list = []
    for dir_i,var_i in zip(direction,mga_variables):
        model_vars = get_var(n,var_i[0],'p_nom')[n.df(var_i[0]).carrier == var_i[1]]
        tmp_expr = linexpr((dir_i/len(model_vars),model_vars)).sum()
        expr_list.append(tmp_expr)

    mga_obj = join_exprs(np.array(expr_list))
    write_objective(n,mga_obj)


def get_var_values(n,mga_variables):

    variable_values = {}
    for var_i in variables:
        val = n.df(variables[var_i][0]).query('carrier == "{}"'.format(variables[var_i][1])).p_nom_opt.sum()
        variable_values[var_i] = val

    return variable_values

#%% MAA Variables
n.objective_optimum = n_objective

variables = {'x1':('Generator','P2X'),
             'x2':('Generator','Data'),
            }

#%% MGA - Search 1 direction

if Should_MGA or Should_MAA:
    direction = [-1, -1] # 1 means minimize, -1 means maximize 
    mga_variables = ['x1','x2'] # The variables that we are investigating
    
    options = dict(mga_slack=mga_slack,
                    mga_variables=[variables[v] for v in mga_variables])
    
    res = n.lopf(pyomo=False,
            solver_name='gurobi',
            keep_references=True,
            keep_shadowprices=True,
            skip_objective=True,
            solver_options={'LogToConsole':0,
                    'crossover':0,
                    'BarConvTol' : 1e-6,                 
                    'FeasibilityTol' : 1e-2,
                'threads':2},
            extra_functionality=lambda n,s: extra_functionality(n,s,options,direction)
        )
    
    all_variable_values = get_var_values(n,mga_variables)
    print(all_variable_values)
else:
    pass

#%% MAA Functions
def search_direction(direction,mga_variables):
    options = dict(mga_slack=mga_slack,
                    mga_variables=[variables[v] for v in mga_variables])

    res = n.lopf(pyomo=False,
            solver_name='gurobi',
            #keep_references=True,
            #keep_shadowprices=True,
            skip_objective=True,
            solver_options={'LogToConsole':0,
                    'crossover':0,
                    'BarConvTol' : 1e-6,                 
                    'FeasibilityTol' : 1e-2,
                'threads':2},
            extra_functionality=lambda n,s: extra_functionality(n,s,options,direction)
        )

    all_variable_values = get_var_values(n,mga_variables)

    return [all_variable_values[v] for v in mga_variables]

if Should_MAA:
    MAA_convergence_tol = 0.05 # How much the volume stops changing before we stop, in %
    dim=len(mga_variables) # number of dimensions 
    dim_fullD = len(variables)
    old_volume = 0 
    epsilon = 1
    directions_searched = np.empty([0,dim])
    hull = None
    computations = 0
    
    solutions = np.empty(shape=[0,dim])
    
    while epsilon>MAA_convergence_tol:
    
        if len(solutions) <= 1:
            directions = np.concatenate([np.diag(np.ones(dim)),-np.diag(np.ones(dim))],axis=0)
        else :
            directions = -np.array(hull.equations)[:,0:-1]
        directions_searched = np.concatenate([directions_searched,directions],axis=0)
    
        # Run computations in series
        for direction_i in directions:
            res = search_direction(direction_i,mga_variables)
            solutions = np.append(solutions,np.array([res]),axis=0)
    
    
        hull = ConvexHull(solutions)
    
        delta_v = hull.volume - old_volume
        old_volume = hull.volume
        epsilon = delta_v/hull.volume
        print('####### EPSILON ###############')
        print(epsilon)
else:
    pass

#%% Plot
if Should_MAA:
    Hull = ConvexHull(solutions)
    
    plt.figure()
    
    DK = solutions[:,0]
    DE = solutions[:,1]
    
    plt.plot(DK, DE,
             'o', label = "near-optimal")
    
    #Plot optimal
    plt.plot(n_optimum.generators.p_nom_opt["P2X"], 
             n_optimum.generators.p_nom_opt["Data"],
              '.', markersize = 20, label = "optimum")
    plt.xlabel("Data")
    plt.ylabel("P2X")
    
    # plt.legend()
    
    # plt.xlim([-500, n.links.p_nom_max.iloc[0]*1.05])
    # plt.ylim([-500, n.links.p_nom_max.iloc[1]*1.05])
    
    for simplex in hull.simplices:
    
        plt.plot(solutions[simplex, 0], solutions[simplex, 1], 'k-')
else:
    pass