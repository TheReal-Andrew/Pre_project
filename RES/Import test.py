
import pandas as pd

#%% Import and format data
data1 = pd.read_excel('data/technology_data_for_el_and_dh.xlsx', 
          sheet_name = '21 Offshore turbines',
          ).iloc[:,1:10]

data1.iloc[0,0] = 'Parameter'
data1.columns   = data1.iloc[0].astype(str)
data1.set_index('Parameter', inplace = True)
data1 = data1[1:]
data1.dropna(inplace = True)

#%% Pull parameters
year     = '2015'
INV      = data1.loc['Nominal investment (M€/MW)', year]
FOM      = data1.loc['Fixed O&M (€/MW/year)', year]
Lifetime = data1.loc['Technical lifetime (years)', year]