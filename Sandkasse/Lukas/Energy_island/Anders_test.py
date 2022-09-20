import pypsa
import numpy as np
import matplotlib as plt
import cartopy.crs as ccrs
import pandas as pd
from makeplots1 import makeplots

network = pypsa.Network()

network.add("Bus","Island")
network.add("Bus","Norway")
network.add("Bus","Denmark")
network.add("Bus","Germany")
network.add("Bus","Britain")
network.add("Bus","Belgium")
network.add("Bus","Netherlands")

for i in network.buses.index.values[1:]:
    network.add(
        "Link",
        "Link to {}".format(i),
        bus0 = "Island", 
        bus1 = i,
        p_nom = 20
    )
    
