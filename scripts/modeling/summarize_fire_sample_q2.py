"""Single September-2022 burn sample: QA/fuel masked regional diagnostic only."""
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.windows import from_bounds, Window
from rasterio.warp import reproject, Resampling
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform, unary_union

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/question2'

def main():
    features=json.loads((ROOT/'data/regions/processed/model_regions.geojson').read_text(encoding='utf-8'))['features']
    raw=ROOT/'data/fire/raw'
    burnpath=next(raw.glob('*2022244*Burn_Date.tif'));qapath=next(raw.glob('*2022244*QA.tif'))
    with rasterio.open(burnpath) as src:
        project=Transformer.from_crs(4326,src.crs,always_xy=True).transform
        geoms=[transform(project,shape(f['geometry']).segmentize(.001)) for f in features]
        bounds=unary_union(geoms).bounds
        window=from_bounds(*bounds,transform=src.transform).round_offsets().round_lengths()
        window=window.intersection(Window(0,0,src.width,src.height))
        burn=src.read(1,window=window);aff=src.window_transform(window);crs=src.crs;pixelarea=abs(aff.a*aff.e)/1e6
    with rasterio.open(qapath) as src:qa=src.read(1,window=window)
    wc=np.zeros(burn.shape,dtype='uint8')
    with rasterio.open(ROOT/'data/ecology/processed/worldcover_2021_etosha.tif') as src:
        reproject(rasterio.band(src,1),wc,src_transform=src.transform,src_crs=src.crs,dst_transform=aff,dst_crs=crs,resampling=Resampling.nearest,src_nodata=0,dst_nodata=0)
    # MCD64 bits 0=land and 1=valid data; exclude shortened mapping (bit 2).
    valid=((qa&3)==3)&((qa&4)==0)&(burn>=0)
    fuel=np.isin(wc,[10,20,30]);sept=(burn>=244)&(burn<=273)
    records=[]
    for i,(f,g) in enumerate(zip(features,geoms)):
        rid=f['properties']['region_id'];mask=rasterize([(mapping(g),1)],out_shape=burn.shape,transform=aff,fill=0,dtype='uint8').astype(bool)
        if rid=='PAN_MAIN':fuel_i=np.zeros_like(fuel)
        else:fuel_i=fuel&mask
        good=fuel_i&valid;area=float(good.sum()*pixelarea);total=float(fuel_i.sum()*pixelarea);burnarea=float((good&sept).sum()*pixelarea)
        records.append({'region_id':rid,'fuel_area_native_sample_km2':total,'QA_valid_fuel_area_km2':area,'QA_fuel_coverage_fraction':area/total if total else None,'september_2022_burned_fuel_area_km2':burnarea,'single_month_burned_fraction':burnarea/area if area else None,'not_multiyear_risk':True})
    report={'scope':'September 2022 only; not annual/multiyear or harmful-fire probability','date_window_doy':[244,273],'native_pixel_area_km2':pixelarea,'fuel_proxy':'nearest-resampled WorldCover 10/20/30; main pan masked; no claim of rare plant value','QA':'land + valid data, nonnegative burn date, exclude shortened mapping','regions':records,'limitations':['single month, strong season/year dependence','fuel class nearest resampling at MODIS resolution is approximate','planned versus harmful fires not distinguished','no rainfall-to-fire causal relationship fitted']}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'fire_sample_regional_2022_09.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'regions':len(records),'burned_fuel_area_km2':sum(r['september_2022_burned_fuel_area_km2'] for r in records),'valid_fuel_area_km2':sum(r['QA_valid_fuel_area_km2'] for r in records)},ensure_ascii=False))

if __name__=='__main__':main()
