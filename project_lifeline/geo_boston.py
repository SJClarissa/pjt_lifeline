#!/usr/bin/env python
# coding: utf-8


import folium
import pandas as pd
import geopandas as gpd
import os
import json
from branca.colormap import linear
from shapely.geometry.polygon import Polygon

# filter geo data with zipcodes and return filtered json
def filter_geo_data(in_file_path, zipcodes):
        
    with open(in_file_path, 'r') as jsonFile:
        data = json.load(jsonFile)

    # Make a json file with the zip codes we're interested in
    geozips = []

    for i in range(len(data['features'])):
        if (data['features'][i]['properties']['POSTCODE'] in list(zipcodes.unique())):
            geozips.append(data['features'][i])

    filtered = dict.fromkeys(['type', 'features'])
    filtered['type'] = 'FeatureCollection'
    filtered['features'] = geozips
    
    return filtered

# return a GeoDataFrame from a geodata and values to match
def shape_geo(geo_data, values):
    
    # Instantiate geodataframe
    crs = {'init': 'epsg:4326'}
    polygon = gpd.GeoDataFrame(crs=crs)
    polygon_sub = gpd.GeoDataFrame(crs=crs)
    
    geo = []
    zipcode = []
    home_val = []
    geo_sub = []
    zipcode_sub = []
    home_val_sub = []

    # Add geodata
    for feature in geo_data['features']:
        try:
            geo.append(Polygon(feature['geometry']['coordinates'][0][0]))
            geo_sub.append(Polygon(feature['geometry']['coordinates'][1][0]))
            zipcode_sub.append(feature['properties']['POSTCODE'])
            home_val_sub.append(values['ZHVIAH'][values['zip'] == feature['properties']['POSTCODE']].values[0])
        except:
            geo.append(Polygon(feature['geometry']['coordinates'][0]))

        zipcode.append(feature['properties']['POSTCODE'])
        home_val.append(values['ZHVIAH'][values['zip'] == feature['properties']['POSTCODE']].values[0])
    
    polygon['zip'] = zipcode
    polygon['geometry'] = geo
    polygon['home_value'] = home_val
    polygon_sub['zip'] = zipcode_sub
    polygon_sub['geometry'] = geo_sub
    polygon_sub['home_value'] = home_val_sub
    
    polygon_mrg = pd.concat([polygon, polygon_sub], axis=0)
    
    return polygon_mrg

def creat_map_bos(polygon_mrg):
    # Credit to Jingwen Zheng
    # https://jingwen-z.github.io/how-to-draw-a-variety-of-maps-with-folium-in-python/

    color_map = linear.Greys_09.scale(min(polygon_mrg['home_value']), max(polygon_mrg['home_value']))
    color_map = color_map.to_step(index=[300000, 400000, 500000, 600000, 700000, 800000, 900000, 1000000, 1100000, 1200000, 1300000, 1400000, 1500000, 1600000])

    m = folium.Map([42.363600, -71.099500], zoom_start=10)

    style_function = lambda x: {
        'fillColor': color_map(x['properties']['home_value']),
        'color': 'black',
        'weight': 1.5,
        'fillOpacity': 0.7
    }

    val = [str("{:,}".format(round(value))) for value in polygon_mrg['home_value']]
    polygon_mrg['all_home_value'] = val

    tooltip = folium.GeoJsonTooltip(fields=['zip','all_home_value'],
                aliases=["Zipcode: ", 'Home Value: '],
                style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"),
                sticky=True)

    folium.GeoJson(
        polygon_mrg,
        style_function=style_function,
        tooltip = tooltip
    ).add_to(m)


    color_map.caption = 'Home value'
    color_map.add_to(m)
    
    return m

def main():
    # Load zipcodes
    val_data = pd.read_csv('./data/zillow_w_na.csv', dtype={'zip': object}, header=0)

    # Load yelp data
    yelp = pd.read_csv("./data/zips_by_lifeline_count_loc_pop_zillow_1.4.csv", dtype={'zipcode': object})

    # Define zillow home value data
    val_data = val_data[['zip', 'ZHVIAH']]
    val_data.loc[val_data['ZHVIAH'].isnull(),'ZHVIAH'] = val_data['ZHVIAH'].mean() # needs imputation

    filtered_geo = filter_geo_data('./data/zipcodes_ma.geojson', val_data['zip'])
    shape_bos = shape_geo(filtered_geo, val_data)
    map_bos = creat_map_bos(shape_bos)

    l_line = [('communications', 'COMMUNICATIONS', 'blue'),
            ('energy', 'ENERGY', 'red'),
            ('food_water_shelter', 'FOOD, WATER, SHELTER', 'black'),
            ('hazmat', 'HAZERDOUS MATERIAL', 'yellow'),
            ('health_medical', 'HEALTH & MEDICAL', 'green'),
            ('safe_sec', 'SAFETY & SECURITY', 'plum'),
            ('transportation', 'TRANSPORTATION', 'purple')]

    for i in yelp.index:
        for line in l_line:
            folium.CircleMarker((yelp[line[0] + ' lat'][i], yelp[line[0] + ' long'][i]),
                            radius = 3, weight = 2, color=line[2], fill_color = line[2], fill_opacity = .5,
                            popup = ((line[1] + '<br>' +
                                        "Total:" + str(yelp[line[0]][i]) + '<br>' +
                                        "Population:" + str("{:,}".format(yelp.population[i])[:-2]) + "<br>" +
                                        'Zipcode:' + str(yelp.zipcode[i])))).add_to(map_bos)

    map_bos.save('./templates/map_boston.html')

def map_one_zipcode(one_zipcode):
    # Load zipcodes
    val_data = pd.read_csv('./data/zillow_w_na.csv', dtype={'zip': object}, header=0)

    # Load yelp data
    yelp_zip = pd.read_csv("./data/final_yelp_scrape.csv", dtype={'zipcode': object})
    yelp_zip = yelp_zip[yelp_zip['zipcode'] == one_zipcode]

    # Define zillow home value data
    val_data = val_data[['zip', 'ZHVIAH']]
    val_data.loc[val_data['ZHVIAH'].isnull(),'ZHVIAH'] = val_data['ZHVIAH'].mean() # needs imputation
    min_val = min(val_data['ZHVIAH'])
    max_val = max(val_data['ZHVIAH'])
    val_data = val_data[val_data['zip'] == one_zipcode]

    filtered_geo = filter_geo_data('./data/zipcodes_ma.geojson', val_data['zip'])
    shape_bos = shape_geo(filtered_geo, val_data)
    map_zip = creat_map_zip(shape_bos, min_val, max_val)

    l_line_color = {'communications': 'blue',
            'energy': 'red',
            'food_water_shelter': 'black',
            'hazmat': 'yellow',
            'health_medical':'green',
            'safe_sec': 'plum',
            'transportation':'purple'}

    for i in yelp_zip.index:
        l_color = l_line_color[yelp_zip.lifeline[i]]
        folium.CircleMarker((yelp_zip.latitude[i],yelp_zip.longitude[i]),
                            radius=3, weight=2, color=l_color, fill_color=l_color,
                            fill_opacity=.5,
                        popup = (("Name:" + yelp_zip.loc[i, 'name'] + '<br>'+
                                    'phone:' + str(yelp_zip.loc[i, 'phone'])))).add_to(map_zip)


    map_zip.save('./templates/map_zipcode.html')
    return map_zip

def creat_map_zip(polygon_mrg, min_hv, max_hv):
    # Credit to Jingwen Zheng
    # https://jingwen-z.github.io/how-to-draw-a-variety-of-maps-with-folium-in-python/

    color_map = linear.Greys_09.scale(min_hv, max_hv)
    color_map = color_map.to_step(index=[300000, 400000, 500000, 600000, 700000, 800000, 900000, 1000000, 1100000, 1200000, 1300000, 1400000, 1500000, 1600000])

    try: 
        m = folium.Map([polygon_mrg['geometry'][0].centroid.y[0].mean(),
                        polygon_mrg['geometry'][0].centroid.x[0].mean()], zoom_start=13)
    except:
        m = folium.Map([polygon_mrg['geometry'][0].centroid.y,
                        polygon_mrg['geometry'][0].centroid.x], zoom_start=13)

    style_function = lambda x: {
        'fillColor': color_map(x['properties']['home_value']),
        'color': 'black',
        'weight': 1.5,
        'fillOpacity': 0.7
    }

    folium.GeoJson(
        polygon_mrg,
        style_function=style_function
    ).add_to(m)


    color_map.caption = 'Home value'
    color_map.add_to(m)
    
    return m

