import pandas as pd
import numpy as np


def list_for_train (train_to_number, station_to_number, L_t):
    n_treni = len(train_to_number)
    L = [[] for _ in range(n_treni)]

    # 2. Popola la lista usando i dizionari
    for train_id, station_list in L_t:
        train_num = train_to_number[train_id]  # numero treno assegnato
        station_nums = [station_to_number[st] for st in station_list if st in station_to_number]  # numeri stazioni
        L[train_num] = station_nums
    return L

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

############## U ##############

df_SOD_1 = pd.read_excel(r"C:\Users\andre\OneDrive\Desktop\Andrea\units Andrea\2 anno 2 semestre\MO\project\RAS-PSC_ValDataset_20200609-06.xlsx",
                             sheet_name='Stn Order & Details', nrows=33, usecols='A:E', engine='openpyxl')
df_SOD_2 = pd.read_excel(r"C:\Users\andre\OneDrive\Desktop\Andrea\units Andrea\2 anno 2 semestre\MO\project\RAS-PSC_ValDataset_20200609-06.xlsx",
                             sheet_name='Stn Order & Details', skiprows=35, nrows=6, usecols='A:E', engine='openpyxl')
df_SOD_3 = pd.read_excel(r"C:\Users\andre\OneDrive\Desktop\Andrea\units Andrea\2 anno 2 semestre\MO\project\RAS-PSC_ValDataset_20200609-06.xlsx",
                             sheet_name='Stn Order & Details', skiprows=49, nrows=11, usecols='A:E', engine='openpyxl')
df_SOD_4 = pd.read_excel(r"C:\Users\andre\OneDrive\Desktop\Andrea\units Andrea\2 anno 2 semestre\MO\project\RAS-PSC_ValDataset_20200609-06.xlsx",
                             sheet_name='Stn Order & Details', skiprows=35, nrows=12, usecols='G:K', engine='openpyxl')
df_SOD_4.columns = df_SOD_1.columns
df_SOD_3.columns = df_SOD_1.columns
df_SOD_2.columns = df_SOD_1.columns

df_SOD = pd.concat([df_SOD_1, df_SOD_4, df_SOD_3, df_SOD_2], ignore_index=True)
# Crea un dizionario di mapping: nome stazione → indice
station_to_number = df_SOD['Station'].to_dict()
station_to_number = {name: idx for idx, name in df_SOD['Station'].items()}

# non yard stations
non_yard_stations_names = df_SOD[df_SOD['Yard_Flg']!='Y']['Station'].tolist()
non_yard_stations = df_SOD[df_SOD['Yard_Flg']!='Y']['Station'].index.tolist()

df_TMD = pd.read_excel(r"C:\Users\andre\OneDrive\Desktop\Andrea\units Andrea\2 anno 2 semestre\MO\project\RAS-PSC_ValDataset_20200609-06.xlsx",
                              sheet_name='Train Mvmt Data', nrows=3978, usecols='A:M', engine='openpyxl')

# stations with do/pu activities
yard_act_stations_names = df_TMD[df_TMD['WORK_ORDR_FLG']=='Y']['STATION'].unique()
yard_act_stations = [station_to_number[name] for name in yard_act_stations_names if name in station_to_number]

# U = set of non yard stations having do/pu activities
U = list(set(non_yard_stations) & set(yard_act_stations))


# associazione terno numero
train_ids = df_TMD['TRAIN_CD'].unique()
train_to_number = {int(train_id): i for i, train_id in enumerate(train_ids)}

############## V ##############
#lista di tuple : (treno, )

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

