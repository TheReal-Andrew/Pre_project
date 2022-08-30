# -*- coding: utf-8 -*-
"""
Created on Fri Aug 26 11:00:44 2022

@author: lukas
"""

import matplotlib.pyplot as plt
plt.rc("figure", figsize=(8, 8))

import cartopy.crs as ccrs
import pypsa
import plotly.io as pio
pio.renderers.default='browser'


network = pypsa.Network()

#%% Import data
csv_folder = "AC-DC meshed/ac-dc-meshed/ac-dc-data"

network.import_from_csv_folder(csv_folder_name = csv_folder)

#%% Find linetype (AC or DC)
lines_type = network.lines.bus0.map(network.buses.carrier)

#%% Plotting
network.plot(line_colors = lines_type.map(lambda ct: "r" if ct == "DC" else "b"),
            projection=ccrs.EqualEarth(),
            color_geomap = True,
            jitter = 0.3,
            title = "AC (blue) and DC (red) Lines")

plt.tight_layout()

#%% Switch p_nom_extandable for Norwich Converter from True to False
network.links.loc["Norwich Converter", "p_nom_extendable"] = False

#%% Determine topology of network and thus determine subnetworks
network.determine_network_topology()

#%% Subnetwork branches and buses
network.sub_networks["nbranches"] = [
    len(sn.branches()) for sn in network.sub_networks.obj
    ]

network.sub_networks["nbuses"] = [
    len(sn.buses()) for sn in network.sub_networks.obj
    ]






















