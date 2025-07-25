import pandas as pd
import numpy as np
from solver import Solver
import datetime
import sys


def indexed_data(data1_to_number, data2_to_number, L_t):
    n_treni = len(data1_to_number)
    L = [[] for _ in range(n_treni)]

    # 2. Popola la lista usando i dizionari
    for train_id, station_list in L_t:
        train_num = data1_to_number[train_id]  # numero treno assegnato
        station_nums = [data2_to_number[st] for st in station_list]
        L[train_num] = station_nums
    return L

def somma_binari(row):
    count = 0
    if row['Siding_Flg'] == 'Y':
        count += row['# of STrks']
    if row['Yard_Flg'] == 'Y':
        count += row['# of YTrks']
    return count

def load_and_solve(n_rows:int, day:str, export:bool):
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
    non_yard_stations = df_SOD[df_SOD['Yard_Flg']!='Y']['Station'].index.tolist()

    df_TMD = pd.read_excel(r"RAS-PSC_ValDataset_20200609-06.xlsx", sheet_name='Train Mvmt Data', nrows=n_rows, usecols='A:M')
    df_TMD = df_TMD[df_TMD['DATE']==day] # modify this to change date

    # delete where STATION == TO_STN
    to_delete = []
    for idx, row in df_TMD.iterrows():
        if row['STATION'] == row['TO_STN']:
            df_TMD.loc[idx+1, 'STN_TYPE'] = 'Origin'
            df_TMD.loc[idx+1, 'PLAN_ARR_TM'] = np.nan
            to_delete.append(idx)
    df_TMD = df_TMD.drop(index=to_delete)

    # associazione treno numero
    train_ids = df_TMD['TRAIN_CD'].unique()
    train_to_number = {int(train_id): i for i, train_id in enumerate(train_ids)}

    # track speed list
    track_speed = [100] * len(J)

    #conversione da data a ora  in decimali 
    df_TMD['PLAN_ARR_TM'] = (pd.to_datetime(df_TMD['PLAN_ARR_TM'])-datetime.datetime.fromisoformat(day))
    df_TMD['PLAN_ARR_TM'] = df_TMD.apply(lambda x: x['PLAN_ARR_TM'].total_seconds()/3600, axis=1)
    
    df_TMD['PLAN_DEP_TM'] = (pd.to_datetime(df_TMD['PLAN_DEP_TM'])-datetime.datetime.fromisoformat(day))
    df_TMD['PLAN_DEP_TM'] = df_TMD.apply(lambda x: x['PLAN_DEP_TM'].total_seconds()/3600, axis=1)

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
                    if (s1 == 12) or (s1 == 14):
                        nc_idx_13.append(index)
                    else:
                        nc_idx_23.append(index)

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
        df_TMD.loc[idx, 'TO_STN'] = 'Bgnphm'

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
        df_TMD.loc[idx, 'TO_STN'] = 'Tb'

    # stations with do/pu activities
    yard_act_stations_names = df_TMD[df_TMD['WORK_ORDR_FLG']=='Y']['STATION'].unique()
    yard_act_stations = [station_to_number[name] for name in yard_act_stations_names if name in station_to_number] # TODO: do we need 'if name in station_to_number'?

    ############## U ##############
    U = list(set(non_yard_stations) & set(yard_act_stations))

    ############## I ##############
    I = list(range(len(train_to_number)))

    ############## H ##############
    train_ids_standard_prty = df_TMD[df_TMD['TRAIN_PRTY']=='S']['TRAIN_CD'].unique()
    H = [train_to_number[id] for id in train_ids_standard_prty]

    ############## L ##############
    train_ids_low_prty = df_TMD[df_TMD['TRAIN_PRTY']=='L']['TRAIN_CD'].unique()
    L = [train_to_number[id] for id in train_ids_low_prty]

    ############## V ##############
    # Filtro: escludi stazioni di tipo 'Origin' e 'Dest', ~df_TMD['STN_TYPE'].isin(['Origin', 'Dest']) restituisce un booleano True per tutte le righe in cui STN_TYPE non è né 'Origin' né 'Dest'.
    df_filtrato = df_TMD[~df_TMD['STN_TYPE'].isin(['Origin', 'Dest'])]

    # Ora raggruppa solo sulle righe filtrate
    V_t = df_filtrato.groupby('TRAIN_CD')['STATION'].apply(list).reset_index().values.tolist()

    V = indexed_data (train_to_number, station_to_number, V_t)


    ############## C ##############
    C_t = df_TMD[df_TMD['WORK_ORDR_FLG']=='Y'].groupby('TRAIN_CD')['STATION'].apply(list).reset_index().values.tolist()

    C = indexed_data (train_to_number, station_to_number, C_t)



    ############## W ##############
    W_t = df_TMD[df_TMD['CREW_CHG_FLG']=='Y'].groupby('TRAIN_CD')['STATION'].apply(list).reset_index().values.tolist()

    W = indexed_data (train_to_number, station_to_number, W_t)

    ############## K ##############
    K_t = df_TMD[df_TMD['STN_TYPE']=='Stop'].groupby('TRAIN_CD')['STATION'].apply(list).reset_index().values.tolist()

    K = indexed_data (train_to_number, station_to_number, K_t)

    ############## o ##############
    o_t = df_TMD[df_TMD['STN_TYPE']=='Origin'].groupby('TRAIN_CD')['STATION'].apply(list).reset_index().values.tolist()

    n_treni = len(train_to_number)
    n_staz = len(station_to_number)
    o = [0]*n_treni

    for train_id, station_list in o_t:
        train_num = train_to_number[train_id]  # numero treno assegnato
        station_nums = [station_to_number[st] for st in station_list if st in station_to_number]  # numeri stazioni
        if len(station_nums) == 1:
            o[train_num] = station_nums[0]
        else:
            print(f"train: {train_id}, origin stations: {station_nums}")
            raise ValueError("La lista non ha un solo elemento")

    ############## f ##############
    f_t = df_TMD[df_TMD['STN_TYPE']=='Dest'].groupby('TRAIN_CD')['STATION'].apply(list).reset_index().values.tolist()

    f = [0]*n_treni

    for train_id, station_list in f_t:
        train_num = train_to_number[train_id]  # numero treno assegnato
        station_nums = [station_to_number[st] for st in station_list if st in station_to_number]  # numeri stazioni
        if len(station_nums) == 1:
            f[train_num] = station_nums[0]
        else:
            raise ValueError("La lista non ha un solo elemento")
        

    ############## G ##############

    G_t = df_filtrato.groupby('STATION')['TRAIN_CD'].apply(list).reset_index().values.tolist()

    G = indexed_data(station_to_number, train_to_number, G_t)


    ############## Gp ##############
    Gp_t = df_filtrato[df_TMD['WORK_ORDR_FLG']=='Y'].groupby('STATION')['TRAIN_CD'].apply(list).reset_index().values.tolist()

    Gp = indexed_data(station_to_number, train_to_number, Gp_t)



    ############## O ##############
    O_t = df_TMD[df_TMD['STN_TYPE']=='Origin'].groupby('STATION')['TRAIN_CD'].apply(list).reset_index().values.tolist()

    O = indexed_data(station_to_number, train_to_number, O_t)



    ############## F ##############
    F_t = df_TMD[df_TMD['STN_TYPE']=='Dest'].groupby('STATION')['TRAIN_CD'].apply(list).reset_index().values.tolist()

    F = indexed_data(station_to_number, train_to_number, F_t)


    ############## t, E, T1, T2 ##############
    t = np.full((n_treni, len(J)), np.nan)
    E = [[] for _ in I]
    T1 = [set() for _ in J]
    T2 = [set() for _ in J]
    for _, row in df_TMD.iterrows():
        i = train_to_number[row['TRAIN_CD']]
        s1 = station_to_number[row['STATION']]
        if row['STN_TYPE'] != 'Dest':
            s2 = station_to_number[row['TO_STN']]
            try:
                j = P.index((s1,s2))
            except ValueError:
                j = P.index((s2,s1))
            E[i].append(j)
            t[i,j] = distances[j]/min(track_speed[j], row['MAX_SPD'])
            if row['DEP_DIR'] == 'E':
                T2[j].add(i)
            else:
                T1[j].add(i)

    ############## a , d ##############

    # Matrice vuota con nan (nessun arrivo)
    a = np.full((n_treni, n_staz), np.nan)

    for _, row in df_TMD.iterrows():
        train_code = row['TRAIN_CD']
        station_name = row['STATION']
        arrival_time = row['PLAN_ARR_TM']

        train_idx = train_to_number[train_code]
        station_idx = station_to_number[station_name]

        a[train_idx, station_idx] = arrival_time

    # Matrice vuota con nan (nessuna partenza)
    d = np.full((n_treni, n_staz), np.nan)

    for _, row in df_TMD.iterrows():
        train_code = row['TRAIN_CD']
        station_name = row['STATION']
        departure_time = row['PLAN_DEP_TM']

        train_idx = train_to_number[train_code]
        station_idx = station_to_number[station_name]

        d[train_idx, station_idx] = departure_time


    ############## n , m ##############

    n = df_SOD.apply(somma_binari, axis=1).tolist()

    m = [2]*n_staz
    m[22] = 4
    for i in range(27, 31):
        m[i] = 4 
    m[40] = 1

    ############## A1 , A2 , A4 ##############
    non2arcs = []
    A1 = []
    for k, (i,j) in enumerate(P) :
        if i in list(range(40,44)):
            non2arcs.append(J[k])
            A1.append(J[k])

    A4 = [21, 22]
    non2arcs.append(21)
    non2arcs.append(22)
    for k, (i,j) in enumerate(P) :
        if i in list(range(26,31)):
            non2arcs.append(J[k])
            A4.append(J[k])

    A2 = []
    for i in range(len(P)) :
        if i not in non2arcs:
            A2.append(i)

    α = 5/60
    β = 1.87
    γ = 1.82
    θ = 1.35
    λ = 5
    τ = lambda a,b : min(a,b)
    M = 48

    solver = Solver(I, S, J, H, L, A1, A2, A4, B, U, V, C, W, K, E, P, o, f, G, Gp, O, F, T1, T2, a, d, t, n, m, α, β, γ, θ, λ, τ, M)
    solver.solve()

    if export is True:
        with open("train_mvmt_estimation.csv", "w") as csv:
            csv.write("TRAIN_CD,STATION,EST_ARR_TM,EST_DEP_TM\n")
            for i in I:
                for s in [o[i]]+V[i]+[f[i]]:
                    if s != o[i] and s != f[i]:
                        csv.write(f"{i},{s},{solver._vars['x'][i,s].X},{solver._vars['y'][i,s].X}\n")
                    elif s == o[i]:
                        csv.write(f"{i},{s},{np.nan},{solver._vars['y'][i,s].X}\n")
                    else:
                        csv.write(f"{i},{s},{solver._vars['x'][i,s].X},{np.nan}\n")
        with open("deviations.csv", "w") as csv:
            csv.write("TRAIN_CD,TRAIN_PRTY,DEST_DEV\n")
            for i in H:
                csv.write(f"{i},H,{solver._vars['dp'][i,f[i]].X}\n")
            for i in L:
                csv.write(f"{i},L,{solver._vars['dp'][i,f[i]].X}\n")


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("Usage: python3 problem.py <x> where 'x' is the day considered (can be 1 or 2)")
        sys.exit(1)
    if sys.argv[1] == '1':
        date = '2017-09-06'
    elif sys.argv[1] == '2':
        date = '2017-09-07'
    else:
        print("Usage: python3 problem.py <x> where 'x' is the day considered (can be 1 or 2)")
        sys.exit(1)
    load_and_solve(n_rows=8013, day=date, export=True)
