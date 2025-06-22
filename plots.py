import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import pandas as pd

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
