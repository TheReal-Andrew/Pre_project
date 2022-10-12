# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 18:58:40 2022

@author: lukas & anders
"""

#%% Get country Data
def get_load_and_price(year): # require year
    import pandas as pd
    cprice = pd.read_csv('data/market/price_%d.csv'%year, index_col = 0)
    cload = pd.read_csv('data/market/load_%d.csv'%year, index_col = 0)
    return cprice, cload

#%% Annuity
def get_annuity(i, n):
    annuity = i/(1.-1./(1.+i)**n)
    return annuity

