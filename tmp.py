import matplotlib.pyplot as plt

nrows = [218,421,628,835,1019,1226,1433,1617,1824,2021,2229,2421,2629,2821,3029,3221,3431,3624,3816,4035]
arr2 = [2.390,2.397,2.476,2.568,2.779,2.769,3.027,3.321,4.826,4.773,5.012,5.483,5.234,5.599,6.200,6.920,7.590,18.9,8.946,9.730]

plt.plot(nrows,arr2,'o-')
plt.xticks(nrows)
plt.xlabel('Number of processed rows')
plt.yticks([y for y in range(0,33,2)])
plt.ylabel('Peak virtual memory usage (GB)')
plt.grid()
plt.show()
