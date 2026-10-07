# 本轮支撑材料与复现

范围：2026-10-07保存输入的复算、论文源/PDF及核查证据。解压到一个新目录，在解压根目录执行；模型文件使用项目相对路径。当前项目计算使用conda，Python及依赖版本见同目录env_check.json。优先沿用已有conda环境，不需重新安装本机运行环境。

快速复算（实际在解压副本中执行过）：

    python -X utf8 scripts/modeling/reproduce_baseline_for_paper.py

应输出57.26、5286.11、144.34，分别为完成率%、人时、机时。这个入口读取保存的真实模型输入重新求解，不是打印结果文件。论文附录自动载入的代码与该.py一致。

完整保存输入重算顺序：

    python -X utf8 scripts/modeling/build_question2.py
    python -X utf8 scripts/modeling/verify_question2.py
    python -X utf8 scripts/modeling/build_question3.py
    python -X utf8 scripts/modeling/verify_question3.py
    python -X utf8 scripts/modeling/build_question4.py
    python -X utf8 scripts/modeling/verify_question4.py
    python -X utf8 scripts/modeling/build_question6_real.py
    python -X utf8 scripts/modeling/verify_question6_real.py
    python -X utf8 scripts/modeling/build_revision_supplement.py

必须按顺序运行，因为后题读取前题结果与指纹。保存结果含生成时间，新复算可产生不同字节SHA，但对应关键数值应一致；这时要重新登记输入、源码和PDF的指纹，不可冒用旧审阅记录。单独对解压后的保存解运行四份verify脚本也已核验。

数值依赖见requirements_saved_input.txt，记录本轮实际版本；prepare_question3.py保留用于来源与代码指纹，重建它还需要requests、osmium和原始OSM快照，保存输入复算无需运行该上游准备脚本。

正文仍为docs/paper/full_paper.tex；中文学习稿为full_paper_zh.tex。两者图件内嵌，英文复现代码也通过filecontents*内嵌，不需要独立图片或代码文件才能编译。保持既有编辑器，直接编译同一源。Windows本机编译入口：

    & ./scripts/modeling/compile_revision_pdfs.ps1

编译及PDF工具路径按本机既有TeX Live2026配置；异机应先将脚本中的可执行程序路径适配到已有环境。无需安装LaTeX编辑器插件。内置编译器的平台目录错误未解决，本轮XeLaTeX导出已获用户授权且成功。

审计入口：scripts/modeling/audit_full_skill_20261007.py。它使用包内未修改的original_check_layout.py，支持英文编号及真实图表分组。PyMuPDF本机临时目录已安装1.28.2；异机可在已有conda环境安装相同版本。原版扫描器的原退出码1及7条误报、逐条裁定均保留，未改原脚本或放宽说明/面积阈值。

PDF重新编译后，依次渲染、文字/字体核验、逐页目视，再运行validate_revision_delivery.py；人工记录必须匹配新PDF指纹。finalize_skill_delivery_20261007.py只接受已有且指纹一致的记录，不会代替目视检查自动填“通过”。本轮300dpi渲染测量与目视记录在包内，90页PNG为节约体积不纳入。

包内包含当前分区/道路处理输入、六类历史调查的质量标记、第三题17处历史BH证据、第六题真实几何与50/100m裁园遥感缓存、当前结果、必要代码、原始来源记录和审计证据。旧方案备份仅有补充对照实际依赖的before_multispecies_revision_20261006.zip；不混入旧合成方案作为当前证据。

本包支持保存输入复算，不承诺从全球raw重建：全国OSM PBF、全球WorldCover瓦片、未用GPCC、其他巨大历史缓存不纳入。重建原始预处理需按data/question6/raw/q6_real_source_manifest.json及其他来源清单补齐原始文件、版本和许可证；修改边界或破坏缓存标签会使第六题需要原始瓦片。奇特旺面积冲突、历史资料质量和现场生态验证限制仍保留。

包内SUPPORT_SHA256.json逐条列出文件指纹，除清单自身；ZIP的SHA和解压复算结果记录在项目旁置support_archive_validation.json/review_support.zip.sha256。ZIP、最终旁置核验和大体积页图不包含于自身。包内复现入口以本说明为准，项目入口中对ZIP及旁置记录的链接指向原项目交付目录。
