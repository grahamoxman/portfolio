import geopandas as gpd
from base import base
import pandas as pd
import csv
import re


class pa(base):
    source = 'pasda'
    state = 'pa'
    iso = 'pjm'
    alias_file = r"C:\Users\GrahamOxman\r3\projects\future_opp\alias_file_pa.csv"

    def aliases(self, merged_df):
        aliases = pd.read_csv(self.alias_file, na_values=[], keep_default_na=False)
        print(aliases.columns)

        
        print("Unique values in 'aliases' DataFrame:")
        print(aliases['operator'].unique())
        print("\nUnique values in 'merged_df' DataFrame:")
        print(merged_df['operator'].unique())

        for col in merged_df.columns:
            if col in aliases:
                print("Found matching column:", col)
                merged_df[col] = merged_df[col].fillna("")
                replace = {
                    i["operator"].strip(): i["new"] for i in aliases.to_dict(orient="records")
                }
                merged_df[col] = merged_df[col].replace(replace)
        return merged_df


    def extract(self):
        shp_paths = [
            r"C:\Users\GrahamOxman\OneDrive - R3 Renewables\GIS\Projects\zOther_GIS_Requests\Future_Opportunities\archive\01_Archive\01_Incoming\State Datasets\Pennsylvania_Coal_data_DEP\Bituminous_Surface_Mine_Permits_202301\Bituminous_Surface_Mine_Permits_202301.shp",
            r'C:\Users\GrahamOxman\OneDrive - R3 Renewables\GIS\Projects\zOther_GIS_Requests\Future_Opportunities\archive\01_Archive\01_Incoming\State Datasets\Pennsylvania_Coal_data_DEP\Anthracite_Surface_Mine_Permits_202212\Anthracite_Surface_Mine_Permits_202212.shp'
        ]

        fields = {
            "geometry": "geometry",
            "name": "MINE_NAME",
            "operator": "COMPANY_NA",
            "type": "PERMIT_TYP",
            "mineral": "MINERAL"
        }

        dfs = []  

        for shp_path in shp_paths:
            df = gpd.GeoDataFrame.from_file(shp_path, crs='epsg:4326')
            df.rename(columns={v: k for k, v in fields.items()}, inplace=True)
            df = df[list(fields.keys())]
            dfs.append(df)

            if 'Bituminous' in shp_path:
                df['mineral'] = 'bituminous'
            elif 'Anthracite' in shp_path:
                df['mineral'] = 'anthracite'

        merged_df = pd.concat(dfs)

        merged_df = self.aliases(merged_df)
    
        merged_df['iso'] = self.iso
        merged_df['state'] = self.state

        merged_df.set_crs('epsg:4326', inplace=True)
        merged_df.to_file('pa_mines.gpkg', driver = 'GPKG')
        return merged_df
    

if __name__ == '__main__':
    pa().extract()
