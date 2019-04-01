import pandas as pd
import numpy as np
import csv
from collections import Counter
from matplotlib import pyplot as plt

def get_year_from_date(date):
    return date.split('/')[2]

evictions = pd.read_csv('Eviction_Notices.csv')
dates = evictions['File Date']

evictions_by_year = [int(get_year_from_date(date)) for date in dates]
evictions_by_year_dict = Counter(evictions_by_year)

print(evictions_by_year_dict)

years_range = [i for i in range(min(evictions_by_year), max(evictions_by_year)+1)]
num_evictions = [evictions_by_year_dict[year] for year in years_range]

plt.plot(years_range, num_evictions)
plt.xlabel('Years')
plt.ylabel('Eviction Notices')
plt.show()
