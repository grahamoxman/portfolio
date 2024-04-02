import geopandas as gpd
from base import base
from esridump.dumper import EsriDumper

class va(base):
    source = 'vdmme'
    iso = 'pjm'

    
    def extract(self):
        url = "https://energy.virginia.gov/gis/rest/services/AML/AML_fs/FeatureServer/3"

        
        fields = {
            "geometry": "geometry",
            "name":"Project_Number",
            }
        
        feat = EsriDumper(url)
        df = gpd.GeoDataFrame.from_features(feat, crs='epsg:4326')
        df.rename(columns={v: k for k, v in fields.items()}, inplace=True)
        df = df[list(fields.keys())]
        df['iso'] = self.iso
       
        return df

if __name__ == '__main__':
    va().extract()   