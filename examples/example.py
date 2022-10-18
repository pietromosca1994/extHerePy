import os
import sys
PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    "../", PROJECT_PATH,"extherepy"
)
sys.path.append(SOURCE_PATH)
from extherepy.ext_geocoder_api import extGeocoderApi
