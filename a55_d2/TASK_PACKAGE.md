# Codex任务包：A5.5-D2 — Query-Free技术方案抽取与知识库原型

## 0. 任务定位

继续FUJIFILM专利项目A5.5。

D1已完成238,541个专利族的无查询聚类实验，包括：

- MiniBatchKMeans
- HDBSCAN
- kNN + Leiden
- BGE-M3和Qwen3-Embedding-0.6B向量对照

D1说明全库专利能够自然形成技术邻域，但当前LLM技术命名机制尚不足以建立具体技术知识库。

本轮D2不重新聚类。

**核心任务：从已冻结的专利聚类结果出发，让LLM识别各专利包含的具体技术方案，完成跨专利技术归并和分层组织，并检验该流程能否发现我们事先没有提供名称的技术路线。**

本轮不要求一次性处理全库238,541族，而是建立、验证一套可扩展到全库的技术知识抽取流程。

---

## 1. 最重要的架构原则

### 1.1 Cluster不等于Technology

一个Cluster可能包含多种技术。

一项技术也可能分布在多个Cluster。

一份专利摘要可能包含多个不同的技术方案。

因此，数据关系应该是：

Patent Family → Technical Contributions → Technology Concepts → Technology Hierarchy

必须支持：

- 一族专利对应多个技术贡献
- 多个专利贡献归并为一个技术节点
- 同一个技术节点关联多个Cluster
- 一个Cluster包含多个技术节点
- 技术节点之间存在父子、相似、替代、互补及应用关系

禁止直接将Cluster ID作为Technology ID。

### 1.2 区分技术对象、问题、手段和效果

不能简单将：

“Piezoelectric Device”

“Thin Film Manufacturing”

“Liquid Ejection Head”

等宽泛名称当成具体技术路线。

要尽可能识别：

- 技术对象：控制或改造什么
- 技术问题：解决什么困难
- 技术手段：采用了什么机制、结构或工艺
- 技术效果：实现什么结果
- 适用条件：在哪些材料或设备环境下成立

### 1.3 不使用已知技术树指导发现

主实验属于Query-Free Technology Discovery。

第一阶段不向LLM提供：

- PZT Sputter历史技术树
- 设备改造历史技术树
- E3 Query Bank
- 既有喷头技术分类
- 人工预设的技术路线名称

历史技术树只能在技术抽取和归并结果冻结后用于事后验证。

不要因为发现的技术与历史树不一致，就重新命名或调整实验结果。

---

# 2. 输入数据

## 2.1 D1已有结果

复用：

- CLUSTER_ASSIGNMENTS.parquet
- CLUSTER_CATALOG.xlsx
- CLUSTER_STATISTICS.xlsx
- RARE_TECHNOLOGY_CANDIDATES.xlsx
- TECHNOLOGY_CATALOG.xlsx
- D1实验Manifest
- E3 Family ID与原始Title/Abstract映射

以及原始BGE、Qwen Embedding和现有向量近邻索引。

如果文件名不同，自动定位实际路径。

原始专利数据库和D1实验文件保持只读。

## 2.2 历史审计数据

如项目中存在，后续验证使用：

- HISTORICAL_FAMILY_REGRESSION.xlsx
- HISTORICAL_TREE_CHECK_D1.csv
- HISTORICAL_TREE_CHECK_D1.md
- Fuji_Sputter_Recipe_Equipment_历史技术树_E4移交包.md

这些文件不是技术抽取输入。

如果历史树文件缺失，保留验证接口，不允许凭模型记忆补造历史清单。

---

# 3. D2.1：确定实验数据集

## 3.1 主实验：Qwen K300 Cluster 139

根据D1实际结果：

- Cluster ID：139
- Embedding：Qwen
- Algorithm：MiniBatchKMeans
- K=300
- Cluster Size：384族

该Cluster包含25个历史Recipe核心族，但这一信息不能提供给技术抽取LLM。

对384族全部进行技术方案抽取。

**不要只抽取中心附近的10–20族。**

本轮要观察一个真实Cluster内部究竟包含多少不同技术手段。

## 3.2 对照实验

至少包含：

| 实验 | Cluster | D1报告规模 |
|---|---|---:|
| Qwen K300 | #139 | 384 |
| Qwen K800 | #286 | 258 |
| Qwen K800 | #168 | 153 |
| BGE K800 | #223 | 190 |
| BGE K800 | #475 | 57 |
| Qwen K800 | #404 | 272 |

上述规模来自既有D1审计记录，执行时必须重新检查实际映射。

对照组的目的：

1. 同一技术空间在不同聚类粒度下是否产生相似技术节点。
2. BGE与Qwen是否识别出不同的技术机制。
3. Recipe与Equipment相关技术是否能被区分。
4. 更小的Cluster是否更容易形成具体技术节点。

## 3.3 非目标领域控制样本

仅研究上述Cluster会带来一个问题：它们已经被我们事后确认与Sputter有一定关系。

因此必须另外从D1结果中选择：

- 至少2个随机中型Cluster
- 至少1个高度混合的Cluster
- 至少1个小型紧密Cluster
- 一批HDBSCAN Noise专利

选择这些控制样本时，不允许按PZT或喷头关键词过滤。

保存选择规则与随机种子。

注意：同一专利可能出现在多个实验Cluster中。

技术抽取应按唯一Family ID缓存，避免重复调用LLM；但保留所有Cluster来源关系。

---

# 4. D2.2：逐专利抽取原子技术贡献

这是本轮最核心的开发任务。

不要直接让LLM给整个Cluster命名。

先逐专利阅读Title和Abstract，识别技术贡献。

## 4.1 技术贡献的数据结构

建议采用：

```json
{
  "family_id": "...",
  "contributions": [
    {
      "contribution_id": "...",
      "technical_object": "...",
      "technical_problem": "...",
      "technical_mechanism": "...",
      "implementation": "...",
      "expected_effect": "...",
      "materials": [],
      "process_methods": [],
      "structures": [],
      "parameters": [],
      "evidence_spans": [],
      "evidence_level": "...",
      "ambiguity_notes": "..."
    }
  ]
}
```

这些字段是数据结构示例，实际实现可扩展，但必须保持稳定Schema。

## 4.2 抽取原则

LLM必须区分以下内容：

**Technical Object**

研究的对象是什么？

例如薄膜、溅射设备、流道、控制电路、压电元件。

**Technical Problem**

具体要解决什么问题？

例如组成偏移、可靠性降低、离子轰击过强、热场不均。

**Technical Mechanism**

通过什么机制解决？

这是识别具体技术路线最重要的字段。

例如通过基板偏压改变入射粒子能量，而不能只写“优化沉积”。

**Implementation**

具体实现方式。

例如调整RF相位、使用可调阻抗、设置导电网格、改变气体比例。

**Expected Effect**

文献披露或主张的技术效果。

禁止把未验证的推测描述成实测结论。

## 4.3 多技术贡献

允许单族专利抽取多个技术贡献。

但不得把一篇专利摘要的每个名词都拆成一个技术。

只有当某个技术贡献能够形成相对独立的：

技术问题 + 技术手段

关系时，才考虑拆分。

如果无法可靠区分，保留一个综合贡献并标记不确定性。

## 4.4 摘要证据限制

当前E3主要只有Title和Abstract。

因此禁止将摘要没有披露的信息补写为Claims或实施例事实。

对于缺少技术手段、只有技术目标的摘要，允许输出：

`MECHANISM_UNDISCLOSED`

对于信息不足的Title-only专利，允许输出：

`INSUFFICIENT_EVIDENCE`

但这不代表该专利没有技术价值。

所有技术抽取必须保留原始证据短句以及对应Title/Abstract字段。

原文引述必须能够通过程序校验其确实来自输入文本；意译应单独存储，不得冒充原文。

---

# 5. D2.3：技术贡献向技术概念归并

在完成逐专利技术抽取后，再执行技术归并。

不能直接根据专利Embedding距离进行合并。

两个专利语义相近，不代表它们采用同一技术机制。

## 5.1 技术等价判断

判断两个技术贡献是否属于同一技术概念，需要综合考虑：

- 技术对象是否相同或可归于同一上级对象
- 解决的问题是否一致
- 核心物理或工程机制是否一致
- 实现方式是否仅为同一机制的变体
- 是否为根本不同的替代方案

例如：

通过可调阻抗控制基板电位

和

通过RF相位差控制基板电位

可以拥有共同上级技术：

基板电位控制

但具体技术手段不完全相同。

应保留两个子技术节点，不得强行合并。

## 5.2 两级技术概念

本轮最少建立：

**Level A：技术对象/问题域**

例如：等离子体沉积过程控制。

**Level B：具体技术机制/解决方案**

例如：利用RF相位差调节基片偏压。

允许继续细分Level C：

不同电路、设备结构、实施工艺。

但不要求所有技术都必须达到相同深度。

## 5.3 技术归并方法

可以结合：

- 技术贡献的结构化字段
- 技术描述Embedding
- 近邻候选召回
- LLM成对技术关系判定
- 层次归并

避免全量O(N²)逐对LLM比较。

推荐：

1. 对每条技术贡献构造规范化技术描述。
2. 使用现有或可复用的本地Embedding模型建立技术贡献向量。
3. 召回可能属于同一技术的候选。
4. LLM判断Same / Parent-Child / Related / Distinct / Uncertain。
5. 建立技术节点与关系图。

这里允许为新生成的技术描述编码少量向量，但不重新编码238,541族专利。

## 5.4 归并质量控制

必须阻止：

- 因为应用领域相同而错误合并
- 因为包含PZT就错误合并
- 因为都是RF控制就错误合并
- 因为材料不同就错误拆分本质相同的工艺机制
- 因为表达语言不同就错误拆分
- 因为摘要很短就过度推断技术一致

每次归并都要保存两个原始Contribution ID和归并理由。

---

# 6. D2.4：建立技术知识库原型

输出一个初步的Technology Knowledge Base。

最低支持以下四张逻辑表：

## Technology Concepts

每个技术节点包含：

- Technology ID
- 技术名称
- 上级技术节点
- 技术对象
- 技术问题
- 核心机制
- 适用条件
- 技术描述
- 证据状态
- 版本

## Patent Contributions

记录每份专利抽取出的技术贡献。

## Patent–Technology Relations

允许多对多关联。

包含：

- Family ID
- Contribution ID
- Technology ID
- 关系类型
- 原文证据
- 证据强度

## Technology Relations

记录技术间的：

- Parent–Child
- Same/Equivalent
- Alternative
- Complementary
- Related

禁止仅凭语义相近就赋予技术继承关系。

所有关系必须可追溯至贡献记录。

---

# 7. D2.5：LLM技术抽取质量实验

不要仅统计成功生成了多少个技术名称。

需要检查真正的技术表达质量。

## 7.1 固定抽样复核

从不同实验区域选取约60–100族进行审计。

包括：

- 明确技术机制
- 复杂多机制
- 高度相似但实际不同的技术
- 摘要不足
- 跨领域技术
- 设备/工艺/材料交界技术
- 小群及Noise

对结果检查：

- 技术对象是否准确
- 技术问题是否有原文依据
- 技术手段是否真实披露
- 是否遗漏多个技术贡献
- 是否虚构工艺参数
- 是否把同一技术错误拆开
- 是否将不同技术错误合并

LLM自检可以用于发现错误，但不能作为独立人工真值。

输出便于用户进行少量人工修订的审核表。

## 7.2 与旧D1命名方式比较

对同一批Cluster比较：

**旧方法：**

Cluster → LLM统一命名

**新方法：**

Patent → Technical Contributions → Technology Concepts

比较：

- 有证据的技术节点数量
- 机制明确程度
- 证据可追溯比例
- 混合技术被拆出的比例
- 重复技术合并情况
- 不确定技术比例
- LLM调用成本

不要仅因为新方法生成的技术节点更多，就认定它更优。

## 7.3 重要观察

特别检查Qwen K300 Cluster 139。

回答：

- 384族中多少族具有可明确抽取的技术机制？
- 共抽取多少独立技术贡献？
- 合并后形成多少候选技术概念？
- 是否有显著的上层技术分类？
- 不同技术机制是否能清晰拆分？
- 哪些摘要无法可靠抽取？
- 哪些技术贡献分布在多个Cluster？

必须给出真实专利案例。

---

# 8. D2.6：跨模型与跨Cluster归并

研究BGE与Qwen划分不同是否会影响技术知识库。

重点使用：

- Qwen K300 #139
- Qwen K800 #286、#168
- BGE K800 #223、#475
- Qwen K800 #404

比较：

1. 同一专利在不同Cluster中的位置。
2. 不同Cluster是否归纳出同一技术概念。
3. Qwen细分群是否对应BGE细分群。
4. 设备技术与Recipe技术是否可以在知识库层区分。
5. 是否存在跨Cluster的相同技术机制。

特别需要验证：

**技术知识库是否能够摆脱对某一种聚类算法和Cluster ID的依赖。**

如果同一技术在不同模型的Cluster中能够归并到同一个Technology ID，说明这套架构具有更好的可复用性。

但不能仅用同一批族交叉重复出现证明技术一致；需要保留真实机制证据。

---

# 9. D2.7：喷头相关性判断

第一阶段技术抽取与归并冻结之后，才开展喷头关联判断。

不能反过来修改已经冻结的技术定义。

针对每个技术节点判断：

- Direct：直接用于喷头或明确描述喷头
- Manufacturing：用于喷头制造或直接适用于对应工艺
- Transferable：原应用不是喷头，但技术机制可能迁移
- Contextual：仅有材料、产业或背景关联
- Unrelated：没有发现合理技术联系
- Uncertain：摘要证据不足

关联判断必须进一步记录：

- 关联的喷头技术对象
- 可能的应用方式
- 需要满足的工艺或物理条件
- 当前证据来自专利还是工程推断
- 是否需要Claims/Description核验

注意：

某个专利属于Fujifilm，不等于必然与喷头相关。

某项技术可迁移，不等于Fuji实际采用。

本轮不需要直接把结果写进最终喷头技术树。

---

# 10. D2.8：历史Sputter技术树事后验证

只有在以下结果冻结后才能开展：

1. 原子技术贡献
2. 技术概念归并
3. 技术名称
4. 技术层级

然后使用历史Recipe与Equipment技术树进行事后核验。

已知：

- E4有27个Recipe历史核心族
- E4有18个Equipment历史核心族

根据D1的后续比对，这45族均已找到全库Cluster映射。

本阶段检查：

- 已知技术是否被抽取出来
- 是否识别出了具体机制
- 不同历史路线是否被错误合并
- 是否遗漏技术贡献
- 未命中是否因为摘要缺乏信息
- 是否存在历史技术树之外、但有明确证据的新机制

这里评价的核心不是：

历史族有没有进入Cluster。

而是：

**在不知道历史技术名称的条件下，系统是否能从摘要中识别对应技术机制。**

建立四种结果：

- Mechanism Recovered
- Broad Topic Only
- Mechanism Missed
- Insufficient Source Evidence

按Recipe与Equipment分别统计。

历史树只是已知路线回归样本，不能据此宣称全库未知技术发现Recall。

---

# 11. D2.9：输出技术知识库与阅读报告

建议交付：

### 1. D2_REPORT.md

必须从真实技术发现案例开始，而不是先介绍算法。

报告首页展示至少15–20个具有原文证据的技术概念。

其中既包含喷头关联技术，也包含非喷头技术。

### 2. TECHNOLOGY_KNOWLEDGE_BASE.xlsx

给人阅读的主文件。

建议工作表：

- Overview
- Technology Concepts
- Patent Contributions
- Patent–Technology
- Technology Relations
- Cluster–Technology
- Review Queue
- Historical Validation

### 3. PATENT_CONTRIBUTIONS.parquet

逐族技术贡献结构化数据。

### 4. TECHNOLOGY_CONCEPTS.parquet

归并后的技术概念。

### 5. TECHNOLOGY_RELATIONS.parquet

技术间关系。

### 6. CLUSTER_TECHNOLOGY_MAPPING.parquet

Cluster与Technology之间的多对多映射。

### 7. EXTRACTION_QUALITY.md

LLM抽取质量和错误分析。

### 8. HISTORICAL_TECHNOLOGY_VALIDATION.md

历史Sputter技术树事后检验结果。

### 9. EXPERIMENT_COMPARISON.md

原D1 Cluster统一命名 vs D2逐族技术抽取。

### 10. EXPERIMENT_MANIFEST.json

保留模型、Prompt、参数、输入哈希、时间、代码版本和数据来源。

### 11. 可复现代码

支持：

- 增量执行
- 断点续跑
- 失败任务重试
- JSON Schema校验
- 同Family ID抽取缓存
- 稳定Technology ID
- 技术归并审计
- 不覆盖D1/E3原文件

---

# 12. 执行成本控制

当前可使用本地Qwen3-Coder 30B，通过已授权的Ollama API调用。

不要默认每族只需一次LLM调用。

必须记录：

- 实际处理Family数
- 平均输入/输出token
- 每族技术贡献数量
- 抽取失败率
- JSON校验失败率
- 重试次数
- 技术归并调用次数
- 实际吞吐与运行耗时

开始时先用30族进行Prompt与Schema测试。

成功后进行100族试运行，再扩展到Cluster 139全部384族。

对照Cluster按去重后的Family ID增量处理。

不允许为了填满字段让模型编造证据。

如果本地LLM处理成本过高，可提出批处理或两级抽取方案，但不能牺牲可追溯性或将未处理记录标记为已处理。

---

# 13. 验收Gate

## Gate 1：逐专利抽取有效

- Schema有效
- 证据可核对
- 可处理单技术和多技术专利
- 信息不足可以弃判
- 原始文本保留

## Gate 2：Cluster 139完整技术抽取

- 384族全部尝试
- 已处理与失败数明确
- 技术贡献统计完整
- 技术概念归并完成
- 真实案例可人工核验

## Gate 3：跨Cluster技术归并

- 完成指定对照Cluster
- 消除重复Family ID抽取
- 允许跨Cluster共用技术节点
- 不同技术机制得到合理区分

## Gate 4：历史事后验证

- 抽取结果冻结
- 与45个历史族核对
- Recipe和Equipment分别统计
- 失败原因可追踪

## Gate 5：知识库原型交付

- Excel能直接阅读
- 原始证据完整
- 可从Technology定位到Patent
- 可从Patent定位到Technology
- 报告明确说明当前知识库不是全库穷尽结果

---

# 14. 最终必须回答的问题

1. Cluster 139的384族，实际包含多少不同的技术机制？
2. 哪些具体技术能够被LLM可靠识别？
3. 一个Cluster内部是否出现明显不同的技术路线？
4. 不同Cluster是否存在相同技术路线？
5. 逐专利抽取是否明显优于直接Cluster命名？
6. 设备、工艺、材料三种类型的技术是否能被区分？
7. 对Title/Abstract信息不足的专利，系统如何避免伪造结论？
8. 历史45族的技术机制实际恢复情况如何？
9. 新方法在其他随机技术群上是否仍然有效？
10. 下一阶段能否扩展到238,541族？主要成本和质量瓶颈是什么？

---

# 15. 执行要求

现在直接执行A5.5-D2。

先定位D1与E3的现有数据、验证Cluster成员和文本映射，然后开始小批量技术贡献抽取。

按照30族 → 100族 → 384族 → 对照Cluster的顺序扩大规模。

本轮不重新生成全库Embedding、不重新跑KMeans/HDBSCAN/Leiden，不引入引用或IPC/CPC网络，也不修改原E3/E4/D1结果。

**最重要的交付不是更多Cluster，而是一套能够从专利摘要独立识别具体技术手段、保留证据、跨聚类归并的技术知识库原型。**