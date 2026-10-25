# FUJIFILM PZT Sputter 历史技术树移交包｜Recipe + 设备改造

> **用途**：将此前对话建立的两部分历史核心技术树移交至新的Codex项目，用于 **A5.3-E4 历史已知核心族回归审计**。此文件是根据历史技术树、历史Recipe研究报告及先前的E3交集审计重新整理的**结构化索引**，不是新一轮外部专利核验，也不是可代替原始专利Claims的证据。
>
> **版本**：Transfer-v1；整理日期 2026-10-25；技术对象：Fuji/Fujifilm Dimatix相关Sputtered PZT及设备，含明确标示的关联OEM/竞品技术。

## 0. 给Codex的使用说明（必须读）

1. **本文件不代表所有条目已确认为一个Google Simple Family。** 每行是一个**历史研究组/技术节点**，给出了当时归并的候选公开文本。重新进入E3库时，必须逐个核对publication/member/family_id、同族成员及优先权。`R`是历史扩展Recipe组，`P`是报告P1–P15重点证据，`H`是设备树20组；三套ID会有技术重合，**不得把它们直接相加作为独立法律族数**。
2. 必须区分：`publication exact` / `same Google Simple Family verified` / `extended or priority-related` / `technical-related only` / `unresolved`。仅凭相同发明人、标题或共同优先权不自动归入同一Simple Family。
3. **Fuji所有权与技术相关性分开标注**。设备树H04是Oerlikon/Evatec关联技术，属于可迁移技术参照，并不默认为Fuji自有。
4. 这是**有选择的历史已知核心族集合**，适合做回归检查，不能用作全库未知技术树的真实Recall。
5. E4先核实其是否在原始238,601族及可检索238,541族中，再做现有Query真实排名与后续预审/入选链路审计。**不得将本文件直接用于给模型的回归排名加分、插队或隐性强制选入**。
6. Recipe技术树中“材料/共掺/晶相”节点对技术研发有价值，但不能仅凭该标签就推断其专利摘要明确公开了PZT本体溅射；需要区分`PZT sputtered`、`another material sputtered`、`sputter equipment`、`PZT material/phase only`及`other deposition`。

## 1. 来源与边界

| 来源 | 先前名称 | 提供信息 | 注意事项 |
|---|---|---|---|
| HIST-REC-DOE | `FUJI_PZT_Sputter_Recipe_Analysis_2026.docx` | 15组P1–P15重点Recipe证据、典型DOE与工艺演变 | 原报告的A/B/C/D是**证据等级**，与E3的P1/P2/P3 **预审等级无关** |
| HIST-REC-TREE | `Fuji sputtered PZT专利总树`（历史对话文本） | 2006–2025年材料、Recipe、生长、可靠性、深度方向工艺演化 | 技术树箭头是**技术承接/主题关联**，不是法律continuation或同族关系 |
| HIST-EQUIP-TREE | `Fuji PZT RF溅射设备改造及关联大尺寸方案技术树`（历史对话JSON） | 20个设备相关技术节点及其当时记录的公开成员 | 含OEM/关联厂家，源关系仍须与E3 family_ID核实 |
| HIST-OVERLAP | `Fuji_Sputter_历史Recipe设备_vs_E3_100族_重合审计.xlsx` | 早期100族与历史树的初步匹配 | 仅核对**被选入100族的公开文本**，不能归因为索引、召回或预审故障 |

**模型与语料边界**：E3已对238,541个具有至少一种有效文本的族建立BM25、BGE-M3和Qwen全库索引。初步交集里，Recipe P1–P15命中5/15，设备20组命中9/20；这个百分比**只代表E3的100族审阅池中存在的历史参考组**，不是全库检索Recall。Codex必须用当前项目索引重做三阶段审计。

## 2. Recipe历史重点证据：P1–P15（E4一级回归集合）

这里的P1–P15来自历史Recipe技术报告的参考证据编号，**不同于人工审核的P1/P2/P3**。

| ID | 研究主题 | 代表号 | 历史列出的公开成员/候选映射 | 历史技术要点 | 核验备注 |
|---|---|---|---|---|---|
| P1 | 高donor Nb-PZT与plasma窗口 | US8100513B2 | US8100513B2/US20080231667A1/EP1973177A2 | 高施主Nb PZT、Ts/靶基距、plasma/shield联合窗口；早期基础平台 | 关联项#60 JP2008270704A共享部分优先权/技术背景，但不同Google Simple Family，不算命中 |
| P2 | Nb含量与压电性能DOE | US8390178B2 | US8390178B2/US20110316393A1/JP5601899B2 | Nb含量梯度DOE、介电/压电响应和等离子体条件 | 以已列publications为候选成员，E4核Family ID |
| P3 | 10–13% Nb、XRD与热漏电 | JP6426310B2 | JP6426310B2/WO2017135166A1 | Nb 10–13%、I200/I100、热处理后漏电 | #47 |
| P4 | 两段温度/速率、Pb与可靠性 | WO2018021197A1 | WO2018021197A1/JP6661771B2/US11195983B2 | 初期与主体成膜温度、速率及Pb/B和可靠性 | 重要缺失 |
| P5 | Pb/Nb与XRD/漏电可靠性 | WO2018180276A1 | WO2018180276A1/JP6850870B2/US11793082B2 | Pb/Nb、晶相和高温漏电联合约束 | 重要缺失 |
| P6 | 初期正偏→后期负偏 | EP4318619B1 | EP4318619B1 | 初期正基板偏压→主体负偏压的分段工艺 | 重要缺失 |
| P7 | 氧分压深度轮廓 | EP4178333B1 | EP4178333B1 | 初期/主体O2比例切换，O2 depth profile、TDDB | 重要缺失 |
| P8 | 陶瓷靶材碳杂质控制 | JP5943870B2 | JP5943870B2/WO2014162999A1 | 陶瓷PZT靶材碳杂质与膜性能 | 重要缺失 |
| P9 | R/T晶相与靶功率密度 | WO2016031134A1 | WO2016031134A1/JP6392360B2/US10011111B2 | 靶功率密度、R/T晶相共存及疲劳 | #45 |
| P10 | Nb/Ni共掺与低压响应 | US10217929B2 | US10217929B2/WO2017085924A1/JP6392469B2 | 高Nb+Ni共掺的低压d31与非钙钛矿相抑制 | #61 |
| P11 | 超薄growth control氧化物界面 | US11985899B2 | US11985899B2/US20220093844A1/WO2020250632A1 | 超薄Growth-control oxide layer、初始成核 | 重要缺失 |
| P12 | 晶柱倾斜/取向与寿命 | JP2011181828A | JP2011181828A/US20110215679A1 | 柱状晶轴倾斜、偏压、耐久性 | 重要缺失 |
| P13 | Mg/Nb共掺 | US8672457B2 | US8672457B2/JP2012039037A/JP5592192B2 | Mg/Nb共掺的形貌、应力和电荷补偿 | #52 |
| P14 | 微量Si成分调节 | JP6284875B2 | JP6284875B2/JP2016103567A/US10103316B2 | 微量Si与结晶/晶格微调 | #37 |
| P15 | 2025 Pt/SrRuO3 seed与预处理 | US20250098540A1 | US20250098540A1/JP2025042312A/CN119630263A | Pt/SrRuO3 seed及reverse sputter预处理，12%Nb-PZT | #46 JP2025042311A是相邻另一个申请/不同Simple Family，不计命中 |

### Recipe P1–P15 工艺主线（历史研究框架）

- **2006–2008早期平台**：High donor/B-site/A-site PZT；组合控制基板温度 Ts、靶—基距离 D、plasma potential、shield/ring与Vs−Vf。US8100513B2及相关日本优先权构成历史研究中的技术平台，但跨申请/多优先权不必然归一个Simple Family。
- **2010–2016性能与材料演化**：Nb含量扫描（高响应）；Mg、Si、Ni、Sc等辅助元素；靶材碳杂质；R/T晶相控制、柱状晶倾斜与疲劳。
- **2016–2018可靠性收敛**：10–13%Nb、Pb/B、XRD峰比、initial/bulk的温度和沉积速率轨迹、高温漏电。
- **2019–2025界面与深度控制**：Growth-control layer、基板bias(z)、O2(z)、18O以及Pt/SRO底层和沉积前处理。

不能把不同时期不同专利Example的最优值拼成唯一Fuji量产Recipe，也不得从公开技术树反推真实SAMBA量产制程。

## 3. Recipe扩展技术树：R01–R29（用于诊断更宽的已知路线）

R01–R29与上一节P1–P15有重复；例如R15≈P2、R23≈P4、R26≈P6。**先做法律族归一化再计数**。

| ID | 技术路线 | 代表号 | 历史候选公开文本 | 技术说明 | 性质 |
|---|---|---|---|---|---|
| R01 | 早期 Ts×靶基距成膜窗口 | JP2008081802A | JP2008081802A / JP4246227B2 / US20080079783A1 | 早期工艺平台；温度与靶基距窗口 | Recipe–equipment boundary |
| R02 | B-site high-donor组成 | JP2008270704A | JP2008270704A / JP5367242B2 | 2007 B-site高施主Nb-PZT组成，注意与US8100513B2不能默认归同Simple Family | Materials+recipe |
| R03 | B-site Ts×靶基距 | JP2008266770A | JP2008266770A | 2007 B-site系列的温度×距离窗口 | Recipe |
| R04 | B-site Ts×plasma potential | JP2008266771A | JP2008266771A / JP2007229788A | 2007 B-site系列的等离子体/基板电位 | Recipe–equipment boundary |
| R05 | B-site Shield×Vs−Vf | JP2008266772A | JP2008266772A / JP4808689B2 / JP2007229789A | 2007 B-site系列靶周屏蔽和电位窗口 | Recipe–equipment boundary |
| R06 | A-site donor组成 | JP2009062207A | JP2009062207A / JP5095315B2 / US20090062114A1 | A-site donor/Bi等组成 | Materials+recipe |
| R07 | A-site Ts×靶基距 | JP2009062564A | JP2009062564A / US20090058954A1 / EP2034042A3 / CN101665908A | A-site工艺温度×距离；CN对应关系须经E3 family表复核 | Recipe |
| R08 | A-site Ts×Vs | JP2009064859A | JP2009064859A / US20090058955A1 / EP2034534A2 / CN101381858A | A-site的plasma potential/基板电位控制 | Recipe–equipment boundary |
| R09 | A-site Shield×Vs−Vf | JP2009062208A | JP2009062208A / JP4993294B2 / US20090058953A1 / US7923906B2 / EP2034041B1 / CN101665907B | A-site的shield和能量窗口 | Recipe–equipment boundary |
| R10 | Bi/Nb共掺与极性响应 | JP2009117592A | JP2009117592A / JP4505492B2 / US20090114875A1 | B-site Nb与A-site Bi路线交汇 | Materials+recipe |
| R11 | Bi的低Pb耐久性应用 | JP5555072B2 | JP5555072B2 / US8672456B2 | 低Pb/Bi补偿与可靠性 | Materials+recipe |
| R12 | 初期/主体温度分段 | JP2010080813A | JP2010080813A / US8354777B2 | 初期成核、两段温度、抑制非钙钛矿相 | Recipe |
| R13 | 初期Pb富集成核 | JP2010084160A | JP2010084160A | initial Pb-rich然后主体相对低Pb | Recipe |
| R14 | 倾斜晶柱、取向与寿命 | JP2011181828A | JP2011181828A / US20110215679A1 | Rocking曲线、晶轴倾斜、偏压与耐久性 | Recipe+microstructure |
| R15 | 高Nb浓度扫描与最大响应 | JP5601899B2 | JP5601899B2 / US20110316393A1 / US8390178B2 | Nb含量扫描、d31、晶向、电学性能 | Recipe+materials |
| R16 | Nb与Mg共掺 | JP5592192B2 | JP5592192B2 / JP2012039037A / US8672457B2 | 表面形态、应力、部分电荷补偿 | Materials |
| R17 | 靶材碳杂质 | JP5943870B2 | JP5943870B2 / WO2014162999A1 | 靶材C含量与高Nb薄膜电学损耗/响应 | Target+recipe |
| R18 | R/T晶相与RF功率密度 | JP6392360B2 | JP6392360B2 / WO2016031134A1 / US10011111B2 | 低功率密度、R/T相比例、可靠性 | Recipe+microstructure |
| R19 | 微量Si调节 | JP2016103567A | JP2016103567A / JP6284875B2 / WO2016084365A1 / US10103316B2 | 微量Si、晶格与薄膜性能 | Materials |
| R20 | Nb与Ni共掺 | JP6392469B2 | JP6392469B2 / WO2017085924A1 / US20180254406A1 / US10217929B2 | 低电压响应及pyrochlore抑制 | Materials |
| R21 | Nb与Sc共掺 | JP6499810B2 | JP6499810B2 / WO2018042946A1 / US10483452B2 | 高Nb下的晶相稳定 | Materials |
| R22 | 10–13%Nb热漏电可靠性 | JP6426310B2 | JP6426310B2 / WO2017135166A1 | Nb、XRD峰比、热处理前后漏电 | Recipe+reliability |
| R23 | 初期温度速率/Pb控制 | WO2018021197A1 | WO2018021197A1 / JP6661771B2 / US11195983B2 / DE112017003091B4 | T1/T2、R1/R2、Pb/B、I200/I100 | Recipe+reliability |
| R24 | Pb/Nb与晶相及高温漏电 | WO2018180276A1 | WO2018180276A1 / JP6850870B2 / US11793082B2 | Pb/Nb与XRD和热漏电的联合窗口 | Recipe+reliability |
| R25 | Growth-control layer界面 | WO2020250632A1 | WO2020250632A1 / US20220093844A1 / US11985899B2 | 超薄界面氧化物控制成核和pyrochlore | Interface+recipe |
| R26 | 分段基板偏压 | EP4318619B1 | EP4318619B1 | 初期正bias→主体负bias，随深度控制 | Recipe |
| R27 | 分段氧气/深度剖面 | EP4178333B1 | EP4178333B1 | O2(z)与缺陷/TDDB可靠性 | Recipe |
| R28 | 氧同位素控制 | EP4231807A1 | EP4231807A1 | 18O同位素富集与氧化学/可靠性 | Recipe |
| R29 | 2025 Pt/SRO底层与预处理 | US20250098540A1 | US20250098540A1 / JP2025042312A / CN119630263A | Pt150/SrRuO3约20nm、12%Nb-PZT及沉积前处理；与JP2025042311A不同Simple Family | Interface+recipe |

### Recipe演化示意（技术关系，非法律同族）

```text
2006  Ts × target-substrate distance；plasma/shield基础平台
        │
2007  B-site high donor/Nb     A-site donor/Bi
        └──────────────┬──────────────┘
                       │
2008–2012     初始成核／Pb初期富集／晶柱取向／高Nb高响应
                       │
2013–2016     Mg、Si、Ni、Sc共掺；target C；R/T相工程
                       │
2016–2018     10–13%Nb + Pb/B + XRD + 初始/主体温度与速率
                       │
2019–2025     Growth-control layer → Bias(z) / O2(z) / 18O
                       │
               interface + depth-dependent recipe
```

注意：R21 Sc、R28氧同位素等节点虽属于研究技术树，不应仅因标题涉及PZT材料或氧就当成“明确PZT溅射工艺”。

## 4. 设备改造树：H01–H20（E4一级回归集合）

历史设备树含28个技术布局节点，其中**有实际候选公开成员的技术组为20个**；本节只列这20组，空节点不应当作独立专利族。

| ID | 设备技术节点 | 代表号 | 历史列出的公开成员 | 历史技术说明 | 权属/同族提示 |
|---|---|---|---|---|---|
| H01 | 靶周电位边界/shield | JP4142706B2 | JP4142706B2/JP2008081803A/US20080081128A1/EP1906433A1 | 调整靶周shield/环结构的位置及高度，控制等离子体电位与基板浮动电位之差 Vs−Vf。 | 历史设备树成员，需逐一核验 |
| H02 | 腔体RF屏蔽 | US8043487B2 | US8043487B2/US20100147681A1/WO2010068624A2/JP5421387B2 | 同心环凸起与扩展接地shield稳定RF边界，抑制寄生放电及plasma spill-out。 | 历史设备树成员，需逐一核验 |
| H03 | 成形阳极RF回流 | US8066857B2 | US8066857B2/US20100147680A1/WO2010068625A2/JP5421388B2 | 成形阳极与shield导通，增加可维持的RF回流面积。 | 历史设备树成员，需逐一核验 |
| H04 | 反电极折叠面积（关联Evatec/Oerlikon） | US10224188B2 | US10224188B2/WO2010058366A1/EP2368258B1/CN102224561B | Oerlikon/Evatec关联技术：折叠/堆叠接地环来扩大反电极面积，**不应默认为Fuji自有专利**。 | 关联OEM，不默认Fuji自有 |
| H05 | 多孔板阳极 | JP2010031343A | JP2010031343A/JP5135106B2 | 多个通孔的多孔阳极板，可多层错孔布局以稳定放电。 | 历史设备树成员，需逐一核验 |
| H06 | 环形捕获阳极 | US20100090154A1 | US20100090154A1/JP2010037566A/JP5047087B2 | 环形捕获阳极/多层中空板，用于捕获/调节基板周围离子。 | 历史设备树成员，需逐一核验 |
| H07 | 多级侧壁阳极 | US8047636B2 | US8047636B2/JP2010043330A/JP5052455B2 | 基板周围的筒壁导体与同轴多级环形板控制离子/电子。 | 历史设备树成员，需逐一核验 |
| H08 | 主动电位调节网格 | US20100206713A1 | US20100206713A1/JP2010242213A | 靶和基板之间的主动grid，施加RF/DC电位以调节到达基板的带电粒子能量。 | 历史设备树成员，需逐一核验 |
| H09 | 基片阻抗控制电位 | EP2031084B1 | EP2031084B1/JP4317888B2/US9111732B2/CN101376965B | 基板支撑电极到地之间的可调阻抗，控制基板电位及离子轰击。 | 历史设备树成员，需逐一核验 |
| H10 | 匹配网络自偏压 | US8540851B2 | US8540851B2/US20100206718A1/WO2010096533A1 | 基板与地之间的可调匹配网络，实现DC self-bias调节。 | 历史设备树成员，需逐一核验 |
| H11 | 双RF相位控制 | US8557088B2 | US8557088B2/US20100206714A1/JP2010242212A | 两路RF源与相位移相器，利用RF相位差调节基板DC自偏置。 | 历史设备树成员，需逐一核验 |
| H12 | 简化RF调谐 | US20130284589A1 | US20130284589A1/EP2660351B1/JP2013231233A | 简化RF调谐与基板偏压网络，降低寄生路径影响。 | 历史设备树成员，需逐一核验 |
| H13 | 大尺寸边缘等电位 | US8172372B2 | US8172372B2/JP2010138485A/JP5399165B2/US8366259B2 | 调节基板外缘及邻近空间电位，减小大尺寸晶圆边缘的离子能量差。 | 历史设备树成员，需逐一核验 |
| H14 | 周边多电位管理 | WO2018207577A1 | WO2018207577A1/JP6900469B2/US20200066494A1 | 分别控制stage、沉积环及外围防沉积板电位，抑制起弧和边缘异常。 | 历史设备树成员，需逐一核验 |
| H15 | 多点导电夹持 | US8133362B2 | US8133362B2/JP2011179120A/JP5580760B2 | 多个独立弹性导电接点连接晶圆边缘，分散RF电流及局部热/电弧。 | 历史设备树成员，需逐一核验 |
| H16 | 绝缘夹持 | US20110209989A1 | US20110209989A1 | 导电夹具与基板之间引入绝缘部件，降低局部放电。 | 历史设备树成员，需逐一核验 |
| H17 | 石墨热扩散/背气 | US9181619B2 | US9181619B2/US20110209985A1/JP2011179119A | 石墨热扩散片和背气通道，改善高温沉积的温度均匀性。 | 历史设备树成员，需逐一核验 |
| H18 | 靶材背板热机械 | JP5344864B2 | JP5344864B2/WO2010013831A1/US20110014394A1 | PZT靶/背板的热膨胀匹配、键合和热机械可靠性。 | 历史设备树成员，需逐一核验 |
| H19 | 面内气压均匀 | WO2010032459A1 | WO2010032459A1/CN102159748A/US20110163181A1/JP5296468B2 | 环形分气器和多点供气调节靶下方气压分布与等离子体均匀性。 | 历史设备树成员，需逐一核验 |
| H20 | 腔壁成分再释放 | US8563091B2 | US8563091B2/JP2010189703A/US20100208005A1 | 腔壁加热或施加电位促进Pb等物质从腔壁再释放，影响成膜成分。 | 历史设备树成员，需逐一核验 |

### 设备技术树结构（技术关联，非权利转让或法律族延续）

```text
PZT RF Sputtering Apparatus
 ├─ 等离子体与反电极 / RF return
 │   ├─ H01 靶周电位边界
 │   ├─ H02 腔体Shield
 │   ├─ H03 成形Anode
 │   ├─ H04 折叠反电极（关联Oerlikon/Evatec）
 │   ├─ H05 多孔板阳极 / H06 环形捕获阳极 / H07 多级阳极
 │   └─ H08 主动Grid
 ├─ 基片电位与RF控制
 │   ├─ H09 基片阻抗 / H10 自偏压匹配 / H11 双RF相位 / H12 RF调谐
 ├─ 大尺寸与晶圆支撑
 │   ├─ H13 边缘等电位 / H14 周边电位
 │   ├─ H15 导电夹持 / H16 绝缘夹持 / H17 热扩散背气
 │   └─ H18 靶材背板
 └─ 成分与气场管理
     ├─ H19 面内气压均匀
     └─ H20 腔壁再释放
```

### 与Recipe的交叉节点

- `R01, R03, R07`中靶基距、温度等是工艺窗口与设备几何的交界；不能仅凭此认定存在独立硬件改造。
- `R04, R05, R08, R09`与`H01–H12`属于等离子体、电位、基板bias的交叉空间；要区分工艺权利要求与装置权利要求。
- `P6/R26`属于沿膜厚变化的recipe，虽然需要bias硬件支持，但不等于新发明了某个chuck偏压电路。
- `P7/R27`属于氧气随膜厚的工艺分段，不等于发现了Fuji专门设计的动态气路硬件。
- `P9/R18`中的target power density可能受到磁场/靶侵蚀结构影响；**历史资料未证明Fuji采用某种特定磁体组件**。

## 5. E4必须优先验证的历史节点（回归测试，而非自动加权白名单）

| 主线 | 历史节点 | 代表号 | 技术关键点 |
|---|---|---|---|
| Recipe | P1 | US8100513B2 | 高施主基础plasma窗口；共享JP优先权不等于同Simple Family |
| Recipe | P2 | US8390178B2 | Nb浓度DOE与高响应 |
| Recipe | P4 | WO2018021197A1 | 初期/主体速率与温度 |
| Recipe | P5 | WO2018180276A1 | Pb/Nb/XRD/高温漏电 |
| Recipe | P6 | EP4318619B1 | Bias(z) |
| Recipe | P7 | EP4178333B1 | O2(z) |
| Recipe | P8 | JP5943870B2 | 靶材C杂质 |
| Recipe | P9 | WO2016031134A1 | R/T phase、靶功率密度 |
| Recipe | P11 | US11985899B2 | GCL及初始结晶 |
| Recipe | P15 | US20250098540A1 | Pt/SRO；与JP2025042311A为相邻不同Simple Family |
| Equipment | H02 | US8043487B2 | Shield |
| Equipment | H03 | US8066857B2 | Anode |
| Equipment | H07 | US8047636B2 | 多级侧壁阳极 |
| Equipment | H09 | EP2031084B1 | 基板阻抗控电位 |
| Equipment | H10 | US8540851B2 | RF Matching |
| Equipment | H11 | US8557088B2 | 相位偏压 |
| Equipment | H15 | US8133362B2 | 多点夹持 |
| Equipment | H17 | US9181619B2 | 背气与热扩散 |
| Equipment | H01 | JP4142706B2 | 靶周电位 |
| Equipment | H13 | JP2010138485A | 大尺寸边缘等电位 |

## 6. 已知法律族映射陷阱（必须保留）

1. **US8100513B2 与 JP2008270704A**：历史研究将二者视作高donor工艺平台关联专利，但前一轮重合审计报告称它们属于不同Google Simple Family。因有多优先权和相关申请，**不得把JP2008270704A在E3出现直接算作P1 US8100513B2的Simple Family命中**。E4重新以本地Family ID核实。
2. **US20250098540A1 与 JP2025042311A**：历史交集审计记录US20250098540A1对应JP2025042312A；JP2025042311A是相邻申请，对应另一公开（US20250098542A1）。**标题/优先权相似不代表同族**。
3. **CN101665908A / JP2009062564A**：历史交集审计提供了它们的国家公开对应线索，但E4必须以现有家族映射数据核实，不要仅凭旧文档文字确认。
4. **Fujifilm / Fujifilm Dimatix / Fuji Xerox / Evatec/Oerlikon**：不同申请人不能混为FUJIFILM Dimatix自有族。`owner_verified`与`technically_relevant`要两列分别填写。
5. 后期`EP4318619B1`、`EP4178333B1`、`EP4231807A1`若仅给一个EP公开号，**不表示只有这一个专利成员**；E4应以原数据库搜索法律同族，不得因历史表缺少其他号码就判为不可检索。

## 7. E4建议导入字段与三阶段检查

以历史P01–P15、H01–H20为基础回归层，R01–R29作为更广泛的已知主题扩展回归层。**统计单位采用实际核验后的Google Simple Family，而非历史ID条数。** 一个实际法律族可在多个技术节点出现，保留多个技术标签，但整体去重。

| 字段 | 描述 |
|---|---|
| `historical_node_id` | P1–P15 / H01–H20 / R01–R29，保留来源层次 |
| `historical_representative_publication` | 本文件中的历史代表号 |
| `historical_candidate_publications` | 候选成员号列表，等待当前库核实 |
| `technology_route` | 技术子方向与实际溅射对象 |
| `ownership_scope` | Fuji / OEM / other / unknown，不从技术主题推断 |
| `match_type` | publication exact / same-simple-family verified / related-family / technical-only / unresolved |
| `corpus_family_id` | 当前E3原始库的实际family_id，缺失则空值 |
| `raw_corpus_present` | 238,601原库是否存在 |
| `searchable_corpus_present` | 238,541可检索库是否存在 |
| `best_rank_bm25 / bge / qwen` | 对E3原Query在当前库的真实最佳排名，注明语言和版本 |
| `found_in_saved_topk` | 是否存在于E3已保存TopK，及窗口200/500 |
| `prescreen_received / final_label` | 是否进入预审及最终预审分类 |
| `review_pool_selected` | 是否进入E3最终PZT100族 |
| `first_failed_stage` | 首个确证失败环节：corpus、retrieval、prescreen、selection或无法还原 |
| `evidence_path` | 数据库行/脚本日志/Query ID/Parquet行级证据 |

**阶段一：Corpus**。核实原始/可检索库，所有历史候选publication匹配，检查成员文本质量、占位摘要和代表成员影响。

**阶段二：Retrieval**。已在库却不在Top200/500的历史族，不应直接算“Embedding无法检索”；针对冻结Query和既有向量计算其真实排序。BM25无匹配则单独标记，不伪造排名。区分Query不足、方法相关性、代表文本不足、截断、TopK截断。

**阶段三：Selection**。依次追查`SEARCH_RUNS` → `CANDIDATES_ALL` → `TECHNICAL_PRESCREEN` → `TECHNICAL_PRESCREEN_FINAL` → `Fuji_A5_E3_300_System` → 最终100族。记录**最后通过**、**首次失败**和可追溯的根因；证据不够写`not reconstructable`。

**报告口径**：分别计算`Recipe 重点P集合`、`Equipment H集合`、`Recipe扩展R集合`回归指标；最终以核验后的不同Google Simple Family为分母，另给技术节点覆盖比例，避免把技术节点数误当作法律族数。不要用这些已知种子证明未知路线的全局Recall。

## 8. 这份移交包没有做的事情

- 未在当前Turn重新打开所有Google Patents页面，也未核验当前法律状态和全部全球家族成员；上述号码、技术说明和成员关系来源于历史资料。
- 未访问Codex本机E3的`SEARCH_RUNS.parquet`、原始238,601族库、`CANDIDATES_ALL`或AI审计日志；因此未判断为什么具体历史族落选。
- 未将技术相似专利自动合并，也未保证上表所有成员在Google Simple Family意义上完全一致。
- 未改动任何历史数据库或E3审核结果。

**交付建议**：将本Markdown文件直接放在Codex项目的 `reference/historical_sputter_tree_recipe_equipment.md`，并将E4任务说明中的“历史文件”统一指向本文件；Codex应据此建立回归种子清单、确认法律族并执行三阶段链路审计。
