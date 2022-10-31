# extHerePy
Extension for HerePy [Herepy](https://github.com/abdullahselek/HerePy)

# Modules 
## extHerePy
### extGeocoderApi
Gets geographic coordinates of a specific place

### extRmeApi
Given a gpx file containing latitude and lonigitude coordinates, altitude and timestamp the API quesries [HERE.com SDK](https://www.here.comy) for spans information and metadata based on the selected tyles.
### extRoutingApi
Given route waypoints a route is computed and relevant information are returned like: 
- Spans
- Latitude 
- Longitude 
- Timestamp
- Length
- Traffic Speed 
- Speed Limit
- Max speed  

Additional or derived information are computed 

### extUtils
Utilities module containing function for data conversion and plotting

# Examples 
test_ext_rme_api.py: testing script for extRmeApi
test_ext_routing_api.py: testing script for extRoutingApi


