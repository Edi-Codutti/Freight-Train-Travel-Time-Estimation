from problem import load_and_solve
import time
import matplotlib.pyplot as plt

nrows = [199, 406, 590, 797, 1004, 1211, 1395, 1602, 1806, 1998, 2206, 2398, 2606, 2798, 3005, 3197, 3407, 3600, 3800, 3978]
times = []

for n in nrows:
    print(f"\n ####### {n} rows #######\n")
    start = time.perf_counter()
    load_and_solve(n, '2017-09-06', False)
    end = time.perf_counter()
    times.append((end-start))

plt.figure(figsize=(19.2, 10.8))
plt.plot(nrows, times, 'o-')
plt.xlabel('Number of processed rows')
plt.xticks(nrows)
plt.xlim((0, 3978))
plt.ylabel('Execution time (seconds)')
plt.yticks([y for y in range(0,240,30)])
plt.ylim((0, 210))
plt.grid()
plt.show()