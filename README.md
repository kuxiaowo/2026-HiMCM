# 2026 HiMCM 数学建模项目

当前研究对象为埃托沙国家公园。第一题已完成一页LaTeX稿及PDF；第二题已完成条件性资源配置模型、正式论文正文、图表及本地PDF编译；第三题人员需求及实际生态成效尚未计算。

## 当前成果入口

- [第一题一页PDF](output/pdf/question1_protection_definition.pdf)、[LaTeX源文件](docs/paper/question1_protection_definition.tex)：12磅正文，三个小节、一张表和两组公式；[编译核验](output/question1/q1_latex_compile_verification.json)。
- [第二题正式PDF](output/pdf/question2_framework.pdf)：15页，30个编号公式、6幅图和5张表。
- [LaTeX源文件](docs/paper/question2_framework.tex)、[Markdown同步正文](docs/paper/question2_resource_allocation.md)、[第二题结构索引](docs/paper/question2_framework.md)。
- [模型结果](output/question2/q2_results.json)、[模型输入](output/question2/q2_model_inputs.json)、[独立模型核验](output/question2/q2_verification.json)。
- [PDF编译与版式核验](output/question2/q2_latex_compile_verification.json)、[章节核验](output/question2/q2_chapter_validation.json)。
- [整体建模计划](docs/整体建模计划.md)、[计算说明](docs/modeling_notes/question2_calculation_notes.md)、[项目状态与上传说明](docs/项目状态与上传说明.md)。
- [第一题详细方法底稿](docs/paper/question1_protection_definition.md)、[第三题精简方案](docs/第三题精简方案.md)。

## 模型范围

第二题优化地面监测人时与无人机机时，结合动物保护责任、可燃生境、道路进入和响应可达性，采用线性规划。当前模型排除水源、降雨与SPI；相关旧资料及计算为历史备查。服务分表示指定协议下的监测服务能力，不能解释为动物存活率、实际减损或完整生态认证。

## 复现与编译

计算优先使用conda环境；依赖入口为[道路环境](environment-roads.yml)、[分区环境](environment-regions.yml)。本项目现有环境路径为`D:/Python/Conda/envs/himcn-roads/python.exe`。在项目根目录执行：

```powershell
& 'D:/Python/Conda/envs/himcn-roads/python.exe' -X utf8 scripts/modeling/build_question2.py
& 'D:/Python/Conda/envs/himcn-roads/python.exe' -X utf8 scripts/modeling/write_question2_report.py
```

PDF已使用本机TeX Live 2026 / XeLaTeX编译并逐页核验。修改源文件后需重新编译两遍，以更新交叉引用；具体命令见[计算说明](docs/modeling_notes/question2_calculation_notes.md)。运行环境路径可按本机调整，项目成果和中间文件保存在本项目内。

## 仓库文件范围

仓库保留文档、脚本、当前模型所需的项目数据、图表、求解结果、最终PDF及历史备查成果。约2.2GB的旧GPCC全球降水原始压缩包不参与当前模型，继续保留本地而不入库；新增临时缓存、Python字节码和LaTeX中间文件也不入库。忽略规则不删除本地文件。

`.gitattributes`保留LaTeX源及关键模型JSON的原始字节，防止Git换行转换改变已有SHA-256核验指纹。现有输入与结果的数值内容保持不变。

开发提交使用`developing`分支，通过PR合并到`main`。项目规则见[AGENTS.md](AGENTS.md)。
