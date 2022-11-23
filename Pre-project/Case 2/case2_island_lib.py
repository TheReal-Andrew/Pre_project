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

#%% Remove outliers
def remove_outliers(df,columns,n_std):
    for col in columns:
        print('Working on column: {}'.format(col))
        
        mean = df[col].mean()
        sd = df[col].std()
        
        df = df[(df[col] <= mean+(n_std*sd))]
        
    return df

