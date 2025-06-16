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

train_ids = df_TMD['TRAIN_CD'].unique()
train_to_number = {int(train_id): i for i, train_id in enumerate(train_ids)}

problematic = set()
cnt1 = 0
cnt2 = 0
crew_failed = []
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
                    cnt2 += 1
print(f"{cnt1+cnt2} problems found: {cnt1} equals and {cnt2} non contiguous")
print(f"Problematic set: {problematic}")
print(f"Crew failed: {crew_failed}")