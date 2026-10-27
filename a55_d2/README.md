# FUJIFILM A5.5-D2 技术知识库原型

本轮完成1117个唯一族的分阶段试验。最终状态、真实失败、技术贡献与候选机制数见 outputs/D2_REPORT.md；当前候选机制926个，贡献1115条。原文引用逐条核对，AI源文复核不等于人类Gold。完整原始响应、失败和修订链均保留。证据坐标使用Unicode码点的[start,end)半开区间，可对相同源文逐字复核。

## 阅读入口
- outputs/D2_REPORT.md：20个真实案例与10个问题。
- outputs/01a171fb-0dd6-7792-b36b-80e200aba942/TECHNOLOGY_KNOWLEDGE_BASE.xlsx：8表，人工编辑列浅黄。
- outputs/TECHNOLOGY_KNOWLEDGE_BASE.sqlite：核心关系表。
- outputs/EXPERIMENT_MANIFEST.json：实际调用、模型、代码、输入与源锁。
- outputs/EXTRACTION_QUALITY.md、HISTORICAL_TECHNOLOGY_VALIDATION.md、EXPERIMENT_COMPARISON.md：错误、事后回归及D1比较。

## 运行约定
仅在 /Volumes/Fuji_SSD_Work/workspaces/a55_d2_technology_kb 使用本目录 run-python。入口检查指定SSD APFS UUID，无挂载即停止，不创建本地同名目录，不回退Mac。D1/E3底座只读。当前本地模型和端点由已保存锁确定，不自动换模型，不重编码238541族，不重聚类。

## 阶段与检查点

以下说明用于理解已保存流程。当前目录已冻结，抽取/重校验/合并/命名/重建入口会拒绝修改发现结果。新盲测必须另建经授权的独立工作区；本轮不自动开始新实验。
1. scripts/prepare.py 检查冻结数据；重复运行只核对已有选取。
2. scripts/extract.py --stage pilot30 / trial100 / primary384 / all_selected：按独立Family缓存；每次启动只对未成功记录增量尝试。必须先源文复核前一阶段。已完成结果勿为迁移重跑。
3. scripts/revalidate.py：无新推理的原响应重校验；scripts/consolidate.py --stage ...：输出当前有效记录。源文修订与二次抽取分别记录，不改原始模型响应。
4. scripts/refine.py --family ...：只用于源文审计识别的完整性问题；结果默认待审，不自动替换。只有adoption_status=ADOPTED_AFTER_SOURCE_REVIEW才采用。
5. scripts/merge.py --stage all_selected --k ...：仅编码新贡献描述、召回候选并判双侧技术关系；参数以实际run收据为准。先运行scripts/confirm_same.py，对Same作第二轮源文复核并保守重组；scripts/concepts.py负责开放域/机制命名，scripts/hierarchy.py从120个平衡样本开放归纳上层目录，再逐机制映射对象/问题域。两轮同一本地模型复核不是独立Gold。
6. scripts/build_kb.py：稳定ID、M:N表及核心冻结。已冻结即校验复用，禁止覆盖。
7. posthoc_history.py / posthoc_relevance.py / relevance_source_review.py 只在核心冻结后工作；首轮相关性及定向源文复核分别保留。历史参照和喷头关联不反改技术定义。
8. review.py生成待人工表；prepare_workbook.py准备阅读视图。Excel仅由捆绑Artifact Tool作者。write_reports.py与verify_delivery.py生成报告和核验；finalize.py打包。

## 双向检索

在本目录运行 ./run-python --offline scripts/lookup.py --family google:40581936，从专利定位贡献、技术与源文。使用 --technology 后接Excel中的Technology ID可反向定位专利与相邻关系；--limit默认20。入口仅以只读方式打开交付SQLite并校验冻结。

## 复核与可复现性
固定80族与抽样种子保存在inputs。evidence/ASSISTANT_SOURCE_AMENDMENTS.json保存助手原文修订；refinements保留二次抽取采用/拒收理由。requests/responses保存实际LAN调用，code_snapshots保存当次代码。state/TECHNOLOGY_ID_REGISTRY.json保持技术身份独立于Cluster。

从历史任务包或本README的运行示例不能推导新BQ/A4/A6/EPO/模型任务授权。新结果未自动发布GitHub。全库扩展未执行；当前质量尚需人审，历史回归不是未知技术全库Recall。
