# The Sage Project
# Jessica Embury

# import statements
from my_tokens import arcgis_token, bing_token, google_token

from geopy import distance
from geopy.geocoders import Nominatim
from geopy.geocoders import GoogleV3
from geopy.geocoders import Bing
import requests


# define Point class
class Point:

    # constructor
    def __init__(self, id_num, name, address, gc_service=None, latitude=None, longitude=None):
        self.id_num = id_num
        self.name = name
        self.address = address
        self.gc_service = gc_service
        self.latitude = latitude
        self.longitude = longitude

    ###########
    # METHODS #
    ###########

    # set gc_service
    def set_gc_service(self, gc=None):
        """
        Set the point's geocoding service using the gc parameter or by requesting user input.
        :param gc: geocoding service providers (nominatim, google, arcpy, bing)
        :return: None
        """
        if gc is None:
            gc = input("Select a geocoding service: 1. Nominatim/OSM, 2. Google, 3. ArcGIS/Esri, 4. Bing \nEnter 1, 2, 3 or 4. Any other entry will cancel the operation.")
        if gc is '1' or gc is 1:
            self.gc_service = 'nominatim'
        elif gc is '2' or gc is 2:
            self.gc_service = 'google'
        elif gc is '3' or gc is 3:
            self.gc_service = 'arcgis'
        elif gc is '4' or gc is 4:
            self.gc_service = 'bing'
        else:
            print("Canceled. Geocoding service has not been selected.")

        return None

    # reset gc_service to None
    def reset_gc_service(self):
        """
        Reset gc_service to None.
        :return: None
        """
        self.gc_service = None

        return None

    # geocode address to get latitude and longitude
    def geocode(self):
        """
        Geocodes the Point object's address using the geocoding service selected by gc_service, sets latitude/longitude
        :return: None
        """
        # set gc_service if None
        if self.gc_service is None:
            self.set_gc_service()

        # create geolocator instance based upon gc_service
        if self.gc_service is 'nominatim':
            geolocator = Nominatim(user_agent='sdsu_geog582_final')
        elif self.gc_service is 'google':
            geolocator = GoogleV3(google_token)
        elif self.gc_service is 'bing':
            geolocator = Bing(bing_token)

        # geocode input address, set self.latitude and self.longitude
        if self.gc_service is 'nominatim' or self.gc_service is 'google' or self.gc_service is 'bing':
            try:
                location = geolocator.geocode(self.address)

                self.latitude = location.latitude
                self.longitude = location.longitude
            # print exception if geocode not successful
            except Exception as e:
                print('Exception for {}, {}, {}: {}'.format(self.id_num, self.name, self.address, e))

        # use requests library to geocode with arcgis
        if self.gc_service is 'arcgis':
            token = arcgis_token
            addr = self.address
            try:
                url = 'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?singleLine={}&forStorage=true&token={}&f=pjson'.format(addr, token)
                r = requests.get(url)
                results = r.json()
                self.latitude = results['candidates'][0]['location']['y']
                self.longitude = results['candidates'][0]['location']['x']
            # print exception if geocode not successful
            except Exception as e:
                print('Exception for {}, {}, {}: {}'.format(self.id_num, self.name, self.address, e))

        return None

    # calculate distance between 2 points
    def calc_distance_feet(self, point2):
        """
        Calculates the distance in feet between 2 Point objects (geodesic distance, WGS84 spatial reference)
        :param point2: Point object used to calculate distance from self
        :return: distance between 2 Point objects in miles
        """
        pt1 = (self.latitude, self.longitude)
        pt2 = (point2.latitude, point2.longitude)
        dist = distance.distance(pt1, pt2).feet

        return dist
