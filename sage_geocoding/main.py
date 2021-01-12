# The Sage Project
# Jessica Embury

# import statements
import os
import pandas as pd

from utility import create_address_table, \
    create_points_known_coords, \
    geocode_address_table, \
    output_geocode_results_shp, \
    output_geocode_results_csv, \
    create_distance_table, \
    calc_distance_statistics, \
    plot_result_distances, \
    map_geocoding_results, \
    create_bubble_map

# create output directories
output_path = './output/central'
if not os.path.exists(output_path):
    os.makedirs(output_path)

shp_path = './output/central/shapefiles'
if not os.path.exists(shp_path):
    os.makedirs(shp_path)


########
# MAIN #
########

def main():

    # csv file with addresses
    csv_in = './data/central_database.csv'

    # base file paths for output
    csv_out = './output/central/{}_results.csv'
    csv_out2 = './output/central/{}_fails.csv'
    shp_out = './output/central/shapefiles/{}_points.shp'

    # distance table out
    dist_out = './output/central/distance_table.csv'

    # stats table out
    stats_out = './output/central/distance_statistics.csv'

    # box plot out
    plot_out = './output/central/boxplot_7k.png'
    plot_out2 = './output/central/boxplot_100k.png'

    # maps out
    map_out = './output/central/{}_map.html'

    # available geocoding services
    gc_services = ['nominatim', 'google', 'arcgis', 'bing']

    # create the address table with unique id numbers for each address (id will stay same for all geocoders)
    addr = create_address_table(csv_in)

    # create known Point objects
    addr, known_pts = create_points_known_coords(addr, 'Name ', 'Address', 'Latitude', 'Longitude')

    # output known Point objects
    output_geocode_results_csv(known_pts, csv_out.format('known'))
    output_geocode_results_shp(known_pts, shp_out.format('known'))

    # geocode list using each service and output results
    for service in gc_services:
        addr, point_list, fails_list = geocode_address_table(addr, 'Name ', 'Address', service)

        # output geocoding results (and fails) as csv files
        output_geocode_results_csv(point_list, csv_out.format(service))
        output_geocode_results_csv(fails_list, csv_out2.format(service))

        # output geocoding results as shapefiles
        output_geocode_results_shp(point_list, shp_out.format(service))

    # create distance table
    dist = create_distance_table(addr, dist_out)

    # dist = pd.read_csv('./output/central/distance_table.csv')

    # calculate distance statistics
    calc_distance_statistics(dist, stats_out)

    # create box plot
    plot_result_distances(dist, plot_out)

    # create maps comparing known coordinates versus geocoded results: nom, goog, arc, bing
    map_geocoding_results(map_out.format(gc_services[0]), ['orange', 'darkpurple'], ['cloud', 'star'], shp_out.format(gc_services[0]), shp_out.format('known'))
    map_geocoding_results(map_out.format(gc_services[1]), ['green', 'darkpurple'], ['flash', 'star'], shp_out.format(gc_services[0]), shp_out.format('known'))
    map_geocoding_results(map_out.format(gc_services[2]), ['red', 'darkpurple'], ['globe', 'star'], shp_out.format(gc_services[1]), shp_out.format('known'))
    map_geocoding_results(map_out.format(gc_services[3]), ['blue', 'darkpurple'], ['paperclip', 'star'], shp_out.format(gc_services[2]), shp_out.format('known'))
    

    # graduated point size using distance from known coord to geocoded coord
    create_bubble_map(shp_out.format('known'), dist, 'Nominatim', 'orange', map_out.format('nominatim_bubble'))
    create_bubble_map(shp_out.format('known'), dist, 'Google', 'green', map_out.format('google_bubble'))
    create_bubble_map(shp_out.format('known'), dist, 'ArcGIS', 'red', map_out.format('arcgis_bubble'))
    create_bubble_map(shp_out.format('known'), dist, 'Bing', 'blue', map_out.format('bing_bubble'))
    

if __name__ == '__main__':
    main()
