# 历史 Sputter 树事后检查

首轮70群命名与标签/参数冻结之后，才读取E4历史输入。仅复用其已核验观察成员的Simple Family映射，未用历史名称、引用、IPC/CPC或核心族改变任何分组。来源快照和SHA256见 [evidence/historical_check.json](evidence/historical_check.json)。

64个历史节点中62个有观察族，合计45个唯一族：Recipe 27、Equipment 18。H04/H16仍无已解析族，不能把它们虚构为两个Noise或库外族。H06/H12的候选成员身份已有本地族证据，但与历史代表的法律同族关系仍未定，单独保留。45/45在本次向量底座内，是以已观察族为条件分母，不替代64节点的完整覆盖口径，也不确认当前权属。

## 1. 已知族分到哪里

|实验|已知观察族|Noise族|非Noise群数|单群最多已知族|纳入首轮命名的相关群|
|---|---|---|---|---|---|
|bge_k100_s42|45|0|10|14|0|
|bge_k300_s42|45|0|16|9|3|
|bge_k800_s42|45|0|12|15|0|
|qwen_k300_s42|45|0|7|26|0|
|bge_n238541_pca30_c30_s15|45|45|0|0|0|
|bge_k30_mutual_r1.0_s42|45|0|4|27|0|
|bge_k30_sym_r1.0_s42|45|0|5|15|0|
|qwen_k30_mutual_r1.0_s42|45|0|5|17|0|
|qwen_k30_sym_r1.0_s42|45|0|4|25|0|

BGE K=300把27个Recipe观察族分到11群，最大一群8族；Qwen K=300分到2群，其中25族同群。BGE mutual Leiden把27族放入一个4255族的社区；Qwen mutual分为4群。不能从这种算法依赖的集中/分散断言一个模型正确、另一个错误。

BGE mutual的已知Recipe与Equipment落在互不重叠的4个群中，但Equipment有一个已知族是单点。Qwen sym的已知Recipe在2群、Equipment在另2群，观察子集也分开；BGE sym有一个13843族群同时含4个Recipe和1个Equipment观察族。历史标签只覆盖群的一小部分，这些数字不能当成全群语义纯度。

**全库HDBSCAN将45个观察族全部标为Noise。** 50k小参数样本中恰好有9个历史族，它们也全部是Noise，另36个是样本外，不能记成Noise。这直接说明Noise不能作为无关或无价值的删除依据。

## 2. 群内机制是否一致

共群只证明分区位置相同。BGE mutual的Recipe群4255族中只有27个属于本次历史观察集合；其通用中心、随机和边缘代表包含喷墨记录、压电元件和声学换能器，模型未找到统一手段。设备相关群也混入半导体工艺、电子设备和微结构制备。它们更像对象/应用区域，不能直接等同历史子路线。

K=800的190族群223包含15个Recipe观察族；57族群475包含8个。细粒度确实更容易显露压电对象，但群475同时出现Nb-PZT/界面层、氧18、Pb计量控制和驱动/退火方案，仍然不是一条配方。更大的K不保证按技术机制细分，且不同K结果并非嵌套树。

## 3. 不提供历史名称时能否命名

首轮Query-Free预算里有3个与观察族相交的BGE K=300群；其他主要相关群未被首轮通用选样覆盖。不能把未进入预算等同模型识别失败。

随后单独做8群事后盲测：历史成员只用于选择已有群，群内代表仍按通用中心/随机/边缘/多样性选取，没有强行插入核心族，没有把历史路线名或核心标记给模型。这8群是**事后验证，不能算首轮自然发现**；与首轮合计78个不同群。

|实验|群ID|群大小|盲命名|模型提取对象|
|---|---|---|---|---|
|bge_k300_s42|229|800|无法确定||
|bge_k300_s42|272|897|无法确定 / 无法确定 / 无法确定|流延膜 /  / 聚酯薄膜|
|bge_k30_mutual_r1.0_s42|17|4255|无法确定||
|bge_k30_mutual_r1.0_s42|24|3623|无法确定||
|bge_k30_sym_r1.0_s42|13|6055|无法确定||
|bge_k30_sym_r1.0_s42|9|8670|无法确定|磁记录介质|
|bge_k800_s42|223|190|无法确定|piezoelectric element|
|bge_k800_s42|475|57|无法确定 / 圧電特性の向上と長期信頼性の確保 / 无法确定|圧電素子 / 圧電積層体及び圧電素子 / 圧電アクチュエータ|

前6个宽泛群均未形成可核验的具名共同技术。两个K=800细群让模型识别出压电元件、钙钛矿和可靠性目标；57族群还给出“压电特性提高与长期可靠性”名称。但是其3份引文分别支持氧18、Nb组成和Pb比例，不能把氧同位体策略套给三族。这是对象/目标层识别，尚未独立复原历史Nb donor/plasma窗口、分段成膜或设备屏蔽等具体路线。代表只抽少量专利，因此未命名也不能推断模型不认识这些技术。

## 4. 可复核文件

- [comparison/historical_assignments.csv](comparison/historical_assignments.csv)：45族逐实验位置、Noise/样本外、原首轮名称和代表关系状态。
- [comparison/historical_cluster_mixing.csv](comparison/historical_cluster_mixing.csv)：Recipe/Equipment观察族在群中的计数。
- [comparison/historical_unresolved_nodes.csv](comparison/historical_unresolved_nodes.csv)：未解析节点保留。
- [technology_catalog/posthoc_blind_panels.json](technology_catalog/posthoc_blind_panels.json) 与 posthoc_blind/：实际盲测原文、输入和原始输出。
- [manifests/historical/historical_sputter_tree_recipe_equipment.md](manifests/historical/historical_sputter_tree_recipe_equipment.md)：冻结后才复制的历史树。

没有计算全局技术发现Recall，没有新增采集、改写法律族、移动成员或修订首轮命名。
