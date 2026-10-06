"""Original Q6 figures; same Canvas emits preview PNG, SVG and embedded TikZ."""
from pathlib import Path
import json, hashlib
import build_question2_paper_figures as drawing
from build_question2_paper_figures import Canvas, BLUE, PALE, GOLD, RED, GREY, INK

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/question6/paper_figures'
OUT.mkdir(parents=True,exist_ok=True)
drawing.OUT=OUT
GREEN='#43856e'

def flow():
    c=Canvas(17,4.7)
    for x,title,detail in [(0.2,'保留：模型结构','服务容量、预算、响应门槛'),(5.95,'替换：本地输入','对象、威胁、路线与技术权限'),(11.7,'重算：规划结果','服务缺口、部署与人员需求')]:
        c.rect(x,3.1,5.1,1.05,BLUE);c.text(x+2.55,3.78,title,11,'white',bold=True);c.text(x+2.55,3.38,detail,9,'white')
    for a,b in [(5.35,5.85),(11.1,11.6)]:c.line([(a,3.6),(b,3.6)],GREY,1,arrow=True)
    c.rect(.2,1.32,5.1,1.05,PALE);c.text(2.75,1.97,'公开资料',11,bold=True);c.text(2.75,1.58,'管理要求、季节机制与法规',9)
    c.rect(5.95,1.32,5.1,1.05,'#f6e7cf');c.text(8.5,1.97,'原型情景假设',11,bold=True);c.text(8.5,1.58,'明确网络、服务需求与作业成本',9)
    c.rect(11.7,1.32,5.1,1.05,PALE);c.text(14.25,1.97,'本地校准',11,bold=True);c.text(14.25,1.58,'GIS、巡护与处置日志、技术试验',9)
    for x in [2.75,8.5,14.25]:c.line([(x,2.44),(x,3.01)],GREY,.8,arrow=True)
    c.text(8.5,.43,'先验证迁移机制，再用当地日志校准；服务分与生态成效分开解释',9,c=GREY)
    c.save('fig1_adaptation_flow')

def networks(cases):
    c=Canvas(17,6.65)
    coordinates={'A':(1.,4.55),'B':(4.25,4.55),'J1':(2.6,5.55),'J2':(4.25,2.85),'J3':(1.,2.85),'J4':(6.75,2.85)}
    parks=json.loads((ROOT/'data/modeling/q6_assumptions.json').read_text(encoding='utf-8'))['parks']
    for offset,park,normalid,stressid,forwardid in [(0.,parks[0],'C0','C2','J4'),(8.6,parks[1],'Y0','Y1','J2')]:
        normal=cases[normalid]['data'];stress=cases[stressid]['data']
        lookup={t['id']:t for t in stress['targets']}
        c.text(offset+4.1,6.25,park['park_label']+'：任务网络原型',11,bold=True)
        for u,v,d,a,b in park['edges']:
            x,y=coordinates[u];xx,yy=coordinates[v]
            c.line([(offset+x,y),(offset+xx,yy)],RED if b==0 else GREY,.8,dashed=b==0)
        for base in ['A','B']:
            x,y=coordinates[base];c.rect(offset+x-.22,y-.2,.44,.4,BLUE);c.text(offset+x,y+.4,'驻点 '+base,8)
        for t in normal['targets']:
            x,y=coordinates[t['id']];s=lookup[t['id']]
            c.circle(offset+x,y,.17,GREEN if s['reachable'] else RED)
            c.text(offset+x,y-.4,t['id']+' '+t['label'],7.5)
            c.text(offset+x,y-.78,f"{t['response_hours']:.2f} → {s['response_hours']:.2f} h",7.3,c=GREY)
        fx,fy=coordinates[forwardid];c.star(offset+fx+.4,fy+.32,.14,RED)
        c.text(offset+4.1,1.20,'红点：压力情景下超出2小时门槛',8,c=RED)
        c.text(offset+4.1,.75,'星号：额外前置驻点候选；每点增加480人时',8,c=GREY)
    c.text(8.5,.22,'示意图无地理比例；网络、速度和驻点均为团队假设，非两园实测地图',8,c=GREY)
    c.save('fig2_prototype_networks')

def results(cases):
    c=Canvas(17,8.)
    order=['C0','C1','C2','C3','Y0','Y1','Y2']
    left=1.95;scorewidth=5.75;hl=10.2;hw=5.;hmax=2200.
    c.text(4.35,7.56,'(a) 固定11人的服务分与地理上限',10.5,bold=True)
    c.text(12.7,7.56,'(b) 达到95分所需人时',10.5,bold=True)
    for n,code in enumerate(order):
        row=cases[code];y=6.72-.75*n;d=row['data'];f=row['fixed_budget_result'];t=row['target_result']
        c.text(left-.15,y,code,9,ha='right');c.text(hl-.15,y,code,9,ha='right')
        if f['success']:
            w=f['score']/100*scorewidth;c.rect(left,y-.18,w,.36,BLUE)
            c.text(8.82,y,f"{f['score']:.2f}",8,ha='right')
        else:c.text(left+.1,y,'11人预算不可行',8,c=RED,ha='left')
        gx=left+d['geographic_cap']/100*scorewidth;c.line([(gx,y-.24),(gx,y+.24)],RED,1.1)
        if t['success']:
            pos=hl
            for key,color in [('reserved_hours',BLUE),('extra_ground_hours',GREY),('ground_hours',GOLD),('operator_hours',GREEN)]:
                ww=t[key]/hmax*hw;c.rect(pos,y-.18,ww,.36,color);pos+=ww
            c.text(pos+.12,y,f"{t['total_person_hours']:.0f} / {t['staff_integer']}人",8,ha='left')
        else:c.text(hl+.05,y,'响应上限不足：95分不可达',8,c=RED,ha='left')
    for value in [0,50,100]:
        x=left+value/100*scorewidth;c.text(x,1.63,str(value),8,c=GREY)
    for value in [0,1000,2000]:
        x=hl+value/hmax*hw;c.text(x,1.63,str(value),8,c=GREY)
    x=hl+1320/hmax*hw;c.line([(x,1.98),(x,7.02)],RED,.7,dashed=True);c.text(x,7.2,'11人：1320人时',7,c=RED)
    c.line([(left,1.9),(left+scorewidth,1.9)],GREY,.6);c.line([(hl,1.9),(hl+hw,1.9)],GREY,.6)
    c.rect(2.8,1.13,.25,.17,BLUE);c.text(3.2,1.2,'服务分 / 响应预留',8,ha='left')
    c.line([(7.,1.08),(7.,1.33)],RED,1.);c.text(7.35,1.2,'地理上限',8,ha='left')
    for x,color,text in [(10.05,GREY,'专属地面工作'),(12.7,GOLD,'地面检查'),(14.8,GREEN,'无人机人工')]:
        c.rect(x,1.13,.25,.17,color);c.text(x+.33,1.2,text,7.3,ha='left')
    c.text(8.5,.63,'C0/C1常规及条件授权；C2/C3季风及前置；Y0常规；Y1/Y2冬季及前置',8,c=GREY)
    c.text(8.5,.18,'全部数值属于假设原型；95分为演示目标，人数不代表实际公园编制',8,c=GREY)
    c.save('fig3_adaptation_results')

def main():
    result=json.loads((ROOT/'output/question6/q6_results.json').read_text(encoding='utf-8'))
    cases={c['id']:c for c in result['cases']};flow();networks(cases);results(cases)
    manifest=dict(figures=['fig1_adaptation_flow','fig2_prototype_networks','fig3_adaptation_results'],
      formats=['png','svg','tikz'],results_sha256=hashlib.sha256((ROOT/'output/question6/q6_results.json').read_bytes()).hexdigest(),
      warning='diagram is an abstract task network, not a real geospatial map')
    (OUT/'figure_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Three original figures saved as PNG, SVG and TikZ.')

if __name__=='__main__':main()
