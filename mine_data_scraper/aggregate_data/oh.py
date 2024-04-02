import geopandas as gpd
import pandas as pd
from base import base

class oh(base):
    source = 'ohdnr'
    state = 'oh'
    iso = 'pjm'
    alias_file = r"C:\Users\GrahamOxman\r3\projects\future_opp\alias_file_oh.csv"

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
        shp = r"C:\Users\GrahamOxman\OneDrive - R3 Renewables\GIS\Projects\zOther_GIS_Requests\Future_Opportunities\archive\01_Archive\01_Incoming\State Datasets\Ohio_Mine_Data_DNR\Surf_CMO\Surf_CMO.shp"
        reclaim = r"C:/Users/GrahamOxman/OneDrive - R3 Renewables/GIS/Projects/zOther_GIS_Requests/Future_Opportunities/archive/01_Archive/01_Incoming/State Datasets/Ohio_Mine_Data_DNR/Land_Rec/Land_Rec.shp"

        fields = {
            "geometry": "geometry",
            "name": "Mine_Name",
            "operator": "Permittee",
            "status": "CMO_Status",
        }

        df = gpd.GeoDataFrame.from_file(shp, crs='epsg:4326')
        df.rename(columns={v: k for k, v in fields.items()}, inplace=True)
        df = df[list(fields.keys())]
        df['iso'] = self.iso
        df['type'] = 'surface'
        df['state'] = self.state
        df['status'] = df['status'].replace({'active': 'ACT', 'abandoned': 'ABA', 'released': 'REL'})

        reclaim_df = gpd.GeoDataFrame.from_file(reclaim, crs='epsg:4326')
        reclaim_df.rename(columns={'Rec_Status': 'reclaim'}, inplace=True)

        joined_df = gpd.sjoin(df, reclaim_df, how='left', predicate='intersects')


        columns_to_drop = [
                            'index_right', 'Law', 'Permittee', 'Permit_ID', 'National_I', 'Surf_Metho',
                            'Release_El', 'Area_Calc', 'Area_Rep', 'Area_RM', 'Pmt_App_Da',
                            'Pmt_App__1', 'Edit_Date', 'Comment', 'Re_Permit', 'Source_Doc',
                            'created_us', 'created_da', 'last_edite', 'last_edi_1', 'SHAPE_Leng',
                            'SHAPE_Area'
                            ]
        joined_df.drop(columns=columns_to_drop, inplace=True)

        joined_df = self.aliases(joined_df)
        joined_df.set_crs('epsg:4326', inplace=True)
        joined_df.to_file('oh_mines.gpkg', driver='GPKG')

        return joined_df
    
if __name__ == '__main__':
    oh().extract()   