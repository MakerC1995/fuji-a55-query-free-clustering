"""Render the final research report from executed results and explicit source reviews."""
from experiment import *
from analyze import allruns
import pandas as pd
def table(rows,columns):
 def fmt(v):
  if v is None:return 'n.a.'
  if isinstance(v,float):return f'{v:.3f}'
  return str(v).replace('|','/').replace('\n',' ')
 return '\n'.join(['|'+'|'.join(label for key,label in columns)+'|','|'+'|'.join('---' for _ in columns)+'|']+['|'+'|'.join(fmt(r.get(key)) for key,label in columns)+'|' for r in rows])
def link(name):return f'[{name}]({W/name})'
def main():
 runs=allruns();by={r['run_id']:r for r in runs}
 prim=json.loads((W/'comparison/primary_runs.json').read_text())
 pairs=pd.read_csv(W/'comparison/partition_comparison.csv')
 hist=pd.read_csv(W/'comparison/historical_summary.csv')
 mix=pd.read_csv(W/'comparison/historical_cluster_mixing.csv')
 qa=json.loads((W/'evidence/quote_audit_summary.json').read_text())
 catalog=json.loads((W/'evidence/catalog_assembly.json').read_text())
 audit=json.loads((W/'evidence/input_audit.json').read_text())
 pca=pd.read_csv(W/'comparison/pca_neighbor_retention.csv')
 models={m:json.loads((W/f'leiden/{m}_knn.json').read_text()) for m in ['bge','qwen']}
 def pair(a,b):
  row=pairs[((pairs.run_a==a)&(pairs.run_b==b))|((pairs.run_a==b)&(pairs.run_b==a))]
  assert len(row)==1;return row.iloc[0].to_dict()
 stats=[]
 for rid in prim:
  r=by[rid]
  stats.append(dict(run=rid,n=r['n'],clusters=r['clusters'],singles=r['singleton_clusters'],ge3=r['clusters_ge3'],noise=f"{r['noise_fraction']:.1%}",median=r['size_median'],maximum=r['size_max']))
 stats_table=table(stats,[('run','实验'),('n','族数'),('clusters','非空群'),('singles','单点'),('ge3','≥3族群'),('noise','Noise'),('median','中位规模'),('maximum','最大规模')])
 stability=[]
 for a,b in [('bge_k300_s42','bge_k300_s137'),('qwen_k300_s42','qwen_k300_s137'),('bge_k30_mutual_r1.0_s42','bge_k30_mutual_r1.0_s137'),('bge_k30_sym_r1.0_s42','bge_k30_sym_r1.0_s137'),('qwen_k30_sym_r1.0_s42','qwen_k30_sym_r1.0_s137'),('bge_k300_s42','qwen_k300_s42'),('bge_k30_mutual_r1.0_s42','qwen_k30_mutual_r1.0_s42'),('bge_k30_sym_r1.0_s42','qwen_k30_sym_r1.0_s42')]:
  p=pair(a,b);stability.append(dict(a=a,b=b,ari=p['ari_noise_as_one_label'],nmi=p['nmi_noise_as_one_label']))
 stable_table=table(stability,[('a','分区A'),('b','分区B'),('ari','ARI'),('nmi','NMI')])
 histories=hist[(hist.tree=='All') & (hist.run_id.map(lambda rid:by[rid]['n'])==N)].to_dict('records')
 hist_table=table(histories,[('run_id','实验'),('known_unique_families','已知观察族'),('noise','Noise族'),('nonnoise_clusters','非Noise群数'),('largest_cluster_core_families','单群最多已知族'),('first_pass_named_core_clusters','纳入首轮命名的相关群')])
 blind=[]
 for p in sorted((W/'technology_catalog/posthoc_blind').glob('*.json')):
  if any(x in p.name for x in ['.input.','.raw.','.error.']):continue
  r=json.loads(p.read_text());blind.append(dict(run=r['run_id'],cluster=r['cluster_id'],size=r['cluster_size'],names=' / '.join(t.get('name','') for t in r['analysis']['themes']),objects=' / '.join(t.get('object','') for t in r['analysis']['themes']),notes=r['analysis'].get('heterogeneity','')))
 blind_table=table(blind,[('run','实验'),('cluster','群ID'),('size','群大小'),('names','盲命名'),('objects','模型提取对象')])
 hc=json.loads((W/'evidence/historical_check.json').read_text())
 history_text=f"""# 历史 Sputter 树事后检查

首轮70群命名与标签/参数冻结之后，才读取E4历史输入。仅复用其已核验观察成员的Simple Family映射，未用历史名称、引用、IPC/CPC或核心族改变任何分组。来源快照和SHA256见 {link('evidence/historical_check.json')}。

64个历史节点中62个有观察族，合计45个唯一族：Recipe 27、Equipment 18。H04/H16仍无已解析族，不能把它们虚构为两个Noise或库外族。H06/H12的候选成员身份已有本地族证据，但与历史代表的法律同族关系仍未定，单独保留。45/45在本次向量底座内，是以已观察族为条件分母，不替代64节点的完整覆盖口径，也不确认当前权属。

## 1. 已知族分到哪里

{hist_table}

BGE K=300把27个Recipe观察族分到11群，最大一群8族；Qwen K=300分到2群，其中25族同群。BGE mutual Leiden把27族放入一个4255族的社区；Qwen mutual分为4群。不能从这种算法依赖的集中/分散断言一个模型正确、另一个错误。

BGE mutual的已知Recipe与Equipment落在互不重叠的4个群中，但Equipment有一个已知族是单点。Qwen sym的已知Recipe在2群、Equipment在另2群，观察子集也分开；BGE sym有一个13843族群同时含4个Recipe和1个Equipment观察族。历史标签只覆盖群的一小部分，这些数字不能当成全群语义纯度。

**全库HDBSCAN将45个观察族全部标为Noise。** 50k小参数样本中恰好有9个历史族，它们也全部是Noise，另36个是样本外，不能记成Noise。这直接说明Noise不能作为无关或无价值的删除依据。

## 2. 群内机制是否一致

共群只证明分区位置相同。BGE mutual的Recipe群4255族中只有27个属于本次历史观察集合；其通用中心、随机和边缘代表包含喷墨记录、压电元件和声学换能器，模型未找到统一手段。设备相关群也混入半导体工艺、电子设备和微结构制备。它们更像对象/应用区域，不能直接等同历史子路线。

K=800的190族群223包含15个Recipe观察族；57族群475包含8个。细粒度确实更容易显露压电对象，但群475同时出现Nb-PZT/界面层、氧18、Pb计量控制和驱动/退火方案，仍然不是一条配方。更大的K不保证按技术机制细分，且不同K结果并非嵌套树。

## 3. 不提供历史名称时能否命名

首轮Query-Free预算里有3个与观察族相交的BGE K=300群；其他主要相关群未被首轮通用选样覆盖。不能把未进入预算等同模型识别失败。

随后单独做8群事后盲测：历史成员只用于选择已有群，群内代表仍按通用中心/随机/边缘/多样性选取，没有强行插入核心族，没有把历史路线名或核心标记给模型。这8群是**事后验证，不能算首轮自然发现**；与首轮合计78个不同群。

{blind_table}

前6个宽泛群均未形成可核验的具名共同技术。两个K=800细群让模型识别出压电元件、钙钛矿和可靠性目标；57族群还给出“压电特性提高与长期可靠性”名称。但是其3份引文分别支持氧18、Nb组成和Pb比例，不能把氧同位体策略套给三族。这是对象/目标层识别，尚未独立复原历史Nb donor/plasma窗口、分段成膜或设备屏蔽等具体路线。代表只抽少量专利，因此未命名也不能推断模型不认识这些技术。

## 4. 可复核文件

- {link('comparison/historical_assignments.csv')}：45族逐实验位置、Noise/样本外、原首轮名称和代表关系状态。
- {link('comparison/historical_cluster_mixing.csv')}：Recipe/Equipment观察族在群中的计数。
- {link('comparison/historical_unresolved_nodes.csv')}：未解析节点保留。
- {link('technology_catalog/posthoc_blind_panels.json')} 与 posthoc_blind/：实际盲测原文、输入和原始输出。
- {link('manifests/historical/historical_sputter_tree_recipe_equipment.md')}：冻结后才复制的历史树。

没有计算全局技术发现Recall，没有新增采集、改写法律族、移动成员或修订首轮命名。
"""
 (W/'HISTORICAL_TREE_CHECK.md').write_text(history_text)
 comparison=f"""# 三种算法的实测比较

## 覆盖、规模与粒度

{stats_table}

K=800的BGE实际非空群为796，不能写成800。mutual Leiden的7120/5173个群中分别有6438/4575个单点；实际至少3族群为238/273。sym Leiden的32/41群没有单点，但群体较大。HDBSCAN的146群只覆盖11.9%全库，88.1%是保留的Noise。

## 稳定性与模型差异

{stable_table}

K=300的同模型双种子ARI约0.46–0.49；BGE sym Leiden约0.84、Qwen约0.76。较稳定不等于技术机制更纯。跨模型K=300 ARI约0.351，平均Top30邻居重合45.1%，不能仅依赖整体一致性判断优劣。

同为K=300，语言NMI：BGE 0.218、Qwen 0.166；sym Leiden分别0.338与0.119。Qwen在这两组设置的语言关联较弱，这是当前实验观察，不是引用过去Top20检索表现预设质量。NMI仍受群数、长度和语料分布影响，不是语言偏差因果估计。

## 方法各有什么用

|方法|实测可用之处|实测限制|
|---|---|---|
|MiniBatchKMeans|快速全覆盖；K=300提供几百族到千族的检查单元，K=800可显露较细对象群|非严格球面KMeans；种子稳定性一般；粒度不嵌套；仍混合材料、结构、工艺和功能|
|HDBSCAN + PCA|能保留10–30族密度小群，50k样本的(10,5)有105个10–30族群|30维仅保留约36%–40%原始Top20邻居；参数/规模敏感；全库45个历史观察族全为Noise；持久性全1不能作稳定证据|
|Leiden sym|全覆盖、无孤点，适合构建领域/对象的上层导航；能分辨部分历史类别|32/41群很粗；语种/长度和语义Hub有影响；一个群通常混多种机制|
|Leiden mutual|保留小型非平凡群；发现5族飞迹提取、17族水耕栽培系统等可调查群|大量孤点/双点；社区数不能当技术数；一些大群仍很宽泛|

HDBSCAN非Noise Silhouette约0.293，高于K=300约0.033，但覆盖仅11.9%，不能据此判胜。群内余弦在两模型中也不宜直接横比。完整指标包括群内/群间、Noise、单点、小群、语言/长度关联和不同种子，见工作簿。

## 下一阶段建议

采用**Leiden分层作为导航主线**：sym图建立粗层，再对大群重新构建局部kNN；mutual图保留小群线索；MiniBatchKMeans保留为独立粒度对照。HDBSCAN用于密度核心和Noise审计，不作为全库剔除器。两个最大BGE社区15185/11963族已分别细分16/15群，局部ANN Recall@15约99.9%；原文代表在 {link('comparison/local_cluster_representatives.csv')}，这些子群未被冒充已验证技术路线。

模型暂保留BGE/Qwen双视图，不据有限语义抽样宣布唯一赢家。下一步需在专利级抽取对象/问题/手段/效果，用证据关系建立多标签目录；对一个群给出一个路线名不足以完成知识库。引用与IPC/CPC值得作为独立后验对照，尚无证据表明必须立即融合进主图。先针对混机制、短文本和语言分割的实际案例验证其增益。
"""
 (W/'ALGORITHM_COMPARISON.md').write_text(comparison)
 source_cases=[
 ('飞迹提取', 'bge_k30_mutual_r1.0_s42__c134',['google:72642920','google:72643036','google:75157643']),
 ('水耕系统', 'qwen_k30_mutual_r1.0_s42__c136',['google:97139098','google:99972696','google:97138839'])]
 docs=[]
 c=db();c.row_factory=sqlite3.Row
 for case,pid,fids in source_cases:
  for fid in fids:
   d=dict(c.execute('select family_id,pub_id,title,abstract from docs where family_id=?',(fid,)).fetchone());docs.append(dict(case=case,panel=pid,**d))
 pd.DataFrame(docs).to_csv(W/'comparison/rare_case_patents.csv',index=False)
 case_table=table([dict(case=d['case'],fid=d['family_id'],pub=d['pub_id'],title=d['title']) for d in docs],[('case','案例'),('fid','Family ID'),('pub','代表公开号'),('title','原始标题')])
 pcatable=table([dict(model=r.model,d=r.pca_dimensions,overlap=f'{r.mean_original_neighbor_overlap:.1%}') for r in pca.itertuples()],[('model','模型'),('d','PCA维数'),('overlap','原始Top20邻居保留')])
 ann_table=table([dict(model=m,ef=v['efSearch'],r15=f"{v['recall_at_k']['15']:.1%}",r30=f"{v['recall_at_k']['30']:.1%}",r50=f"{v['recall_at_k']['50']:.1%}") for m,v in models.items()],[('model','模型'),('ef','efSearch'),('r15','Recall@15'),('r30','Recall@30'),('r50','Recall@50')])
 report=f"""# A5.5-D1｜FUJIFILM全库 Query-Free 聚类与初步技术目录

日期：2026-10-25。输入为已完成的238,541族BGE-M3与Qwen3-Embedding-0.6B向量；没有重编码、关键词筛选、引用/IPC特征、历史核心种子或人工移动成员。全部工作与输出位于核验UUID的SSD独立目录。56个主实验已实际完成，另有两个大型社区的局部细分。

**主要结论：全库存在可用的领域、对象、材料和部分方法族结构，但Cluster不能直接当技术路线。** sym Leiden适合上层导航，mutual能保留有价值的小群，同时产生大量孤点。HDBSCAN能找密度小群，却把全部45个历史观察族标为Noise。LLM能给出初步主题，但“引文逐字存在”仍不足以保证共通技术手段成立。

## Q1 三种算法形成多少群

以下为主要设置；56次完整参数与种子结果在 {link('comparison/run_statistics.csv')} 及统计工作簿。

{stats_table}

这些是特定模型、输入空间和参数下的分区数，没有唯一“天然技术数量”。K值、图规则、分辨率、PCA和密度阈值都会改变结果。特别是BGE mutual的7120群中6438是单点，不能称作7120条路线。K=800仅796个非空群。HDBSCAN的全库146群与50k样本155群有不同分母，不能混为全库结果。

## Q2 形成的是哪一层技术

实际结构是混合的：

- K=300 Cluster 18（212族）同时含感射线树脂、嵌段共聚物自组织和处理液。材料体系、图案形成方法与辅助化学品并存。
- BGE sym Cluster 16（5294族）包含导光读取结构、图像显示过程、接收方列表及其他对象，属于应用/对象区域。
- Qwen K=300 Cluster 228（29族）围绕黑白热显影感光材料，但粒子外延、位错、乳胶、银盐和多层配方仍是不同手段。
- BGE mutual Cluster 134（5族）已接近“利用断层图像提取荷电粒子飞迹”的方法族；其内部也有中心定位、端部定位和多图选择差别。

15条具名候选均增加了“证据支持层级”和“共同手段核查说明”，见技术工作簿与 {link('TECHNOLOGY_CATALOG.md')}。不能把同一材料或同一应用当成同一工艺。

## Q3 哪种更容易分出具体手段

在本轮实际案例中，**Leiden非平凡小群和局部细分更适合继续追查方法族**，但尚不能据有限、非均匀语义抽样宣布全库的绝对赢家。5族飞迹提取是正例；17族水耕系统仍包含不同子手段。HDBSCAN的92族电荷传输群和323族纤维素酰化物膜群，主要是器件/材料体系，并非单一机制。

细粒度K=800的57族压电群能让盲测模型识别压电对象与可靠性目标，却把氧18、Nb组成和Pb比例等不同策略合在一起。它说明更细能改善对象聚焦，不能证明一个群就是一条Recipe。此例来自事后检查，未计入首轮自然发现。

## Q4 哪种对小众技术有帮助

本次最清楚的两个可调查小群来自mutual Leiden：

1. **5族断层图像/荷电粒子飞迹提取**：三份原文分别涉及最大对比度层定位、按黑点数估计记录层端部、从多张断层图选择含潜像黑点的两图。它们支持一个具体方法族，尚不是完全相同算法。
2. **17族果菜水耕栽培与光照系统**：原文涉及湛液式水耕、人工光与反射结构、水耕架等。它是本次Query-Free选样显露的目录线索，和喷头关系分开判定，未因应用不同而删除。

{case_table}

这些是值得进一步阅读的真实专利群，不是“新发明”或趋势已证实的结论。完整摘要见 {link('comparison/rare_case_patents.csv')}。

HDBSCAN 50k样本的(10,5)配置有105个10–30族群；本轮未证明这些小群都是独立技术。稀有区域清单有2329条记录，类型、实验分母、双模型近邻和数据质量标记分开保存。小群、Noise、标题缺失与重复文本不能混成“无关”。

## Q5 Embedding模型是否影响结构

影响明显：全库Top30近邻平均重合45.1%；同K=300跨模型ARI 0.351、NMI 0.685。BGE/Qwen sym在相同k=30、resolution=1时分别32/41群。

{stable_table}

历史Recipe观察族在Qwen K=300中25/27同群，而BGE K=300分成11群；换用mutual Leiden，BGE又把27族集中一群，Qwen分成4群。相对集中程度取决于模型和算法，不能据一个交集数字断言语义质量。

同K=300语言NMI为BGE 0.218、Qwen 0.166；sym为0.338与0.119。Qwen在这些设置的语言关联较弱，但NMI受群数、文本长度和语料分布影响。两模型原始余弦尺度也不可直接排名。未沿用过去Top20检索结论预设优劣。

## Q6 LLM能否可靠命名

本地qwen3-coder:30b（Q4_K_M，digest 06c1097e…）实际完成70群的Query-Free首轮及独立喷头关系第二轮，输入/原始输出均保存。首轮112次主题尝试中，模型原本给出48个名称、64次主动待定；每主题至少3族可核引文的保守门槛保留15条具名，另外33个原名转为待定，总待定97条。原名没有删除，**这不是命名准确率或技术发现Recall**。

296条原始引文中，273条在实际发送片段的声明字段逐字存在（92.2%）；18条无逐字匹配，2条字段错配，2条为空，1条虽在完整源文存在却不在发送片段。所有计数按实际输入hash复核，见 {link('evidence/quote_audit_summary.json')}。

更重要的是语义：

- 正确保留不确定：13族“開閉式画像形成装置”代表只有标题，模型没有编造具体手段。
- 层级可用：感射线树脂、光热成像材料等名称可作为材料目录，但不能把不同配方合并。
- 引文真、机制不成立：BGE sym Cluster 0的颜色校正候选，把真实的颜色校正摘要与真实的A/D控制、锁相环标题当作共同证据。三段都存在，却不能支持同一颜色校正机制。
- 部分支持：嵌段共聚物候选有两份自组织证据，第三份google:52468210完整摘要是电子束/EUV曝光与有机溶剂显影，不能作为嵌段共聚物的第三份支持。

因此LLM可辅助提出主题和提示异质性，**不能自动把Cluster转为可靠技术路线**。已对15条具名候选逐条阅读证据并标注支持层级/风险；这是Codex证据抽查，不是人工Gold。模型自评、逐字核查和共同机制核查分别呈现。第二阶段喷头关系属于独立模型推断，未唯一匹配或首轮待定者不输出确定关联。

## Q7 Sputter Recipe与设备路线在空间里如何分布

45个E4观察族全部在输入底座。BGE mutual使27个Recipe族集中一个4255族群，Equipment在另外3群；Qwen sym使Recipe在2群、Equipment在另2群。它们对这份观察子集有区分能力，但不能据此推断全群纯度或全部路线正确。

**HDBSCAN全库45族全部Noise。** 这是一条明确反例：Noise不等于无技术价值。H04/H16仍无已解析族；H06/H12仍保留“候选成员已核验、历史代表关系未定”状态，未伪造映射。

首轮命名后才读取历史树，并另做8群不提示历史名称的事后盲测。宽泛6群没有形成可核验共同名称；细K=800能识别压电对象和可靠性目标，但仍混合具体策略。事后选群不能算首轮Query-Free发现。

详见 {link('HISTORICAL_TREE_CHECK.md')}，其中分开报告：族在群中、群有共同机制、模型识别路线三种结论。

## Q8 是否发现值得调查的潜在技术

有真实目录线索：5族飞迹提取方法族和17族水耕系统，以及光热成像材料、感射线树脂等材料体系。前两者给出小群与原文证据，说明全库探索可以显露预先未输入的主题。此处“值得调查”指有可读证据和明确对象/子手段，未做新颖性、商业价值或趋势判断，不为达到数量把15个名称称作15条新路线。

## Q9 下一阶段主算法

建议采用**Leiden分层导航 + mutual小群补充**，保留MiniBatchKMeans独立粒度对照。sym作为领域/对象根层；在大型社区内部重建局部图，再看实际子机制，不把调整全局resolution当作唯一细分方式。两个最大BGE群15185/11963族已局部细分16/15群，局部Recall@15约99.9%，155条中心/边缘/随机原文代表见 {link('comparison/local_cluster_representatives.csv')}。这些局部子群未逐一冒充已命名路线。

HDBSCAN作为密度核心/Noise审计工具，保留所有Noise；不作全库入口删除器。模型继续保留BGE/Qwen两视图，当前语义抽样不足以锁定唯一模型。技术知识库下一步应建立专利—技术候选多标签、对象—问题—手段—效果及逐条证据关系，而不是Cluster ID直接当Technology ID。

## Q10 是否需要引用与IPC/CPC

值得做独立后验对照，但没有证据表明必须立刻融合。实际不足是语言/长度关联、仅标题、材料/功能混机制、稀有族被密度法排为Noise，以及单条代表文本不能完整表达全族。引用或IPC可能补充关系，也可能只强化领域/时间偏差；应围绕这些具体案例验证增益。当前已完成实验没有把它们作为特征。

## 方法和资源限制

原始代表文本保留229994条标题+摘要、8537条仅标题、10条仅摘要；完全重复代表文本1146组、相同摘要370组均未删除或合并法律族。族内其他成员/语种没有在本轮重新编码，60个原底座不可编码族不进入238541分母。

PCA保留30/50维方差约40.9%/50.4%（BGE），不能视作同等语义保留：

{pcatable}

近似图另有128固定查询的精确对照：

{ann_table}

这里的Recall是近邻索引指标，不是技术发现Recall。没有构造全库N×N密集矩阵。二维图只展示固定分层样本，不定义原始距离真值：

![固定样本三算法PCA展示]({W/'figures/bge_pca_display.png'})

![全库HDBSCAN群体大小]({W/'figures/bge_n238541_pca30_c30_s15_sizes.png'})

主机实际16GiB Mac，聚类用CPU；重任务开始时串行，按实测内存允许至多两个低内存独立进程有界重叠。全库HDBSCAN核心过程约19.4分钟，观测峰值约0.49GiB；最大图阶段观测峰值约2.78GiB。PCA、索引构建和共享图预处理另计，不能把单次partition耗时当全部建图成本。HDBSCAN的146个持久性全为1，已查到119重合PCA向量与实现的无穷密度回退分支，不作“完美稳定”证据。

算法版本、具体预处理差异、欧氏MiniBatchKMeans与严格球面方法的区别、抽样和指标分母见 {link('reports/METHODS.md')}。没有运行新BQ/EPO/全量编码，没有改服务器配置、原始库、向量或人工标签。

## 交付与复核

- {link('CLUSTER_ASSIGNMENTS.parquet')}：11044345行、56实验；45个实验为全库，11个为固定样本。每行族ID、行号、标签和分母已全部回读对照冻结数组，原输入与标签保持不变。
- 统计工作簿：56个实验、181组一致性比较、8张图结构诊断。
- 聚类工作簿：主比较分区14163群、533条代表原文；最大20群实际ID另在 {link('comparison/largest20_clusters.csv')}。
- 技术工作簿：112次主题尝试，15条具名/97条待定；273条可核原文引用；模型原名、支持层级与共同手段说明并列。
- 稀有审查工作簿：2329条小群、Noise、边界与模型分歧记录，数据质量标记独立保留。
- {link('ALGORITHM_COMPARISON.md')}、{link('HISTORICAL_TREE_CHECK.md')}、{link('TECHNOLOGY_CATALOG.md')}。
- figures/：12幅实际静态图；scripts/、configs/requirements.lock.txt：复现代码与25个独立依赖版本锁；EXPERIMENT_MANIFEST.json：输入、模型、代码、参数、种子和交付hash。
- 四份Excel保存在 {W/'outputs/01a171fb-0dd6-7792-b36b-80e200aba942'}。它们是实验快照，修改表内数值不会自动重跑聚类。

所有结果来自实际执行。阶段Gate和检查记录在evidence/；目录是初步技术候选，不是最终技术树。主要误差来自粒度混合、代表文本、降维与模型归纳，已以真实失败案例保留。
"""
 (W/'REPORT.md').write_text(report)
 # A short independent source review reference for the workbook annotations.
 sem=json.loads((W/'evidence/semantic_source_review.json').read_text())
 (W/'reports/SEMANTIC_REVIEW.md').write_text('# 15条具名候选的证据层级抽查\n\nCodex对实际提供的原文与引文逐条阅读；不作为人工Gold或语义准确率测量，没有修改首轮模型文件或聚类。\n\n'+table(sem['rows'],[('panel_id','证据组'),('theme_index','主题索引'),('supported_level','支持层级'),('mechanism_notes','共同手段核查')])+'\n')
 print('REPORT.md, ALGORITHM_COMPARISON.md and HISTORICAL_TREE_CHECK.md written')
if __name__=='__main__':main()
