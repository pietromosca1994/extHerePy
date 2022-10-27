#!/usr/bin/env python

from herepy import RmeApi
from datetime import datetime
from extherepy import extUtils
import io
import pandas as pd
import numpy as np
from geopy import distance

class extRmeApi(RmeApi):
    '''
    An extension of RoutingApi from HerePy.
    Find the original HerePy at https://github.com/abdullahselek/HerePy
    '''
    def __init__(self, api_key: str = None, timeout: int = None):
        """Returns a RoutingApi instance.
        
        :param str api_key: HERE Api Key
        :param int timeout: Timeout limit for requests
        """
        super(extRmeApi, self).__init__(api_key, timeout)

    def getRouteReport(self,
                       gpx_file: str,
                       return_GPS_trace: bool =False):
        """Returns a Route Match report
        
        :param str gpx_file: path to .gpx file
        :param bool return_polyline: return spans 

        :returns: route_profile_df: Route Profile Info

        :rtype: pandas.DataFrame 
        """
        with io.open(gpx_file, encoding="utf-8") as gpx_file:
                gpx_content = gpx_file.read()
        
        rme_response = self.match_route(gpx_content, pde_layers=['SPEED_LIMITS_FCn(*)'])
        rme_response_dict=rme_response.as_dict()

        route_profile=[]

        # parsing dictionary entries
        RouteLinks=rme_response_dict['RouteLinks']
        TracePoints=rme_response_dict['TracePoints']

        for id in range(len(TracePoints)):
            TracePoint=TracePoints[id]
            RouteLink=RouteLinks[TracePoint['routeLinkSeqNrMatched']]
            route_profile.append({  'span': TracePoint['routeLinkSeqNrMatched'],
                                    'routelink': TracePoint['routeLinkSeqNrMatched'], 
                                    'tracepoint': id,
                                    'timestamp': str(datetime.fromtimestamp(TracePoint['timestamp']/1000)),
                                    'GPS_latitude[deg]': TracePoint['lat'],
                                    'GPS_longitude[deg]': TracePoint['lon'],
                                    'latitude[deg]': TracePoint['latMatched'],              # matched by here
                                    'longitude[deg]': TracePoint['lonMatched'],             # matched by here
                                    'GPS_altitude[m]': TracePoint['elevation'],
                                    'confidenceValue[-]': TracePoint['confidenceValue'],
                                    'confidence[-]': RouteLink['confidence'],
                                    'functionalClass': RouteLink['functionalClass'],
                                    'GPS_vehicleSpeed[km/h]': extUtils.mps2kmph(np.round(np.array(TracePoint['speedMps']), 1)),
                                    #'speedLimit[km/h]': float(RouteLink['attributes']['SPEED_LIMITS_FCN'][0]['FROM_REF_SPEED_LIMIT'])        # FROM_REF_SPEEED_LIMIT from A to B
                                                                                                                                            # TO_REF_SPEED_LIMIT from B to A
        })
        route_profile_df = pd.DataFrame(route_profile)  # make pandas dataframe

        if return_GPS_trace==False:
            route_profile_df.drop(['tracepoint', 'GPS_latitude[deg]', 'GPS_longitude[deg]', 'confidenceValue[-]', 'GPS_vehicleSpeed[km/h]'], axis=1, inplace=True)
            route_profile_df=route_profile_df.drop_duplicates(subset='span', keep='first') # get only the spans 
            waypoints = list(route_profile_df[['latitude[deg]', 'longitude[deg]']].to_records(index=False))
        else:
            waypoints = list(route_profile_df[['GPS_latitude[deg]', 'GPS_longitude[deg]']].to_records(index=False))
        
        delta_distance=[distance.geodesic(waypoints[i], waypoints[i + 1]).m for i in
                                range(0, len(waypoints) - 1)]  # compute geodesic distance based on geographic coordinates
        delta_distance.append(0)
        route_profile_df['length[m]']=delta_distance

        # compute derived information
        # compute distance
        delta_distance=np.round(delta_distance, 1).tolist() # round to 0.1 meter precision
        distance_f = np.cumsum(delta_distance)
        distance_i = np.insert(distance_f[:-1], 0, 0)
        
        # compute time 
        timestamps=route_profile_df['timestamp'].tolist()
        delta_time = [(datetime.strptime(timestamps[i+1], '%Y-%m-%d %H:%M:%S')-datetime.strptime(timestamps[i], '%Y-%m-%d %H:%M:%S')).total_seconds()
                    for i in range(0, len(timestamps) - 1)]
        delta_time.append(0)
        time_f = np.cumsum(delta_time)
        time_i = np.insert(time_f[:-1], 0, 0)

        # compute altitude
        delta_altitude = -route_profile_df['GPS_altitude[m]'].diff(periods=-1).fillna(0).values
        altitude_i = route_profile_df['GPS_altitude[m]'].values
        altitude_f = altitude_i + delta_altitude

        # compute speed
        vehicleSpeed=np.divide(np.array(delta_distance), np.array(delta_time), where=np.array(delta_time)!=0)

        # integrate in dataframe
        route_profile_df['distance_i[m]'] = distance_i
        route_profile_df['distance_f[m]'] = distance_f
        route_profile_df['delta_distance[m]'] = delta_distance

        route_profile_df['time_i[s]'] = time_i
        route_profile_df['time_f[s]'] = time_f
        route_profile_df['delta_time[s]'] = delta_time

        route_profile_df['altitude_i[m]'] = altitude_i
        route_profile_df['altitude_f[m]'] = altitude_f
        route_profile_df['delta_altitude[m]'] = delta_altitude        

        route_profile_df['vehicleSpeed[km/h]']=extUtils.mps2kmph(np.round(vehicleSpeed, 1))

        return route_profile_df