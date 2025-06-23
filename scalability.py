from problem import load_and_solve
import time
import matplotlib.pyplot as plt
import sys
import numpy as np
import pandas as pd

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("Usage: python3 scalability.py <x> where 'x' is the day considered (can be 1 or 2)")
        sys.exit(1)
    if sys.argv[1] == '1':
        nrows = [199, 406, 590, 797, 1004, 1211, 1395, 1602, 1806, 1998, 2206, 2398, 2606, 2798, 3005, 3197, 3407, 3600, 3800, 3978]
        date = '2017-09-06'
        m = 0
    elif sys.argv[1] == '2':
        nrows = [4196, 4399, 4606, 4813, 4997, 5204, 5411, 5595, 5802, 5999, 6207, 6399, 6607, 6799, 7007, 7199, 7409, 7602, 7794, 8013]
        date = '2017-09-07'
        m = 3978
    else:
        print("Usage: python3 scalability.py <x> where 'x' is the day considered (can be 1 or 2)")
        sys.exit(1)
    # Execution time
    times = []
    x = []

    input('Press enter to start...')
    for i,n in enumerate(nrows):
        print(f"\n ####### {n-m} rows ({i+1}/{len(nrows)}) #######\n")
        start = time.perf_counter()
        load_and_solve(n, date, False)
        end = time.perf_counter()
        times.append((end-start))
        x.append(n-m)
        inkey = input("Continue? [y/n]: ")
        if inkey != 'y':
            break

    plt.figure(figsize=(19.2, 10.8))
    plt.plot(x, times, 'o-')
    plt.xlabel('Number of processed rows')
    plt.xticks(x)
    plt.xlim((x[0], x[-1]))
    plt.ylabel('Execution time (seconds)')
    plt.yticks([y for y in range(0,240,30)])
    plt.ylim((0, max(times)))
    plt.grid()
    plt.savefig('scalability.png')
    plt.show()

    # RAM usage
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
    plt.savefig('scalability_ram.png')
    plt.show()