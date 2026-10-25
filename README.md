# FUJIFILM A5.5-D1｜全库 Query-Free 聚类与技术主题发现

2026-10-25 完成的实验与交付归档。BGE-M3 / Qwen 已有向量各覆盖 238,541 个专利族，共 56 组 KMeans、HDBSCAN、Leiden 实验。本库独立于后续检索项目，保留本次代码和实际输出。

## 阅读入口

- [完整报告（10 个问题）](REPORT.md)
- [算法比较](ALGORITHM_COMPARISON.md) · [历史树核查](HISTORICAL_TREE_CHECK.md)
- [技术候选目录](TECHNOLOGY_CATALOG.md)
- [实验清单](EXPERIMENT_MANIFEST.json) · [原实验最终验收](evidence/FINAL_VALIDATION.json)
- [原实验运行说明](EXPERIMENT_README.md)

聚类可能混合对象、材料、应用及技术手段。112 条命名尝试中，15 条满足逐字引文及至少三族规则；这不等于验证了 15 条技术路线。完整限制见报告。

## 四个 Excel 交付

- [CLUSTER_STATISTICS.xlsx](outputs/01a171fb-0dd6-7792-b36b-80e200aba942/CLUSTER_STATISTICS.xlsx)
- [CLUSTER_CATALOG.xlsx](outputs/01a171fb-0dd6-7792-b36b-80e200aba942/CLUSTER_CATALOG.xlsx)
- [TECHNOLOGY_CATALOG.xlsx](outputs/01a171fb-0dd6-7792-b36b-80e200aba942/TECHNOLOGY_CATALOG.xlsx)
- [RARE_TECHNOLOGY_CANDIDATES.xlsx](outputs/01a171fb-0dd6-7792-b36b-80e200aba942/RARE_TECHNOLOGY_CANDIDATES.xlsx)

## 完整分配数据

CLUSTER_ASSIGNMENTS.parquet 共 **11,044,345 行、118,949,766 字节**，以约 23.3 MB 的无损 XZ 压缩包提交在 [data/cluster_assignments](data/cluster_assignments)。没有抽样或删行。克隆后还原：

    ./run-python --offline scripts/restore_assignments.py

脚本验证压缩包及还原后完整文件 SHA-256；不会覆盖已有的不同内容。其他设备可使用 Python 3 运行同一还原脚本；本机计算和分析仍使用指定 SSD 入口。阅读 Excel 无需还原分配表。

## 代码、数据与证据

|目录|内容|
|---|---|
|scripts/|实验、统计、命名、引文审计、历史核查、报告与工作簿代码|
|configs/|原始实验参数、25 项精确版本依赖锁|
|kmeans/, hdbscan/, leiden/|实际结果、冻结标签、KMeans 中心；可再生成工作缓存留在 SSD|
|comparison/|统计、模型比较、稀有候选、代表族、历史对应|
|technology_catalog/|候选关系、引文审计、148 份本地模型响应及派生目录 SQLite|
|manifests/|全库族映射、抽样索引、冻结历史输入副本|
|figures/|12 张图|
|reports/|方法、语义复核及工作簿生成数据|
|evidence/|冻结记录、验收、可视化复核|

本库包含用户授权上传的交付和专利证据摘录；不包含原始 Fuji 数据库、原始 BGE/Qwen 全库向量、人工审核库、凭据、依赖缓存、运行日志或私人授权对话。technology_catalog/catalog.sqlite 是本次生成的小型候选目录。

## 运行与复核

实验已完成，无需重跑。活动只读底座在指定 SSD 的 patent/embedding_benchmark/vector_corpus/v1，APFS UUID 为 534D9B75-27C9-49B5-89A0-4DF7E631107C。本库 run-python 委托 SSD 守护入口；SSD 不可用时停止，不回退 Mac。

依赖见 configs/requirements.lock.txt；原计算使用本项目 deps/ 隔离依赖，未提交依赖二进制。复算须先准备匹配环境及外部只读底座。工作簿作者需要 Codex 提供的 @oai/artifact-tool，未复制其运行库；现有 XLSX 可直接打开。历史核查的原源目录已归档，冻结副本保留于 manifests/historical/；复核应使用冻结副本，不能直接运行依赖旧源目录的复制步骤。

发布代码中的本地模型地址由 OLLAMA_BASE_URL 配置，默认 loopback。模型和 digest 锁保留原记录。复核现有结果不需要模型请求。归档 JSON 中保留当时路径与资源记录，不应将历史绝对路径当作新写入目的地。

[PUBLICATION_MANIFEST.json](PUBLICATION_MANIFEST.json) 记录原文件与发布文件 SHA-256、链接和运行路径适配及明确排除项。原 SSD 实验目录保持不变。原实验清单和验收哈希对应原交付；发布版路径适配另记于发布清单，不伪造原验收。

    ./run-python --offline scripts/verify_publication.py

只检查发布文件哈希、压缩包还原、Python 语法及冻结标签，不重新聚类或调用模型。

## 可再生成工作缓存

PCA 投影、ANN 邻居及相似度、由标签和原始向量可计算的语义中心未提交 Git，仍保留于 SSD 原实验及发布副本。完整清单和 SHA-256 见发布清单的 excluded_recomputable_work_cache。所有正式交付、56 组实验元数据、冻结标签、原生 KMeans 中心、主题命名及引文证据均保留；未删减分配表任何一行。此处调整只影响发布内容，不修改原算法或结果。
