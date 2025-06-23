import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

df1 = pd.read_csv('ram_usage_auto.csv')
arr1 = df1.to_numpy()[:, 1:]

df2 = pd.read_csv('ram_usage_simplex.csv')
arr2 = df2.to_numpy()[:, 1:].flatten()

nrows = df1.columns[1:].to_numpy(dtype=np.int32)
mean = arr1.mean(axis=0)
std = arr1.std(axis=0)

plt.errorbar(x=nrows,y=mean,yerr=std,fmt='o-',label='auto')
plt.plot(nrows,arr2,'o-',label='concurrent simplex')
plt.xticks(nrows)
plt.xlabel('Number of processed rows')
plt.yticks([y for y in range(0,33,2)])
plt.ylabel('Peak virtual memory usage (GB)')
plt.grid()
plt.legend()
plt.show()
