from sqlalchemy import create_engine
import geopandas as gpd
import subprocess
import os
import pandas as pd
import datetime
import string

engine = create_engine(os.getenv('devdb'))

class base():
    source = None
    table = 'future_opportunities'

    def __init__(self, test=False):
        self.test = test
        if self.test:
            self.table += '_oxman'

    def extract(self):
       return gpd.GeoDataFrame()
    
    def aliases(self, df):
        aliases = pd.read_csv(self.alias_file, na_values=[], keep_default_na=False)
        for col in df.columns:
            if col in aliases:
                df[col] = df[col].fillna("")
                replace = {
                    i["old"]: i["new"] for i in aliases.to_dict(orient="records")
                }
                df[col] = df[col].replace(replace)

        print(df.head())
        return df

    
    def reset(self):
        engine.execute(f'drop table if exists {self.table}')

    def export(self):
        df = pd.read_sql_query(f"select * from {self.table}", engine)
        df.drop(columns=['geom'], inplace=True)
        df.to_csv('mines_output.csv')
    
    def update(self):
        df = self.extract()
        
        assert df is not None, f'{self.source}: not implemented' 
        assert df.shape[0], f'{self.source}: no rows'
        # assert 'geom' in df.columns, f'{self.source}: no geometry'
        
        df['source'] = self.source

        q = f"""
            CREATE TABLE if not exists {self.table} (
                gid serial,
                iso varchar,
                state varchar,
                source varchar,
                name varchar,
                operator varchar,
                type varchar,
                status varchar,
                reclaim varchar, 
                mineral varchar,
                geom geometry(POLYGON, 4326)
            );

            create index if not exists {self.table}_gist_geom
            on {self.table} using gist(geom); 
            
            delete from {self.table}
            where source = '{self.source}';
            """

        engine.execute(q)
        
        df.to_file(self.source + '.gpkg', driver='GPKG')

        cmd = [
            "ogr2ogr",
            "-f", "PostgreSQL", f"PG:{os.getenv('devdb')}",
            "-nln", self.table,
            "-nlt", "POLYGON", 
            "-t_srs", "epsg:4326",
            "-lco", "FID=GID",
            "-lco", "GEOMETRY_NAME=geom",
            self.source + '.gpkg'
            ]

        subprocess.run(cmd, check=True)

        os.remove(self.source + '.gpkg')

        print(f'{self.source}: {df.shape[0]}')
