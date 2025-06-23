import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import pandas as pd
import numpy as np

deviations = pd.read_csv('deviations.csv')
sns.kdeplot(data=deviations,
            x='DEST_DEV', hue='TRAIN_PRTY', common_norm=False,
            palette=['C6', 'C0'], fill=True)
ylims = plt.ylim()
plt.vlines([deviations[deviations['TRAIN_PRTY']=='H']['DEST_DEV'].mean(),
            deviations[deviations['TRAIN_PRTY']=='L']['DEST_DEV'].mean()],
            ymin=0, ymax=ylims[1], colors=['C6', 'C0'], linestyles='dashed')
plt.xlabel('Deviation (hours)')
plt.xticks([x for x in range(15)])
plt.xlim((1,15))
plt.ylim(ylims)
plt.show()

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

day='2017-09-06'
n_rows = 8013

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
# Crea un dizionario di mapping: nome stazione → indice
station_to_number = {name: idx for idx, name in df_SOD['Station'].items()}


def plot_route( file_name, route, trains):
    #prendo il file csv e lo trasformo in df
    df = pd.read_csv(file_name)

    # Inversi
    number_to_train = {v: k for k, v in train_to_number.items()}
    number_to_station = {v: k for k, v in station_to_number.items()}

    # Plot
    plt.figure(figsize=(10, 6))
    cmap = plt.colormaps['tab10']
    colors = ['lightblue', 'blue', 'palegreen', 'green', 'pink', 'red', 'navajowhite', 'orange', 'plum', 'purple']

    trains_num = []
    for train_id in trains:
        trains_num.append(train_to_number[train_id])
    
    filt_df = df[df['TRAIN_CD'].isin(trains_num)]

    match route: 
        case 'W':
            #ordino stazioni della route sulla y
            stations_num = [i for i in range(32)]  # questo cambia per ogni route

        case 'E':
            #ordino stazioni della route sulla y
            stations_num = [i for i in range(44, 55)]  # questo cambia per ogni route 
        
        case 'S':
            #ordino stazioni della route sulla y
            stations_num = [i for i in range(55, 61)]  # questo cambia per ogni route 

        case 'N':
            #ordino stazioni della route sulla y
            stations_num = [i for i in range(32, 44)]  # questo cambia per ogni route 
            
        case _:
            print('default case')

    stations_to_y = {station: i for i, station in enumerate(stations_num)}  
    # Mappa train_id → colore
    train_colors = {
        train_id: colors[i % len(colors)]
        for i, train_id in enumerate(trains)
    }

    #per ogni treno (groupby)
    for train_num, group in filt_df.groupby('TRAIN_CD'):
        color = train_colors[number_to_train[train_num]]
        train_label = f"Train {number_to_train[train_num]}"
        labeled = False  # flag per etichetta

        for i in range(len(group)-1):
            row = group.iloc[i]
            st = row['STATION']
            arr = row['EST_ARR_TM']
            dep = row['EST_DEP_TM']
            
            next_row = group.iloc[i+1]
            next_st = next_row['STATION']
            next_arr = next_row['EST_ARR_TM']

            if st in stations_num :
                # Fermata
                if pd.notna(arr) and pd.notna(dep) and arr != dep:
                    y = stations_to_y[int(st)]
                    plt.plot([arr, dep], [y, y], color=color, linewidth=2,
                            label=train_label if not labeled else "")
                    labeled = True

                # Movimento
                if pd.notna(dep) and pd.notna(next_arr) and next_st in stations_num:
                    y1, y2 = stations_to_y[int(st)], stations_to_y[int(next_st)]
                    plt.plot([dep, next_arr], [y1, y2], color=color, linewidth=2,
                            label=train_label if not labeled else "")
                    labeled = True

    # Etichette asse Y con nomi delle stazioni
    plt.yticks(
        [stations_to_y[s] for s in stations_num],
        [number_to_station[s] for s in stations_num]
    )
    plt.xlabel("Time")
    plt.ylabel("Station")
    plt.title("Train Movement Diagram")

    # Legenda con codici treno
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(sorted(zip(labels, handles)))  # ordina per label
    plt.legend(by_label.values(), by_label.keys(), title="Train Number", loc='center left', bbox_to_anchor=(1, 0.5))
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    return


train_W = [222, 820, 834, 853, 866, 884, 2253, 2277, 3522, 3533]
train_E = [107, 823, 824, 839, 856, 882, 892, 3546, 3553, 3565]
train_N = [54, 107, 212, 333, 511, 537]
train_S = [815, 817, 818, 819, 820, 821, 822, 823, 824, 825]

plot_route( r"train_mvmt_estimation.csv", 'E', train_E )
plot_route( r"train_mvmt_estimation.csv", 'W', train_W )
plot_route( r"train_mvmt_estimation.csv", 'S', train_S )
plot_route( r"train_mvmt_estimation.csv", 'N', train_N )
