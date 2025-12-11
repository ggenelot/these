# import osmnx
import osmnx as ox
import geopandas as gpd

place_name="martinique"


# List key-value pairs for tags
tags = {'building': True}   

buildings = ox.features_from_place(place_name, tags)
print(buildings.head())
