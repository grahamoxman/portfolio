import geopandas as gpd
from base import base
from esridump.dumper import EsriDumper

class il(base):
    source = 'ilmines'
    iso = 'serc'

    
    def extract(self):
        url = "https://services9.arcgis.com/9NSsJKjbseNHCAQD/arcgis/rest/services/ISGS__ILMINES_04_01_2023_WFL1/FeatureServer//1"

        
        fields = {
            "geometry": "geometry",
            "name":"TYPE_LABEL",
            "acres" :"Shape__Area"
            }
        
        feat = EsriDumper(url)
        df = gpd.GeoDataFrame.from_features(feat, crs='epsg:4326')
        df = df.drop([0,1])
        df.rename(columns={v: k for k, v in fields.items()}, inplace=True)
        df = df[list(fields.keys())]
        df['iso'] = self.iso
        df = df.explode(index_parts=True).reset_index(drop=True)


        return df

if __name__ == '__main__':
    il().extract()   