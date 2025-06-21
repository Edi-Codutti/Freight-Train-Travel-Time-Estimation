from problem import load_and_solve
import time
import matplotlib.pyplot as plt

nrows = []
times = []

for n in nrows:
    start = time.perf_counter()
    load_and_solve(n, '2017-09-06', False)
    end = time.perf_counter()
    times.append((end-start))

plt.plot(nrows, times, 'o-')
plt.show()