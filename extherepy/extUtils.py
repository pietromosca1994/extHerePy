from herepy.utils import Utils
import numpy as np
import folium
from branca import colormap as cm
import pandas as pd
import matplotlib.pyplot as plt
import os
import gpxpy.gpx 

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
                    latitude_channel: str = 'latitude[deg]',
                    longitude_channel: str = 'longitude[deg]',
                    channel: str = None,
                    channel_min: float = None,
                    channel_max: float = None) -> folium.Map:

    '''This method create a geographic plot

    :param pandas.Dataframe route_profile_df: route profile information
    :param string channel: channel to be plotted

    :returns: map

    :rtype: folium.Map
    '''  

    # get folium map 
    north=  route_profile_df[latitude_channel].max()
    south=  route_profile_df[latitude_channel].min()
    east=   route_profile_df[longitude_channel].min()
    west=   route_profile_df[longitude_channel].max()

    m = folium.Map(location=tuple([north, east]))
    m.fit_bounds([[south, west], [north, east]])
    x_y_coordinates = route_profile_df[[latitude_channel, longitude_channel]]
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
    '''Methods for converting a numpy.array of m to km

    :param numpy.array m: [m]

    :returns: km: [km]

    :rtype: numpy.array
    '''  
    return m/1000

def plotSegmentsvsTime(route_profile_df: pd.DataFrame, 
                channel: str):
    '''Methods for plotting a route channel vs time

    :param pandas.DataFrame route_profile_df: route profile dataframe
    :param str: channel to plot 

    :returns: plot 

    :rtype: matplotlib.pyplot
    ''' 
    plt.figure(figsize=(30,5))
    plt.bar(x=route_profile_df['time_i[s]'], 
            height=route_profile_df[channel], 
            width=route_profile_df['delta_time[s]'],
            align='edge',
            linewidth=0.5,
            edgecolor='black')
    plt.xlabel('Time [s]')
    plt.ylabel(channel)
    plt.xticks(route_profile_df['time_i[s]'], rotation='vertical')
    return plt

def plotSegmentsvsDistance(route_profile_df: pd.DataFrame, 
                channel: str):
    '''Methods for plotting a route channel vs distance

    :param pandas.DataFrame route_profile_df: route profile dataframe
    :param str: channel to plot 

    :returns: plot 

    :rtype: matplotlib.pyplot
    '''               
    plt.figure(figsize=(30,5))
    plt.bar(x=m2km(route_profile_df['distance_i[m]'].values), 
            height=route_profile_df[channel], 
            width=m2km(route_profile_df['delta_distance[m]'].values),
            align='edge',
            linewidth=0.5,
            edgecolor='black')
    plt.xlabel('Distance [km]')
    plt.ylabel(channel)
    plt.xticks(m2km(route_profile_df['distance_i[m]'].values), rotation='vertical')
    return plt

def dataframe2gpx(input_df, lats_colname='latitude', longs_colname='longitude', times_colname=None, alts_colname=None, output_file=None):
    '''Methods for converting a dataframe in a gpx file 

    :param str lats_colname
    :param str longs_colname
    :param str times_colname
    :param str alts_colname
    :param str output_file

    :returns: None 

    :rtype: None
    '''    
    if not output_file:
        raise Exception("[ERROR] Please provide an output file")

    output_extension = os.path.splitext(output_file)[1]
    if output_extension != ".gpx":
        raise TypeError(f"[ERROR] output file must be a gpx file")

    gpx = gpxpy.gpx.GPX()

    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Create points:
    for idx in input_df.index:

        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(input_df.loc[idx, lats_colname],
                                                            input_df.loc[idx, longs_colname],
                                                            time=pd.Timestamp(input_df.loc[idx, times_colname], unit='s') if times_colname else None, # timestamp accepted is in unixtime
                                                            elevation=input_df.loc[idx, alts_colname] if alts_colname else None))

    with open(output_file, 'w') as f:
        f.write(gpx.to_xml())
    return gpx.to_xml()