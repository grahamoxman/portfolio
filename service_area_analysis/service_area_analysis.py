import openrouteservice
import geopandas as gpd
import pandas as pd
import json
from shapely.geometry import LineString
import argparse

"""
This script performs a service area analysis using the OpenRouteService API.
It reads in a CSV file of points, creates isochrones around each point, and saves the results as a GeoPackage.
"""


with open("creds.txt", 'r') as file:
    api_key = file.readline().strip()

client = openrouteservice.Client(key=api_key)


def chunks(lst, n):
    """
    Yield successive n-sized chunks from lst.

    Parameters:
    lst (list): The list to be divided into chunks.
    n (int): The size of each chunk.

    Returns:
    generator: A generator that yields list chunks.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def input_csv(csv):
    """
    Reads a CSV file into a GeoDataFrame.

    Parameters:
    csv (str): The path to the CSV file.

    Returns:
    GeoDataFrame: A GeoDataFrame containing the data from the CSV file.
    """
    df = pd.read_csv(csv)
    df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat))

    return df


def linestring(df):
    """
    Converts a GeoDataFrame of points into a LineString.

    Parameters:
    df (GeoDataFrame): The GeoDataFrame of points.

    Returns:
    GeoDataFrame: A GeoDataFrame containing a single LineString.
    """
    df = LineString( [[a.x, a.y] for a in df.geometry.values])
    line_df = pd.DataFrame()
    line_gdf = gpd.GeoDataFrame(line_df, geometry=[lineStringObj,])
    return line_gdf


def read_csv_to_gdf(csv_file, lon_col, lat_col):
    """
    Reads a CSV file into a GeoDataFrame.

    Parameters:
    csv_file (str): The path to the CSV file.
    lon_col (str): The name of the longitude column.
    lat_col (str): The name of the latitude column.

    Returns:
    GeoDataFrame: A GeoDataFrame containing the data from the CSV file.
    """
    df = pd.read_csv(csv_file)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]))
    return gdf


def get_isochrones(coordinates_chunks):
    """
    Makes API requests to get isochrones and processes the responses.

    Parameters:
    coordinates_chunks (list): A list of chunks of coordinates.

    Returns:
    GeoDataFrame: A GeoDataFrame containing the isochrones.
    """
    gdfs = []

    for chunk in coordinates_chunks:
        iso = client.isochrones(
            locations=chunk,
            profile='foot-walking',
            range=[900, 900],
            validate=False,
            attributes=['total_pop']
        )

        output_iso = json.loads(json.dumps(iso))
        chunk_gdf = gpd.GeoDataFrame.from_features(output_iso["features"])

        gdfs.append(chunk_gdf)

    gdf = pd.concat(gdfs, ignore_index=True)
    gdf.drop(columns=["center"], inplace=True)

    return gdf


def create_linestring_gdf(gdf):
    """
    Creates a LineString GeoDataFrame from a GeoDataFrame of points.

    Parameters:
    gdf (GeoDataFrame): The GeoDataFrame of points.

    Returns:
    GeoDataFrame: A GeoDataFrame containing a single LineString.
    """
    line_string_obj = LineString([[point.x, point.y] for point in gdf.geometry.values])
    line_df = pd.DataFrame()
    line_gdf = gpd.GeoDataFrame(line_df, geometry=[line_string_obj])
    return line_gdf

# Read the CSV files into GeoDataFrames
shapes_gdf = read_csv_to_gdf("KMRL-Open-Data\shapes.txt", "shape_pt_lon", "shape_pt_lat")
stops_gdf = read_csv_to_gdf("KMRL-Open-Data\stops.txt", "stop_lon", "stop_lat")

# Create a LineString GeoDataFrame from the shapes GeoDataFrame
line_gdf = create_linestring_gdf(shapes_gdf)

# Extract the coordinates from the stops GeoDataFrame
coordinates = stops_gdf.geometry.apply(lambda point: [point.x, point.y]).tolist()
coordinates_chunks = list(chunks(coordinates, 5))

# Get the isochrones
gdf = get_isochrones(coordinates_chunks)

# Save the results
gdf.to_file("isochrones.gpkg", driver="GPKG")