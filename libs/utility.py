# Jessica Embury
# RedID 823859615
# GEOG-582 Final Project

# import statements
from .point import Point

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import os
from osgeo import ogr
from osgeo import osr
import pandas as pd
import random
import seaborn as sns
import time

# ignore pandas dataframe slice warning
pd.options.mode.chained_assignment = None  # default='warn'


# generate random id numbers for Point objects
def generate_id_nums(quantity=None, min_num=10000, max_num=99999):
    """
    Returns a list of 'quantity' random numbers between 'min_num' and 'max_num'
    :param quantity: int, number of values
    :param min_num: int, minimum random number
    :param max_num: int, maximum random number
    :return: list of random numbers
    """
    # ask for appropriate quantity, if needed
    if type(quantity) is not int or quantity <= 0:
        quantity = int(input('Invalid quantity. Please enter an integer greater than zero.'))

    # generate list of unique random integeres between min and max parameters
    try:
        id_num_list = random.sample(range(min_num, max_num), quantity)
        return id_num_list

    except Exception as e:
        print('Exception: {}'.format(e))
        return e


def create_address_table(csv_path):
    """
    Create a pandas df from csv file and add unique identifiers.
    :param csv_path: path to csv with address info
    :return: dataframe with csv info and unique id numbers added to each record
    """
    # create dataframe
    table = pd.read_csv(csv_path)

    # generate random ids
    id_num_list = generate_id_nums(len(table))

    # assign random ids
    table['id_num'] = ''
    for i, row in table.iterrows():
        table['id_num'][i] = id_num_list[i]

    return table


# create point object list from address tables with known coordinates
def create_points_known_coords(address_table, name_col, address_col, latitude, longitude):
    """
    Create Point objects from known coordinates in the address table.
    :param address_table: pandas df with addresses and identifiers
    :param name_col: name field
    :param address_col: address field
    :param latitude: latitude field
    :param longitude: longitude field
    :return: updated address table and list containing known points objects
    """
    # list to store Point objects
    point_list = []

    # add column for known Point objects
    address_table['known'] = None

    # for each row in the address table
    for i, row in address_table.iterrows():
        # create a Point object
        point = Point(address_table['id_num'][i], address_table[name_col][i], address_table[address_col][i], latitude=address_table[latitude][i], longitude=address_table[longitude][i])

        # add Point object to table and list
        address_table['known'][i] = point
        point_list.append(point)

    return address_table, point_list


# using address table, create a list of geocoded points for each service
def geocode_address_table(address_table, name_col, address_col, gc_service):
    """
    Geocode addresses in the address table and create point objects.
    :param address_table: pandas df containing string addresses
    :param name_col: name field
    :param address_col: address field
    :param gc_service: which geocoding service to use to get coordinates
    :return: updated address table, list of successful Point objects, list of failed Point objects
    """
    # list to store successful Point objects
    point_list = []

    # list to store failed Point objects
    fail_list = []

    # add column for geocoded Point objects
    address_table[gc_service] = None

    # for each row in address table
    for i, row in address_table.iterrows():

        # create a Point object
        point = Point(address_table['id_num'][i], address_table[name_col][i], address_table[address_col][i], gc_service)

        # geocode the address to get lat, lon
        point.geocode()

        # if successful geocode, add to point list and address table
        if point.latitude is not None and point.longitude is not None:
            point_list.append(point)
            address_table[gc_service][i] = point

        # if failed geocode, add to fail list
        else:
            fail_list.append(point)

        # wait 1 second between geocoding requests
        time.sleep(1)

    return address_table, point_list, fail_list


def output_geocode_results_csv(point_list, csv_path):
    """
    Output geocode results from the Point object list as a CSV.
    :param point_list: list of Point objects
    :param csv_path: path to save csv file
    :return: None
    """
    # with the file open
    with open(csv_path, 'w') as f:
        # write point info to file
        f.write('id_num,name,address,gc_service,latitude,longitude\n')
        for point in point_list:
            f.write('{},{},{},{},{},{}\n'.format(point.id_num, point.name, point.address, point.gc_service, point.latitude, point.longitude))


def output_geocode_results_shp(point_list, shp_path):
    """
    Output geocode results from the Point object list as a shapefile.
    :param point_list: list of Point objects
    :param shp_path: path to save shapefile
    :return: None
    """
    # create shapefile using given lat/lon coordinates
    # driver
    driver = ogr.GetDriverByName('ESRI Shapefile')

    # check if path exists and delete
    if os.path.exists(shp_path):
        driver.DeleteDataSource(shp_path)

    # create new data source
    ds = driver.CreateDataSource(shp_path)

    # create spatial reference object, WGS84 EPSG=4326
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)

    # get layer name from shp_path
    name = shp_path.split('/')[-1:][0].replace('.shp', '')

    # create layer
    layer = ds.CreateLayer(name, srs=srs, geom_type=ogr.wkbPoint)

    # field definition objects
    fd1 = ogr.FieldDefn('id_num', ogr.OFTInteger)
    fd2 = ogr.FieldDefn('name', ogr.OFTString)
    fd3 = ogr.FieldDefn('address', ogr.OFTString)
    fd4 = ogr.FieldDefn('latitude', ogr.OFTReal)
    fd5 = ogr.FieldDefn('longitude', ogr.OFTReal)

    # add fields to layer
    layer.CreateField(fd1)
    layer.CreateField(fd2)
    layer.CreateField(fd3)
    layer.CreateField(fd4)
    layer.CreateField(fd5)

    # create feature definition object
    feature_defn = layer.GetLayerDefn()

    # populate features
    # iterate through points in list
    for p in point_list:
        # create new feature object
        feature = ogr.Feature(feature_defn)

        # geometry
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(p.longitude, p.latitude)
        feature.SetGeometry(point)

        # fields
        feature.SetField('id_num', p.id_num)
        feature.SetField('name', p.name)
        feature.SetField('address', p.address)
        feature.SetField('latitude', p.latitude)
        feature.SetField('longitude', p.longitude)

        # add feature to layer
        layer.CreateFeature(feature)

        # destroy feature
        feature.Destroy()

    # sync changes to disk
    ds.SyncToDisk()

    # destroy objects when done
    ds.Destroy()


# create distance comparison tables
def create_distance_table(address_table, csv_out):
    """
    Calculate distance between geocoded points and known coords, then save as CSV.
    :param address_table: address table containing geocoded and known Point objects
    :param csv_out: path to save distance table as CSV
    :return: distance table
    """
    # list of geocoding services used
    services = []

    # add services to list if present in address table
    if 'nominatim' in address_table.columns:
        services.append('Nominatim')
    if 'google' in address_table.columns:
        services.append('Google')
    if 'arcgis' in address_table.columns:
        services.append('ArcGIS')
    if 'bing' in address_table.columns:
        services.append('Bing')

    # for each service
    for service in services:

        # add column to table
        col_name = service
        address_table[col_name] = None

        # calculate distances
        for i, row in address_table.iterrows():
            try:
                address_table[col_name][i] = address_table['known'][i].calc_distance_feet(address_table[service.lower()][i])
            except Exception as e:
                print('Exception: {}'.format(e))

    # delete Point object columns
    for service in services:
        del address_table[service.lower()]
    del address_table['known']

    # output distance table as csv
    address_table.to_csv(csv_out, index=False)

    # return distance table
    return address_table


# calculate statistics for distance tables
def calc_distance_statistics(distance_table, csv_out):
    """
    Calculate distance statistics (mean, max, std dev, percent matched) and output table as CSV.
    :param distance_table: pandas df with distances between geocode results and known coords
    :param csv_out: path to save statistics table as CSV.
    :return: statistics tables
    """
    # get column names containing distances
    cols = list(distance_table.columns)
    cols.remove('name')
    cols.remove('address')
    cols.remove('id_num')
    cols.remove('latitude')
    cols.remove('longitude')

    # create empty statistics dataframe
    table = pd.DataFrame(columns={'comparison', 'percent_match', 'mean_distance', 'std_dev', 'max_distance'})

    # add a row to the statistics table for each geocoding service
    for col in cols:
        success = distance_table[col].count()/distance_table['id_num'].count()*100
        new_row = {'comparison': col, 'percent_match': success, 'mean_distance': distance_table[col].mean(), 'max_distance': distance_table[col].max(), 'std_dev': distance_table[col].std()} #, 'max_dist_id': max_id}

        table = table.append(new_row, ignore_index=True)

    # save statistics table
    table.to_csv(csv_out, index=False)

    return table


# plot distances between results by different services
def plot_result_distances(distance_table, plot_out=None):
    """
    Visualize geocoding results as a box plot
    :param distance_table: pandas df containing all distance calculations
    :param plot_out: path to save box plot
    :return: None
    """
    # Draw Box Plot
    # https://www.machinelearningplus.com/plots/top-50-matplotlib-visualizations-the-master-plots-python/
    # get column names containing distances
    cols = list(distance_table.columns)
    cols.remove('name')
    cols.remove('address')
    cols.remove('id_num')
    cols.remove('latitude')
    cols.remove('longitude')

    # create new table with all distances in one column rather than a column for each service
    table = pd.DataFrame(columns={'id_num', 'Geocoding Service', 'Distance (Feet)'})

    # add a new row containing each distance and its associated service
    for col in cols:
        for i, row in distance_table.iterrows():
            if pd.isna(distance_table[col][i]) is False:
                new_row = {'id_num': distance_table['id_num'][i], 'Geocoding Service': col, 'Distance (Feet)': distance_table[col][i]}
                table = table.append(new_row, ignore_index=True)

    # set up box plot
    plt.figure(figsize=(13, 10), dpi=80)

    sns.boxplot(x='Geocoding Service', y='Distance (Feet)', data=table, palette=['darkorange', 'lawngreen', 'red', 'deepskyblue'], notch=False)

    # Decoration
    plt.title('Distance Between Geocoded Results and Known Locations (Feet)', fontsize=14)
    plt.ylim(0, 1010)
    # plt.show()

    # save box plot
    if plot_out is not None:
        plt.savefig(plot_out)

    return None


# map geocoded results
def map_geocoding_results(map_out, color, icon, *args):
    """
    Save a html map of points
    :param map_out: path to save map html file
    :param color: list containing colors for each point layer in *args
    :param icon: list containing icon symbols for each point layer in *args
    :param args: each arg is a shapefile to be added as a point layer to be added to the map
    :return: None
    """
    # counter for color and icon symbology lists
    num = 0

    # create map object
    mapobj = folium.Map(location=(32.81, -117.05), zoom_start=13)

    # for each shapefile
    for arg in args:
        # create geodataframe
        gdf = gpd.read_file(arg)

        # add each row of geodatframe to map
        for i, row in gdf.iterrows():
            # popup
            label = gdf.name[i]
            # add point to map
            mapobj.add_child(folium.Marker(location=(gdf.latitude[i], gdf.longitude[i]), popup=label, icon=folium.Icon(color=color[num], icon=icon[num])))

        # increment num for color and icon symbology lists
        num += 1

    # save map
    mapobj.save(map_out)


# bubble map
def create_bubble_map(shp_in, distance_table, bubble_size_parameter, color, map_out):
    """
    Save a map showing geocoded locations at the known coordinates, with point size determined by distance to geocoded result.
    :param shp_in: shapefile with given coordinates
    :param distance_table: distance table with distances from geocoded result to given coordinates
    :param bubble_size_parameter: name of geocoder to use as size parameter (gdf column name)
    :param color: point color
    :param map_out: path for saving map as a .html file
    :return: None
    """
    # read shapefile
    gdf = gpd.read_file(shp_in)
    # merge distance table to shapefile
    gdf = gdf.merge(distance_table, on='id_num')
    # create column that flags null distances (geocode fails)
    gdf['null_flag'] = gdf[bubble_size_parameter].isnull()

    # create map object
    mapobj = folium.Map(location=(32.81, -117.05), zoom_start=13)

    # add markers to the map
    for i, row in gdf.iterrows():
        # black marker for null distance (geocode failed)
        if gdf['null_flag'][i]:
            folium.Circle(
                location=[gdf.latitude_x[i], gdf.longitude_x[i]],
                popup=gdf.name_x[i],
                radius=250,
                color='black',
                fill=True,
                fill_color='black'
            ).add_to(mapobj)
        # if geocode successful, graduated point with distance to known location determining radius
        else:
            folium.Circle(
                location=[gdf.latitude_x[i], gdf.longitude_x[i]],
                popup=gdf.name_x[i],
                radius=gdf[bubble_size_parameter][i],
                color=color,
                fill=True,
                fill_color=color
            ).add_to(mapobj)

        # save map
        mapobj.save(map_out)
