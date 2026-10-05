"""Extract local GPCC subsets, build 1971-2020 baseline SPI and 2024 context."""
from __future__ import annotations
import csv, gzip, hashlib, json, shutil, struct
from pathlib import Path
import numpy as np
from scipy.io import netcdf_file
from scipy.stats import gamma, norm, kstest
from shapely.geometry import shape, box
from shapely.ops import transform
from pyproj import Transformer
from inspect_gpcc_example import decode_times, clean

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/rainfall'
TMP = ROOT / 'tmp/rainfall'

def save(path, data):
    path.write_text(json.dumps(clean(data), ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def main():
    OUT.mkdir(parents=True, exist_ok=True); TMP.mkdir(parents=True, exist_ok=True)
    features = json.loads((ROOT/'data/regions/processed/model_regions.geojson').read_text(encoding='utf-8'))['features']
    ids = [f['properties']['region_id'] for f in features]
    project = Transformer.from_crs(4326, '+proj=laea +lat_0=-19 +lon_0=15.75 +datum=WGS84 +units=m +no_defs', always_xy=True).transform
    regions = [transform(project, shape(f['geometry']).segmentize(.001)) for f in features]
    example = json.loads((OUT/'gpcc_1971_1975_inspection.json').read_text(encoding='utf-8'))
    co = example['coordinates']; lats=np.asarray(co['etosha_bbox_latitude_centers']); lons=np.asarray(co['etosha_bbox_longitude_centers'])
    cells=[transform(project, box(x-.125,y-.125,x+.125,y+.125).segmentize(.001)) for y in lats for x in lons]
    weights=np.asarray([[r.intersection(c).area for c in cells] for r in regions])
    assert np.allclose(weights.sum(axis=1), [r.area for r in regions], rtol=1e-7)
    chunks=[]; manifests=[]
    for source in sorted((ROOT/'output').glob('gpcc_precipitation_analysis_monthly_*_v2025_025.nc.gz')):
        cache=OUT/(source.name.replace('.nc.gz','')+'_local.json')
        signature={'compressed_bytes':source.stat().st_size,'mtime_ns':source.stat().st_mtime_ns}
        cached=json.loads(cache.read_text(encoding='utf-8')) if cache.exists() else None
        if cached and cached.get('file_signature')==signature:
            chunk=cached
        else:
            print('extracting '+source.name, flush=True)
            with source.open('rb') as stream:
                stream.seek(-4,2); expected=struct.unpack('<I',stream.read(4))[0]
            nc=TMP/'q2_gpcc_extract.nc'
            if shutil.disk_usage(TMP).free < expected+100_000_000: raise RuntimeError('Insufficient scratch space')
            with gzip.open(source,'rb') as inp, nc.open('wb') as out:
                shutil.copyfileobj(inp,out,4*1024*1024)
            assert nc.stat().st_size==expected
            with netcdf_file(nc,'r',mmap=True) as ds:
                lat=np.array(ds.variables['lat'][:],copy=True); lon=np.array(ds.variables['lon'][:],copy=True)
                la=np.flatnonzero(np.isin(lat,lats)); lo=np.flatnonzero(np.isin(lon,lons))
                assert np.allclose(lat[la],lats) and np.allclose(lon[lo],lons)
                tv=ds.variables['time']; months=[d[:7] for d in decode_times(np.array(tv[:],copy=True),clean(tv.units),clean(getattr(tv,'calendar',None)))]; tv=None
                var=ds.variables['precip']; assert var.dimensions==('time','lat','lon')
                units=clean(var.units); assert units=='mm/month',units
                p=np.array(var[:,la[0]:la[-1]+1,lo[0]:lo[-1]+1],dtype=float,copy=True)
                for attr in ['_FillValue','missing_value']:
                    for marker in np.atleast_1d(getattr(var,attr,[])):p[p==float(marker)]=np.nan
                p=p*float(getattr(var,'scale_factor',1))+float(getattr(var,'add_offset',0));var=None
            assert np.isfinite(p).all() and (p>=0).all()
            assert nc.resolve().is_relative_to(TMP.resolve()); nc.unlink()
            chunk={'source':str(source.relative_to(ROOT)), 'file_signature':signature,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'units':units,'months':months,'values':p.reshape(len(months),-1).tolist()}
            save(cache,chunk)
        chunks.append(chunk);manifests.append({k:chunk[k] for k in ['source','file_signature','sha256']})
        print('ready '+chunk['months'][0]+'..'+chunk['months'][-1],flush=True)
    months=sum([x['months'] for x in chunks],[])
    assert months==[f'{y}-{m:02d}' for y in range(1971,2025) for m in range(1,13)]
    p=np.concatenate([np.asarray(x['values']) for x in chunks])
    regional=p@weights.T/weights.sum(axis=1)
    park=p@weights.sum(axis=0)/weights.sum()
    records=[]; climatology=[]
    for i,rid in enumerate(ids):
        series=regional[:,i]; clim=np.asarray([series[:600][np.arange(600)%12==m].mean() for m in range(12)])
        climatology.append({'region_id':rid,'monthly_mean_mm_1971_2020':clim.tolist(),'nov_apr_rainfall_fraction':float(clim[[10,11,0,1,2,3]].sum()/clim.sum())})
        cumulative=np.asarray([series[(y-1971)*12-2:(y-1971)*12+4].sum() for y in range(1972,2025)])
        base=cumulative[:49]; q=float((base==0).mean()); pos=base[base>0]
        assert len(pos)>=30 and np.std(pos)>0
        shape_a,loc,scale=gamma.fit(pos,floc=0)
        cdf=q+(1-q)*gamma.cdf(cumulative,shape_a,loc=0,scale=scale)
        spi=norm.ppf(np.clip(cdf,1e-6,1-1e-6)); delta=np.clip(-spi/2,0,1)
        diagnostic=kstest(pos, 'gamma', args=(shape_a,0,scale))
        empirical=(np.searchsorted(np.sort(base),cumulative,side='left')+.5)/(len(base)+1)
        empirical_spi=norm.ppf(np.clip(empirical,1e-6,1-1e-6))
        records.append({'region_id':rid,'baseline':'1971-2020 (49 complete Nov-Apr seasons)','baseline_n':49,'gamma_shape':float(shape_a),'gamma_scale_mm':float(scale),'zero_mass':q,'ks_statistic':float(diagnostic.statistic),'ks_pvalue_naive_not_formal_fit_test':float(diagnostic.pvalue),'rainy_season_years':list(range(1972,2025)),'wet6_precipitation_mm':cumulative.tolist(),'spi_wet6':spi.tolist(),'rainfall_deficit_index':delta.tolist(),'empirical_spi_diagnostic':empirical_spi.tolist(),'latest_year':2024,'latest_spi':float(spi[-1]),'latest_delta':float(delta[-1]),'latest_wet6_mm':float(cumulative[-1])})
    result={'scope':'precipitation anomaly only; no water availability or staffing multiplier','months':months,'regional_monthly_mm':{rid:regional[:,i].tolist() for i,rid in enumerate(ids)},'park_monthly_mm':park.tolist(),'climatology':climatology,'spi_records':records,'source_manifest':manifests,'checks':{'648_contiguous_months':True,'17_regions':len(ids)==17,'49_complete_baseline_seasons':True,'nonnegative_precipitation':True,'regional_area_conservation':True},'limitations':['0.25-degree interpolation, not independent local observations','Gamma KS p-values have estimated parameters and are diagnostic only','SPI is not groundwater or water-point availability','2024 is the latest available complete season, not 2026 observations','Rainfall is contextual and does not automatically change allocation or staffing']}
    save(OUT/'gpcc_regional_monthly_1971_2024.json',result)
    with (OUT/'rainfall_spi_wet6.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['region_id','year','wet6_precipitation_mm','spi_wet6','deficit_delta','baseline_n'])
        for row in records:
            for y,wet,spi,delta in zip(row['rainy_season_years'],row['wet6_precipitation_mm'],row['spi_wet6'],row['rainfall_deficit_index']):writer.writerow([row['region_id'],y,wet,spi,delta,49])
    print(json.dumps({'months':len(months),'years':'1971-2024','baseline_seasons':49,'latest_spi_range':[min(x['latest_spi'] for x in records),max(x['latest_spi'] for x in records)],'wet_season_share_range':[min(x['nov_apr_rainfall_fraction'] for x in climatology),max(x['nov_apr_rainfall_fraction'] for x in climatology)]},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
