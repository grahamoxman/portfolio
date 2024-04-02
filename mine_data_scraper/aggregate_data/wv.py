import geopandas as gpd
from base import base

class wv(base):
    source = 'wvdep'
    iso = 'pjm'

    
    def extract(self):
        shp = r'C:\Users\GrahamOxman\OneDrive - R3 Renewables\GIS\Projects\zOther_GIS_Requests\Future_Opportunities\01_Archive\01_Incoming\State Datasets\West_Virginia_Mine_Data_DEP\WVDEP_Mining Reclamation\underground mining limits.shp'
        
        fields = {
            "geometry": "geometry",
            "name":"facility_n",
            "operator":"permittee",
            }
        

        df = gpd.GeoDataFrame.from_file(shp, crs='epsg:4326')
        df = df.drop('operator', axis=1)
        df.rename(columns={v: k for k, v in fields.items()}, inplace=True)
        df = df[list(fields.keys())]
        # df['source'] = self.source
        df['iso'] = self.iso
       
        return df

if __name__ == '__main__':
    wv().extract()   