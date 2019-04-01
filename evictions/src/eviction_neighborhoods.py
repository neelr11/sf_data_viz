import pandas as pd
import numpy as np
import json
from pprint import pprint
from shapely.geometry import shape, Point
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.exc import GeocoderServiceError
import collections
from matplotlib import pyplot as plt
import time
import csv


geolocator = Nominatim(user_agent='Neel')

def get_neighborhoods():
    with open('AnalysisNeighborhoods.geojson') as f:
        neighborhoods_obj = json.load(f)
    return neighborhoods_obj

def get_point_from_loc(location_str):
    location_str = location_str.replace('(', '')
    location_str = location_str.replace(')', '')
    location_str = location_str.replace(',', '')
    lat_lon = location_str.split(' ')
    return Point(float(lat_lon[1]), float(lat_lon[0]))

def get_address_from_block(block_addr):
    block_addr = block_addr.replace('Block Of', '')
    block_addr_split = block_addr.split('  ')

    block_addr = block_addr_split
    # make it an address instead of block start
    #print block_addr
    block_addr[0] = str(int(block_addr[0]) + 1)
    block_addr = ' '.join(block_addr) + ' San Francisco CA'
    return block_addr

# Using latitude longitude location, find the neighborhood the eviction belongs to
def get_neighborhoods_from_locations(evictions, neighborhoods):
    num_found = 0
    num_total = 0
    locations_dict = collections.defaultdict(int)
    locations_with_years_dict = collections.defaultdict(lambda: collections.defaultdict(int))
    for index, eviction in evictions.iterrows():
        point = get_point_from_loc(eviction['Location'])
        found_location = False
        for feature in neighborhoods['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                #print('Found containing polygon:', feature['properties']['nhood']())
                num_found += 1
                found_location = True
                neighborhood = feature['properties']['nhood']
                year = int(eviction['File Date'].split('/')[2])
                if year > 90: year = year + 1900
                else: year = year + 2000

                locations_dict[neighborhood] += 1
                locations_with_years_dict[neighborhood][str(year)] += 1
                break
        if not found_location:
            print('Location ' + str(eviction['Eviction ID']) + ' not found, Given [location: ' + str(eviction['Neighborhoods - Analysis Boundaries']))
        num_total += 1

    years = [str(i) for i in range(1997, 2019)]
    #years = ['97', '98', '99', '00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18']
    with open('Evictions_By_Location.csv', mode='w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"')
        csv_writer.writerow(['Location', 'Number of Evictions'])
        for k, v in locations_dict.items():
            csv_writer.writerow([k, v])

    with open('Evictions_By_Year_Location.csv', mode='w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"')
        header = ['Location']
        for year in years:
            header.append(year)
        csv_writer.writerow(header)
        for k, v in locations_with_years_dict.items():
            row = [k]
            for year in years:
                row.append(v[year])
            csv_writer.writerow(row)


    for k, v in locations_with_years_dict.items():
        print k
        evictions = [int(v[year]) for year in years]
        # plt.figure()
        # plt.plot(years, evictions)
        plt.title(k)
        for year in years:
            print year + ': ' + str(v[year])
        print ''
    # plt.show()
    return locations_dict, locations_with_years_dict


def get_geocode_address(addr):
    try:
        return geolocator.geocode(addr)
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        time.sleep(5)
        return get_geocode_address(addr)

#For rows missing latitude longitude location,
# use the block address to add missing lat long to dataframe
# If the block address is incorrect, print it so we can correct it manually
def set_missing_locations(evictions):

    missing_location_rows = evictions[evictions['Location'].isnull()]
    print('Num missing ' + str(len(missing_location_rows)))
    num_not_found = 0
    num_found = 0
    for index, row in missing_location_rows.iterrows():
        #print row['Eviction ID']
        addr = get_address_from_block(row['Address'])
        location = get_geocode_address(addr)
        if location == None:
            num_not_found += 1
            print('NOT FOUND ' + str(row['Eviction ID']) + ': ' + addr)
        else:
            evictions.at[index, 'Location'] = '(' + str(location.latitude) + ', ' + str(location.longitude) + ')'
            num_found += 1
        if (num_found + num_not_found) % 50 == 0:
            print('Processed ' + str(num_found + num_not_found) + ' evictions')

    print 'Total not found ' + str(num_not_found)
    print 'Total found ' + str(num_found)
    evictions.to_csv('Eviction_Notices_With_Locations.csv')


evictions = pd.read_csv('Eviction_Notices_With_Locations.csv')
neighborhoods = get_neighborhoods()
#set_missing_locations(evictions)

locations_dict, locations_with_years_dict = get_neighborhoods_from_locations(evictions, neighborhoods)

with open('AnalysisNeighborhoods.geojson') as f:
  data = json.loads(f.read())

years = [i for i in range(1997, 2019)]

for neighborhood_obj in data['features']:
    neighborhood_name = neighborhood_obj['properties']['nhood']
    neighborhood_obj['properties']['evictions'] = {}
    neighborhood_obj['properties']['evictions']['total'] = locations_dict[neighborhood_name]
    for year in years:
        neighborhood_obj['properties']['evictions'][str(year)] = locations_with_years_dict[neighborhood_name][year]

with open('AnalysisNeighborhoods.geojson', 'w') as f:
    json.dump(data, f)