from herepy import GeocoderApi

class extGeocoderApi(GeocoderApi):
    '''
    An extension of GeocoderApi from HerePy.
    Find the original HerePy at https://github.com/abdullahselek/HerePy
    '''

    def __init__(self, api_key: str = None, timeout: int = None):
        """Returns a RoutingApi instance.
        
        :param str api_key: HERE Api Key
        :param int timeout: Timeout limit for requests
        """

        super(extGeocoderApi, self).__init__(api_key, timeout)

    def getCoordinates(self, 
                        place: str) -> tuple:
        '''This method returns a latitude/longitude touple

        :param string place: place 

        :returns: coordinates: geographical coordinates of the place (latitude, longitude)

        :rtype: tuple 
        '''
        geocoder_response=self.free_form(searchtext=place)
        geocoder_response_dict=geocoder_response.as_dict()
        latitude=geocoder_response_dict['items'][0]['position']['lat']
        longitude=geocoder_response_dict['items'][0]['position']['lng']

        coordinates=(latitude, longitude)
        return coordinates
