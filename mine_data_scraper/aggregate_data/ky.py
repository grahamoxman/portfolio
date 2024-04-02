import geopandas as gpd
from base import base
import pandas as pd

class ky(base):
    source = 'eppc'
    state = 'ky'
    iso = 'pjm'
    alias_file = "alias_file_ky.csv"

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
        shp = 'MinedOutAreas.shp'
        
        fields = {
            "geometry": "geometry",
            "name":"MineName",
            "operator":"Operator",
            "status": "Status",
            "type":"MineTypeDe",
            }
        

        df = gpd.GeoDataFrame.from_file(shp, crs='epsg:4326')
        df.rename(columns={v: k for k, v in fields.items()}, inplace=True)
        df = df[list(fields.keys())]
        df['iso'] = self.iso
        df['state'] = self.state
        df = self.aliases(df)
        df.set_crs('epsg:4326', inplace=True)
        df.to_file('ky_mines.gpkg', driver = 'GPKG')

        return df

if __name__ == '__main__':
    ky().extract()   