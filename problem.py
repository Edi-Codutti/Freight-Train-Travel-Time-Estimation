import pandas as pd
import numpy as np


def list_for_train (train_to_number, station_to_number, L_t):
    n_treni = len(train_to_number)
    L = [[] for _ in range(n_treni)]

    # 2. Popola la lista usando i dizionari
    for train_id, station_list in L_t:
        train_num = train_to_number[train_id]  # numero treno assegnato
        station_nums = [station_to_number[st] for st in station_list if st in station_to_number]  # numeri stazioni TODO: è veramente necessario 'if st in station_to_number'?
        L[train_num] = station_nums
    return L

# TODO: è possibile eliminare questa funzione e chiamare quella sopra invertendo il primo ed il secondo parametro?
def list_for_station (train_to_number, station_to_number, L_t):
    n_staz = len(station_to_number)
    L = [[] for _ in range(n_staz)]

    for station_id, train_list in L_t:
        station_num = station_to_number[station_id]
        train_nums = [train_to_number[tr] for tr in train_list if tr in train_to_number]
        L[station_num] = train_nums
    return L

def somma_binari(row):
    count = 0
    if row['Siding_Flg'] == 'Y':
        count += row['# of STrks']
    if row['Yard_Flg'] == 'Y':
        count += row['# of YTrks']
    return count

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

# Crea un dizionario di mapping: nome stazione → indice
# station_to_number = df_SOD['Station'].to_dict() TODO: remove because immediately overwritten
station_to_number = {name: idx for idx, name in df_SOD['Station'].items()}

############## S ##############
S = df_SOD.index.to_list()

############## P ##############
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

############## J ##############
J = list(range(len(P)))

# extract distances for every arc
df_TLEN = pd.read_excel(r"RAS-PSC_ValDataset_20200609-06.xlsx", sheet_name='Distances', nrows=105, usecols='A:C')
df_NTC = pd.read_excel(r"RAS-PSC_ValDataset_20200609-06.xlsx", sheet_name='Num Track Chart', nrows=45, usecols='A:E')

distances = [-1 for _ in range(len(J))]
print(len(distances))
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

############## B ##############
B = df_SOD.query("Yard_Flg == 'Y' | Siding_Flg == 'Y'")['Station'].index.to_list()

# non yard stations
non_yard_stations_names = df_SOD[df_SOD['Yard_Flg']!='Y']['Station'].tolist()
non_yard_stations = df_SOD[df_SOD['Yard_Flg']!='Y']['Station'].index.tolist()

df_TMD = pd.read_excel(r"RAS-PSC_ValDataset_20200609-06.xlsx", sheet_name='Train Mvmt Data', nrows=8013, usecols='A:M')
df_TMD = df_TMD[df_TMD['DATE']=='2017-09-06'] # modify this to change date

# stations with do/pu activities
yard_act_stations_names = df_TMD[df_TMD['WORK_ORDR_FLG']=='Y']['STATION'].unique()
yard_act_stations = [station_to_number[name] for name in yard_act_stations_names if name in station_to_number] # TODO: do we need 'if name in station_to_number'?

############## U ##############
# U = set of non yard stations having do/pu activities
U = list(set(non_yard_stations) & set(yard_act_stations))


# associazione treno numero
train_ids = df_TMD['TRAIN_CD'].unique()
train_to_number = {int(train_id): i for i, train_id in enumerate(train_ids)}

############## I ##############
I = list(range(len(train_to_number)))

############## H ##############
train_ids_standard_prty = df_TMD[df_TMD['TRAIN_PRTY']=='S']['TRAIN_CD'].unique()
H = [train_to_number[id] for id in train_ids_standard_prty]

############## L ##############
train_ids_low_prty = df_TMD[df_TMD['TRAIN_PRTY']=='L']['TRAIN_CD'].unique()
L = [train_to_number[id] for id in train_ids_low_prty]

############## V ##############
# V_t: lista di tuple : (treno, lista stazioni visitate)
V_t = df_TMD.groupby('TRAIN_CD')['STATION'].apply(list).reset_index().values.tolist()

# for train_id, stazioni in V_t:
#     print(f"{train_id}: {stazioni}")

V = list_for_train (train_to_number, station_to_number, V_t)


############## C ##############
C_t = df_TMD[df_TMD['WORK_ORDR_FLG']=='Y'].groupby('TRAIN_CD')['STATION'].apply(list).reset_index().values.tolist()
# for train_id, stazioni in C_t:
#     print(f"{train_id}: {stazioni}")

C = list_for_train (train_to_number, station_to_number, C_t)



############## W ##############
W_t = df_TMD[df_TMD['CREW_CHG_FLG']=='Y'].groupby('TRAIN_CD')['STATION'].apply(list).reset_index().values.tolist()
# for train_id, stazioni in W_t:
#     print(f"{train_id}: {stazioni}")

W = list_for_train (train_to_number, station_to_number, W_t)


############## Cp ##############
Cp_t = [[train_id, [st for st in stazioni if st in non_yard_stations_names]] for train_id, stazioni in C_t]
# for train_id, stazioni in Cp_t:
#     print(f"{train_id}: {stazioni}")

Cp = list_for_train (train_to_number, station_to_number, Cp_t)

############## K ##############
K_t = df_TMD[df_TMD['STN_TYPE']=='Stop'].groupby('TRAIN_CD')['STATION'].apply(list).reset_index().values.tolist()
# for train_id, stazioni in K_t:
#     print(f"{train_id}: {stazioni}")

K = list_for_train (train_to_number, station_to_number, K_t)

############## o ##############
o_t = df_TMD[df_TMD['STN_TYPE']=='Origin'].groupby('TRAIN_CD')['STATION'].apply(list).reset_index().values.tolist()
# for train_id, stazioni in o_t:
#     print(f"{train_id}: {stazioni}")

n_treni = len(train_to_number)
n_staz = len(station_to_number)
o = [0]*n_treni

for train_id, station_list in o_t:
    train_num = train_to_number[train_id]  # numero treno assegnato
    station_nums = [station_to_number[st] for st in station_list if st in station_to_number]  # numeri stazioni
    if len(station_nums) == 1:
        o[train_num] = station_nums[0]
    else:
        raise ValueError("La lista non ha un solo elemento")

############## f ##############
f_t = df_TMD[df_TMD['STN_TYPE']=='Dest'].groupby('TRAIN_CD')['STATION'].apply(list).reset_index().values.tolist()
# for train_id, stazioni in f_t:
#     print(f"{train_id}: {stazioni}")

f = [0]*n_treni

for train_id, station_list in f_t:
    train_num = train_to_number[train_id]  # numero treno assegnato
    station_nums = [station_to_number[st] for st in station_list if st in station_to_number]  # numeri stazioni
    if len(station_nums) == 1:
        f[train_num] = station_nums[0]
    else:
        raise ValueError("La lista non ha un solo elemento")
    

############## G ##############
G_t = df_TMD.groupby('STATION')['TRAIN_CD'].apply(list).reset_index().values.tolist()
# for stazioni, train_id in G_t:
#     print(f"{stazioni}: {train_id}")

G = list_for_station (train_to_number, station_to_number, G_t)


############## Gp ##############
Gp_t = df_TMD[df_TMD['WORK_ORDR_FLG']=='Y'].groupby('STATION')['TRAIN_CD'].apply(list).reset_index().values.tolist()
# for stazioni, train_id in Gp_t:
#     print(f"{stazioni}: {train_id}")

Gp = list_for_station (train_to_number, station_to_number, Gp_t)



############## O ##############
O_t = df_TMD[df_TMD['STN_TYPE']=='Origin'].groupby('STATION')['TRAIN_CD'].apply(list).reset_index().values.tolist()
# for stazioni, train_id in O_t:
#     print(f"{stazioni}: {train_id}")

O = list_for_station (train_to_number, station_to_number, O_t)



############## F ##############
F_t = df_TMD[df_TMD['STN_TYPE']=='Dest'].groupby('STATION')['TRAIN_CD'].apply(list).reset_index().values.tolist()
# for stazioni, train_id in F_t:
#     print(f"{stazioni}: {train_id}")

F = list_for_station (train_to_number, station_to_number, F_t)

############## E ##############
E = [[] for _ in I]
for _, row in df_TMD.iterrows():
    s1 = station_to_number[row['STATION']]
    s2 = station_to_number[row['TO_STN']]
    i = train_to_number[row['TRAIN_CD']]
    if row['STN_TYPE'] != 'Origin' or row['STN_TYPE'] != 'Dest':
        try:
            E[i].append(P.index((s1,s2)))
        except ValueError:
            E[i].append(P.index((s2,s1)))

# track speed list
track_speed = [100] * len(J)

############## t ##############
t = [[] for _ in I]


############## a , d ##############

#conversione da data a ora  in decimali 
df_TMD['PLAN_ARR_TM'] = (pd.to_datetime(df_TMD['PLAN_ARR_TM']).dt.hour +
                        pd.to_datetime(df_TMD['PLAN_ARR_TM']).dt.minute / 60 +
                        pd.to_datetime(df_TMD['PLAN_ARR_TM']).dt.second / 3600)

df_TMD['PLAN_DEP_TM'] = (pd.to_datetime(df_TMD['PLAN_DEP_TM']).dt.hour +
                        pd.to_datetime(df_TMD['PLAN_DEP_TM']).dt.minute / 60 +
                        pd.to_datetime(df_TMD['PLAN_DEP_TM']).dt.second / 3600)

# Matrice vuota con NaN (nessun arrivo)
a = np.full((n_treni, n_staz), np.nan)

for _, row in df_TMD.iterrows(): # row è tipo diz, iterrows() restituisce una tupla (index, row), ma non ci serve l'indice, quindi mettiamo _.
    train_code = row['TRAIN_CD']
    station_name = row['STATION']
    arrival_time = row['PLAN_ARR_TM']  # può essere datetime o stringa

    # TODO: è necessario questo if?
    if train_code in train_to_number and station_name in station_to_number:
        train_idx = train_to_number[train_code]
        station_idx = station_to_number[station_name]

        a[train_idx, station_idx] = arrival_time

# Matrice vuota con NaN (nessun arrivo)
d = np.full((n_treni, n_staz), np.nan)

for _, row in df_TMD.iterrows(): # row è tipo diz, iterrows() restituisce una tupla (index, row), ma non ci serve l'indice, quindi mettiamo _.
    train_code = row['TRAIN_CD']
    station_name = row['STATION']
    departure_time = row['PLAN_DEP_TM']  # può essere datetime o stringa

    if train_code in train_to_number and station_name in station_to_number:
        train_idx = train_to_number[train_code]
        station_idx = station_to_number[station_name]

        d[train_idx, station_idx] = departure_time


############## n ,m ##############

n = df_SOD.apply(somma_binari, axis=1).tolist()

