import json

with open('AnalysisNeighborhoods.geojson') as f:
  data = json.loads(f.read())

neighborhoods = data['features']
for neighborhood in neighborhoods:
  neighborhood['properties']['evictions'] = 5

print data

