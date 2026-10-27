# A5.5-D3 技术抽取质量收敛

活动目录在SSD；`./run-python`验证APFS身份，拒绝Mac旧项目回退。数据和已冻结D2只读。任务范围1117个既有族，另外6个历史补充探针单独统计。本任务的新语义判断只使用官方`deepseek-flash`，Codex负责程序、确定性校验和导出。

## 执行与恢复

- `./run-python --offline tests/test_integrity.py`：Unicode证据、分集隔离、D2哈希保护。
- `./run-python --offline scripts/resume_probe.py`：禁用网络验证已完成族缓存恢复，不产生模型请求。
- `./run-python scripts/pipeline.py --stage development --mode full --workers 12`
- 冻结后：`./run-python scripts/pipeline.py --stage holdout --mode full --workers 12`
- 同一固定消融子集：`--mode extract_only`、`--mode d2_replay`，开发用`--stage pilot30`，盲测用`--stage holdout`。
- `./run-python scripts/experiments.py --stage development`或`--stage holdout`：匿名候选同源Silver评价。
- `./run-python scripts/pipeline.py --stage main --mode full --workers 32`：全既有D2范围。先完成holdout三种模式后再执行，避免同指纹并发重复。
- `./run-python scripts/related_audit.py --run`：固定151个节点双向复审。
- 主范围终态后：`./run-python scripts/history_complete.py`、`./run-python scripts/d4_cases.py --run`，随后 `./run-python --offline scripts/d4_citation_recover.py`。

所有步骤幂等缓存；每次调用最多3次尝试、每个指纹累计最多6次，语义修订最多2轮并分别审计。失败、来源不足弃判、未解决证据争议分开。成功结果只读复用；重跑不会重算Embedding、聚类或旧D2。正式盲测允许固定重试规则和缓存续跑，不允许看结果改提示词后反复盲测。

请求体、响应、usage、模型返回名、输入/提示词/Schema/代码快照哈希留档。API不提供权重Digest，manifest留null并解释，不把云端别名冒称权重锁。凭据只从SSD非Git私密目录读取到内存，不在代码、请求或日志中。

## 质量解释

L1逐字/位置通过不等于语义准确。L2字段支持和L3完整结论由独立调用重新读原文，仍为同模型Silver；未收集人工Gold时Gold指标N/A。`Inferred`/`Unsupported`不进入确认候选事实，争议版本保留隔离。D4文件仅作为困难样本测试接口，不改D2概念ID或执行正式归并。

人工审核后使用 `./run-python --offline scripts/import_gold.py --workbook D3_EVALUATION_SET.xlsx --confirm-human-reviewed`，会写入独立human_imports，不覆盖Silver。先用`--dry-run`检查；默认空表不会创建Gold。

消费贡献表时保留field_support_json、supported_candidate_paths和silver_supported_candidate，原始字段不能自动视为已确认事实；所有human_confirmed仍为false。主处理失败与全文/人工待复核队列分别提供。
