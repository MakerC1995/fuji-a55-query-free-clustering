# A5.5-D1｜全库 Query-Free 聚类

活动输出目录为本目录。原始任务见 TASK_PACKAGE.md。最终入口为 REPORT.md。

## SSD 工作方式
已只读查看相关 Fuji 与 Embedding 对话，确认其他对话已将完整向量另存为 vector_corpus/v1，并正在把旧实验转存 NAS。本任务使用独立 workspaces 目录，避免被旧实验清理任务纳入归档。

- 唯一底座：/Volumes/Fuji_SSD_Work/patent/embedding_benchmark/vector_corpus/v1
- 运行入口：/Volumes/Fuji_SSD_Work/patent/embedding_benchmark/run-python
- 入口核验 APFS UUID 534D9B75-27C9-49B5-89A0-4DF7E631107C。
- 数据、结果、依赖、缓存、日志、临时文件均在 SSD；不回退 Mac，不向 NAS 活动库写入。
- SQLite 以 mode=ro 与 query_only 读取；源向量 mmap_mode=r。断点恢复前检查源文件大小和 mtime。
- 本任务包已授权本地 LLM 命名；不重编码、不跑BQ/EPO、不改服务端配置。

## 实际执行与复现

在本目录依次运行以下命令。已有结果会从检查点复用。

```sh
/Volumes/Fuji_SSD_Work/patent/embedding_benchmark/run-python --offline scripts/supervise.py
/Volumes/Fuji_SSD_Work/patent/embedding_benchmark/run-python --offline scripts/diagnostics.py
/Volumes/Fuji_SSD_Work/patent/embedding_benchmark/run-python --offline scripts/analyze.py
/Volumes/Fuji_SSD_Work/patent/embedding_benchmark/run-python --offline scripts/plot_sizes.py
```

命名必须等待 ASSIGNMENTS_FROZEN.json 和 LLM_INPUT_FREEZE.json。只有命名脚本允许连接固定局域网 Ollama：

```sh
/Volumes/Fuji_SSD_Work/patent/embedding_benchmark/run-python scripts/name_topics.py
```

依赖隔离在 deps/；版本锁见 configs/requirements.lock.txt。逐次参数保存在各 run/result.json；真实标签、输入空间、规模和日志全部保留。未成功的实验不生成填充标签。

技术主题与 Cluster 保持多对多；第二阶段喷头关系独立保存，不改变成员或删除候选。历史技术树仅在首轮命名冻结后读取。

## 已完成交付

最终结果见 REPORT.md、ALGORITHM_COMPARISON.md、HISTORICAL_TREE_CHECK.md 与 TECHNOLOGY_CATALOG.md。四份正式Excel在 outputs/01a171fb-0dd6-7792-b36b-80e200aba942/。

算法56实验、首轮70群及第二轮70群、本地历史事后8群均已实际完成；后验8群不混入首轮发现。15条具名候选具有逐字引文，但其技术机制支持层级另列，不是15条已验证路线。112次尝试与97条待定均保留。

首轮命名完成后依次使用 audit_quotes.py、check_history.py、name_history_blind.py（仅LAN）、assemble.py、write_reports.py、verify_workbooks.py。Excel使用同目录build_workbooks.mjs和捆绑Artifact Tool。finalize_freeze.py是本次推理前预算校正的单次审计辅助，不应在已冻结的模型结果上重做。恢复已完成analyze/name_topics阶段会验证后复用，不重写输入或重新调用模型。
