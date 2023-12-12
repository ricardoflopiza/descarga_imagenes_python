# Promedios mensuales de los ultimos 3 años

# pip install earthengine-api

import ee
import geopandas as gpd
import json
import pandas as pd
import time
import numpy as np
import os.path
import geemap


start_time = time.perf_counter()

# https://developers.google.com/earth-engine/guides/service_account#use-a-service-account-with-a-private-key

service_account = 'gee-ine@ee-ricpizarrosine.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(service_account, 'privatekey.json')
ee.Initialize(credentials)

### shapes in local to python
#shapefile = gpd.read_file("ips_shapes/ips_shapes.shp")
shapefile_ALL = gpd.read_file("gran_santiago/gran_santiago.shp")
#shapefile_ALL = gpd.read_file("Manzanas/pob_manzana_censo2017.shp")

#shapefile_ALL = shapefile_ALL.iloc[0:40,]

mylist = [[i+1]*100 for i in range(len(shapefile_ALL))]
shapefile_ALL['group_id'] = np.resize(mylist,len(shapefile_ALL))

# print(shapefile_ALL)

for i in range(shapefile_ALL["group_id"].max()):
    print(i+1)
    shapefile = shapefile_ALL[shapefile_ALL.group_id == i+1]
    #print(df_new)

    features = []
    for i in range(shapefile.shape[0]):
        geom = shapefile.iloc[i:i+1,:] 
        jsonDict = eval(geom.to_json()) 
        geojsonDict = jsonDict['features'][0] 
        features.append(ee.Feature(geojsonDict)) 

    fc = ee.FeatureCollection(features)

    print("crear feature")

       ## NDVI function
    def add_ndvi(image):
         # Normalized difference vegetation index (NDVI)
         ndvi = image.normalizedDifference(['B8','B4']).rename("NDVI")
         image = image.addBands(ndvi)
         return(image)

       ## barrel soil function
    formula_barrel_soil = "((b('B11') + b('B4')) - (b('B8') + b('B2'))) / ((b('B11') + b('B4')) + (b('B8') + b('B2')))"

    def add_barrel_soil(image):
           barrel_soil =  image.expression(formula_barrel_soil).rename('BARREL_SOIL')
           image = image.addBands(barrel_soil)
           return(image)

       ## build index function
    formula_build_index = "(b('B11') - b('B8')) / (b('B11') + b('B8'))";

    def add_buil_index(image):
           build_index =  image.expression(formula_build_index).rename('BUILD_INDEX');
           return image.addBands(build_index)


       # Import the Sentinel-2 image collection ##### fechas casem
    S2_SR = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')\
                 .filterBounds(fc)\
                 .filterDate('2022-11-01', '2023-02-02')\
                 .map(add_ndvi).map(add_barrel_soil).map(add_buil_index)

       #print('Image collection:', S2_SR.first().getInfo())

       # # Select the NDVI band and reduce all dates by mean
    veget = S2_SR#.select('NDVI')
    veget_red = veget.reduce(ee.Reducer.median())

    print("promedio tiempo")
       #veget_red


        ### Calculate the mean NDVI inside each polygon

    def calcmean(feature):
          reduced = veget_red.reduceRegions(
                    collection = feature,
                    reducer = ee.Reducer.mean(),
                    scale = 10)
          #print("si")

          return reduced


    final = fc.map(calcmean).flatten()

    print("promedio regiones")

    #print(final.getInfo())

    ### acá se cae

    df = geemap.ee_to_pandas(final)

    print("to df")

    #print(df)

    if os.path.isfile('./prueba_descarga_all_bands.csv') :
        df.to_csv('prueba_descarga_all_bands.csv', mode='a', header=False)
    else:
        df.to_csv('prueba_descarga_all_bands.csv')
    time.sleep(5)

 

end_time = time.perf_counter()

# Calculate elapsed time
elapsed_time = end_time - start_time
print("Elapsed time: ", elapsed_time/60)