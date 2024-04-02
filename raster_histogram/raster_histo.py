import pandas as pd
import numpy as np 
import argparse

"""
This script processes a CSV or Excel file, maps the 'value' column to categories based on a predefined mapping,
calculates the sum and percentage of 'count' for each category, and writes the results to an output file.
"""

def read_file(file_path):
    """
    Reads a file into a pandas DataFrame.
    Supports CSV and Excel files.

    Parameters:
    file_path (str): The path to the file.

    Returns:
    DataFrame: A DataFrame containing the data from the file.
    """
    if file_path.endswith('.csv'):
        dataframe = pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        dataframe = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file type. Please provide a CSV or Excel file.")
    return dataframe


def map_values_to_categories(dataframe, category_mapping):
    """
    Maps the 'value' column of the dataframe to 'category' using the provided mapping.

    Parameters:
    dataframe (DataFrame): The DataFrame to map.
    category_mapping (dict): The mapping from values to categories.

    Returns:
    DataFrame: The DataFrame with the 'value' column mapped to 'category'.
    """
    if 'value' not in dataframe.columns:
        raise ValueError("'value' column not found in the dataframe.")
    dataframe['category'] = dataframe['value'].map(category_mapping)
    return dataframe


def calculate_category_percentages(dataframe):
    """
    Groups the dataframe by 'category' and calculates the sum and percentage of 'count' for each category.

    Parameters:
    dataframe (DataFrame): The DataFrame to group and calculate percentages.

    Returns:
    DataFrame: A DataFrame with the sum and percentage of 'count' for each category.
    """
    result = dataframe.groupby('category')['count'].sum().reset_index()
    result['percentage'] = (result['count'] / result['count'].sum()) * 100
    return result


def main(args):
    """
    Main function that reads the input file, maps values to categories, calculates category percentages,
    and writes the results to the output files.

    Parameters:
    args (Namespace): The command-line arguments.
    """
    category_mapping = {
        -1: 'flat',
        **{value: 'north' for value in range(0, 23)},
        **{value: 'northeast' for value in range(23, 68)},
        **{value: 'east' for value in range(68, 113)},
        **{value: 'southeast' for value in range(113, 158)},
        **{value: 'south' for value in range(158, 203)},
        **{value: 'southwest' for value in range(203, 248)},
        **{value: 'west' for value in range(248, 293)},
        **{value: 'northwest' for value in range(293, 338)},
        **{value: 'north' for value in range(338, 361)}
    }

    dataframe = read_file(args.input_file)
    dataframe = map_values_to_categories(dataframe, category_mapping)
    dataframe[['value', 'category']].to_csv(args.intermediate_file, index=False)
    result = calculate_category_percentages(dataframe)
    result_str = result.to_string(index=False, formatters={'count': '{:,}'.format, 'percentage': '{:.2f}%'.format})
    with open(args.final_file, 'w') as f:
        f.write(result_str)
    print(result_str)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a CSV or Excel file and calculate category percentages.")
    parser.add_argument('input_file', metavar='input_file', type=str, help='Input CSV or Excel file.')
    parser.add_argument('intermediate_file', metavar='intermediate_file', type=str, help='Output CSV file for intermediate results.')
    parser.add_argument('final_file', metavar='final_file', type=str, help='Output text file for final results.')
    args = parser.parse_args()
    main(args)