#!/usr/bin/env python

from herepy import RoutingApi
import pandas as pd 
from datetime import datetime
import flexpolyline
from typing import List, Dict, Union, Optional, Tuple
from geopy import distance
import numpy as np
import extUtils 

class extRoutingApi(RoutingApi):
    '''
    An extension of RoutingApi from HerePy.
    Find the original HerePy at https://github.com/abdullahselek/HerePy
    '''
    def __init__(self, api_key: str = None, timeout: int = None):
        """Returns a RoutingApi instance.
        
        :param str api_key: HERE Api Key
        :param int timeout: Timeout limit for requests
        """
        super(extRoutingApi, self).__init__(api_key, timeout)

    def getRouteReport(self,
                        waypoints: List[tuple], 
                        departure_time: datetime =datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), 
                        return_polyline: bool =False) -> pd.DataFrame:
        '''This method returns a route report

        :param List[Tuple(float)] waypoints: route waypoints
        :param datetime departure_time: time of departure
        :param bool return_polyline: return polyline 

        :returns: route_profile_df: Route Profile Info

        :rtype: pandas.DataFrame 
        '''

        # input parsing
        # define origin and destination
        origin=waypoints[0]
        destination=waypoints[-1]
        # in case waypoints is more than two intermidiate routes are computed
        if len(waypoints)>2:
            via=waypoints[1:-1]
        else:
            via=None

        routing_response=self.route_v8(transport_mode='car', 
                                                origin=origin, 
                                                destination=destination,
                                                via=via,
                                                departure_time=departure_time,
                                                return_fields=['polyline', 'elevation'],
                                                span_fields=['speedLimit',
                                                                'maxSpeed',
                                                                'dynamicSpeedInfo',
                                                                'segmentId',
                                                                'segmentRef',
                                                                'routeNumbers',
                                                                'length',
                                                                'duration',
                                                                'baseDuration',
                                                                'names',
                                                                'countryCode',
                                                                'functionalClass',
                                                                'streetAttributes'])
        
        # extract data from the API response
        # convert response to dict
        routing_response_dict = routing_response.as_dict()
        
        route_profile = []
        for route in range(len(routing_response_dict['routes'])):
            route_data = routing_response_dict['routes'][route]  # loop through routes
            for section in range(len(routing_response_dict['routes'][route]['sections'])):  # loop through sections
                section_data = route_data['sections'][section]
                departure_time=section_data['departure']['time']
                polyline = section_data['polyline']
                polyline_decoded = flexpolyline.decode(polyline)  # decode polyline
                offsets = [section_data['spans'][span]['offset'] for span in range(len(section_data['spans']))]
                for polyline_element in range(len(polyline_decoded)):  # loop through polyline elements
                    span = sum((offset <= polyline_element for offset in offsets)) - 1  # get the span
                    span_data = section_data['spans'][span]

                    # treat missing data
                    if 'speedLimit' in span_data.keys():
                        speedLimit = span_data['speedLimit']
                    else:
                        speedLimit = 0

                    if 'names' in span_data.keys():
                        place = span_data['names'][0]['value']
                    else:
                        place = ''

                    if 'maxSpeed' in span_data.keys():
                        maxSpeed = span_data['maxSpeed']
                    else:
                        maxSpeed = 0
                    
                    latitude=polyline_decoded[polyline_element][0]
                    longitude=polyline_decoded[polyline_element][1]
                    altitude=polyline_decoded[polyline_element][2]

                    #try:
                    #    weather_response=destination_weather_api.weather_for_coordinates(latitude, longitude, product=WeatherProductType.observation)
                    #    weather_rensponse_dict=weather_response.as_dict()
                    #    amb_temperature=float(weather_rensponse_dict['observations']['location'][0]['observation'][0]['temperature'])
                    #    amb_humidity=float(weather_rensponse_dict['observations']['location'][0]['observation'][0]['humidity'])
                    #except:
                    #    amb_temperature=float('nan')
                    #    amb_humidity=float('nan')

                    route_profile.append({'route':                  route,
                                        'section':                  section,
                                        'span':                     span+section*1000,        # give unique span ID with section*1000
                                        'latitude[deg]':            latitude,
                                        'longitude[deg]':           longitude,
                                        'altitude[m]':              altitude,
                                        'place':                    place,
                                        'countrycode':              span_data['countryCode'],
                                        'functionalClass':          span_data['functionalClass'],
                                        'length[m]':                span_data['length'],
                                        'duration[s]':              span_data['duration'],
                                        'baseDuration[s]':          span_data['baseDuration'],
                                        #'speedLimit[m/s]':          speedLimit,
                                        #'maxSpeed[m/s]':            maxSpeed,
                                        #'trafficSpeed[m/s]':        span_data['dynamicSpeedInfo']['trafficSpeed'],
                                        #'baseSpeed[m/s]':           span_data['dynamicSpeedInfo']['baseSpeed'],
                                        'speedLimit[km/h]':          np.round(extUtils.mps2kmph(np.array(speedLimit)), 1), 
                                        'maxSpeed[km/h]':            np.round(extUtils.mps2kmph(np.array(maxSpeed)), 1), 
                                        'trafficSpeed[km/h]':        np.round(extUtils.mps2kmph(np.array(span_data['dynamicSpeedInfo']['trafficSpeed'])), 1), 
                                        'baseSpeed[km/h]':           np.round(extUtils.mps2kmph(np.array(span_data['dynamicSpeedInfo']['baseSpeed'])), 1), 
                                        #'ambTemperature[degC]':     amb_temperature,
                                        #'ambHumidity[Perc]':        amb_humidity
                                        })
            route_profile_df = pd.DataFrame(route_profile)  # make pandas dataframe

        # in case the full polyline is not desired remove duplicates 
        if return_polyline==False:
            route_profile_df=route_profile_df.drop_duplicates(subset='span', keep='first')
            delta_distance=route_profile_df['length[m]'].tolist()
        else:
            waypoints = list(route_profile_df[['latitude[deg]', 'longitude[deg]']].to_records(index=False))
            delta_distance = [distance.geodesic(waypoints[i], waypoints[i + 1]).m for i in
                              range(0, len(waypoints) - 1)]  # compute geodesic distance based on geographic coordinates
            delta_distance.append(0)

        # compute derived information
        # compute distance
        delta_distance=np.round(delta_distance, 1).tolist() # round to 0.1 meter precision
        distance_f = np.cumsum(delta_distance)
        distance_i = np.insert(distance_f[:-1], 0, 0)

        # compute time based on traffic speed
        delta_time = np.round(delta_distance / extUtils.kmph2mps(route_profile_df['trafficSpeed[km/h]'].values), 2)
        time_f = np.cumsum(delta_time)
        time_i = np.insert(time_f[:-1], 0, 0)
        timestamp=[pd.Timestamp(departure_time)+pd.Timedelta(time_i[i], 'sec') for i in range(len(time_i))]

        # compute altitude
        delta_altitude = -route_profile_df['altitude[m]'].diff(periods=-1).fillna(0).values
        altitude_i = route_profile_df['altitude[m]'].values
        altitude_f = altitude_i + delta_altitude

        route_profile_df['distance_i[m]'] = distance_i
        route_profile_df['distance_f[m]'] = distance_f
        route_profile_df['delta_distance[m]'] = delta_distance

        route_profile_df['time_i[s]'] = time_i
        route_profile_df['time_f[s]'] = time_f
        route_profile_df['delta_time[s]'] = delta_time
        route_profile_df['timestamp']=timestamp

        route_profile_df['altitude_i[m]'] = altitude_i
        route_profile_df['altitude_f[m]'] = altitude_f
        route_profile_df['delta_altitude[m]'] = delta_altitude

        return route_profile_df 


