import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('ram_usage.csv')
arr = df.to_numpy()[:, 1:]

nrows = df.columns[1:].to_numpy(dtype=np.int32)
mean = arr.mean(axis=0)
std = arr.std(axis=0)

plt.errorbar(x=nrows,y=mean,yerr=std,fmt='o-')
plt.xticks(nrows)
plt.xlabel('Number of processed rows')
plt.yticks([y for y in range(0,33,2)])
plt.ylabel('Peak virtual memory usage (GB)')
plt.grid()
plt.show()
