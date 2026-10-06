"""Real maps and computed response caps, with shared PNG/SVG/TikZ geometry."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import shape,box
from shapely.ops import transform,unary_union
from pyproj import Transformer
import build_question2_paper_figures as draw
from build_question2_paper_figures import Canvas,BLUE,GOLD,GREY,INK,PALE,RED
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/question6/paper_figures';GEO=ROOT/'data/question6/processed'
OUT.mkdir(parents=True,exist_ok=True);draw.OUT=OUT
GREEN='#43856e'

def flow():
 c=Canvas(17,4.7)
 for x,title,detail in [(0.2,'真实空间数据','边界、道路、驻点位置与生境'),(5.95,'迁移计算关系','路径 → 成本 → 服务 → 人时'),(11.7,'本地作业校准','物种任务、速度、权限与日志')]:
  c.rect(x,3.1,5.1,1.05,BLUE);c.text(x+2.55,3.78,title,11,'white',bold=True);c.text(x+2.55,3.38,detail,9,'white')
 for a,b in [(5.35,5.85),(11.1,11.6)]:c.line([(a,3.6),(b,3.6)],GREY,1,arrow=True)
 for x,title,detail,col in [(.2,'数据计算','面积、土地覆盖与路网距离',PALE),(5.95,'明确假设','速度、频次、服务目标与预留', '#f6e7cf'),(11.7,'条件性输出','可达比例与服务所需人时',PALE)]:
  c.rect(x,1.32,5.1,1.05,col);c.text(x+2.55,1.97,title,11,bold=True);c.text(x+2.55,1.58,detail,9)
 c.text(8.5,.43,'先验证空间服务子模型，再接入当地物种、风险与工作量；数据和假设分别记录',9,c=GREY)
 c.save('fig1_adaptation_flow')

def parts(g):return list(g.geoms) if hasattr(g,'geoms') else [g]
def maps(r):
 c=Canvas(17,8.6)
 for offset,park in [(0,'chitwan'),(8.6,'yellowstone')]:
  p=r['parks'][park];fwd=Transformer.from_crs(4326,p['epsg'],always_xy=True).transform
  poly=transform(fwd,shape(json.loads((GEO/(park+'_boundary.geojson')).read_text())['features'][0]['geometry']))
  x0,y0,x1,y1=poly.bounds;scale=min(7.6/(x1-x0),6.4/(y1-y0));ox=offset+.4+(7.6-(x1-x0)*scale)/2;oy=1.1+(6.4-(y1-y0)*scale)/2
  def xy(pt):return ox+(pt[0]-x0)*scale,oy+(pt[1]-y0)*scale
  title='奇特旺：WDPCA发布范围（待校准）' if park=='chitwan' else '黄石：NPS边界、路网与候选驻点'
  c.text(offset+4.1,8.18,title,10.5,bold=True)
  for part in parts(poly.simplify(50,preserve_topology=True)):
   if part.geom_type!='Polygon':continue
   c.poly([[xy(z) for z in part.exterior.coords]]+[[xy(z) for z in ring.coords] for ring in part.interiors],PALE,GREY,.5)
  case=next(z for z in r['cases'] if z['park']==park and z['id'].endswith('0'))
  for t in case['targets']:
   if not t['eligible']:continue
   size=p['grid_m'];x=np.floor(t['x']/size)*size;y=np.floor(t['y']/size)*size
   g=box(x,y,x+size,y+size).intersection(poly).simplify(70,preserve_topology=True)
   for part in parts(g):
    if part.geom_type=='Polygon':c.poly([[xy(z) for z in part.exterior.coords]],'#c3decc','white',.15)
  roads=[]
  for f in json.loads((GEO/(park+'_roads.geojson')).read_text())['features']:
   props=f['properties']
   if park=='yellowstone' and props.get('RDCLASS')=='Private':continue
   if park=='chitwan' and (props.get('highway') in ['path','footway','steps','cycleway','construction'] or props.get('access') in ['no','private']):continue
   g=transform(fwd,shape(f['geometry'])).intersection(poly)
   if g.length>800:roads.append(g)
  merged=unary_union(roads).simplify(120)
  for line in parts(merged):
   if line.geom_type=='LineString':c.line([xy(z) for z in line.coords],BLUE,.42)
  for i,b in enumerate(p['bases']):
   x,y=xy(b['xy']);c.star(x,y,.13,GOLD if i<2 else RED)
   label={'Norris':'Norris','Lake':'Lake','South Entrance':'South','Kasara':'Kasara','Sauraha':'Sauraha','Amaltari':'Amaltari'}
   name=b['name'].replace(' Ranger Station','');name=label.get(name,name)
   c.text(x+.17,y+.15,name,7,ha='left',c=INK)
  c.text(offset+4.1,.74,f"陆域可达比例：{case['geographic_cap']:.2f}%  |  车速30、步速4 km/h",8,c=GREY)
  L=10 if park=='chitwan' else 20;ax=offset+.55;ay=1.25;c.line([(ax,ay),(ax+L*1000*scale,ay)],INK,1.);c.text(ax+L*500*scale,ay+.17,str(L)+' km',7)
 c.rect(.9,.2,.23,.16,'#c3decc');c.text(1.25,.28,'条件可达单元',8,ha='left');c.star(5.4,.28,.1,GOLD);c.text(5.6,.28,'两处基准候选',8,ha='left');c.star(9.9,.28,.1,RED);c.text(10.1,.28,'第三处候选',8,ha='left')
 c.text(16.2,.28,'北向为上',8,ha='right',c=GREY)
 c.save('fig2_real_maps')

def results(r):
 c=Canvas(17,7.2)
 for offset,park in [(0,'chitwan'),(8.6,'yellowstone')]:
  cases=[z for z in r['cases'] if z['park']==park];title='奇特旺：发布范围试算（边界待校准）' if park=='chitwan' else '黄石：条件响应范围变化'
  c.text(offset+4.1,6.82,title,10.5,bold=True)
  x0=offset+2.;width=4.5
  for i,z in enumerate(cases):
   y=5.92-i*.93;cap=z['geographic_cap'];c.text(x0-.18,y,z['id'],9,ha='right');c.rect(x0,y-.17,width*cap/100,.34,BLUE)
   c.text(x0+width+.15,y,f'{cap:.2f}%',8,ha='left')
   target=x0+width*z['target_score']/100;c.line([(target,y-.25),(target,y+.25)],RED,1.)
   msg=(f"所需人时 {z['solution']['total_person_hours']:.1f}；人员当量上取整 {z['solution']['staff_integer']}" if z['solution'] else '固定基准目标不可达')
   c.text(x0,y-.36,z['label'],7.3,ha='left',c=GREY)
   c.text(x0,y-.62,msg,7.3,ha='left',c=GREY)
  for value in [0,25,50,75,100]:
   x=x0+width*value/100;c.text(x,1.96,str(value),8,c=GREY)
  c.line([(x0,2.2),(x0+width,2.2)],GREY,.6)
 c.text(8.5,1.35,'蓝条：陆域面积加权的条件响应上限；红线：固定为各园基准上限的90%',8.5,c=GREY)
 c.text(8.5,.82,'几何来自真实数据；速度、服务协议和候选驻点配置为假设。车速压力不等于实测季节交通。',8.2,c=GREY)
 c.text(8.5,.28,'欧式道路外行程尚未计入山地、河流和许可限制；结果用于初步迁移验证。',8.2,c=GREY)
 c.save('fig3_real_results')

if __name__=='__main__':
 r=json.loads((ROOT/'output/question6/q6_results.json').read_text(encoding='utf8'));flow();maps(r);results(r)
 (OUT/'figure_manifest.json').write_text(json.dumps(dict(figures=['fig1_adaptation_flow','fig2_real_maps','fig3_real_results'],source='q6_results.json and actual processed GeoJSON',formats=['png','svg','tikz'],land_cover_attribution='© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium'),ensure_ascii=False,indent=2),encoding='utf8')
 print('Real GIS figures saved.')
