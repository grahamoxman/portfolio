import rasterio
import geopandas as gpd
import os
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from rasterio.features import geometry_mask
from rasterio.features import shapes
from shapely.geometry import shape
import pandas as pd
import argparse


def read_aoi(inshp):
    """
    Reads an Area of Interest (AOI) from a shapefile.

    :param inshp: The path to the shapefile.
    :return: A GeoDataFrame containing the AOI.
    """
    aoi = gpd.read_file(inshp)
    return aoi


def merge_shapefiles(output_dir):
    """
    Merges all shapefiles in a directory into a single shapefile.

    :param output_dir: The directory containing the shapefiles.
    """
    shapefiles = [os.path.join(output_dir, filename) for filename in os.listdir(output_dir) if filename.endswith('.shp')]
    gdfs = [gpd.read_file(shp) for shp in shapefiles]
    merged_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
    merged_gdf.to_file(os.path.join(output_dir, 'merged.shp'))


def raster_to_polygons(raster_path, output_dir):
    """
    Converts a raster to polygons and saves the polygons to a new shapefile.

    :param raster_path: The path to the raster.
    :param output_dir: The directory to save the new shapefile in.
    :return: The path to the new shapefile.
    """
    # Convert the raster to polygons
    with rasterio.open(raster_path) as src:
        image = src.read(1)  # assumes a single band
        results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) 
            in enumerate(shapes(image, mask=image==2, transform=src.transform)))  # only consider pixels with value 2

    geoms = list(results)
    if not geoms:
        print(f"No geometries found in {raster_path}. Skipping polygon conversion.")
        return

    gdf = gpd.GeoDataFrame.from_features(geoms)
    gdf.crs = src.crs

    # Save polygons to a new shapefile
    filename = os.path.basename(raster_path)
    polygon_path = os.path.join(output_dir, filename.replace('.tif', '_polygons.shp'))
    gdf.to_file(polygon_path)

    return polygon_path


def reproject_raster_to_match_aoi(raster_path, aoi_crs, output_dir):
    """
    Reprojects a raster to match the coordinate reference system (CRS) of an AOI.

    :param raster_path: The path to the raster.
    :param aoi_crs: The CRS of the AOI.
    :param output_dir: The directory to save the reprojected raster in.
    :return: The path to the reprojected raster.
    """
    with rasterio.open(raster_path) as src:
        transform, width, height = calculate_default_transform(src.crs, aoi_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': aoi_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        filename = os.path.basename(raster_path)
        reprojected_raster_path = os.path.join(output_dir, filename.replace('.tif', '_reprojected.tif'))

        with rasterio.open(reprojected_raster_path, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=aoi_crs,
                    resampling=Resampling.nearest)

    return reprojected_raster_path


def mask_raster_with_aoi(raster_path, aoi, output_dir):
    """
    Masks a raster with an AOI and saves the masked raster to a new file.

    :param raster_path: The path to the raster.
    :param aoi: The AOI to mask the raster with.
    :param output_dir: The directory to save the masked raster in.
    :return: The path to the masked raster.
    """
    with rasterio.open(raster_path) as src:
        out_image, out_transform = mask(src, [aoi.geometry.unary_union.__geo_interface__], crop=True)
        out_meta = src.meta.copy()

    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

    filename = os.path.basename(raster_path)
    masked_raster_path = os.path.join(output_dir, filename.replace('.tif', '_masked.tif'))

    with rasterio.open(masked_raster_path, "w", **out_meta) as dest:
        dest.write(out_image)

    return masked_raster_path


def main(dirpath, inshp, output_dir):
    """
    Main function to read an AOI, reproject and mask rasters to match the AOI, convert the masked rasters to polygons, 
    and merge all resulting shapefiles.

    :param dirpath: The directory containing the rasters.
    :param inshp: The path to the AOI shapefile.
    :param output_dir: The directory to save the output files in.
    """
    aoi = read_aoi(inshp)
    aoi_crs = aoi.crs.to_string()

    for filename in os.listdir(dirpath):
        if filename.endswith('.tif'):
            raster_path = os.path.join(dirpath, filename)
            reprojected_raster_path = reproject_raster_to_match_aoi(raster_path, aoi_crs, output_dir)

            try:
                masked_raster_path = mask_raster_with_aoi(reprojected_raster_path, aoi, output_dir)
                polygon_path = raster_to_polygons(masked_raster_path, output_dir)
            except ValueError as e:
                if 'Input shapes do not overlap raster.' in str(e):
                    print(f"No overlap between {filename} and the AOI. Skipping masking process.")
                else:
                    raise e

    print('Export of intersected files complete')
    merge_shapefiles(output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to process rasters.")
    parser.add_argument('dirpath', metavar='dirpath', type=str, help='The directory containing the rasters.')
    parser.add_argument('inshp', metavar='inshp', type=str, help='The path to the AOI shapefile.')
    parser.add_argument('output_dir', metavar='output_dir', type=str, help='The directory to save the output files in.')
    args = parser.parse_args()

    main(args.dirpath, args.inshp, args.output_dir)
