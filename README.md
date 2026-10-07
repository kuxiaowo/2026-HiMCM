# 2026 HiMCM 数学建模项目

当前以埃托沙的多物种保护为主线，动物量化采用2015年六类调查记录，并将道路响应、人员及无人机容量连接到规定巡检任务。2026-10-06改造修正了二阶段最少人工目标，补充技术协议、资源压力、网格、权重及黄石历史生态情景。2026-10-07已完成math-modeling-skill全流程适用项核查、修复与交付复核。计算结果和实测证据的适用范围分别记录。

## 当前成果入口

- [英文完整版PDF](output/pdf/caption_revision_20261007/full_paper.pdf)、[当前LaTeX源](docs/paper/full_paper.tex)：22页短题注版，含摘要、目录、16页主体解答、补充附录、一页信、参考与AI报告，7图、17表、19式、17条参考。
- [中文白话详解PDF](output/pdf/skill_checked_20261007/full_paper_zh_explained.pdf)、[详解源](docs/paper/full_paper_zh.tex)：40页学习稿，含逐项解释、教学算例及新增敏感性，6图、17表、19式。中文详解不采用英文稿页数上限。
- [本轮引言与短题注修改](docs/modeling_notes/caption_revision_20261007.md)、[当前核验](output/full_paper/caption_revision_20261007/caption_revision_validation.json)：7图17表题注均为一句话，解释并入正文，字号12pt保留。
- [前轮全流程核查报告](docs/modeling_notes/skill_full_audit_20261007.md)、[九维评分与问题关闭记录](output/full_paper/skill_audit_20261007/scored_review.json)、[前轮支撑材料ZIP](output/full_paper/skill_audit_20261007/review_support.zip)、[复现说明](output/full_paper/skill_audit_20261007/REPRODUCE.md)。
- [前轮改造报告](docs/modeling_notes/revision_implementation_20261006.md)：改动、前后数字、数据冲突及剩余实证限制，保留为历史记录。
- [交付核验](output/full_paper/revision_delivery_validation.json)、[目视记录](output/full_paper/revision_visual_review.json)、[完整稿清单](output/full_paper/full_paper_manifest.json)：绑定当前文件指纹。
- [数据可行性核查](docs/modeling_notes/revision_data_feasibility_20261006.md)、[补充计算](output/revision_feasibility/20261006/revision_results.json)、[黄石独立历史生态情景](output/revision_feasibility/20261006/yellowstone_historical_priority_scenario.json)。

当前英文PDF在 output/pdf/caption_revision_20261007/；中文学习稿及独立章节仍在 output/pdf/skill_checked_20261007/。英文第1页摘要、第2页目录、第3—18页主体解答、第19页附录、第20页信、第21页参考、第22页AI报告；赛题计入19页，总PDF22页。前轮87MB支撑包中的模型输入与代码仍适用，包内文稿保留其24页长题注版本。此前revision_20261006/及PDF根目录中的旧完整稿、中文译文及章节PDF保留为历史，不代表当前源。改造前245个文件及指纹保存在[备份](output/full_paper/history/before_multispecies_revision_20261006.zip)。

## 章节与结果

| 题目 | 当前PDF | 正文与计算入口 |
|---|---|---|
| 第一题 | [1页PDF](output/pdf/skill_checked_20261007/question1_protection_definition.pdf) | [LaTeX源](docs/paper/question1_protection_definition.tex)、[详细方法底稿](docs/paper/question1_protection_definition.md) |
| 第二题 | [8页PDF](output/pdf/skill_checked_20261007/question2_framework.pdf) | [LaTeX源](docs/paper/question2_framework.tex)、[正式Markdown](docs/paper/question2_resource_allocation.md)、[框架](docs/paper/question2_framework.md)、[结果](output/question2/q2_results.json)、[模型核验](output/question2/q2_verification.json) |
| 第三题 | [6页PDF](output/pdf/skill_checked_20261007/question3_framework.pdf) | [LaTeX源](docs/paper/question3_framework.tex)、[正式Markdown](docs/paper/question3_seasonal_staffing.md)、[框架](docs/paper/question3_framework.md)、[结果](output/question3/q3_results.json)、[独立核验](output/question3/q3_independent_verification.json) |
| 第四题 | [4页PDF](output/pdf/skill_checked_20261007/question4_sensitivity.pdf) | [正式正文](docs/paper/question4_sensitivity.md)、[结果](output/question4/q4_results.json)、[127个可行解核验](output/question4/q4_independent_verification.json) |
| 第五题 | [1页PDF](output/pdf/skill_checked_20261007/question5_evaluation.pdf) | [正式正文](docs/paper/question5_evaluation.md) |
| 第六题 | [6页PDF](output/pdf/skill_checked_20261007/question6_adaptation.pdf) | [LaTeX源](docs/paper/question6_adaptation.tex)、[正式Markdown](docs/paper/question6_adaptation.md)、[原面积基准结果](output/question6/q6_results.json) |

## 当前基准与结论范围

人员可用比例60%，无人机30架；每人120小时/月、每100平方千米每月8次检查、2小时地面响应。预算21240人时及1200机时，共享待命2880人时。第二阶段保持最优总分，在全部可行配置中最小化人工。完成率57.26%不变，人工由5379.02降为5286.11，飞行由151.82降为144.34机时。

第三题独立增加17处历史钻井样本维护和季节火险检查，常规峰值57人当量、指定旱季维护情景62人当量。第二题继续排除水源、降雨和SPI；第三题不编造运水量、不预测种群、不建立复杂轮班。服务完成率不等于动物存活率或实测减损，月总量人数不等于实际编制。

管理目标面向野生动物，六类历史输入只是可量化范围。犀牛偷猎定性保留，源报告冲突表不作为主输入。奇特旺源几何与官方面积仍不一致，结果是条件试算。黄石2022年狼群范围是独立历史优先事项情景，不是当前密度或偷猎概率。

## 复现与编译

计算优先使用现有conda环境 D:/Python/Conda/envs/himcn-roads/python.exe。在项目根目录依次运行第二至四题build/verify、第六题及补充计算，详见[复现说明](output/full_paper/skill_audit_20261007/REPRODUCE.md)。支撑包包含保存输入的复算材料；从全球原始遥感瓦片或全国OSM重建需另取源清单列出的原始资料。

当前完整版源已原地修订，图件内嵌，直接编译既有.tex。revise_multispecies_paper.py是有标记保护的首次应用脚本；旧write_full_paper.py、中文译文及扩写生成器不用于覆盖当前修订源。

    & './scripts/modeling/compile_revision_pdfs.ps1'
    & 'C:/Users/admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -X utf8 scripts/modeling/review_revision_pdf_layout.py
    & 'C:/Users/admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -X utf8 scripts/modeling/validate_full_paper.py
    & 'C:/Users/admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -X utf8 scripts/modeling/validate_revision_delivery.py

编译脚本使用已有TeX Live2026/XeLaTeX两遍更新同一目录。PDF检查使用带pdfplumber、pypdf及Pillow的文档Python。重新编译或改模型后，文件指纹可能改变，需重新核验和目视检查，不能自动复用旧“通过”。

内置LaTeX编辑器保持打开，但编译器仍报平台目录错误；本机XeLaTeX已按用户明确授权成功导出。题注、符号表、页眉及封面普通文字均为至少12pt；正文12pt、一级22pt、二级16pt及Arial题注字体保留。数学上下标正常缩小。赛题页数、纸张、边距和普通文字字号检查通过。

当前按用户要求采用一句话题注，覆盖skill通用100—150长度规则；数值解释在相邻正文，图表位置与面积阈值保留。前轮原版skill扫描器已运行，7条同图内部绘制带误报保留原退出码1；[逐条裁定](output/full_paper/skill_audit_20261007/raw_scanner_adjudication.json)与支持英文、按真实图表对象分组的增强检查共同记录。没有把原退出码改为0。基准结果本轮不变；边界与实际生态有效性仍不因此获得认证。

## 上传与历史材料

当前项目目录为 D:/Python/programs/GitHub/2026-HiMCM，成果和中间文件均在项目内，文档使用相对链接。旧F盘环境说明属于迁移历史。上传范围见[项目状态与上传说明](docs/项目状态与上传说明.md)。

原始资料、取消方案和旧PDF保留备查。旧GPCC全球降水压缩包不参与当前模型，不纳入本轮交付；忽略规则不删除本地原始文件。Git换行规则保留关键LaTeX源与JSON的字节指纹。

本轮未提交或推送。后续如授权同步，必须在developing提交，再通过PR合并main。
