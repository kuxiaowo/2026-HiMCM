# 2026-10-07 引言、limitations与短题注修改

本轮按用户提供的英文表达修改当前 `docs/paper/full_paper.tex`，保持原编辑器。Introduction保留四段的背景、定义、方法和结果顺序，明确第二阶段是保留最优分数后全局最少人工，而非仅“尝试减少”；120有效工时明确为每人每月。limitations以两个正文段落解释历史与缺失记录、任务假设、通行权限、人员资质、维护样本和生态验证限制，与表14相邻。

全部7图17表的题注改为一句简短概要；图号、表号仍由LaTeX自动生成。方法、数值和解释并入相邻正文，与原有解释合并，避免题注与正文重复。一句话可因物理宽度折成两行，不再堆入100—150词的长块。用户这轮明确要求覆盖math-modeling-skill此前的长题注规则；12pt题注、符号表及正文、22/16pt标题样式保留。

24个图表的内部数据、TikZ几何和标签，以及原有19个编号公式均与修改前一致。共同权重评价的既有计算口径另以未编号公式明确，未改变求解模型。57.26%、5286.11人时、144.34机时与57/62人当量未变。

英文新导出为[22页PDF](../../output/pdf/caption_revision_20261007/full_paper.pdf)：摘要1、目录2、主体解答3—18（16页）、补充附录19、信20、参考21、AI报告22。按原题计入19页，主体不超过20页，总PDF也不超过用户25页上限。每个图表与首次引用在同页或邻页，最多2个对象/页，最大图表占比约59.5%；当前编译无溢出、缺字或未定义引用。22页300dpi渲染已全部目视复核。

核验见[本轮记录](../../output/full_paper/caption_revision_20261007/caption_revision_validation.json)、[字体与完整稿检查](../../output/full_paper/caption_revision_20261007/typography_and_document_validation.json)、[图表对象检查](../../output/full_paper/caption_revision_20261007/english_layout_audit.json)。[修改前备份](../../output/full_paper/caption_revision_20261007/before_caption_revision.zip)及[前轮交付记录](../../output/full_paper/caption_revision_20261007/previous_delivery_records.zip)保留旧版本事实。

原skill全流程报告及87MB支撑包对应此前24页长题注版；模型输入、求解代码和数值仍适用，包内文稿不是当前短题注稿。中文学习详解及独立章节未发生本轮数据或源码变更，仍使用原来已核验的PDF。新旧版本的目视指纹分别保留，不复用旧英文记录认证新版。

内置编译器的平台目录错误仍在；原PDF被阅读器占用，因此按已有XeLaTeX导出授权将新版存入项目导出目录，源文件仍在原编辑器中原地修改。本轮未提交或推送。
