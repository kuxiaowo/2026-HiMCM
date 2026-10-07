"""Render concise preliminary Q3 explanation and inspectable static figures."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt, font_manager
from matplotlib.patches import Polygon
from matplotlib.collections import LineCollection
from shapely.geometry import shape
from shapely.ops import transform
from build_question2 import ROOT, FWD, load_geometry, polygons
from build_question3 import inputs, period

OUT=ROOT/'output/question3'

def figures(data,result):
    font=Path('C:/Windows/Fonts/msyh.ttc');plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams.update({'axes.unicode_minus':False,'svg.fonttype':'none','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    def save(fig,name):
        fig.savefig(OUT/(name+'.png'),dpi=220,bbox_inches='tight',facecolor='white');fig.savefig(OUT/(name+'.svg'),bbox_inches='tight');plt.close(fig)
    rows=result['monthly'];months=np.arange(1,13);eta=result['target_score']
    drought=next(s for s in result['full_sensitivity_solutions'] if s['name']=='base_drought')
    bymonth={s['period']['month']:s for s in drought['solutions']}
    dm=lambda m:8 if m in [8,9,10] else 5 if m in [5,6,7] else 11 if m==11 else 1
    stress_staff=[bymonth[dm(m)]['inverse']['required_staff'] for m in months]
    stress_score=[bymonth[dm(m)]['fixed_reference']['score'] for m in months]
    fig,axs=plt.subplots(3,1,figsize=(11.8,9),height_ratios=[2.2,1.2,1.1],sharex=True,layout='constrained')
    colors=['#8fa4b4','#24638c','#e19b43','#48a8a1'];bottom=np.zeros(12)
    for key,label,color in zip(['response_hours','base_monitoring_person_hours','extra_fire_person_hours','water_hours'],['驻点响应','基准监测','新增火险检查','17处水点运维'],colors):
        values=np.array([r[key] for r in rows]);axs[0].bar(months,values,bottom=bottom,label=label,color=color,width=.65);bottom+=values
    axs[0].axhline(59*120,color='#a83236',linestyle='--',linewidth=1.3,label='59人 × 120小时')
    for m,h in zip(months,bottom):axs[0].text(m,h+90,f'{h:.0f}',ha='center',fontsize=8)
    axs[0].set_ylim(0,8450);axs[0].set_ylabel('维持目标所需人时 / 月');axs[0].legend(ncol=3,loc='upper left',fontsize=8,frameon=False)
    axs[1].step(months,[r['required_staff'] for r in rows],where='mid',color='#24638c',linewidth=2,label='中档季节方案');axs[1].scatter(months,[r['required_staff'] for r in rows],color='#24638c',s=22)
    axs[1].step(months,stress_staff,where='mid',color='#a83236',linewidth=1.8,linestyle='--',label='异常干旱运维加密情景')
    axs[1].axhline(59,color='#777777',linestyle=':',label='第二题59人假设');axs[1].set_ylim(42,66);axs[1].set_ylabel('规划人数');axs[1].legend(ncol=3,loc='upper left',fontsize=8,frameon=False)
    axs[2].plot(months,[r['fixed_reference_score'] for r in rows],color='#24638c',marker='o',markersize=3,label='59人：中档季节方案')
    axs[2].plot(months,stress_score,color='#a83236',marker='s',markersize=3,label='59人：异常干旱情景')
    axs[2].axhline(eta,color='#444444',linestyle=':',linewidth=1,label=f'全年目标 {eta:.2f}分')
    axs[2].set_ylim(53,59);axs[2].set_ylabel('基准服务分');axs[2].set_xlabel('规划月份（每月标准化为30天）');axs[2].legend(ncol=3,loc='lower left',fontsize=8,frameon=False)
    axs[2].set_xticks(months,[f'{m}月' for m in months])
    for ax in axs:
        ax.grid(axis='y',alpha=.15);ax.set_xlim(.4,12.6)
    fig.suptitle('第三题初算：季节工作量、人员需求与固定59人的服务水平\n条件：六处候选驻点、120小时/人月、17处历史钻井样本；频次为规划假设',fontsize=13)
    save(fig,'q3_monthly_staff_and_service')
    fig,axs=plt.subplots(1,2,figsize=(11.6,4.8),layout='constrained');xx=np.arange(3);ss=result['sensitivity']
    regular=[next(r['annual_fixed_staff'] for r in ss if r['scenario']==name and not r['abnormal_drought']) for name in ['low','base','high']]
    stress=[next(r['annual_fixed_staff'] for r in ss if r['scenario']==name and r['abnormal_drought']) for name in ['low','base','high']]
    for offset,values,label,color in [(-.18,regular,'季节方案','#24638c'),(.18,stress,'异常干旱运维加密','#e19b43')]:
        bars=axs[0].bar(xx+offset,values,width=.34,label=label,color=color)
        for b,v in zip(bars,values):axs[0].text(b.get_x()+b.get_width()/2,v+1,str(v),ha='center')
    axs[0].set_xticks(xx,['低档','中档','高档']);axs[0].set_ylim(0,90);axs[0].axhline(59,color='#a83236',linestyle=':',linewidth=1);axs[0].set_ylabel('全年峰值规划人数');axs[0].legend(loc='upper left',frameon=False,fontsize=8)
    inv=result['water_inventory_workload_sensitivity'];bars=axs[1].bar(range(3),[r['required_staff'] for r in inv],color=['#24638c','#7b9eaf','#a6bdc6'])
    for b,r in zip(bars,inv):axs[1].text(b.get_x()+b.get_width()/2,b.get_height()+1,str(r['required_staff']),ha='center')
    axs[1].set_xticks(range(3),['已知样本工作量','水点工作量×2','水点工作量×3']);axs[1].set_ylim(0,90);axs[1].set_ylabel('中档方案峰值规划人数');axs[1].set_title('清单不全的工时压力检验',fontsize=11)
    fig.suptitle('标准和水点清单会影响人数：情景范围，不是统计置信区间\n倍增只复制样本工作量，不代表园内实际水点数量',fontsize=12)
    save(fig,'q3_staff_sensitivity')
    fig,ax=plt.subplots(figsize=(11.8,5.7),layout='constrained')
    regions=load_geometry()
    for rid,g in regions:
        for poly in polygons(g):ax.add_patch(Polygon(np.array(poly.exterior.coords)/1000,closed=True,facecolor='#f4f4ed' if rid!='PAN_MAIN' else '#e7ebec',edgecolor='#b9b9b3',linewidth=.5))
    roads=json.loads((ROOT/'data/roads/processed/park_edges.geojson').read_text(encoding='utf-8'))['features']
    ax.add_collection(LineCollection([np.array(transform(FWD,shape(f['geometry'])).coords)/1000 for f in roads],linewidths=.3,colors='#b5b9b5',alpha=.7))
    water=[r for r in data['water']['points'] if r['included']];dry=period(data,8);wd={r['name']:r for r in dry['water_rows']}
    natural=[r for r in data['water']['points'] if r.get('latitude') and r['type'] in ['A','C','C-dry']]
    ax.scatter([FWD(r['longitude'],r['latitude'])[0]/1000 for r in natural],[FWD(r['longitude'],r['latitude'])[1]/1000 for r in natural],marker='^',s=20,c='#8f9b95',label='天然泉点：未计抽水运维',zorder=3)
    sc=ax.scatter([FWD(r['longitude'],r['latitude'])[0]/1000 for r in water],[FWD(r['longitude'],r['latitude'])[1]/1000 for r in water],s=[25+wd[r['name']]['monthly_person_hours']*1.6 for r in water],c=[wd[r['name']]['monthly_person_hours'] for r in water],cmap='YlOrBr',edgecolors='#805c2d',linewidths=.5,label='17处钻井：大小与颜色表示人时',zorder=4)
    plt.colorbar(sc,ax=ax,shrink=.65,pad=.02,label='中档旱季运维人时 / 点月')
    for b in data['bases']:
        x,y=FWD(b['lon'],b['lat']);ax.scatter(x/1000,y/1000,marker='*',s=95,c='#24638c',edgecolors='white',linewidths=.5,zorder=5);ax.annotate(b['name'],(x/1000,y/1000),xytext=(3,-12),textcoords='offset points',fontsize=7,color='#24638c')
    ax.scatter([],[],marker='*',s=85,c='#24638c',label='第二题六处候选驻点')
    for r in sorted(water,key=lambda r:wd[r['name']]['monthly_person_hours'],reverse=True)[:4]:
        x,y=FWD(r['longitude'],r['latitude']);ax.annotate(r['name'],(x/1000,y/1000),xytext=(5,7),textcoords='offset points',fontsize=7)
    ax.autoscale_view();ax.set_aspect('equal');ax.set_xlabel('UTM东向 / km');ax.set_ylabel('UTM北向 / km');ax.legend(loc='lower left',fontsize=8,frameon=True)
    ax.set_title('公开研究水点样本与运维出行成本\n2013年坐标 + 2026年道路；当前运行状态未知，非全园完整清单',fontsize=12)
    save(fig,'q3_water_workload_map')

def report(data,result):
    monthly=result['monthly'];peak=monthly[7];v=result['verification_summary'];eta=result['target_score'];ss=result['sensitivity'];water=data['water'];fuel=sum(t['fuel_support_area_km2'] for t in data['targets']);rfuel=sum(t['fuel_support_area_km2'] for t in data['targets'] if t['response_eligible'])
    table='\n'.join(f'|{label}|{monthly[i]["required_person_hours"]:.1f}|{monthly[i]["required_staff"]}|{monthly[i]["flight_hours"]:.1f}|{monthly[i]["fixed_reference_score"]:.2f}|' for label,i in [('1—4月、12月',0),('5—7月',4),('8—10月',7),('11月',10)])
    sens='\n'.join(f'|{label}|{next(r["annual_fixed_staff"] for r in ss if r["scenario"]==name and not r["abnormal_drought"])}|{next(r["annual_fixed_staff"] for r in ss if r["scenario"]==name and r["abnormal_drought"])}|' for name,label in [('low','低档'),('base','中档'),('high','高档')])
    text=rf'''# 第三题：模型实算与待校准参数

2026-10-05，讨论用初算；模型、数据、核验和图表已完成，尚未扩写正式论文。

**当前结论：中档季节方案全年需57名保护岗位人员；若旱季出现所设的异常干旱运维压力，需62人。** 人数针对第二题的监测/日间响应任务及17处历史钻井水点样本，不是公园全体工作人员的真实最低编制。第二题假设的59名保护人员足以完成中档季节工作。

## 数据与假设怎么分

|内容|取得的依据|本次用法|
|---|---|---|
|旱季5—10月、湿季11—4月|[2024年研究数据说明](https://datadryad.org/dataset/doi:10.5061/dryad.4qrfj6qm3)，研究范围主要在东北部|采用季节划分；不声称2026年已发生异常干旱|
|早旱季5—7月、重点火管理8—11月|[官方2016年火管理策略](https://www.meft.gov.na/files/downloads/66c_Fire%20Management_Strategy%20Final%20Version.pdf)，Etosha章节PDF第33、40页|决定加密检查的时间窗口；不从历史过火比例推算工作人员|
|水点坐标与类型|[Koedoe原研究Table1](https://koedoe.co.za/index.php/koedoe/article/view/1329/1890)，2013年5月现场调查|42条记录，其中17条BH钻井全部可沿模型路网到达；A/C天然泉不计抽水设备运维，缺坐标和缺类别保留未知|
|人工水点工作方式|[MEFT 2021/2022年报](https://www.meft.gov.na/files/downloads/MEFT%20Annual%20Report%202021-2022.pdf)，PDF第28页有太阳能改造记录|把补水保障表示为到场检查抽水系统、清理和小修；不虚构运水车载量或供水体积|
|道路、成本、机队、评分权重|第二题保存的599点模型|直接复用；17个父区用于汇总，不再按区域中心代替小单元|

OSM另抽取287个候选水面/水井要素，仅7个明确标为water_well，且存在邻近重复、用途和运行状态未知。不能把287或7当人工动物水点总数。当前采用有原研究类型证据的17处样本，完整点位台账仍是正式写作前最需要补充的数据。原图、下载文件、链接和SHA-256已保存在[data/question3](../data/question3/raw/source_manifest.json)。

## 模型：保持基准服务，加上两项明确工作

目标使用第二题同一条件下的最优服务分：

\[
\eta=P_2^*={eta:.8f},\qquad P_t=100\sum_jw_js_{{jt}}\ge\eta.
\]

它表示保持第二题已实现的服务水平，客观地来自已有优化结果；**它不能证明第二题的服务标准已足以产生某种生态成效。** 原每100km²每月8点次、2小时响应、每区可达部分15%底线等仍是第二题的规划假设。

|决策量|容易理解的含义|单位|
|---|---|---|
|$x_{{jt}},h_{{jt}}$|用于原有合格监测的地面人工、无人机飞行|人时、机时|
|$s_{{jt}}$|第$j$个检查单元的基准检查完成比例|0至可达上限$r_j$|
|$y_{{jt}},v_{{jt}}$|用于额外火险检查的地面人工、无人机飞行|人时、机时|
|$N_t$|先求最少总人时，再向上取整得到人数；不是LP直接决策|人|

水点必须到场工作，所以其人时预先按路线算好，不可用无人机替代。单人有效工时固定120小时，各月统一按30天规划；未另扣节假日等因素。

令第二题的$a_j,b_j,o_j$分别为一次完整检查的地面人时、飞行机时和无人机配套人时，$\gamma_j=o_j/b_j$。$C_j$为原规定检查数；额外火险检查数为

\[
D_{{jt}}=k_t\frac{{A_j^{{fuel}}}}{{100}}r_j.
\]

$A_j^{{fuel}}$由区域可燃生境比例乘检查单元真实面积计算。中档$k_t$：常规月0、5—7月2、8—11月4，单位为每100km²可燃生境每月额外点次。增加的是独立火险筛查任务，保持与第二题相同的观察协议和成本；不把同一次检查算两次，也未加入扑救和计划燃烧人时。

每月逆向LP：

\[
\min H_t=H_0+W_t+\sum_j(x_{{jt}}+\gamma_jh_{{jt}}+y_{{jt}}+\gamma_jv_{{jt}}),
\]

\[
\frac{{x_{{jt}}}}{{a_j}}+\frac{{h_{{jt}}}}{{b_j}}\ge C_js_{{jt}},\quad
\frac{{y_{{jt}}}}{{a_j}}+\frac{{v_{{jt}}}}{{b_j}}\ge D_{{jt}},\quad
\sum_j(h_{{jt}}+v_{{jt}})\le240.
\]

同时保留$0\le s_{{jt}}\le r_j$、原区域底线和无人机适用条件。$H_0=2880$人时每月，只预留一次。逆向求解移除7080人时上限；固定资源分析则加入$H_t\le59\times120$并最大化同一$P_t$。全年人数为$\max_t\lceil H_t/120\rceil$。

固定驻点可响应的可燃生境约{rfuel:.1f}km²，占模型可燃生境{rfuel/fuel:.1%}。峰值新增任务可履行275.76点次，另428.45点次位于原响应不可达范围，单独记录未保障；**增加人员不能修复这个地理缺口，本次不称全园火管理已全部达标。**

## 增加次数和人时是怎么来的

次数不是资料给定的官方定额，而是可核对的规划规则。中档以等间隔运维为安排原则，把湿季水点检查目标间隔设为15天，旱季7.5天，因此标准30天月分别安排2、4次；异常干旱压力下设3.75天，即8次。LP核验月度工作量，尚未安排实际日期，不能证明每次间隔均满足。现场时间平时0.5小时、压力下1小时，均为假设，不是测得的故障率。

每处水点$\ell$的一次作业人时：

\[
a_\ell^W=2\left(T_\ell^{{round}}+\tau_t+\frac1{{12}}\right),\qquad W_t=\sum_\ell f_ta_\ell^W.
\]

两人同行，$T^{{round}}$是六处候选驻点中往返最快方案的路网行车及道路外步行时间，保留单行限制。17处合计往返经过42.87565小时；没有2小时维护到场限制，因为这是预先安排的运维。

中档旱季水点人时为$4\times2[42.87565+17(0.5+1/12)]=422.34$；湿季211.17；异常干旱980.68。火险额外2、4点次对应561.69、1123.38人时，由LP根据逐点成本选择地面或无人机，不能将火风险比例直接乘总人数。独立出行没有合并路线抵扣，可能偏高；大修、地下水位下降和实际缺水体积尚未建模。

## 求解结果与图表

|时期|需要人时/月|需要人数|使用机时/月|固定59人服务分|
|---|---:|---:|---:|---:|
{table}

8—10月：$2880+2406.11+1123.38+422.34=6831.83$人时，除以120向上取整为57人。全年固定57人可维持同一目标；56人在峰值月只能得到{v['one_fewer_peak_staff_forward_score']:.2f}分。59人是第二题的295×20%假设保护岗位数，不能解释为实际已有59名巡护人员，也不据此建议现实裁员。

异常干旱运维加密时，峰值7390.17人时，即62人；固定59人峰值服务54.97分，比目标低2.29分。需要比参考配置增加3个同口径保护岗位，或先调整已验证的作业方案。

![月份工作量、人员与服务](../output/question3/q3_monthly_staff_and_service.png)

|假设服务强度|季节方案峰值人数|异常干旱压力下|
|---|---:|---:|
{sens}

低/中/高档水点湿季频次1/2/4、旱季2/4/8，火险早期1/2/4、晚期2/4/8；完整参数见[q3_assumptions.json](../data/modeling/q3_assumptions.json)。它们不是置信区间，说明选择不同服务标准会得到不同人数。若按相同样本平均成本复制水点工作量2、3倍，中档峰值为61、64人；这只是清单缺失压力检验，不能当真实水点数量或空间外推。

![标准与清单敏感性](../output/question3/q3_staff_sensitivity.png)

![水点样本与路线成本](../output/question3/q3_water_workload_map.png)

## 核验及本轮微调

- 36个月份/求解模式组合均通过逐点容量、火险额外任务、区域底线、机时、人时、评分和取整核验；低中高情景另查。独立脚本直接读取保存的Q2输入与Q3解，核对新增需求、全部保存的可行解、分区CSV和指纹。比地理上限高的目标正确拒绝，响应预算不足正确无解。
- 锁定第二题原$s_j$可复现5288.3749人时，误差小于$10^{{-9}}$。第三题让同分方案自由重新选择后，无新增工作时最省5286.1143人时：主盐沼零评分权重单元的通用底线配置改变，节省2.26人时，不改变评分或第二题保存结果。
- 可燃生境需求统一为“面积×同口径比例”，避免混用投影后的面积分母；极小权重做数值缩放。达到地理上限时固定所有正权重可达点完成率为1，这是原评分约束的等价处理。
- 新水点路由补入同一条道路上的直接通行，避免不必要地绕行道路端点；Q2成本与结果原样保留。
- 六点各2人响应、六机各2人、一支2人水点队的同时人员数为26，小于规划57人；最长中档水点出行及作业6.39小时。但月均连续LP仍不证明详细排班、每次派遣的整数性或每驻点并发任务可行。

正式写作前优先校准：当前完整人工水点清单及岗位归属、到场频次与耗时、季节火险筛查定额。当前结果足以讨论模型结构和参数方向；没有真实作业日志，不给人数精确到个位的现实承诺。

复算命令（项目根目录，conda环境himcn-roads）：

```powershell
python -B scripts/modeling/prepare_question3.py
python -B scripts/modeling/build_question3.py
python -B scripts/modeling/write_question3_report.py
python -B scripts/modeling/verify_question3.py
```

结果：[月表](../output/question3/q3_monthly.csv)、[完整解](../output/question3/q3_results.json)、[核验](../output/question3/q3_verification.json)、[独立核验](../output/question3/q3_independent_verification.json)、[每点水运维](../output/question3/q3_water_visits_base.csv)。没有提交或推送。
'''
    (ROOT/'docs/第三题模型实算.md').write_text(text,encoding='utf-8')

if __name__=='__main__':
    data=inputs();result=json.loads((OUT/'q3_results.json').read_text(encoding='utf-8'));figures(data,result);report(data,result)
    print('Wrote docs/第三题模型实算.md and three PNG/SVG figure pairs.')
