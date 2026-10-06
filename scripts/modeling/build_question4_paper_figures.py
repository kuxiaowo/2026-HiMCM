"""Q4 figures share Q2's vector canvas and palette; no new data inferred."""
import hashlib
import json
from pathlib import Path
from matplotlib import colors
import numpy as np
import build_question2_paper_figures as draw
from build_question2_paper_figures import Canvas,BLUE,GOLD,RED,INK,GREY,PALE

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/question4/paper_figures'


def axes(c,x,y,w,h,xlim,ylim,xticks,yticks,xlabel,ylabel):
    def pos(xv,yv):return (x+(xv-xlim[0])/(xlim[1]-xlim[0])*w,y+(yv-ylim[0])/(ylim[1]-ylim[0])*h)
    for value in yticks:
        xx,yy=pos(xlim[0],value);c.line([(xx,yy),(xx+w,yy)],PALE,.6)
        c.text(xx-.18,yy,str(value),8,INK,ha='right')
    c.line([(x,y+h),(x,y),(x+w,y)],GREY,.7)
    for value in xticks:
        xx,yy=pos(value,ylim[0]);c.line([(xx,yy),(xx,yy-.08)],GREY,.6)
        c.text(xx,yy-.29,str(value),8)
    c.text(x+w/2,y-.72,xlabel,9)
    c.text(x,y+h+.35,ylabel,9,ha='left')
    return pos


def resource(r):
    c=Canvas(17,6.2)
    c.text(4.35,5.83,'(a) 人员预算与最高服务分',11,bold=True)
    c.text(12.8,5.83,'(b) 机时预算与峰值所需人员',11,bold=True)
    left=axes(c,.9,1.3,6.75,3.7,(24,59),(0,60),[24,30,35,40,45,50,55,59],[0,15,30,45,60],
              '同口径保护岗位数（120小时/人/月）','服务分')
    right=axes(c,9.25,1.3,6.75,3.7,(0,240),(55,70),[0,40,80,120,160,200,240],[55,60,65,70],
               '可用无人机机时/月','维持57.26分所需人员')
    for scope,color,label in [('q2_monitoring',BLUE,'Q2基准监测'),('q3_peak_base',GOLD,'Q3中档峰值月')]:
        pts=[]
        for row in r['resource_sensitivity']:
            if row['scope']!=scope:continue
            if row['success']:
                point=left(row['staff'],row['score']);pts.append(point);c.circle(*point,.045,color)
            else:
                if len(pts)>1:c.line(pts,color,1.1)
                pts=[]
        if len(pts)>1:c.line(pts,color,1.1)
    for x,color,label in [(1.3,BLUE,'Q2基准监测'),(4.65,GOLD,'Q3中档峰值月')]:
        c.line([(x,.27),(x+.35,.27)],color,1.2);c.text(x+.46,.27,label,8,ha='left')
    c.text(7.65,5.35,'无解情景不填零分',8,GREY,ha='right')
    for N,y in [(45,57.26),(57,57.26)]:c.line([left(N,0),left(N,y)],GREY,.6,dashed=True)
    c.text(*left(45,51),'45人',8,BLUE)
    c.text(*left(56.5,48),'57人',8,GOLD)
    curve=[right(v['drone_budget'],v['required_staff']) for v in r['technology_sensitivity'] if v['scope']=='q3_peak_base']
    c.line(curve,BLUE,1.2)
    for p in curve:c.circle(*p,.055,BLUE)
    c.line([right(0,59),right(240,59)],GREY,.65,dashed=True)
    c.text(*right(212,59.7),'59人参考',8,GREY)
    for U,N in [(0,67),(120,60),(240,57)]:
        x,y=right(U,N);c.text(x+(0.2 if U==0 else -.15 if U==240 else 0),y+.3,str(N)+'人',8,BLUE)
    c.text(12.6,.27,'点为计算情景，连线用于辅助阅读',8,GREY)
    c.save('fig1_resource_sensitivity')


def joint(r):
    c=Canvas(17,6.7)
    c.text(8.5,6.35,'中档峰值月：人员与机时的联合约束',11,bold=True)
    xs=[0,80,120,160,200,240];ys=[45,50,55,57,59,62,67]
    x0=2.0;y0=1.35;cw=1.9;ch=.58
    lookup={(v['staff'],v['drone_budget']):v for v in r['joint_peak_scenarios']}
    for i,N in enumerate(ys):
        c.text(x0-.35,y0+i*ch+ch/2,str(N),9,ha='right')
        for j,U in enumerate(xs):
            v=lookup[N,U];score=v.get('score')
            if score is None:fill=PALE;text='无解';ink=GREY
            else:
                frac=max(0,min(1,(score-20)/(r['target_score']-20)))
                low=np.array(colors.to_rgb(PALE));hi=np.array(colors.to_rgb(BLUE))
                fill=colors.to_hex(low*(1-frac)+hi*frac);text=f'{score:.2f}'
                ink='white' if frac>.6 else INK
            c.rect(x0+j*cw,y0+i*ch,cw-.06,ch-.04,fill)
            c.text(x0+j*cw+cw/2,y0+i*ch+ch/2,text,9,ink)
            if score is not None and score>=r['target_score']-1e-6:
                c.rect(x0+j*cw,y0+i*ch,cw-.06,ch-.04,fill,GOLD,1.2)
                c.text(x0+j*cw+cw-.17,y0+i*ch+ch-.15,'+',8,GOLD,bold=True)
    for j,U in enumerate(xs):c.text(x0+j*cw+cw/2,y0-.25,str(U),9)
    c.text(8.0,.65,'无人机可用机时/月',9)
    c.text(.5,5.8,'人员数',9,ha='left')
    c.text(15.25,4.77,'金框＋',9,GOLD)
    c.text(15.25,4.25,'维持目标',9)
    c.text(15.25,3.72,'57.26分',9)
    c.text(8.5,.2,'每格均重新优化；固定响应、额外火险和水点运维计入同一人工预算',8,GREY)
    c.save('fig2_joint_resources')


def main():
    OUT.mkdir(parents=True,exist_ok=True);draw.OUT=OUT
    path=ROOT/'output/question4/q4_results.json';r=json.loads(path.read_text(encoding='utf-8'))
    resource(r);joint(r)
    manifest={'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'figures':['fig1_resource_sensitivity','fig2_joint_resources'],
              'formats':['png','svg','tikz'],'style':'same vector canvas and palette as Q2',
              'notes':['no infeasible case shown as zero score','same service target and 120h/person/month','lines join computed samples; no confidence intervals']}
    (OUT/'figure_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=True))


if __name__=='__main__':main()
