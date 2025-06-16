import pandas as pd
import numpy as np
df_TMD = pd.read_excel(r"RAS-PSC_ValDataset_20200609-06.xlsx", sheet_name='Train Mvmt Data', nrows=8013, usecols='A:M')
df_TMD = df_TMD[df_TMD['DATE']=='2017-09-06'] # modify this to change date

to_delete = []
for idx, row in df_TMD.iterrows():
    if row['STATION'] == row['TO_STN']:
        df_TMD['STN_TYPE'].iloc[idx+1] = 'Origin'
        df_TMD['PLAN_ARR_TM'].iloc[idx+1] = np.nan
        to_delete.append(idx)
df_TMD = df_TMD.drop(index=to_delete)

# main pt. 1
df_SOD_1 = pd.read_excel(r"RAS-PSC_ValDataset_20200609-06.xlsx", sheet_name='Stn Order & Details', nrows=33, usecols='A:E')

# south route
df_SOD_2 = pd.read_excel(r"RAS-PSC_ValDataset_20200609-06.xlsx", sheet_name='Stn Order & Details', skiprows=35, nrows=6, usecols='A:E')

# main pt. 2
df_SOD_3 = pd.read_excel(r"RAS-PSC_ValDataset_20200609-06.xlsx", sheet_name='Stn Order & Details', skiprows=49, nrows=11, usecols='A:E')

# north route
df_SOD_4 = pd.read_excel(r"RAS-PSC_ValDataset_20200609-06.xlsx", sheet_name='Stn Order & Details', skiprows=35, nrows=12, usecols='G:K')

df_SOD_4.columns = df_SOD_1.columns
df_SOD_3.columns = df_SOD_1.columns
df_SOD_2.columns = df_SOD_1.columns

df_SOD = pd.concat([df_SOD_1, df_SOD_4, df_SOD_3, df_SOD_2], ignore_index=True)

station_to_number = {name: idx for idx, name in df_SOD['Station'].items()}
S = df_SOD.index.to_list()

P = []
j = 0
for _ in range(len(df_SOD_1) + len(df_SOD_4) + len(df_SOD_3) - 1):
    P.append((j,j+1))
    j += 1
j += 1
for _ in range(len(df_SOD_2) - 1):
    P.append((j,j+1))
    j += 1
P.append((station_to_number[df_SOD_1['Station'].iloc[-1]], station_to_number[df_SOD_2['Station'].iloc[0]]))
P.append((station_to_number[df_SOD_2['Station'].iloc[-1]], station_to_number[df_SOD_3['Station'].iloc[0]]))

J = list(range(len(P)))

# extract distances for every arc
df_TLEN = pd.read_excel(r"RAS-PSC_ValDataset_20200609-06.xlsx", sheet_name='Distances', nrows=105, usecols='A:C')
df_NTC = pd.read_excel(r"RAS-PSC_ValDataset_20200609-06.xlsx", sheet_name='Num Track Chart', nrows=45, usecols='A:E')

distances = [-1 for _ in range(len(J))]
for j in range(len(distances)):
    s1_index, s2_index = P[j]
    s1_name = df_SOD['Station'].iloc[s1_index]
    s2_name = df_SOD['Station'].iloc[s2_index]
    res = df_TLEN.query(f"(From == '{s1_name}' & To == '{s2_name}') | (From == '{s2_name}' & To == '{s1_name}')")['Distance (km)'].values
    if res.size > 0:
        distances[j] = res[0]
        continue
    else:
        res = df_NTC.query(f"(FromLocation == '{s1_name}' & ToLocation == '{s2_name}') | (FromLocation == '{s2_name}' & ToLocation == '{s1_name}')")['Kilometers'].values
        if res.size > 0:
            distances[j] = res[0]
distances[16] = 8.5 # Etn->Bda = Etn->Bd - Bda->Bd






train_ids = df_TMD['TRAIN_CD'].unique()
train_to_number = {int(train_id): i for i, train_id in enumerate(train_ids)}

# track speed list
track_speed = [100] * len(J)

problematic = set()
cnt1 = 0
cnt2 = 0
crew_failed = []
nc_idx_13 = []
nc_idx_23 = []
for index, row in df_TMD.iterrows():
    i = train_to_number[row['TRAIN_CD']]
    s1 = station_to_number[row['STATION']]
    if row['STN_TYPE'] != 'Dest':
        s2 = station_to_number[row['TO_STN']]
        try:
            j = P.index((s1,s2))
        except ValueError:
            try:
                j = P.index((s2,s1))
            except ValueError:
                print(f"row: {index} - {(s1,s2)} not found!")
                problematic.add((s1,s2))
                if s1 == s2:
                    cnt1 += 1
                    if df_TMD['CREW_CHG_FLG'].iloc[index] != df_TMD['CREW_CHG_FLG'].iloc[index+1] and not np.isnan(df_TMD['CREW_CHG_FLG'].iloc[index]) and not np.isnan(df_TMD['CREW_CHG_FLG'].iloc[index+1]):
                        crew_failed.append(index)
                else:
                    if (s1 == 12) or (s1 == 14):
                        nc_idx_13.append(index)
                    else:
                        nc_idx_23.append(index)
                    cnt2 += 1

print(f"{cnt1+cnt2} problems found: {cnt1} equals and {cnt2} non contiguous")
print(f"Problematic set: {problematic}")
print(f"Crew failed: {crew_failed}")


df_TMD['PLAN_ARR_TM'] = (pd.to_datetime(df_TMD['PLAN_ARR_TM']).dt.hour +
                        pd.to_datetime(df_TMD['PLAN_ARR_TM']).dt.minute / 60 +
                        pd.to_datetime(df_TMD['PLAN_ARR_TM']).dt.second / 3600)

df_TMD['PLAN_DEP_TM'] = (pd.to_datetime(df_TMD['PLAN_DEP_TM']).dt.hour +
                        pd.to_datetime(df_TMD['PLAN_DEP_TM']).dt.minute / 60 +
                        pd.to_datetime(df_TMD['PLAN_DEP_TM']).dt.second / 3600)

for idx in nc_idx_13:
    
    j = P.index((12,13)) if df_TMD['STATION'].loc[idx] == 'Bgn' else P.index((13,14))
    t_j = distances[j]/min(track_speed[j], df_TMD['MAX_SPD'].loc[idx])
    new_row = pd.DataFrame({'DATE': df_TMD['DATE'].loc[idx], 
                            'TRAIN_CD': df_TMD['TRAIN_CD'].loc[idx], 
                            'TRAIN_PRTY': df_TMD['TRAIN_PRTY'].loc[idx], 
                            'DEP_DIR': df_TMD['DEP_DIR'].loc[idx], 
                            'STATION': 'Bgnphm', 
                            'STN_TYPE': 'Int', 
                            'ORDER_#': 0, 
                            'TO_STN': df_TMD['TO_STN'].loc[idx], 
                            'PLAN_ARR_TM': (df_TMD['PLAN_DEP_TM'].loc[idx] + t_j), 
                            'PLAN_DEP_TM': (df_TMD['PLAN_DEP_TM'].loc[idx] + t_j), 
                            'MAX_SPD': df_TMD['MAX_SPD'].loc[idx], 
                            'WORK_ORDR_FLG': np.nan, 
                            'CREW_CHG_FLG': np.nan}, index = [idx + 0.5])
    df_TMD = pd.concat([df_TMD, new_row])
    df_TMD['TO_STN'].loc[idx] = 'Bgnphm'

for idx in nc_idx_23:
    
    j = P.index((22,23)) if df_TMD['STATION'].loc[idx] == 'Tbge' else P.index((23,24))
    t_j = distances[j]/min(track_speed[j], df_TMD['MAX_SPD'].loc[idx])
    new_row = pd.DataFrame({'DATE': df_TMD['DATE'].loc[idx], 
                            'TRAIN_CD': df_TMD['TRAIN_CD'].loc[idx], 
                            'TRAIN_PRTY': df_TMD['TRAIN_PRTY'].loc[idx], 
                            'DEP_DIR': df_TMD['DEP_DIR'].loc[idx], 
                            'STATION': 'Tb', 
                            'STN_TYPE': 'Int', 
                            'ORDER_#': 0, 
                            'TO_STN': df_TMD['TO_STN'].loc[idx], 
                            'PLAN_ARR_TM': (df_TMD['PLAN_DEP_TM'].loc[idx] + t_j), 
                            'PLAN_DEP_TM': (df_TMD['PLAN_DEP_TM'].loc[idx] + t_j), 
                            'MAX_SPD': df_TMD['MAX_SPD'].loc[idx], 
                            'WORK_ORDR_FLG': np.nan, 
                            'CREW_CHG_FLG': np.nan}, index = [idx + 0.5])
    df_TMD = pd.concat([df_TMD, new_row])
    df_TMD['TO_STN'].loc[idx] = 'Tb'

# for idx in nc_idx_23:
    
#     df_TMD['TO_STN'].iloc[idx] = 'Tb'
#     j = P.index((22,23)) if df_TMD['STATION'].iloc[idx] == 'Tbge' else P.index((23,24))
#     t_j = distances[j]/min(track_speed[j], df_TMD['MAX_SPD'].iloc[idx])
#     new_row = pd.DataFrame({'DATE': df_TMD['DATE'].iloc[idx], 
#                             'TRAIN_CD': df_TMD['TRAIN_CD'].iloc[idx], 
#                             'TRAIN_PRTY': df_TMD['TRAIN_PRTY'].iloc[idx], 
#                             'DEP_DIR': df_TMD['DEP_DIR'].iloc[idx], 
#                             'STATION': 'Tb', 
#                             'STN_TYPE': 'Int', 
#                             'ORDER_#': 0, 
#                             'TO_STN': df_TMD['TO_STN'].iloc[idx], 
#                             'PLAN_ARR_TM': (df_TMD['PLAN_DEP_TM'].iloc[idx] + t_j), 
#                             'PLAN_DEP_TM': (df_TMD['PLAN_DEP_TM'].iloc[idx] + t_j), 
#                             'MAX_SPD': df_TMD['MAX_SPD'].iloc[idx], 
#                             'WORK_ORDR_FLG': np.nan, 
#                             'CREW_CHG_FLG': np.nan}, index = [idx + 0.5])
#     df_TMD = pd.concat([df_TMD, new_row])

problematic = set()
cnt1 = 0
cnt2 = 0
crew_failed = []
nc_idx_13 = []
nc_idx_23 = []
for index, row in df_TMD.iterrows():
    i = train_to_number[row['TRAIN_CD']]
    s1 = station_to_number[row['STATION']]
    if row['STN_TYPE'] != 'Dest':
        s2 = station_to_number[row['TO_STN']]
        try:
            j = P.index((s1,s2))
        except ValueError:
            try:
                j = P.index((s2,s1))
            except ValueError:
                print(f"row: {index} - {(s1,s2)} not found!")
                problematic.add((s1,s2))
                if s1 == s2:
                    cnt1 += 1
                    if df_TMD['CREW_CHG_FLG'].iloc[index] != df_TMD['CREW_CHG_FLG'].iloc[index+1] and not np.isnan(df_TMD['CREW_CHG_FLG'].iloc[index]) and not np.isnan(df_TMD['CREW_CHG_FLG'].iloc[index+1]):
                        crew_failed.append(index)
                else:
                    if (s1 == 12) or (s1 == 14):
                        nc_idx_13.append(index)
                    else:
                        nc_idx_23.append(index)
                    cnt2 += 1

print(f"{cnt1+cnt2} problems found: {cnt1} equals and {cnt2} non contiguous")
print(f"Problematic set: {problematic}")
print(f"Crew failed: {crew_failed}")

