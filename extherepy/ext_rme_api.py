#!/usr/bin/env python

from herepy import RmeApi
from datetime import datetime
from extherepy import extUtils
import io
import pandas as pd
import numpy as np

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
                       return_polyline: bool =False):
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
                                    'latitude[deg]': TracePoint['lat'],
                                    'longitude[deg]': TracePoint['lon'],
                                    'latitude_matched[deg]': TracePoint['latMatched'],
                                    'longitude_matched[deg]': TracePoint['lonMatched'],
                                    'altitude[m]': TracePoint['elevation'],
                                    'confidenceValue[-]': TracePoint['confidenceValue'],
                                    'confidence[-]': RouteLink['confidence'],
                                    'functionalClass': RouteLink['functionalClass'],
                                    'vehicleSpeed[km/h]': extUtils.mps2kmph(np.round(np.array(TracePoint['speedMps']), 1)),
                                    'speedLimit[km/h]': float(RouteLink['attributes']['SPEED_LIMITS_FCN'][0]['FROM_REF_SPEED_LIMIT'])        # FROM_REF_SPEEED_LIMIT from A to B
                                                                                                                                            # TO_REF_SPEED_LIMIT from B to A
        })
        route_profile_df = pd.DataFrame(route_profile)  # make pandas dataframe

        if return_polyline==False:
            route_profile_df.drop(['tracepoint', 'latitude_matched[deg]', 'longitude_matched[deg]', 'confidenceValue[-]', 'vehicleSpeed[km/h]'], axis=1, inplace=True)
            route_profile_df=route_profile_df.drop_duplicates(subset='span', keep='first') # get only the spans 

        #waypoints = list(route_profile_df[['latitude[deg]', 'longitude[deg]']].to_records(index=False))

        return route_profile_df