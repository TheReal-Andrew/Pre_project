# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 14:09:23 2023

@author: lukas
"""

import pandas as pd

#%% Improt and format data
data = pd.read_excel('data/technology_data_for_el_and_dh.xlsx', 
              sheet_name = '20 Onshore turbines',
              ).iloc[:,1:10]

data.iloc[0,0] = 'Parameter'

data.columns   = data.iloc[0].astype(str)

data.set_index('Parameter', inplace = True)

data = data[1:]

data.dropna(inplace = True)

#%% Pull parameters

year     = '2015'

INV      = data.loc['Nominal investment (*total) [2015-MEUR/MW_e]',
            year]

FOM      = data.loc['Fixed O&M (*total) [2015-EUR/MW_e/y]',
            year]

Lifetime = data.loc['Technical lifetime [years]',
            year]