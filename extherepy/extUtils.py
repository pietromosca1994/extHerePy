from herepy.utils import Utils
import numpy as np
import folium
from branca import colormap as cm
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# colormap list
list_colors = [
    "#00FF00",
    "#12FF00",
    "#24FF00",
    "#35FF00",
    "#47FF00",
    "#58FF00",
    "#6AFF00",
    "#7CFF00",
    "#8DFF00",
    "#9FFF00",
    "#B0FF00",
    "#C2FF00",
    "#D4FF00",
    "#E5FF00",
    "#F7FF00",
    "#FFF600",
    "#FFE400",
    "#FFD300",
    "#FFC100",
    "#FFAF00",
    "#FF9E00",
    "#FF8C00",
    "#FF7B00",
    "#FF6900",
    "#FF5700",
    "#FF4600",
    "#FF3400",
    "#FF2300",
    "#FF1100",
    "#FF0000",
]
list_colors.reverse()

def mps2kmph(mps: np.array) -> np.array:
    '''This method converts speed from m/s to km/h

    :param np.array mps: speed in m/s

    :returns: speed in km/h

    :rtype: np.array
    '''           
    return mps*3.6


def kmph2mps(kmph: np.array) -> np.array:
    '''This method converts speed from km/h to m/s

    :param np.array kmph: speed in m/s

    :returns: speed in m/s

    :rtype: np.array
    '''  
    return kmph/3.6

def getPolylineMap(route_profile_df: pd.DataFrame, 
                    channel: str,
                    channel_min: float = None,
                    channel_max: float = None) -> folium.Map:

    '''This method create a geographic plot

    :param pandas.Dataframe route_profile_df: route profile information
    :param string channel: channel to be plotted

    :returns: map

    :rtype: folium.Map
    '''  

    # get folium map 
    north=  route_profile_df['latitude[deg]'].max()
    south=  route_profile_df['latitude[deg]'].min()
    east=   route_profile_df['longitude[deg]'].min()
    west=   route_profile_df['longitude[deg]'].max()

    m = folium.Map(location=tuple([north, east]))
    m.fit_bounds([[south, west], [north, east]])
    x_y_coordinates = route_profile_df[['latitude[deg]', 'longitude[deg]']]
    polyline = [tuple(x) for x in x_y_coordinates.to_numpy()]

    # create colormap
    if (channel_max==None):
        channel_max=route_profile_df[channel].max()
    
    if (channel_min==None):
        channel_min=route_profile_df[channel].min()

    colormap=cm.LinearColormap(colors=list_colors,
                               index=np.linspace(int(channel_min), int(channel_max), len(list_colors)),
                               vmin=channel_min,
                               vmax=channel_max)
    m.add_child(colormap)

    folium.ColorLine(positions=polyline,
                        colors=route_profile_df[channel],
                        colormap=colormap,
                        weight=10,
                        opacity=0.8).add_to(m)
    return m

def m2km(m: np.array) -> np.array:
    return m/1000

def plotSegmentsvsTime(route_profile_df: pd.DataFrame, 
                channel: str):
    plt.figure(figsize=(30,5))
    plt.bar(x=route_profile_df['time_i[s]'], 
            height=route_profile_df[channel], 
            width=route_profile_df['delta_time[s]'],
            align='edge')
    plt.xlabel('Time [s]')
    plt.ylabel(channel)
    plt.xticks(route_profile_df['time_i[s]'])
    return plt

def plotSegmentsvsDistance(route_profile_df: pd.DataFrame, 
                channel: str):
    plt.figure(figsize=(30,5))
    plt.bar(x=m2km(route_profile_df['distance_i[m]'].values), 
            height=route_profile_df[channel], 
            width=m2km(route_profile_df['delta_distance[m]'].values),
            align='edge')
    plt.xlabel('Distance [km]')
    plt.ylabel(channel)
    plt.xticks(m2km(route_profile_df['distance_i[m]'].values))
    return plt
    