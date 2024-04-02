import os
import argparse
from osgeo import gdal, ogr, osr
from shapely.wkt import loads
import geopandas as gpd
import numpy as np


def load_aoi(aoi_file):
    """
    Loads an Area of Interest (AOI) from a file.

    :param aoi_file: The path to the AOI file.
    :return: A GeoDataFrame containing the AOI.
    """
    return gpd.read_file(aoi_file)


def get_intersecting_rasters(raster_folder, aoi):
    """
    Gets the rasters in a folder that intersect with an AOI.

    :param raster_folder: The path to the folder containing the rasters.
    :param aoi: The AOI to check for intersection.
    :return: A list of raster files that intersect with the AOI.
    """
    raster_files = os.listdir(raster_folder)
    intersecting_rasters = []

    for raster_file in raster_files:
        if not raster_file.endswith('.tif'):
            continue

        raster_path = os.path.join(raster_folder, raster_file)
        raster_ds = gdal.Open(raster_path)
        if raster_ds is None:
            print(f"Failed to open {raster_file}. Skipping...")
            continue

        raster_srs = osr.SpatialReference()
        raster_srs.ImportFromWkt(raster_ds.GetProjection())
        aoi = aoi.to_crs(raster_srs.ExportToProj4())

        raster_extent = raster_ds.GetGeoTransform()
        raster_extent = (raster_extent[0], raster_extent[0] + raster_ds.RasterXSize * raster_extent[1],
                         raster_extent[3] + raster_ds.RasterYSize * raster_extent[5], raster_extent[3])

        ogr_geometry = ogr.CreateGeometryFromWkt(f'POLYGON(({raster_extent[0]} {raster_extent[2]}, {raster_extent[1]} {raster_extent[2]}, {raster_extent[1]} {raster_extent[3]}, {raster_extent[0]} {raster_extent[3]}, {raster_extent[0]} {raster_extent[2]}))')
        shapely_geometry = loads(ogr_geometry.ExportToWkt())
        if aoi.geometry.intersects(shapely_geometry).any():
            intersecting_rasters.append(raster_file)

    return intersecting_rasters


def extract_values_and_create_new_raster(raster_folder, output_folder, intersecting_rasters, specific_values):
    """
    Extracts specific values from intersecting rasters and creates new rasters with those values.

    :param raster_folder: The path to the folder containing the rasters.
    :param output_folder: The path to the folder to save the new rasters in.
    :param intersecting_rasters: A list of raster files that intersect with the AOI.
    :param specific_values: The values to extract from the rasters.
    """
    for raster_file in intersecting_rasters:
        raster_path = os.path.join(raster_folder, raster_file)
        output_raster_path = os.path.join(output_folder, f"{raster_file[:-4]}_extracted.tif")  # Output file name

        # Open raster dataset
        raster_ds = gdal.Open(raster_path)
        raster_array = raster_ds.ReadAsArray()

        # Specify values to extract
        specific_values = [2]

        # Create an array to hold extracted values
        extracted_array = np.zeros_like(raster_array, dtype=np.float32)
        extracted_array.fill(raster_ds.GetRasterBand(1).GetNoDataValue())  # Fill with nodata initially

        # Extract specified values
        for value in specific_values:
            extracted_array[np.where(raster_array == value)] = value

        # Create new raster file
        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(output_raster_path, raster_ds.RasterXSize, raster_ds.RasterYSize, 1, gdal.GDT_Float32)

        # Set the geotransform
        out_ds.SetGeoTransform(raster_ds.GetGeoTransform())

        # Set the projection
        out_ds.SetProjection(raster_ds.GetProjection())

        # Write the data to the raster
        out_band = out_ds.GetRasterBand(1)
        out_band.WriteArray(extracted_array)

        # Flush data to disk
        out_band.FlushCache()

        # Set the NoData value
        out_band.SetNoDataValue(raster_ds.GetRasterBand(1).GetNoDataValue())

        # Georeference the image
        out_ds.SetGeoTransform(raster_ds.GetGeoTransform())

        # Write metadata
        out_ds.SetMetadata(raster_ds.GetMetadata())

        # Close the datasets
        raster_ds = None
        out_ds = None


def main(**args):
    """
    Main function to load an AOI, get intersecting rasters, and extract specific values from those rasters.

    :param args: A dictionary of arguments, including 'aoi_file', 'raster_folder', 'output_folder', and 'specific_values'.
    """
    aoi = load_aoi(args['aoi_file'])
    intersecting_rasters = get_intersecting_rasters(args['raster_folder'], aoi)
    print(f"Intersecting rasters: {intersecting_rasters}")

    extract_values_and_create_new_raster(args['raster_folder'], args['output_folder'], intersecting_rasters, args['specific_values'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('aoi_file', metavar='aoi_file', type=str, help='aoi input, either shp or gpkg')
    parser.add_argument('raster_folder', metavar='raster_folder', type=str, help='input raster folder from sentinel2 data as path')
    parser.add_argument('output_folder', metavar='output_folder', type=str, help='where to dump data')
    parser.add_argument('--specific_values', metavar='specific_values', type=int, nargs='+', default=[2], help='values to extract from raster')

    args = parser.parse_args()
    main(**vars(args))
