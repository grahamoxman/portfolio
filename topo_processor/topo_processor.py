import arcpy
from arcpy.sa import *
# from arcpy.sa import Raster
import arcpy.ia
import argparse
import os

USER = arcpy.GetParameterAsText(0)
PROJECT_FOLDER = arcpy.GetParameterAsText(1)
SOURCE_NAME = arcpy.GetParameterAsText(2)
SOURCE_DATE = arcpy.GetParameterAsText(3)
DEM = arcpy.GetParameterAsText(4)
PROJECTION = arcpy.GetParameterAsText(5)
POLYGON_OUTPUT = arcpy.GetParameterAsText(6) 
CONTOUR_LINES = arcpy.GetParameterAsText(7) 
CONTOUR_INTERVAL1= arcpy.GetParameterAsText(8) 
CONTOUR_INTERVAL2 = arcpy.GetParameterAsText(9) 
SLOPE_CLASS_LABELS_DICT = {
    1: 'LTE3',
    2: 'GT3_LTE5',
    3: 'GT5_LTE7',
    4: 'GT7_LTE10',
    5: 'GT10_LTE15'
}

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("3D")
arcpy.CheckOutExtension("spatial")
arcpy.ImportToolbox(r"c:\program files\arcgis\pro\Resources\ArcToolbox\toolboxes\Analysis Tools.tbx")


def create_file_geodatabase(USER, PROJECT_FOLDER, topo_gdb_name):
    """
    Creates a new file geodatabase.

    Parameters:
    USER (str): The username.
    PROJECT_FOLDER (str): The project folder name.
    topo_gdb_name (str): The name of the geodatabase to be created.

    Returns:
    str: The path to the created geodatabase.
    """
    GDBFolder = f"C:\\Users\\{USER}\\OneDrive - R3 Renewables\\GIS\\Projects\\{PROJECT_FOLDER}\\03_GIS\\03_Data\\GDB"
    TopoGDBName = topo_gdb_name
    TopoGDB = f"C:\\Users\\{USER}\\OneDrive - R3 Renewables\\GIS\\Projects\\{PROJECT_FOLDER}\\03_GIS\\03_Data\\GDB\\{TopoGDBName}.gdb"

    # Check if the file geodatabase already exists, and if it does, delete it
    if arcpy.Exists(TopoGDB):
        arcpy.Delete_management(TopoGDB)

    # Process: Create File Geodatabase (Create File Geodatabase) (management)
    TopoGDB = arcpy.management.CreateFileGDB(out_folder_path=GDBFolder, out_name=TopoGDBName)[0]
    print('made gdb at', TopoGDB)
    arcpy.AddMessage(f"Created file geodatabase: {TopoGDB}")
    return TopoGDB


def prepare_dem(dem_directory, output_directory, PROJECTION):
    """
    Prepares the DEM by creating a mosaic if there are multiple DEM files.

    Parameters:
    dem_directory (str): The directory containing the DEM files.
    output_directory (str): The directory where the output will be saved.
    PROJECTION (str): The expected projection of the DEM.

    Returns:
    str: The path to the DEM to be processed.
    """
    # Create a list of all input DEM files
    input_dems = [os.path.join(dem_directory, file) for file in os.listdir(dem_directory) if file.endswith(".tif")]

    print(f"Input DEMs: {input_dems}")  # Print the list of input DEM files
    arcpy.AddMessage(f"Input DEMs: {input_dems}")

    # Check the number of DEM files
    if len(input_dems) > 1:
        # If there's more than one DEM file, create a mosaic
        mosaic_dem = "mosaic_dem"
        dem_to_process = os.path.join(output_directory, mosaic_dem)
        arcpy.CreateRasterDataset_management(out_path=output_directory, out_name=mosaic_dem, pixel_type="32_BIT_FLOAT")
        arcpy.Mosaic_management(inputs=";".join(input_dems), target=dem_to_process)
    else:
        # If there's only one DEM file, use it directly
        dem_to_process = input_dems[0]

    print(f"DEM to process: {dem_to_process}")  # Print the path to the DEM to be processed
    arcpy.AddMessage(f"DEM to process: {dem_to_process}")

    # Check if the DEM file exists
    if not arcpy.Exists(dem_to_process):
        raise FileNotFoundError(f"The DEM file does not exist: {dem_to_process}")

    # # Get the spatial reference of the DEM
    # dem_spatial_ref = arcpy.Describe(dem_to_process).spatialReference

    # # Check if the DEM's spatial reference matches the expected projection
    # if dem_spatial_ref.name != PROJECTION:
    #     raise ValueError(f"The DEM's spatial reference does not match the expected projection: {PROJECTION}")

    return dem_to_process


def process_slope(DEM, FILE_OUTPUT):
    """
    Processes the slope of the DEM.

    Parameters:
    DEM (str): The path to the DEM.
    FILE_OUTPUT (str): The path where the output will be saved.

    Returns:
    str: The path to the processed slope.
    """
    SlopePercentGrid = arcpy.sa.Slope(DEM, "PERCENT_RISE", 1, "PLANAR", "METER", "GPU_THEN_CPU")
    SlopePercentGrid.save(FILE_OUTPUT)
    return FILE_OUTPUT


def reclassify(SlopePercentGrid, FILE_OUTPUT):
    """
    Reclassifies the slope percent grid.

    Parameters:
    SlopePercentGrid (str): The path to the slope percent grid.
    FILE_OUTPUT (str): The path where the output will be saved.

    Returns:
    str: The path to the reclassified slope grid.
    """
    # Reclassify = ReclassedSlopeGrid
    ReclassedSlopeGrid = arcpy.sa.Reclassify(SlopePercentGrid, "VALUE", "0 3 1;3 5 2;5 7 3;7 10 4;10 15 5;15 20 6;20 999.999990 7", "DATA")
    ReclassedSlopeGrid.save(FILE_OUTPUT)
    return FILE_OUTPUT


def join_field(reclassed_slope_grid, SLOPE_CLASS_LABELS_DICT):
    """
    Joins a new field to the reclassified slope grid.

    Parameters:
    reclassed_slope_grid (str): The path to the reclassified slope grid.
    SLOPE_CLASS_LABELS_DICT (dict): A dictionary mapping the slope class labels.

    Returns:
    str: The path to the slope grid with the joined field.
    """
    # Create a new field 'Label' in the reclassed_slope_grid
    arcpy.management.AddField(reclassed_slope_grid, "Label", "TEXT")

    # Create an update cursor to iterate through the reclassed_slope_grid
    with arcpy.da.UpdateCursor(reclassed_slope_grid, ["VALUE", "Label"]) as cursor:
        for row in cursor:
            # Use the dictionary to map the 'VALUE' to 'Label'
            row[1] = SLOPE_CLASS_LABELS_DICT.get(row[0])
            cursor.updateRow(row)

    return reclassed_slope_grid


def raster_to_polygon(SlopeGridWithLabels, TopoGDB, SOURCE_NAME):
    """
    Converts a raster to a polygon.

    Parameters:
    SlopeGridWithLabels (str): The path to the slope grid with labels.
    TopoGDB (str): The path to the geodatabase.
    SOURCE_NAME (str): The name of the data source.

    Returns:
    str: The path to the created polygon.
    """
    SlopeGradeClasses = f"{TopoGDB}\\{SOURCE_NAME}_Slope_GradeClasses"
    with arcpy.EnvManager(outputMFlag="Disabled", outputZFlag="Disabled"):
        arcpy.conversion.RasterToPolygon(in_raster=SlopeGridWithLabels, out_polygon_features=SlopeGradeClasses, raster_field="Label", create_multipart_features="SINGLE_OUTER_PART")
    return SlopeGradeClasses


def pairwise_dissolve(input_file, topo_gdb, source_name):
    """
    Performs a pairwise dissolve on the input file.

    Parameters:
    input_file (str): The path to the input file.
    topo_gdb (str): The path to the geodatabase.
    source_name (str): The name of the data source.

    Returns:
    str: The path to the dissolved file.
    """
    slope_grade_classes_dissolved = fr"{topo_gdb}\{source_name}_Slope_GradeClasses_Dissolved"
    arcpy.analysis.PairwiseDissolve(in_features=input_file, out_feature_class=slope_grade_classes_dissolved, dissolve_field=["Label"], statistics_fields=[["GRIDCODE", "FIRST"]])
    return slope_grade_classes_dissolved


def split_by_attributes(SlopeGradeClassesDissolved, TopoGDB, SOURCE_NAME):
    """
    Splits the dissolved slope grade classes by attributes.

    Parameters:
    SlopeGradeClassesDissolved (str): The path to the dissolved slope grade classes.
    TopoGDB (str): The path to the geodatabase.
    SOURCE_NAME (str): The name of the data source.

    Returns:
    str: The path to the split file.
    """
    SplitLabelFeatureClasses = arcpy.analysis.SplitByAttributes(Input_Table=SlopeGradeClassesDissolved, Target_Workspace=TopoGDB, Split_Fields=["Label"])[0]

    if SplitLabelFeatureClasses:
        SlopesGT10 = arcpy.conversion.FeatureClassToFeatureClass(in_features=SlopeGradeClassesDissolved, out_path=TopoGDB, out_name="GT10", where_clause="Label IN ('GT10_LTE15', 'GT15_LTE20', 'GT20')", field_mapping=fr"Label \"Label\" true true false 10 Text 0 0,First,#,{TopoGDB}\\{SOURCE_NAME}_Slope_GradeClasses_Dissolved,Label,0,10;FIRST_GRIDCODE \"gridcode\" true true false 4 Long 0 0,First,#,{TopoGDB}\\{SOURCE_NAME}_Slope_GradeClasses_Dissolved,FIRST_GRIDCODE,-1,-1")[0]
    
    return SlopesGT10


def generate_contours(dem, output_directory, contour_interval, contour_name):
    """
    Generates contours from the DEM.

    Parameters:
    dem (str): The path to the DEM.
    output_directory (str): The directory where the output will be saved.
    contour_interval (int): The interval for the contours.
    contour_name (str): The name of the contour.

    Returns:
    str: The path to the generated contours.
    """
    # Convert the DEM from meters to feet
    try:
        dem_in_feet = arcpy.sa.Times(dem, 3.281)

        # Define the output path for the contour lines
        out_contour = os.path.join(output_directory, contour_name)

        # Generate the contours
        arcpy.sa.Contour(dem_in_feet, out_contour, contour_interval)

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    return out_contour


def main(USER, PROJECT_FOLDER, SOURCE_NAME, SOURCE_DATE, DEM, PROJECTION, GDB, POLYGON_OUTPUT, CONTOUR_LINES, CONTOUR_INTERVAL1, CONTOUR_INTERVAL2):
    
    
    topo_gdb_name = f"Topo_{SOURCE_NAME}_{SOURCE_DATE}"
    topo_gdb = create_file_geodatabase(USER, PROJECT_FOLDER, topo_gdb_name)

    dem_to_process = prepare_dem(DEM, topo_gdb, PROJECTION)

    slope_percent_grid = fr"{topo_gdb}\{SOURCE_NAME}_Slope"
    SlopePercentGrid = process_slope(dem_to_process, slope_percent_grid)

    reclassed_slope_grid = f"{topo_gdb}\\{SOURCE_NAME}_Slope_Reclass"
    reclassify_slope = reclassify(SlopePercentGrid, reclassed_slope_grid)  

    slope_grid_with_labels = join_field(reclassify_slope, SLOPE_CLASS_LABELS_DICT)

    if POLYGON_OUTPUT and POLYGON_OUTPUT.lower() in ['true', '1', 'yes']:
        polygon = raster_to_polygon(slope_grid_with_labels, topo_gdb, SOURCE_NAME)

        dissolved = pairwise_dissolve(polygon, topo_gdb, SOURCE_NAME)

        split = split_by_attributes(dissolved, topo_gdb, SOURCE_NAME)

        print('polygon output created')
        arcpy.AddMessage('polygon output created')

        return split
        
    if CONTOUR_LINES and CONTOUR_LINES.lower() in ['true', '1', 'yes']:
        contours1 = generate_contours(dem_to_process, topo_gdb, int(CONTOUR_INTERVAL1), f"{SOURCE_NAME}_contours_interval1")
        contours2 = generate_contours(dem_to_process, topo_gdb, int(CONTOUR_INTERVAL2), f"{SOURCE_NAME}_contours_interval2")
        print('contour lines generated')
        arcpy.AddMessage('contour lines generated')

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('USER', metavar='USER', type=str, help='username, must be written like GrahamOxman')
    parser.add_argument('PROJECT_FOLDER', metavar='PROJECT_FOLDER', type=str, help='project folder, example like TwentyMile_RouttCo_CO')
    parser.add_argument('SOURCE_NAME', metavar='SOURCE_NAME', type=str, help='data source name, for example like USGS')
    parser.add_argument('SOURCE_DATE', metavar='SOURCE_DATE', type=str, help='date tool is run, for example like 20240120')
    parser.add_argument('DEM', metavar='DEM', type=str, help='location of dem files as path')
    parser.add_argument('PROJECTION', metavar='PROJECTION', type=str, help='desired projection of output data')
    parser.add_argument('GDB', metavar='GDB', type=str, help='desired output folder for geodatabase, will create if does not exist')
    parser.add_argument('--POLYGON_OUTPUT', metavar='POLYGON_OUTPUT', type=str, help='allows option of creating polygon from raster output')
    parser.add_argument('--CONTOUR_LINES', metavar='CONTOUR_LINES', type=str, help='allows option of creating contours from raster output - default 3 and 5 feet')
    parser.add_argument('--CONTOUR_INTERVAL1', metavar='CONTOUR_INTERVAL1', type=str, help='select contour interval - like 3 and 5 (will be in feet)')
    parser.add_argument('--CONTOUR_INTERVAL2', metavar='CONTOUR_INTERVAL2', type=str, help='select contour interval - like 3 and 5 (will be in feet)')
    args = parser.parse_args()
    main(args.USER, args.PROJECT_FOLDER, args.SOURCE_NAME, args.SOURCE_DATE, args.DEM, args.PROJECTION, args.GDB, args.POLYGON_OUTPUT, args.CONTOUR_LINES, args.CONTOUR_INTERVAL1, args.CONTOUR_INTERVAL2)
