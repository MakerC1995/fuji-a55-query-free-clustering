# D3 执行边界
仅在本 SSD 独立目录写入，守护入口 ./run-python；每次执行验证 APFS UUID。D2/E3/D1 全部只读。
本任务包授权 D3 对照及现有1117族主版本；不扩到全库，不采集/编码/聚类，不修改旧概念ID或归并。
生成式语义任务全部使用官方 DeepSeek deepseek-flash；不得静默改模型或由 Codex 填入最终语义判断。密钥只在内存读取，不复制到工作区，不写请求/日志/Git。
先固定开发/holdout，开发后冻结模型提示词/Schema/代码，然后单次主holdout。历史45回归后置，不能作为独立Gold。模型审核为Silver，Human Gold留空。所有原始响应/修订链保留。
