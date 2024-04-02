import geopandas as gpd
import argparse
import os
import pandas as pd
import shutil

"""
This script is used for intersecting multiple shapefiles with an Area of Interest (AOI), filtering the features by attribute values, calculating the total acreage of the intersections, and generating CSV files with the results.

The script defines several functions:

- clear_directory: Deletes all files and directories in the specified directory.
- read_shapefile: Reads a shapefile into a GeoDataFrame.
- generate_csv: Generates a CSV file with the specified data.
- intersect_with_aoi: Intersects a shapefile with an AOI, filters the features by attribute value, calculates the total acreage of the intersection, and generates a CSV file with the results.
- main: Main function to intersect multiple shapefiles with an AOI, filter the features by attribute values, calculate the total acreage of the intersections, and generate CSV files with the results.

The script uses argparse to parse command line arguments for the AOI shapefile, the shapefiles to intersect with the AOI, the output folder, the attribute name to filter by, and the attribute values to filter by.

The script is executed from the command line and requires the geopandas, argparse, os, pandas, and shutil libraries.
"""


def clear_directory(directory):
    """
    Deletes all files and directories in the specified directory.

    :param directory: The directory to clear.
    """    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def read_shapefile(shp_path):
    """
    Reads a shapefile into a GeoDataFrame.

    :param shp_path: The path to the shapefile.
    :return: A GeoDataFrame containing the shapefile data.
    """
    return gpd.read_file(shp_path)


def generate_csv(output_dir, base_name, attribute_name, filter_value, total_acreage):
    # Round the total acreage to 2 decimal places
    """
    Generates a CSV file with the specified data.

    :param output_dir: The directory to save the CSV file in.
    :param base_name: The base name for the CSV file.
    :param attribute_name: The attribute name to include in the CSV file.
    :param filter_value: The filter value to include in the CSV file.
    :param total_acreage: The total acreage to include in the CSV file.
    """
    # Round the total acreage to 2 decimal places
    total_acreage = round(total_acreage, 2)

    # Create a DataFrame for the CSV output
    csv_data = pd.DataFrame({
        'Attribute Name': [attribute_name],
        'Filter Value': [filter_value],
        'Total Acreage': [total_acreage]
    })

    # Save the DataFrame to a CSV file
    csv_file_name = f"{base_name}_aoi_intersect.csv"
    csv_file = os.path.join(output_dir, csv_file_name)

    # Check if the CSV file already exists
    if os.path.exists(csv_file):
        # If it exists, append without writing the header
        csv_data.to_csv(csv_file, mode='a', header=False, index=False)
    else:
        # If it doesn't exist, write the DataFrame to a new CSV file
        csv_data.to_csv(csv_file, index=False)


def intersect_with_aoi(aoi, input_file, output_dir, attribute_name, filter_value):
    """
    Intersects a shapefile with an Area of Interest (AOI), filters the features by attribute value, 
    calculates the total acreage of the intersection, and generates a CSV file with the results.

    :param aoi: The AOI to intersect with.
    :param input_file: The shapefile to intersect with the AOI.
    :param output_dir: The directory to save the output files in.
    :param attribute_name: The attribute name to filter by.
    :param filter_value: The attribute value to filter by.
    """
    # Load the input file
    input_gdf = read_shapefile(input_file)
    print(f"Loaded input file with {len(input_gdf)} features.")

    # Filter the input file based on the attribute value
    filtered_gdf = input_gdf[input_gdf[attribute_name].str.contains(filter_value)]
    print(f"Filtered input file to {len(filtered_gdf)} features.")

    print(aoi.crs)
    # Check if the CRS of the input file matches the CRS of the AOI
    if filtered_gdf.crs != aoi.crs:
        # If not, reproject the input file to match the AOI's CRS
        filtered_gdf = filtered_gdf.to_crs(aoi.crs)

    # Perform the intersection
    intersection = gpd.overlay(filtered_gdf, aoi, how='intersection')
    print(f"Found {len(intersection)} intersections.")

    # Calculate the area of the intersection in acres and round to 2 decimal places
    intersection['area_acres'] = intersection['geometry'].area / 43560
    intersection['area_acres'] = intersection['area_acres'].round(2)

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Modify the output file name
    base_name, ext = os.path.splitext(os.path.basename(input_file))
    output_file_name = f"{base_name}_{filter_value}_aoi_intersect{ext}"

    # Delete any existing file with the same name
    output_file = os.path.join(output_dir, output_file_name)
    if os.path.exists(output_file):
        os.remove(output_file)

    # Save the result
    intersection.to_file(output_file)
    print(f"Saved intersection to {output_file}.")

    # Generate the CSV file
    total_acreage = intersection['area_acres'].sum()
    generate_csv(output_dir, base_name, attribute_name, filter_value, total_acreage)
    print(f"Generated CSV file with total acreage.")


def main(aoi_path, intersect_files, output_folder, attribute_name, filter_values):
    """
    Main function to intersect multiple shapefiles with an AOI, filter the features by attribute values, 
    calculate the total acreage of the intersections, and generate CSV files with the results.

    :param aoi_path: The path to the AOI shapefile.
    :param intersect_files: A list of paths to the shapefiles to intersect with the AOI.
    :param output_folder: The directory to save the output files in.
    :param attribute_name: The attribute name to filter by.
    :param filter_values: A list of attribute values to filter by.
    """
    # Clear the output folder
    clear_directory(output_folder)

    aoi = read_shapefile(aoi_path)
    for intersect_file in intersect_files:
        for filter_value in filter_values:
            intersect_with_aoi(aoi, intersect_file, output_folder, attribute_name, filter_value)
    
    # Save the AOI to the output directory
    aoi_output_file = os.path.join(output_folder, "aoi.shp")
    aoi.to_file(aoi_output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Intersect shapefiles with an AOI")
    parser.add_argument('--aoi', metavar='aoi', type=str, required=True, help='path to aoi shapefile')
    parser.add_argument('--intersect_files', metavar='intersect_files', type=str, nargs='+', required=True, help='paths to intersect shapefiles')
    parser.add_argument('--output_folder', metavar='output_folder', type=str, required=True, help='path to output folder')
    parser.add_argument('--attribute_name', metavar='attribute_name', type=str, required=True, help='attribute name to filter by')
    parser.add_argument('--filter_values', metavar='filter_values', type=str, nargs='*', help='attribute values to filter by')
    args = parser.parse_args()
    main(args.aoi, args.intersect_files, args.output_folder, args.attribute_name, args.filter_values)