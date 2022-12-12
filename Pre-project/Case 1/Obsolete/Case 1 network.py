#%% Info
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 22 14:40:56 2022

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

Should_MGA = False
Should_MAA = False
n_hrs = 8760
mga_slack = 0.5
MAA_tol   = 0.05

#%% Build network and import

#Build network
n = pypsa.Network()
t = pd.date_range('2030-01-01 00:00', '2030-12-31 23:00', freq = 'H')[:n_hrs]
n.set_snapshots(t)

#Import data
cf_wind_df = pd.read_csv(r'Data/Wind/wind_test.csv',index_col = [0], sep=",")[:n_hrs]

#%% Add components

#Add bus for the island
n.add("Bus", "Island")

#Add wind generator
n.add("Generator",
      "Wind",
      bus = "Island",
      carrier = "wind",
      p_nom = 3000,
      p_max_pu = cf_wind_df['electricity'].values,
      marginal_cost = 0,
      )

n.add("Generator",
      "Coal1",
      bus = "Island",
      carrier = "Coal",
      p_nom_extendable = True,
      marginal_cost = 30,
      )

#Dummy load
n.add("Load",
      "DummyLoad",
      bus = "Island",
      p_set = 1000,
      )

#Add storage
n.add("Store",
      "Store1",
      bus = "Island",
      e_nom_extendable = True,
      e_nom_max = 10000,
      e_cyclic = True,
      marginal_cost = 5,
      standing_loss = 0.1
      )

#Add "loads" in the form of negative generators
n.add("Generator",
      "P2X",
      bus = "Island",
      carrier = "P2X",
      p_nom_extendable = True,
      p_nom_max = 3000,
      p_max_pu = 0,
      p_min_pu = -1,
      marginal_cost = 10,
      )

n.add("Generator",
      "Data",
      bus = "Island",
      carrier = "Data",
      p_nom_extendable = True,
      # p_nom_min = 500,
      p_nom_max = 3000,
      p_max_pu = -1,
      p_min_pu = -1,
      marginal_cost = 11,
      )

#%% Extra functionality
# def area_constraint(n, snapshots):
#     vars_gen   = get_var(n, 'Generator', 'p_nom')
#     vars_store = get_var(n, 'Store', 'e_nom')
    
#     k1 = 1 #[m^2/MW] For P2X
#     k2 = 1 #[m^2/MW] For Data
#     k3 = 1 #[m^2/MW] For Storage
    
#     lhs = linexpr((k1, vars_gen["P2X"]),
#                   (k2, vars_gen["Data"]),
#                   (k3, vars_store),
#                   )
    
#     rhs = 10000 #[m^2]
    
#     #Make constraint limiting the area
#     define_constraints(n, lhs, '=', rhs, 'Generator', 'Area_Use')

# def extra_functionality1(n, snapshots):
#     pass
#     # area_constraint(n, snapshots)

#%% Solve --------------------------------------------------------------------

n.lopf(pyomo = False,
       solver_name = 'gurobi',
       keep_shadowprices = True,
       keep_references = True,
       # extra_functionality = extra_functionality1,
       )

#%% Plot area use
# k1 = 1 #[m^2/MW] For P2X
# k2 = 1 #[m^2/MW] For Data
# k3 = 1 #[m^2/MW] For Storage

# P2X_A   = k1 * n.generators.loc["P2X"].p_nom_opt
# Data_A  = k2 * n.generators.loc["Data"].p_nom_opt
# Store_A = k3 * n.stores.loc["Store1"].e_nom_opt

# pie_data = [P2X_A, Data_A, Store_A]
# labels   =  "P2X", "Data", "Store"

# fig, ax = plt.subplots()
# ax.pie(pie_data, labels = labels, autopct='%1.1f%%')
# ax.set_title('Share of area by technology')

#%% MGA functions
def extra_functionality(n,snapshots,options,direction):
    define_mga_constraint(n,snapshots,options['mga_slack'])
    define_mga_objective(n,snapshots,direction,options)
    # area_constraint(n,snapshots)

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

#%% Set up MGA

# Reduce snapshots used for faster computing
if Should_MGA:
    n.snapshots = n.snapshots[:n_hrs]
    n.snapshot_weightings = n.snapshot_weightings[:n_hrs] 
    
    n1 = n.copy() #Copy the solved, optimal network
    
    n1.lopf(pyomo = False,
           solver_name = 'gurobi',
           keep_shadowprices = True,
           keep_references = True,
           # extra_functionality = extra_functionality1,
           )
    
    n.objective_optimum = n1.objective
    
    variables = {'x1':('Generator','P2X'),
                 'x2':('Generator','Data'),
                }
else:
    pass

#%% MGA - Search 1 direction

if Should_MGA or Should_MAA:
    direction = [1, 1] # 1 means minimize, -1 means maximize 
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

#%% MAA - Run

if Should_MAA:
    MAA_convergence_tol = MAA_tol # How much the volume stops changing before we stop, in %
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

#%% Plot Hull

if Should_MAA:
    Hull = ConvexHull(solutions)
    
    plt.figure()
    
    P2X_sol  = solutions[:,0]
    Data_sol = solutions[:,1]
    
    plt.plot(P2X_sol, Data_sol,
             'o', label = "near-optimal")
    
    #Plot optimal
    plt.plot(n1.generators.p_nom_opt["P2X"], 
             n1.generators.p_nom_opt["Data"],
             '.', markersize = 20, label = "optimum")
    
    plt.legend()
    
    plt.xlim([-500, n.links.p_nom_max.iloc[0]*1.05])
    plt.ylim([-500, n.links.p_nom_max.iloc[1]*1.05])
    
    for simplex in hull.simplices:
    
        plt.plot(solutions[simplex, 0], solutions[simplex, 1], 'k-')
else:
    pass