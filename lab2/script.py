import numpy as np 
import matplotlib.pyplot as plt
import sys

if len(sys.argv) < 2:
    print("Usage: sudo python3 script.py <path/to/datafile.txt>")

path2file = sys.argv[1] # "assignment2/frames002/data.txt"

lat, lon, dbs, _ = np.loadtxt(path2file, skiprows=25, unpack=True) 

# skiprows=6 skips the first header lines
# unpack=True imports the columns instead of the rows

dbs_sort = np.sort(dbs)
dbs_normalized = np.arange(1, len(dbs_sort)+1) / len(dbs_sort)

print(f"Number of data points: {len(dbs)}")

thresholds = [0, 5, 10, 15, 20, 25, 30]

print("-" * 35)

for t in thresholds:
    count = np.sum(dbs < t)
    percentage = (count / len(dbs)) * 100

    Pr = -95 + t

    # Just copy pasted
    note = ""
    if t == 0: note = "<- Area without coverage"
    if t == 5: note = "<- Area below g"

    print(f"Pr < {Pr} dBm (Rx < {t} dB): {percentage:6.2f}% {note}") 

# Plot
plt.plot(dbs_sort, dbs_normalized, '.', color='blue')
plt.xlabel('Rx values - dBs')         
plt.ylabel('CumulativeDistributionFunction')                  
plt.title('CDF via Sorting')       
plt.grid()                         
plt.show()

"""

# Percentage without coverage
no_coverage_count = np.sum(dbs < 0)
percent_no_coverage = (no_coverage_count / len(dbs)) * 100
 
# Percentage with good coverage
good_coverage_count = np.sum(dbs > 5)
percent_good_coverage = (good_coverage_count / len(dbs)) * 100
  
print("-" * 35)
print(f"Points with dB < 0: {no_coverage_count}")
print(f"Percentage of Area without coverage: {percent_no_coverage:.2f}%")

print("-" * 35)
print(f"Points with dB > 5: {good_coverage_count}")
print(f"Percentage of Area with good coverage: {percent_good_coverage:.2f}%")
print("-" * 35)
 
"""
 





