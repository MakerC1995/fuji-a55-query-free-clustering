# 抽取质量

范围1117族，状态{'VALID': 1114, 'FAILED_VALIDATION': 3}，贡献/弃判记录1115条（明确手段贡献975条），明确手段标签族974个。逐字/坐标通过4299条，只代表结构与复制完整性。

固定80族有源文预读与逐族AI对照记录；人审栏留空，没有独立Gold，不提供全样本语义准确率。

## 已证实的错误与边界

- 初期将明确结构/工艺错误弃判；保留全部校准成本。
- HTML/长公式反复抄写造成改写、重复与截断；改为片段ID后由程序复制原句，但引用相关性仍需语义审计。
- 40581936漏晶格体积V；角度被标COUNT、压电系数被标组成比、导热率被标TIME，已保留原始记录及源文修订。
- 首批将Ca含量范围与厚度方向Ca梯度仅因共同材料判Same，源文复核后保留Related；原始判断与修订均保留。不同Family ID的完全相同摘要属于重复文本证据，不能当独立跨群发现。
- 变量V1、T0和图号不等于定量值；需核对物理量与单位，不能仅查数字。
- SEM/XPS观察条件不可冒充制造步骤；材料表征限定不可自动写成制程。
- 97217328的柱径差≤10%与97218156的>10%首轮也被误判Same；第二轮按不兼容限定改判Distinct，最终分组隔离见CONDITION_CONTRAST_CHECK.json。
- 初始384族全部单贡献；49512008经source-only复核接受两项拆分，58557302二次输出改写关系被拒收。没有独立量化多贡献Recall。
- 全半角、Unicode负号、日文割/百分数和千分符存在确定性表示等价；源文引句始终逐字保存，单位仍须核查。
- 无图外观声明不能补几何形状，缺失公式不能凭历史或专利号补全。

当前889条贡献有字段证据缺口，242个参数提议被留在拒收记录，47条含助手修订。不能用修订后结果冒充原始模型准确率。

## 归并诊断

当前有效贡献的原第二轮Same检查状态（包含后来又经助手撤销的判断）：{'DOWNGRADED_FROM_SAME': 116, 'NO_SECOND_SAME_CHECK': 674, 'DUAL_SAME': 67}。固定随机抽查十对原始Same提议，并诊断六对当时已双轮确认的Same。源文诊断指出共同材料、对象和上位结构可能掩盖具体办法；其中仍残留的3对Same在命名前由助手按原文撤销，记录及原始响应均保留。该小样本是AI诊断，不是独立人工精确率。逐字相同摘要即使Family ID不同，也不当两份独立佐证。

## 归并边界

向量只提候选，Same由双侧源文LLM判断，并另作一次保守源文复核；两轮同意才可支持归并。两轮均是同一本地模型，不是独立人类Gold。小组要求全对Same，大组双锚点加冲突否决。未比较不当Uncertain。对象/问题域组织与机制范围继承分开，循环继承暂缓；关系均是可追溯候选。有限近邻不能保证找齐同义技术。

## 命名及源文修订

19个命名记录由原响应离线重校验恢复，可选备注null只转为空字符串，原始在线失败状态保留；无新模型调用。9条命名源文修订及4处后续贡献修订有单独审计，最终另区分2对凸起结构相关的来源关系。

## 成本

| 请求类型 | 请求数 | 已知输入token回执数 | 同键追加请求 | 输入token | 输出token | 均输入 | 均输出 | 原契约失败 | API拒绝 | 网络失败 | 区间并集小时 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| d1_baseline | 11 | 11 | 0 | 23735 | 9979 | 2157.7 | 907.2 | 0 | 0 | 0 | 0.06 |
| embed | 44 | 44 | 0 | 198639 | 0 | 4514.5 | 0 | 0 | 0 | 0 | 0.011 |
| extract | 1191 | 1188 | 144 | 2420381 | 704798 | 2037.4 | 593.3 | 169 | 2 | 0 | 3.717 |
| hierarchy | 69 | 69 | 2 | 245973 | 39731 | 3564.8 | 575.8 | 3 | 0 | 0 | 0.247 |
| hierarchy_catalog | 1 | 1 | 0 | 3513 | 1000 | 3513 | 1000 | 0 | 0 | 0 | 0.006 |
| history | 23 | 23 | 0 | 66621 | 9015 | 2896.6 | 392.0 | 0 | 0 | 0 | 0.061 |
| name | 451 | 448 | 33 | 1116176 | 168571 | 2491.5 | 376.3 | 48 | 0 | 3 | 1.336 |
| pair | 334 | 333 | 9 | 1620357 | 133570 | 4865.9 | 401.1 | 8 | 0 | 1 | 1.254 |
| pair_confirm | 66 | 66 | 0 | 327412 | 37708 | 4960.8 | 571.3 | 0 | 0 | 0 | 0.292 |
| refine_extract | 9 | 9 | 0 | 19297 | 4922 | 2144.1 | 546.9 | 0 | 0 | 0 | 0.034 |
| relevance | 1065 | 1059 | 357 | 2691875 | 518537 | 2541.9 | 489.6 | 451 | 0 | 3 | 3.619 |

JSON语法统计：{"d1_baseline":{"json_parse_failures":0,"responses":11,"truncated":0},"extract":{"json_parse_failures":16,"responses":1189,"truncated":14},"hierarchy":{"json_parse_failures":0,"responses":69,"truncated":0},"hierarchy_catalog":{"json_parse_failures":0,"responses":1,"truncated":0},"history":{"json_parse_failures":0,"responses":23,"truncated":0},"name":{"json_parse_failures":0,"responses":448,"truncated":0},"pair":{"json_parse_failures":0,"responses":333,"truncated":0},"pair_confirm":{"json_parse_failures":0,"responses":66,"truncated":0},"refine_extract":{"json_parse_failures":0,"responses":9,"truncated":0},"relevance":{"json_parse_failures":0,"responses":1059,"truncated":0}}

助手最终对读14个相关性案例，判断及原始模型响应分别保存；其中早先未通过本地契约的5项，经真实原文审查采用助手判断，明确标为ASSISTANT而非本地模型成功。字符规则漏识别drop/droplet、delivering head及液体喷出等真实措辞导致过误拒收，修复与回读另存；契约失败数不能直接解释成模型语义错误率。

## 相关性复核接口失败与修复

原双节点复核230项，仅54项整批通过；其余有目标字段缺失或源片段编号错误。按同一逐项契约离线恢复57项，未新增模型调用；失败批次状态未改为成功。剩余采用单概念、全局X源片段枚举的独立协议补跑；缓存、Prompt/Schema与采用映射另存，原始错误和成本保留。格式通过仍不是工程关联判断准确。

主人工审核队列198族，包含固定80族、已知语义疑点、处理失败与独立事后探针。全量932族的引用/参数标记保存在ALL_REVIEW_FLAGS.parquet，未进入主审核页不代表问题已解决。

## 冻结后相关性与命名疑点

定向相关性复核235个节点，类别修订90个；样本偏向可疑与正向案例，不估计总体准确率。保留首轮与复核请求、逐字S源片段。

| Family ID | 已知冻结定义疑点 | 处理 |
|---|---|---|
| google:39794835 | 冻结名称“脉冲电场辅助溅射极化反向工艺”将源文 alternating-current electric field 概括为脉冲，摘要不足以支持脉冲波形；贡献正文使用交流电场，应以原文和贡献限定为准。 | 记录待人工修订。核心已冻结且历史已揭盲，不回写核心名称以避免事后污染。 |
| google:34468469 | 冻结贡献将嵌件注塑、排出部斜肋和盖口厚度三个结构/工艺限定合在一条，尚未证明已可靠拆成原子贡献。 | 保留冻结原记录，加入人工拆分复核；不以现有候选数估计真实机制总量。 |
| google:45351863 | 冻结mechanism中的Zr/Ti下标写成Zr1−x/Tix，原文为Zrx/Ti1−x；且原始机器译文“calcium titanium ore/calcium titanate”不可当作含Ca材料事实。 | 冻结后源文诊断，保留核心原版本并加入人工修订队列；不依历史参照回写。 |
| google:43903909 | 冻结mechanism对晶界的否定作用域表述歧义：源文排除层叠产生且基本平行基板的晶界，不能泛化为所有晶界均不存在。 | 冻结后源文诊断，保留核心原版本并加入人工修订队列；不依历史参照回写。 |
| google:41541242 | 冻结名“多孔陶瓷模压成型”可能让人误读为压制成型；原文仅披露陶瓷模具、晶种、填充前驱体、烧成及热处理单晶化，没有施压步骤。 | 保留冻结名称与贡献，添加人工命名复核，报告示例使用原文能支持的措辞。 |
| google:16586379 | 冻结名“振动频率自适应调节”可能过度暗示自动反馈；摘要披露电磁铁吸引环形件增重而改共振频率，没有说明传感器或闭环自适应控制。 | 保留冻结名称与贡献，添加人工命名复核，报告示例使用原文能支持的措辞。 |

其他冻结定义疑点：[{"issue":"名称中虽含'actuator'，但未明确指向喷墨头或液滴喷射领域，存在概念泛化可能，但不影响冻结判断。","technology_id":"T_d81c027a750e0df813c5"},{"issue":"名称中虽含‘piezoelectric laminate’和‘piezoelectric element’，但未明确指出其为喷墨头或与液滴喷射相关。","technology_id":"T_e894f4ed1824cf8a0374"},{"issue":"名称可能过度概括，但不影响冻结机制分类判断。原机制未明确涉及喷墨头或液滴喷射领域。","technology_id":"T_9683cd67a4c91526d3f9"},{"issue":"名称可能有过度概括，但不影响冻结结果。","technology_id":"T_cc6208d3e1b5615178b1"},{"issue":"标题中使用了'圧電体膜とその製造方法、圧電素子、及び液体吐出装置'，其中'液体吐出装置'可理解为喷墨头的一种形式，但未明确说明是喷墨头本身。然而，结合摘要内容，该技术确实适用于液体喷射装置，因此可视为直接适用。","technology_id":"T_7fe318a89a322cbb64aa"},{"issue":"名称中虽含'Vacuum deposition apparatus'，但未体现喷墨头相关术语，可能过度概括，但不影响冻结概念判断。","technology_id":"T_1e5f166c3c55f7576450"},{"issue":"名称中‘基于许容因子控制的钙钛矿氧化物制造方法’可能过度概括，但不影响其在喷墨头制造中的适用性判断。","technology_id":"T_dfe6eee1ad4f05da82b9"},{"issue":"名称中虽含‘film-forming apparatus’，但未体现与喷墨头的直接关联，存在术语泛化可能，但不影响冻结判断结果。","technology_id":"T_ae978197c2129e31b9fd"},{"issue":"名称中的'物理气相沉积中粒子动能控制方法'可能过度概括，但不影响冻结机制的判断。","technology_id":"T_f43f00a39e754e38c5b3"},{"issue":"机制名称虽含'喷雾沉积法粒子流向调控装置'，但其核心为气溶胶生成和颗粒定向控制，并非传统意义上的喷墨头结构。","technology_id":"T_6a913c0c50ac2134a6ef"},{"issue":"冻结名称“反向极化层叠压电结构”未体现喷墨头特性。","technology_id":"T_b5b6bb9033f21df7cac6"},{"issue":"名称中虽包含'压电元件'，但未明确指出其与喷墨头的直接关系，存在一定的概念模糊性，但不影响冻结判断结果。","technology_id":"T_e92279f9468038b04314"},{"issue":"名称中提及'树脂基板上集成振动膜结构'可能具有一定的通用性，但未体现与喷墨技术的具体关联。","technology_id":"T_3de24ee28ad3fc93f01e"},{"issue":"名称可能过度概括，未明确限定于喷墨头领域。","technology_id":"T_57678c80b159d5d5e16e"},{"issue":"名称中虽包含'堆叠型压电元件'，但该术语在本技术背景中仅指代超声探头中的压电结构，并非喷墨头相关定义。未见明确将此机制用于液滴喷射或喷墨头的描述。因此，冻结定义无误，不构成适用性问题。","technology_id":"T_f9b9242888e23610b3b8"},{"issue":"名称中虽含'液体吐出装置'，但未具体说明为喷墨头或其组件，存在概念模糊风险。","technology_id":"T_d2a99506c7a6a8d1b646"},{"issue":"名称可能有过度概括，但不影响冻结结果判断。","technology_id":"T_8b431f011697ef8f12b1"},{"issue":"名称中虽含有'蒸着装置'等词汇，但未明确指出其为喷墨头或具备喷墨头功能，属于技术术语的通用表达，不影响冻结机制分类结果。","technology_id":"T_5a091606eec65f75ba54"},{"issue":"名称可能具有过度概括性，但不影响冻结结果判断。该结构为PVD腔体中的一部分，与喷墨头无直接关联。","technology_id":"T_3ea553206f6ca0f6b70c"},{"issue":"名称可能有过度概括，但不影响冻结机制的适用性判断。","technology_id":"T_5c717b3f85665ed47f0f"},{"issue":"名称中虽含'バイアス'（bias）一词，但此处指代的是电学偏置而非喷墨头相关术语。","technology_id":"T_4bf7cd8b5b24e026cbc4"},{"issue":"名称可能过度概括为'多级分支气体控制薄膜沉积'，但实际机制与喷墨头无关。此名称未影响冻结判断结果。","technology_id":"T_01142ac2faeae422c82e"},{"issue":"名称中的“层叠结构与平坦化处理的压电装置”可能过于宽泛，但不影响其作为喷墨头适用性的判断。","technology_id":"T_1e718c8075d0e94e473b"},{"issue":"名称可能有过度概括，但不影响冻结结果判断。","technology_id":"T_8f50f97e6b32c86839e2"},{"issue":"The name '钙钛矿氧化物组成调控压电性能' is a general description and may be overly abstract, but does not affect the classification as Direct since the source clearly identifies the application in the context of a liquid delivery head.","technology_id":"T_28aeb9caa90f4826aee2"},{"issue":"名称可能过度概括，但不影响分类结果","technology_id":"T_51301f92b02b51a8c411"},{"issue":"The name 'high potential electrode metal combination structure' may be overly general, but it does not affect the classification as Direct since the mechanism is clearly tied to a piezoelectric element used in a droplet discharge head.","technology_id":"T_4ef31760f416fcb64bcb"},{"issue":"无冻结定义问题。机制名称虽含'蒸着'，但属于PVD领域，非喷墨头相关术语。此为技术领域差异，不构成冻结概念错误。","technology_id":"T_47d45b17dcec88f54d48"},{"issue":"名称可能有过度概括，但不影响冻结机制判断","technology_id":"T_7a0ac01fdcdc6fe5ca15"},{"issue":"The term 'piezoelectric element plate' may be broadly used but in this context it's clearly related to a component of a droplet ejection head.","technology_id":"T_45d8d52e3ad853208601"},{"issue":"名称可能具有一定的概括性，但不影响冻结机制的适用性判断。","technology_id":"T_6fad1b62cf888cb91b3c"},{"issue":"可调间距不应被理解为自动连续调距；原文为规定节距的整数倍关系。","technology_id":"T_f8aa433f1a48634ab46e"},{"issue":"名称可能过度概括，但不影响分类结果","technology_id":"T_522b558e0a02668675dd"},{"issue":"原文未明确说明该工艺是否用于喷墨头制造或喷头组件，仅描述了磷光体层的形成过程。因此，其与喷墨头的直接关系不明确，需通过工程推断确定适用性。","technology_id":"T_fd0a95280c8b6e8abeaa"},{"issue":"The term 'piezoelectric element substrate' may be overly general but is clearly intended for use in a droplet ejection head context based on the title and abstract.","technology_id":"T_65e6fff37afdd2dc92b3"},{"issue":"名称可能过度概括，但不影响冻结判断。","technology_id":"T_d809b945e7528ca592a2"},{"issue":"名称可能过度概括为‘聚合物基压电复合材料的微观区域组成均匀性控制方法’，但实际内容并未涉及喷墨头相关技术。","technology_id":"T_4a88debee2ef5fbb69ad"},{"issue":"名称可能过度概括为'针状晶种定向生长压电膜技术'，但根据上下文，其应用明确指向喷墨打印组件。","technology_id":"T_83e353df871073a02ded"},{"issue":"名称可能过度概括，但不影响分类判断。","technology_id":"T_f6d40352872780e7268b"},{"issue":"名称中包含'气流吹扫与负压集尘结构'，但未体现喷墨头或液滴喷射概念，存在术语过度概括之嫌。但不影响冻结判断结果。","technology_id":"T_9cc3fe5ecf841d0c14fb"},{"issue":"名称可能有过度概括，但不影响冻结结果判断","technology_id":"T_9de4ca215e076e4cd35c"},{"issue":"名称中包含'喷雾系统'和'JPS'可能引起混淆，但实际应用为压电薄膜沉积而非喷墨打印。","technology_id":"T_44cddab0f4fe05ab7884"},{"issue":"名称中虽含'压电体'但未明确指出其用于喷墨技术。","technology_id":"T_c5ad5f52b82ec4677f18"},{"issue":"名称中虽含'piezoelectric body'和'piezoelectric film'，但未明确指出该结构用于喷墨头或液滴喷射系统。","technology_id":"T_95944d9fddf1001dd932"},{"issue":"未发现与喷墨头相关的冻结定义问题。","technology_id":"T_87070720d43c012eb785"},{"issue":"机制名称为'基于压力传感的加压空气引入与控制机制'，虽涉及压力控制，但未体现喷墨头或液滴喷射特性。未见明确喷头适用性描述。","technology_id":"T_7e541f8feb37640801d5"},{"issue":"机制名称虽包含'薄膜沉积方法'，但未明确指向喷墨头相关技术，存在术语概括性问题，但不影响冻结结果判断。","technology_id":"T_407d657c702c49255363"},{"issue":"名称可能有过度概括，但不影响冻结机制的适用性判断。该方法聚焦于压电特性控制而非喷墨头功能实现。","technology_id":"T_0589d9d3df5bf59b4c35"},{"issue":"名称中虽含“压电mems开关”，但未明确说明其适用于喷墨头或液滴喷射。","technology_id":"T_8049f2519a13cf64af0f"},{"issue":"名称中包含'evaporation film'可能与喷墨头中的蒸发沉积概念有语义重叠，但无实质技术关联。","technology_id":"T_bbaf0fd3a76a7bc6bc92"},{"issue":"冻结名称为'电子束加热诱导熔融金属凹坑形成工艺'，与喷墨头适用性无关。","technology_id":"T_890f3a3a00611e948fdc"},{"issue":"冻结名称中提及'压电体膜压缩应力增强振动性能工艺'，但实际应用为超声波处理具中的共振振子结构，与喷墨头无关。","technology_id":"T_f391c06b21c947a8ab0b"},{"issue":"无冻结定义问题。该机制为蒸着装置的一部分，与喷墨头无直接关联。","technology_id":"T_1c549748e7659ee9ff5b"},{"issue":"名称中虽含'滑动压送件'，但未明确指向喷墨头相关结构或功能，存在概念泛化可能。","technology_id":"T_59539b85a066f90acdb2"},{"issue":"名称中的'compression head'可能造成混淆，但根据其实际功能描述，该组件并非喷墨头。此名称在冻结概念中未引起实质性的定义问题，仅属术语使用上的过度概括。因此不构成冻结定义问题。","technology_id":"T_a113811a745006dfd3bb"},{"issue":"名称中虽含'蒸発源'，但未明确涉及喷墨头或液滴喷射结构。","technology_id":"T_17a5f80818e4aa9bc3be"},{"issue":"名称可能过度概括，但不影响冻结机制的适用性判断。","technology_id":"T_210d2ce489dfcbb4f896"},{"issue":"名称可能过度概括为'用于蒸发沉积的带选择性通孔的中间罩结构'，但实际机制并未涉及喷头或液滴喷射功能，仅是物理气相沉积中的防护结构。此名称未误导技术分类，但存在术语使用上的泛化倾向。","technology_id":"T_cbfb7cd8178eb365c3fd"},{"issue":"spot-deposition此处为液体点样，不是真空成膜。","technology_id":"T_b4ad1a0e1405f1936718"},{"issue":"名称可能过度概括，但不影响分类结果。该机制未体现喷头相关特性。","technology_id":"T_b6aedf20a104bfacb785"},{"issue":"The term 'piezoelectric element' may be overly general and not specifically tied to inkjet head applications in the original text, but the mechanism is clearly directed towards manufacturing actuators for such use cases.","technology_id":"T_955834bc37d8efc6b553"},{"issue":"名称中的'等电位围栅均一化成膜工艺'可能过度概括了实际应用范围，但不影响冻结结果。","technology_id":"T_0732142d40e6cc28525b"},{"issue":"名称中虽含'piezoelectric film-equipped substrate and piezoelectric element'，但实际技术内容不涉及喷墨头。","technology_id":"T_29d203591cf0d84d42b0"},{"issue":"名称中虽含'电声转换薄膜'，但未明确说明其是否用于喷墨头或液滴喷射领域，存在概念模糊风险。但不影响当前分类判断。","technology_id":"T_16cfbed33f93cc6a286d"},{"issue":"冻结名称中提及'喷墨头'可能为过度概括，但原文未提供喷墨头相关技术内容。","technology_id":"T_378dade14fa3f624dabf"},{"issue":"无冻结定义问题。该机制未涉及喷墨头相关概念，故无需进一步判断冻结定义是否存在问题。","technology_id":"T_149ad03c88aba8a2997f"},{"issue":"未发现冻结定义问题","technology_id":"T_cfe96223382d7cf87aab"},{"issue":"名称中包含'干式分析膜'，可能与喷墨技术领域存在概念混淆，但实际机制不涉及喷墨头相关功能。此为命名问题，不影响冻结机制判断。","technology_id":"T_ae32124a3ecad9fa1b8b"},{"issue":"未发现明确的喷墨头或液滴喷射头相关描述","technology_id":"T_2f8588676c521fcb2561"},{"issue":"名称「気溶膠沉积垂直配線構造」が技術内容を正確に反映していない可能性があるが、原文の技術内容に基づく分類は適切である。","technology_id":"T_7da9e3495038978c6b5e"},{"issue":"The term 'aerosol deposition' is used, which may be related to spray-based processes but does not inherently imply inkjet head application or mechanism.","technology_id":"T_eaab2117e3c0d37508a2"},{"issue":"名称中的'hybridization device'（杂交装置）与喷墨头/液滴喷射技术无直接关联，未体现冻结概念中所要求的喷头适用性。但该名称未明显过度概括或误导性地使用术语。因此不记录为定义问题。","technology_id":"T_58d3533b3475ceee86ad"},{"issue":"The term 'piezoelectric element' is used broadly but clearly refers to a component of a droplet discharge head, which is a specific application area for piezoelectric actuators in inkjet printing systems.","technology_id":"T_2a8bd854717bbdc9c266"},{"issue":"The term 'liquid ejection head' is not explicitly defined in the provided abstracts but is implied through the context of piezoelectric actuators used in inkjet printing systems.","technology_id":"T_b4a02f52ce21a3c1f226"},{"issue":"名称中虽含'film forming device'，但未体现与喷墨头的直接联系，存在术语泛化可能。","technology_id":"T_c1ccba7edae4c744280e"},{"issue":"名称中虽含'压电膜'，但未明确指出与喷墨头或液滴喷射相关的具体结构或功能定义，存在轻微过度概括之嫌，但不影响冻结结果判断。","technology_id":"T_520be1790ff05100df2b"},{"issue":"未发现与喷墨头或液滴喷射相关的明确技术定义。","technology_id":"T_be75b5dfcaa8a18d7450"},{"issue":"标题中的'liquid discharge device'可能引起混淆，但无证据表明其与喷墨头存在直接关系。","technology_id":"T_05de3a57df41277653c3"},{"issue":"冻结机制名称为交错层叠电极突出连接结构，与喷墨头无关。","technology_id":"T_599b52b6d6e92339d900"},{"issue":"名称中虽含'喷墨头'字样，但实际机制为真空蒸镀，存在概念混淆风险，需注意冻结定义准确性。但不影响当前分类结果。","technology_id":"T_48712a1e741c225be325"},{"issue":"名称中'ペロブスカイト型酸化物'可能过度概括，但不影响其在喷墨头应用中的适用性判断。","technology_id":"T_b1a5202422be819b46e1"},{"issue":"名称可能有过度概括，但不影响冻结结果判断","technology_id":"T_cf7c08dda49362db0b40"},{"issue":"名称可能过度概括，但不影响分类结果。","technology_id":"T_1ca5980987d2054a8375"},{"issue":"名称可能过度概括，但不影响冻结结果判断。原机制未涉及喷墨头相关概念。","technology_id":"T_e17da6d4fe9518f5b610"},{"issue":"The term 'liquid droplet delivering head' in the title and abstract refers to a specific type of device that includes a piezoelectric element substrate. The mechanism described is directly applicable to this type of head.","technology_id":"T_198148f4538968f337d8"}]


## 冻结后确认的归并差异

| Technology ID | 已知源文差异/误并 | 处置 |
|---|---|---|
| T_f41194f1f669d94686fb | 41681057为筒壁内多个间隔环形板，中心孔大于基板；41736165为一个或叠层板件具有多个贯通孔。共同阳极/等离子稳定目标不足以证明具体结构等价。冻结名“多孔板”会误导41681057。 | 保留冻结共用节点，显式标为已知误并候选，待下一独立版本拆分；本轮不借历史标签回改。 |
| T_8f1f68dd44e345adde71 | 41346026摘要明确Pb相关a/b≤1.06且单相无烧绿石；61300486明确Nb/Sc共掺窗口0.1≤x≤0.3、0<y≤0.49x。只有通用钙钛矿/摩尔比不足以确立Same。61300486机制主字段过泛，关键共掺条件是否充分进入贡献需历史核验及人工复核。41346026摘要未披露历史R12的两段温度，不能据历史补写。 | 冻结节点保留并记录误并与粒度不足，真实机制总量不可由926候选直接推算。 |
