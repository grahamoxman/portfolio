import geopandas as gpd
import pandas as pd
from base import base

class al(base):
    source = 'asmc'
    state = 'al'
    iso = 'serc'
    alias_file = r"C:\Users\GrahamOxman\r3\projects\future_opp\alias_file_al.csv"

    def aliases(self, merged_df):
        aliases = pd.read_csv(self.alias_file, na_values=[], keep_default_na=False)
        print(aliases.columns)

        
        # print("Unique values in 'aliases' DataFrame:")
        # print(aliases['operator'].unique())
        # print("\nUnique values in 'merged_df' DataFrame:")
        # print(merged_df['operator'].unique())

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
        gdb1 = r"C:\Users\GrahamOxman\Desktop\projects\future_opp\merged_data\al_closed_mines.shp"
        gdb2 = r"C:\Users\GrahamOxman\Desktop\projects\future_opp\merged_data\al_active_mines.shp"
        gdb3 = r"C:\Users\GrahamOxman\Desktop\projects\future_opp\merged_data\al_expired_mines.shp"
        

        fields = {
            "geometry": "geometry",
            "operator": "al_close_4",
            "name": "al_close_6",
            "status": "al_close_2",
            "type": "Type", 
        }

        dfs = []  

        # Extract data from the first geodatabase
        df1 = gpd.GeoDataFrame.from_file(gdb1, crs='epsg:4326')
        df1.rename(columns={v: k for k, v in fields.items()}, inplace=True)
        df1 = df1[list(fields.keys())]
        df1['iso'] = self.iso
        df1['source_type'] = 'closed_mines'
        dfs.append(df1)

        fields = {
            "geometry": "geometry",
            "operator": "al_activ_4",
            "name": "al_activ_6",
            "status": "al_activ_2",
            "type": "Type", 
        }

        # Extract data from the second geodatabase
        df2 = gpd.GeoDataFrame.from_file(gdb2, crs='epsg:4326')
        df2.rename(columns={v: k for k, v in fields.items()}, inplace=True)
        df2 = df2[list(fields.keys())]
        df2['iso'] = self.iso
        df2['source_type'] = 'active_mines'
        dfs.append(df2)

        fields = {
            "geometry": "geometry",
            "operator": "al_expir_4",
            "name": "al_expir_6",
            "status": "al_expir_2",
            "type": "Permit_Typ", 
        }

        # # Extract data from the third geodatabase
        df3 = gpd.GeoDataFrame.from_file(gdb3, crs='epsg:4326')
        df3.rename(columns={v: k for k, v in fields.items()}, inplace=True)
        df3 = df3[list(fields.keys())]
        df3['iso'] = self.iso
        
        df3['source_type'] = 'expired_mines'
        dfs.append(df3)

        merged_df = pd.concat(dfs)
        merged_df['state'] = self.state
        merged_df = self.aliases(merged_df)
        merged_df.set_crs('epsg:4326', inplace=True)
        # merged_df.to_file('al_mines.gpkg', driver='GPKG')
        return merged_df

if __name__ == '__main__':
    al().extract()
