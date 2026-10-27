# D3 失败分析

模型抽取/证据错误与摘要不足分列。以下根因和修复判断来自DeepSeek Silver审计，不是独立人工确认。修订后未再报出不等于证明修复。全部逐族记录在D3_ERRORS.parquet。

| 类型 | 原始审计条目 | 最终审计条目 |
|---|---:|---:|
| Missing Contribution | 0 | 1 |
| Over-splitting | 31 | 3 |
| Missing Critical Material | 1 | 0 |
| Wrong Deposition Object | 0 | 0 |
| Lost Process Sequence | 5 | 2 |
| Lost Parameter Context | 22 | 4 |
| Mechanism Hallucination | 20 | 1 |
| Unsupported Evidence | 7 | 1 |
| Evidence Field Mismatch | 120 | 14 |
| False Unrelated | 0 | 0 |
| False Direct Relevance | 0 | 0 |
| Ambiguous Transferability | 10 | 3 |
| Insufficient Source | 537 | 544 |
| Model Output Failure | 1 | 0 |

## 仍待复核案例

### google:12756646 — Lost Process Sequence
草稿将“螺丝55容纳于吸收管43后”的摆动/方向转换与DC电机驱动批头紧固、定位/按压等步骤整合为连续实施顺序，但原文未明确这些步骤之间的整体先后及阶段归属；组合结论存在顺序过度整合。
证据：[{"end":600,"field":"abstract","id":"S003","start":300,"text":"part 60, and are fed to the lower part of an absorption pipe 43 by means of a block 53 through slewing of the block 53 and are held through the action of a vacuum suction part 45. After a screw fastening machine 20 is positioned to a work, the work is pressed by an air cylinder device 40, and a bit "},{"end":899,"field":"abstract","id":"S004","start":600,"text":"42 is driven with the aid of a DC motor 34 for fastening. After the screw 55 is contained in the absorption pipe 43, through drive of a rotary actuator 22, a body frame 30 is rocked centering around shafts 31 and 36 through a screw fastening direction converting gear 33, and by arbitrarily setting "}]
D2：A body frame to which a screw fastening machine is mounted is situated to the support frame of a robot so that a screw fastening angle can be set arbitrarily, and a screw fastening machine is positioned to a work, the work is pressed by an air cylinder device, and a bit is driven with the aid of a DC motor for fastening
D3：本体框架30上安装螺丝紧固机20并设于机器人支撑框架，使螺丝紧固角度可任意设定；螺丝55从螺丝供给部60逐个取出，经块体53回转送至吸收管43下部并由真空吸附部45保持；螺丝紧固机20定位到工件后，气缸装置40压住工件，DC电机34驱动批头42进行紧固；螺丝55容纳于吸收管43后，旋转致动器22驱动本体框架30绕轴31和36摆动，经螺丝紧固方向转换齿轮33转换紧固方向，通过任意设定角度在横向或倾斜方向进行螺丝锁付作业。
状态：Still flagged by final Silver audit

### google:12756646 — Evidence Field Mismatch
process_steps[8]以“任意设定角度”为method、以“螺丝锁付作业”为object，原文该句是角度设定后的作业效果/方式，不是独立工艺步骤对象；字段归属不精确。
证据：[{"end":899,"field":"abstract","id":"S004","start":600,"text":"42 is driven with the aid of a DC motor 34 for fastening. After the screw 55 is contained in the absorption pipe 43, through drive of a rotary actuator 22, a body frame 30 is rocked centering around shafts 31 and 36 through a screw fastening direction converting gear 33, and by arbitrarily setting "},{"end":1090,"field":"abstract","id":"S005","start":899,"text":"an angle, a screw lock work is effected in a lateral or an inclination direction. This constitution enables automatic and stable execution of a screw fastening work in an arbitrary direction."}]
D2：A body frame to which a screw fastening machine is mounted is situated to the support frame of a robot so that a screw fastening angle can be set arbitrarily, and a screw fastening machine is positioned to a work, the work is pressed by an air cylinder device, and a bit is driven with the aid of a DC motor for fastening
D3：本体框架30上安装螺丝紧固机20并设于机器人支撑框架，使螺丝紧固角度可任意设定；螺丝55从螺丝供给部60逐个取出，经块体53回转送至吸收管43下部并由真空吸附部45保持；螺丝紧固机20定位到工件后，气缸装置40压住工件，DC电机34驱动批头42进行紧固；螺丝55容纳于吸收管43后，旋转致动器22驱动本体框架30绕轴31和36摆动，经螺丝紧固方向转换齿轮33转换紧固方向，通过任意设定角度在横向或倾斜方向进行螺丝锁付作业。
状态：Still flagged by final Silver audit

### google:15507674 — Missing Contribution
摘要明确记载释放机构59及其推动、压下接合凸起58a和多个凸起59施加抽出方向滑动力的防滑机制，草稿仅在uncertainty中提及，未作为独立工程手段贡献抽取。
证据：[{"end":882,"field":"abstract","id":"S004","start":588,"text":"cartridge 40 is inserted to the unit frame 49, and the engaging projection 58a is engaged with the engaging plate after the cartridge 40 is fitted when the cartridge 40 is inserted and the imprudent falling-off of the cartridge 40 is prevented. A release mechanism 59 pushes a section near the "},{"end":1179,"field":"abstract","id":"S005","start":882,"text":"engaging projection 58a and pushes down the engaging projection 58a, and conducts non-slip, and a plurality of projections 59 are shaped near the engaging projection 58a working sliding force in the direction of extraction to the cartridge 40. Accordingly, the imprudent falling-off of a cassette "}]
D2：an engaging member engaging a cassette frame and a unit frame in which the cartridge is housed, and a release mechanism
D3：在盒40与单元框架49上安装相互接合的接合构件58；接合凸起58a在盒40设置时能与接合板58b的一端面联动，盒40插入单元框架49时其高度可接触并穿过接合板58b下侧，盒40插入并装配后接合凸起58a与接合板接合，从而阻止盒40不慎脱落
状态：Still flagged by final Silver audit

### google:15622240 — Evidence Field Mismatch
core_mechanism中“与各基板保持架等距的位置”主要依据目的句S002，但该句未明确实施例中支撑体与各保持架等距；草稿将目的性设置与实施例结构合并，需限定为文献目的或装置设置主张。
证据：[{"end":294,"field":"abstract","id":"S002","start":0,"text":"PURPOSE:To provide vapor-deposited films of a uniform thickness on many substrates with one time of vapor deposition treatment by providing a supporting body for a vapor source at the center of a vacuum vessel in the position equidistant from respective substrate holders, and moving the vapor "},{"end":589,"field":"abstract","id":"S003","start":294,"text":"source vertically along the supporting body. CONSTITUTION:Substrate holders 3 are mounted to the cryogenic panels 2 disposed in a bell-jar 1, and substrates 4 are fixed and held to the holders 3. A supporting body 5 for a vapor source is located on the centerline of the bell-jar 1, and a vapor "}]
D2：moving the vapor source vertically along the supporting body
D3：蒸发源支撑体设于真空容器中心、与各基板保持架等距的位置；蒸发源沿支撑体垂直移动。
状态：Still flagged by final Silver audit

### google:16773374 — Evidence Field Mismatch
control_variables[0]将目的段中“使气体流量与流向均匀”的意图表述为已设定的控制变量，原文未给出具体控制手段或设定值，属部分成立。
证据：[{"end":288,"field":"abstract","id":"S002","start":0,"text":"PURPOSE:To improve a flow of gas discharged through a diffusing plate provided to an electrode in uniformity of discharge rate so as to generate plasma excellent in uniformity by a method wherein a flow of gas fed to the diffusing plate provided to a counter electrode of a semiconductor "},{"end":586,"field":"abstract","id":"S003","start":288,"text":"manufacturing equipment is set uniform in flow rate and flow direction. CONSTITUTION:A counter electrode 60 provided inside a vacuum chamber 50 is possessed of a case 62 connected to a gas feed means 66 and provided with an open side which faces toward a table 65 and a diffusing plate 64 provided "}]
D2：setting the flow rate and flow direction of gas fed to the diffusing plate provided to a counter electrode uniform, and setting the depth of the case connected to the gas feed means 66 as large as 3/10 or above its inner diameter, so that gas flows in the radial direction as far as a distance 3/10 or above as long as the inner diameter of the case
D3：对向电极60的壳体62深度d设为内径的3/10以上，使经气体供给装置66供入空腔68的气体沿径向流动至少壳体内径的3/10的距离，再向下流至扩散板64，减小扩散板64中心与周边的压力差，使气体以近乎均匀的压力经扩散板64排出。
状态：Still flagged by final Silver audit

### google:18162049 — Lost Parameter Context
0.25r/V<20中的r仅说明为某辊半径(mm)，草稿未将该参数明确绑定到具体辊，属于参数归属不确定而非错误；但若后续确认需补全归属。
证据：[{"end":294,"field":"abstract","id":"S002","start":0,"text":"PURPOSE:To eliminate the electro static charge of a vapor-deposition film and to increase the working rate by carrying the vapor-deposited tape by suspending on a roll coated with polytetrafluoroethylene. CONSTITUTION:A base film 10a is suspended on a cooling can 2 and carried at a velocity V "},{"end":585,"field":"abstract","id":"S003","start":294,"text":"(0.25r/V&lt;20 where (r) is the radius in mm of a roll), a vapor deposition material 3 is deposited on the film when the film passes through the opening 8a of a shield plate 8, and a ferromagnetic layer 10b is formed. A laminated body 10 of the ferromagnetic layers 10b and base film 10a is "}]
D2：suspension of the vapor-deposited tape on a roll coated with polytetrafluoroethylene, and charging the laminated body by electron beam to generate electrostatic charge between the laminated body and the polytetrafluoroethylene surface layer of the destaticizer roll
D3：层叠体10悬置于靠近冷却罐2设置的除静电辊20；该辊表层22含聚四氟乙烯，层叠体10从辊20脱离时在层叠体与聚四氟乙烯之间产生静电电荷，使层叠体呈电中性。
状态：Still flagged by final Silver audit；需全文/Claims

### google:26418426 — Evidence Field Mismatch
contributions[0].materials[0]将干式化学分析薄膜的role标为“被分析物”，原文仅称其为干式化学分析薄膜，未断言其为被分析物；属角色字段轻微不精确，不影响材料名称提取。
证据：[{"end":299,"field":"abstract","id":"S002","start":0,"text":"A plurality of dry chemical analysis films are stacked in a cartridge. A chemical analysis film supplier has a cartridge storage chamber in which a plurality of cartridges are stored so that the chemical analysis films in each cartridge can be taken out by a chemical analysis film removing device. "}]
D2：将多个干式化学分析薄膜堆叠在容器中，并通过化学分析薄膜取出装置将薄膜从容器中取出的结构办法
D3：将多个干式化学分析薄膜堆叠于卡盒中，并将多个卡盒存储于供应装置的卡盒存储室，使各卡盒中的薄膜能够由化学分析薄膜取出装置取出。
在卡盒存储室内将卡盒排列成圆形，并在该圆形内侧形成吸湿剂保持部，吸湿剂装载于该保持部中。
状态：Still flagged by final Silver audit

### google:34468469 — Evidence Field Mismatch
contributions[1].split_reason和contributions[2].split_reason以原文未明确的内容作为拆分依据，属于拆分理由证据不足，而非事实字段错误。
证据：[{"end":880,"field":"abstract","id":"S004","start":588,"text":"purification ( 100 ) is composed of: an insert member ( 110 ) including a bottom member ( 120 ) and a nucleic acid-adsorptive porous membrane (F); and a barrel ( 140 ) which is formed by insert injection molding with the insert member ( 110 ). A rib ( 226 ) of the cartridge for nucleic acid "},{"end":1179,"field":"abstract","id":"S005","start":880,"text":"separation and purification ( 200 ) slopes down to the discharge part ( 224 ) in a direction from an outer side end part ( 226   a ) to an inner side end part ( 226   b ). A thickness (T) at an end face ( 324 ), which is a part forming the second opening ( 321 ) of the cap ( 320 ) of the cartridge "},{"end":1256,"field":"abstract","id":"S006","start":1179,"text":"for nucleic acid separation and purification ( 300 ), is made 0.2 mm or more."}]
D2：a cartridge for nucleic acid separation and purification composed of an insert member including a bottom member and a nucleic acid-adsorptive porous membrane; and a barrel formed by insert injection molding with the insert member, wherein a rib slopes down to the discharge part in a direction from an outer side end part to an inner side end part, and a thickness at an end face forming a second opening of a cap is made 0.2 mm or more
D3：筒体(140)通过插入构件(110)的插入注塑成型形成。
肋(226)从外侧端部(226a)到内侧端部(226b)的方向朝排出部(224)向下倾斜。
盖(320)的端面(324)为形成第二开口(321)的部分，其厚度(T)设为0.2 mm以上。
状态：Still flagged by final Silver audit

### google:35092834 — Ambiguous Transferability
C1与C2各自对应哪个课题（定位工时/高密度化）在原文中未明确分配，split_reason中的对应关系属于推断。
证据：[{"end":217,"field":"abstract","id":"S002","start":0,"text":"【課題】積層圧電体の層間電極の配線を形成する際の位置決め工数を減らして、高密度化を達成する。 【解決手段】圧電体層と電極層が交互に積層され、前記電極層間を接続する配線が形成された積層圧電体において、前記圧電体層、前記電極層及び前記配線をエアロゾル法を用いて、堆積形成する。また、前記配線を前記圧電体層及び電極層と垂直な平面として前記電極層との接触部が直線状となるように形成することにより前記課題を解決する。 【選択図】      図５"}]
D2：エアロゾル法を用いて圧電体層、電極層及び配線を堆積形成する
D3：圧電体層、電極層及び配線をエアロゾル法を用いて堆積形成する
配線を圧電体層及び電極層と垂直な平面として、電極層との接触部が直線状となるように形成する
状态：Still flagged by final Silver audit

### google:35322406 — Evidence Field Mismatch
contributions[1].technical_problem将“焼成時の反りを防止する”效果与课题混同，且“问题はS002の課題で概括”非原文直接表述。
证据：[{"end":217,"field":"abstract","id":"S002","start":0,"text":"【課題】薄板状の圧電体を容易に製造できると共に圧電体の焼成時に起こる反りを防止する吐出ヘッド及び吐出ヘッド製造方法を提供する。 【解決手段】圧電材料と電極材料を交互に積層させて形成される圧電体基板５５の内部には、単層の圧電体から成る圧電活性部５８の圧力室５２と反対側に空洞部から成る低剛性部５９が設けられている。圧電体基板５５の厚みを厚くすることで製造時のハンドリング容易性を確保しつつ、薄板状の圧電活性部５８を形成することができる。"},{"end":377,"field":"abstract","id":"S003","start":217,"text":"また、圧電体基板５５内部には低剛性部５９と圧電体基板５５の厚み方向を略２等分する面に対して対象の位置に低剛性部５９と略同一形状、略同一サイズの第２の低剛性部を設けると、圧電体基板５５の焼成時におこる反りを防止することができる。低剛性部５９には空洞部に代わり圧電体に比べて剛性が低い部材を用いてもよい。 【選択図】  図４"}]
D2：圧電材料と電極材料を交互に積層させて形成される圧電体基板の内部に、単層の圧電体から成る圧電活性部の圧力室と反対側に空洞部から成る低剛性部を設けることで、圧電体基板の厚みを厚くすることで製造時のハンドリング容易性を確保しつつ薄板状の圧電活性部を形成し、さらに圧電体基板内部の低剛性部と圧電体基板の厚み方向を略２等分する面に対して対象の位置に低剛性部と略同一形状・略同一サイズの第２の低剛性部を設けることで焼成時におこる反りを防止する技術手段
D3：圧電材料と電極材料を交互に積層して形成される圧電体基板55の内部に、単層の圧電体から成る圧電活性部58の圧力室52と反対側に空洞部から成る低剛性部59を設ける構造
圧電体基板55内部に、低剛性部59と圧電体基板55の厚み方向を略2等分する面に対して対象の位置に、低剛性部59と略同一形状、略同一サイズの第2の低剛性部を設ける
状态：Still flagged by final Silver audit

### google:35322406 — Ambiguous Transferability
contributions[1].technical_object中“備え得る”及与吐出ヘッド的组合为部分支持，不能作为完整明示对象。
证据：[{"end":217,"field":"abstract","id":"S002","start":0,"text":"【課題】薄板状の圧電体を容易に製造できると共に圧電体の焼成時に起こる反りを防止する吐出ヘッド及び吐出ヘッド製造方法を提供する。 【解決手段】圧電材料と電極材料を交互に積層させて形成される圧電体基板５５の内部には、単層の圧電体から成る圧電活性部５８の圧力室５２と反対側に空洞部から成る低剛性部５９が設けられている。圧電体基板５５の厚みを厚くすることで製造時のハンドリング容易性を確保しつつ、薄板状の圧電活性部５８を形成することができる。"},{"end":377,"field":"abstract","id":"S003","start":217,"text":"また、圧電体基板５５内部には低剛性部５９と圧電体基板５５の厚み方向を略２等分する面に対して対象の位置に低剛性部５９と略同一形状、略同一サイズの第２の低剛性部を設けると、圧電体基板５５の焼成時におこる反りを防止することができる。低剛性部５９には空洞部に代わり圧電体に比べて剛性が低い部材を用いてもよい。 【選択図】  図４"}]
D2：圧電材料と電極材料を交互に積層させて形成される圧電体基板の内部に、単層の圧電体から成る圧電活性部の圧力室と反対側に空洞部から成る低剛性部を設けることで、圧電体基板の厚みを厚くすることで製造時のハンドリング容易性を確保しつつ薄板状の圧電活性部を形成し、さらに圧電体基板内部の低剛性部と圧電体基板の厚み方向を略２等分する面に対して対象の位置に低剛性部と略同一形状・略同一サイズの第２の低剛性部を設けることで焼成時におこる反りを防止する技術手段
D3：圧電材料と電極材料を交互に積層して形成される圧電体基板55の内部に、単層の圧電体から成る圧電活性部58の圧力室52と反対側に空洞部から成る低剛性部59を設ける構造
圧電体基板55内部に、低剛性部59と圧電体基板55の厚み方向を略2等分する面に対して対象の位置に、低剛性部59と略同一形状、略同一サイズの第2の低剛性部を設ける
状态：Still flagged by final Silver audit

### google:36635088 — Evidence Field Mismatch
implementation与equipment_components[4]将“振动膜23经由气隙15设置”从原文“between upper electrodes 22”语境中截出，且原文句法关系有歧义；草稿虽声明未确定层间关系，但表述仍可能被读作已确认气隙位置。
证据：[{"end":598,"field":"abstract","id":"S003","start":299,"text":"base plate 30 formed of a material containing a resin, and a vibrator cell 10 arranged at the base plate 30. Further, the vibrator cell includes a lower electrode 25, a support section 23a and a beam 23b formed integrally, a vibrating membrane 23 arranged via an air gap 15 between upper electrodes "},{"end":762,"field":"abstract","id":"S004","start":598,"text":"22, when this beam 23b is supported by the supporter 23a and the upper electrode 22 formed in this vibrating membrane 23.  &lt;P&gt;COPYRIGHT: (C)2006,JPO&amp;NCIPI"}]
D2：a vibrator cell arranged at a base plate formed of a material containing a resin, the vibrator cell including a lower electrode, a support section and a beam formed integrally, a vibrating membrane arranged via an air gap between upper electrodes, when this beam is supported by the supporter and the upper electrode formed in this vibrating membrane
D3：基板30由含树脂的材料形成，振动器单元10布置在该基板30上。
状态：Still flagged by final Silver audit

### google:37095878 — Over-splitting
草稿将“一系统电源生成两种振动能量”与“电荷回生及两个电容器串并联切换充放电”分列为独立贡献，但原文未明示二者为独立贡献或不同课题；该句更可能是同一驱动方案中的附加构成，拆分依据不足。
证据：[{"end":253,"field":"abstract","id":"S002","start":0,"text":"【課題】  圧電素子が容量性であることを利用して、この圧電素子に蓄積された電荷分を回生し、再利用することで、エネルギー効率を向上する。１系統の電源によって、圧電素子の駆動による２種類の振動エネルギーを生成する。 【解決手段】  圧電素子４２が容量性であることに着目し、従来は、この圧電素子４２へ印加したときに蓄積される電荷を放電、廃棄していた分を２個のコンデンサ１１８、１２４を直列接続又は並列接続に切り替えることで、電位差を持たせ充放電を繰り返すように構成したため、エネルギーを有効利用することができる。"}]
D2：圧電素子が容量性であることに着目し、従来は、この圧電素子へ印加したときに蓄積される電荷を放電、廃棄していた分を２個のコンデンサを直列接続又は並列接続に切り替えることで、電位差を持たせ充放電を繰り返すように構成したため、エネルギーを有効利用することができる。
D3：圧電素子が容量性であることを利用し、圧電素子に蓄積された電荷分を回生・再利用する。２個のコンデンサを直列接続又は並列接続に切り替えることで電位差を持たせ、充放電を繰り返す。
１系統の電源によって、圧電素子の駆動による２種類の振動エネルギーを生成する。
圧電素子４２をインク吐出用の記録ヘッドとして適用し、圧力室４６内のインクの粘性調整のための振動エネルギー源として利用する。
状态：Still flagged by final Silver audit

### google:37095878 — Over-splitting
草稿将压电元件42用作喷墨记录头及压力室46内墨水粘度调整的振动能量源分列为独立贡献，但原文以“特に”表述为对前述方案的应用场景/用途，未明示独立工程手段或独立贡献关系。
证据：[{"end":345,"field":"abstract","id":"S003","start":253,"text":"特に、圧電素子４２をインク吐出用の記録ヘッドとして適用した場合における圧力室４６内のインクの粘性調整のための振動エネルギー源として利用することができる。 【選択図】        図５"}]
D2：圧電素子が容量性であることに着目し、従来は、この圧電素子へ印加したときに蓄積される電荷を放電、廃棄していた分を２個のコンデンサを直列接続又は並列接続に切り替えることで、電位差を持たせ充放電を繰り返すように構成したため、エネルギーを有効利用することができる。
D3：圧電素子が容量性であることを利用し、圧電素子に蓄積された電荷分を回生・再利用する。２個のコンデンサを直列接続又は並列接続に切り替えることで電位差を持たせ、充放電を繰り返す。
１系統の電源によって、圧電素子の駆動による２種類の振動エネルギーを生成する。
圧電素子４２をインク吐出用の記録ヘッドとして適用し、圧力室４６内のインクの粘性調整のための振動エネルギー源として利用する。
状态：Still flagged by final Silver audit

### google:37888426 — Evidence Field Mismatch
process_conditions[0] 将摘要中比较基准自指的“隔室 expanse 为所述隔室两倍”改写为“隔室 expanse 与所述隔室之比”，并作为明确关系参数；原文计量对象不清，应降级为部分成立或保留原文表述。
证据：[{"end":290,"field":"abstract","id":"S002","start":0,"text":"A cartridge accommodating case including: a cartridge accommodating upper case as defined herein; and a cartridge accommodating lower case as defined herein, a partitioned chamber of an expanse which is twice as large as the partitioned chamber being formed in an interior of the cartridge "},{"end":590,"field":"abstract","id":"S003","start":290,"text":"accommodating case by superposing on each other the upper case and the lower case which respectively have a protruding portion and a recessed portion for mutual engagement and are of a same structure, and by engaging the protruding portion and the recessed portion, wherein a detour portion which is "}]
D2：Forming a partitioned chamber in the interior of the cartridge accommodating case by superposing an upper case and a lower case, which have mutually engaging protruding and recessed portions, and forming a detour portion spaced apart from a ridge line of the cartridge accommodated in the cartridge accommodating case to form a space portion on an inner side of the detour portion in an area surrounding the ridge line
D3：上壳与下壳为相同结构，分别具有用于相互啮合的突出部和凹陷部；通过将上壳与下壳相互叠合并使突出部与凹陷部啮合，在 cartridge 容纳壳体内部形成隔室。
在围绕被容纳 cartridge 脊线的区域形成绕行部，该绕行部与脊线间隔一段距离，从而在绕行部内侧形成空间部。
状态：Still flagged by final Silver audit

### google:38237597 — Over-splitting
将“施加预定电压”与“使压电元件板57强制翘曲”拆为两个顺序步骤；后者是前者的结果，不是独立工程步骤。
证据：[{"end":590,"field":"abstract","id":"S003","start":290,"text":"piezoelectric element plate 57 is forcibly warped by applying a predetermined voltage to the piezoelectric element plate 57 prior to being bonded to the diaphragm 34. Thereby, the defects can be confirmed by appearance inspection because the surface of the piezoelectric element plate 57 is deformed "}]
D2：The piezoelectric element plate is forcibly warped by applying a predetermined voltage to the piezoelectric element plate prior to being bonded to the diaphragm
D3：在接合至振动板34之前，对压电元件板57施加预定电压使其强制翘曲；内部存在瑕疵、裂纹或空洞时，板表面在对应部位发生变形，从而可通过外观检查确认缺陷；当缺陷为沿厚度方向贯穿的孔时，电流经形成于板两面的电极膜泄漏，导致即使施加电压压电元件板57也不翘曲，该不翘曲情形属于同一检查方案下的缺陷判定情形。
状态：Still flagged by final Silver audit

### google:38584891 — Evidence Field Mismatch
contributions[0].technical_effects[1]将减小设置空间的效果归因于旋转台周边配置及蒸发单元分散配置，原文仅并列主张课题，未明示该因果归因；应降为Partial或改为不归因的课题陈述。
证据：[{"end":259,"field":"abstract","id":"S002","start":0,"text":"【課題】   真空蒸着装置による放射線画像変換器の層の成膜において、蒸着膜の厚膜化、多層化および蒸着面積の大型化を容易に達成するとともに、装置の設置スペースを小さくする。 【解決手段】  蒸着エリア３２に対向する同一面内の蒸着エリアの周辺に、複数個の回転テーブル３３を配置する。回転テーブル３３の回転軸３６を中心とした同一円周上に所定の間隔をおいて複数個の蒸発セル３４が設けられ、蒸着エリア３２に対して最も均一な蒸着膜が得られる蒸発源の配置位置Ｐｃの全てに蒸発セルを分散配置し、複数の蒸発セルを同時に用いて蒸着を行う。"}]
D2：在与蒸着区域相对的同一面内，在蒸着区域周边配置多个旋转台；在以旋转台的旋转轴为中心的同一圆周上，按预定间隔设置多个蒸发单元；将所有蒸发单元分散配置于能够获得最均匀蒸着膜的蒸发源配置位置Pc处，并同时使用多个蒸发单元进行蒸着。
D3：在蒸着区域32对向的同一面内的蒸着区域周边配置多个旋转台33；在各旋转台33的旋转轴36为中心的同一圆周上以规定间隔设置多个蒸发单元34；将蒸发单元分散配置于蒸着区域32可获得最均匀蒸着膜的蒸发源配置位置Pc的全部位置；同时使用多个蒸发单元进行蒸着
旋转旋转台33，将各旋转台上配置的蒸发单元34依次送至蒸发源配置位置Pc，进行多层蒸着处理
状态：Still flagged by final Silver audit

### google:38767432 — Evidence Field Mismatch
contributions[1].technical_object将C1的坩埚主体与圆筒状排出口结构并入系统对象，但S004仅支持坩埚排列、基板往复输送及排出口倾斜于排列方向，未明确该系统包含C1结构。
证据：[{"end":286,"field":"abstract","id":"S002","start":0,"text":"&lt;P&gt;PROBLEM TO BE SOLVED: To provide a crucible for vacuum deposition capable obtaining the required directivity of an evaporation flow, and to provide a vacuum deposition system capable of forming a vapor deposited layer having high uniformity in layer thickness using the same.  "},{"end":821,"field":"abstract","id":"S004","start":584,"text":"conveyed so as to be reciprocated in a direction orthogonal to the arrangement direction, and also, the vapor exhaust port of the crucible is tilted in the arrangement direction of the crucible.  &lt;P&gt;COPYRIGHT: (C)2008,JPO&amp;INPIT"}]
D2：The crucible has a cylindrical vapor exhaust port projected from a crucible body, and the side face of the vapor exhaust port is tilted at least to one direction so as to widen to the vapor exhaust direction.
D3：蒸气排出口为从坩埚主体突出的圆筒状，其侧面至少向一个方向倾斜，从而向蒸气排出方向扩宽。
坩埚沿一个方向排列，基板沿与坩埚排列方向正交的方向被输送以进行往复运动，且坩埚的蒸气排出口倾斜于坩埚的排列方向。
状态：Still flagged by final Silver audit

### google:38767432 — Unsupported Evidence
contributions[1].split_reason中关于两个目的之间关系的判断无原文明确依据，摘要仅并列列出两个目的。
证据：[{"end":286,"field":"abstract","id":"S002","start":0,"text":"&lt;P&gt;PROBLEM TO BE SOLVED: To provide a crucible for vacuum deposition capable obtaining the required directivity of an evaporation flow, and to provide a vacuum deposition system capable of forming a vapor deposited layer having high uniformity in layer thickness using the same.  "}]
D2：The crucible has a cylindrical vapor exhaust port projected from a crucible body, and the side face of the vapor exhaust port is tilted at least to one direction so as to widen to the vapor exhaust direction.
D3：蒸气排出口为从坩埚主体突出的圆筒状，其侧面至少向一个方向倾斜，从而向蒸气排出方向扩宽。
坩埚沿一个方向排列，基板沿与坩埚排列方向正交的方向被输送以进行往复运动，且坩埚的蒸气排出口倾斜于坩埚的排列方向。
状态：Still flagged by final Silver audit

### google:42202888 — Lost Parameter Context
C1中“一定温度”仅指蒸发源加热蒸镀材料使其蒸发的温度，不是被膜形成温度；草稿已将其归入C1，但需防止跨贡献误用。
证据：[{"end":280,"field":"abstract","id":"S002","start":0,"text":"【課題】安価でかつ耐食性の高いオーステナイト系ステンレス材料からなる蒸発源や制御板等の蒸発源用治具およびその製造方法を提供する。 【解決手段】被蒸着物質に対して蒸着する際に用いられる蒸着材料を収容し一定温度に加熱して蒸着材料を蒸発させる蒸発源と、蒸着材料が加熱・溶融した際に突沸を起こして飛び散った液体が直接、被蒸着物質である基板へ飛行するのを防ぐ金属メッシュ等の分球ふるいからなる蒸発源用治具であって、この蒸発源用治具をＣｒ主体のクロム系酸化物被膜とＦｅ主体の鉄系酸化物被膜の少なくとも２層でこの順に覆われたオーステナイト系ステンレスとする。 【選択図】なし"}]
D2：蒸発源用治具をＣｒ主体のクロム系酸化物被膜とＦｅ主体の鉄系酸化物被膜の少なくとも２層でこの順に覆われたオーステナイト系ステンレスとする
D3：金属メッシュ等の分球ふるいにより、突沸して飛び散った液体が基板へ直接飛行するのを防ぐ
オーステナイト系ステンレスからなる蒸発源用治具を、Ｃｒ主体のクロム系酸化物被膜とＦｅ主体の鉄系酸化物被膜の少なくとも２層でこの順に覆う
状态：Still flagged by final Silver audit

### google:42202888 — Evidence Field Mismatch
C2的split_reason为审核推断而非原文事实，不能作为确认候选事实；独立贡献计数应基于原文工程手段而非该推断文本。
证据：[{"end":280,"field":"abstract","id":"S002","start":0,"text":"【課題】安価でかつ耐食性の高いオーステナイト系ステンレス材料からなる蒸発源や制御板等の蒸発源用治具およびその製造方法を提供する。 【解決手段】被蒸着物質に対して蒸着する際に用いられる蒸着材料を収容し一定温度に加熱して蒸着材料を蒸発させる蒸発源と、蒸着材料が加熱・溶融した際に突沸を起こして飛び散った液体が直接、被蒸着物質である基板へ飛行するのを防ぐ金属メッシュ等の分球ふるいからなる蒸発源用治具であって、この蒸発源用治具をＣｒ主体のクロム系酸化物被膜とＦｅ主体の鉄系酸化物被膜の少なくとも２層でこの順に覆われたオーステナイト系ステンレスとする。 【選択図】なし"}]
D2：蒸発源用治具をＣｒ主体のクロム系酸化物被膜とＦｅ主体の鉄系酸化物被膜の少なくとも２層でこの順に覆われたオーステナイト系ステンレスとする
D3：金属メッシュ等の分球ふるいにより、突沸して飛び散った液体が基板へ直接飛行するのを防ぐ
オーステナイト系ステンレスからなる蒸発源用治具を、Ｃｒ主体のクロム系酸化物被膜とＦｅ主体の鉄系酸化物被膜の少なくとも２層でこの順に覆う
状态：Still flagged by final Silver audit

### google:46652173 — Lost Parameter Context
优选10%的“杨氏模量的差”未明示计量基准；草稿process_conditions[1]将其对象写为“振动板与压电膜”且value为“不超过10%”，基准关系不完整，应保留原文不确定性。
证据：[{"end":153,"field":"abstract","id":"S002","start":0,"text":"本发明的目的在于提供能够获得高振动速度的谐振换能器以及包括谐振换能器的超声处置装置。该谐振换能器包括振动板以及压电元件，其中压电元件包括压电膜和上电极。振动板的杨氏模量和压电膜的杨氏模量之间的差不超过振动板的杨氏模量的20％。本发明还提供了包括该谐振换能器的超声处置装置。优选地，杨氏模量的差不超过10％。"}]
D2：通过控制振动板的杨氏模量与压电膜的杨氏模量之间的差值来实现高振动速度，具体为使该差值不超过振动板杨氏模量的20%，优选不超过10%
D3：使振动板的杨氏模量与压电膜的杨氏模量之间的差不超过振动板的杨氏模量的20%。
状态：Still flagged by final Silver audit

### google:46926924 — Ambiguous Transferability
标题提及可変容量コンデンサ及光偏向素子，但摘要未说明该压电アクチュエータ在这些应用中的具体结构或适用关系，不能据此扩展应用贡献。
证据：[{"end":26,"field":"title","id":"S001","start":0,"text":"圧電アクチュエータ、可変容量コンデンサ及び光偏向素子"},{"end":288,"field":"abstract","id":"S002","start":0,"text":"【課題】圧電体の残留応力に起因する初期たわみによる初期変位の影響を無くすことができ、かつ、純粋な厚み方向変位（ｚ方向並進運動）を実現する。 【解決手段】長手方向の中央部が支持される第１アクチュエータ（12）と、長手方向の両端部が第１アクチュエータ（12）の長手方向の両端部に連結される第２アクチュエータ（14）と備える。第１アクチュエータ（12）は、第１圧電駆動部（12A）の駆動によって撓んで変形し、両端部が厚み方向に変位する。第２アクチュエータ（14）は第２圧電駆動部（14A）の駆動によって第1アクチュエータと逆方向に撓んで変形し、長手方向の中央部が厚み方向に変位する。"}]
D2：第１アクチュエータと第２アクチュエータを組み合わせて配置し、それぞれの圧電駆動部の駆動によって逆方向に変形させることにより、初期変位の影響を低減し、純粋な厚み方向変位を実現する
D3：第１アクチュエータは第１圧電駆動部の駆動によって撓んで変形し両端部が厚み方向に変位し、第２アクチュエータは第２圧電駆動部の駆動によって第１アクチュエータと逆方向に撓んで変形し長手方向中央部が厚み方向に変位する。
同様の構成のアクチュエータ群（101、102）を複数組連結する。
状态：Still flagged by final Silver audit；需全文/Claims

### google:50106350 — Lost Parameter Context
摘要中x、y、z、w未与通式Zn(A,B,C)O中的具体元素/位点对应，草稿已注明未明示，但参数对象仍为不确定；不应推断其归属。
证据：[{"end":587,"field":"abstract","id":"S003","start":287,"text":"piezoelectric material represented by the following general formula (P). (P) is Zn(A, B, C)O (where, 0.6≤x&lt;1, 0&lt;y, 0≤z and 0&lt;w, A: a M site element having a monovalent ion and at least one kind of metal elements selected from the group consisting of Li, Na and K, B: a M site element having "}]
D2：通过在ZnO基体中引入特定的M位元素A、B、C来调控材料的离子价态和晶体结构，从而获得优异的绝缘与压电性能
D3：采用通式Zn(A, B, C)O表示的纤锌矿型复合氧化物；A为一价离子M位元素且选自Li、Na、K中的至少一种，B为二价离子M位元素且选自Be、Mg、Ca、Ni、Sr、Ba中的至少一种，C为平均离子价大于二价的M位元素且选自Al、Si、Sc、Ti、V、Cr、Mn、Fe、Co、Ni、Cu、Ga、Zr、Nb、Mo、Ta、W中的至少一种。
状态：Still flagged by final Silver audit；需全文/Claims

### google:56018886 — Evidence Field Mismatch
core_mechanism中“应力调整层12的热膨胀系数大于压电膜20”未在evidence_ids中列出S005，而该关系由S005明示；应补充S005。
证据：[{"end":1189,"field":"abstract","id":"S005","start":896,"text":"layer 12 of which the thermal expansion coefficient is larger than a piezoelectric film 20, and a lower electrode 13; a dielectric film deposition step for depositing a columnar structure film 20 on the base structure 10; a thermal expansion coefficient adjustment step for making the thermal "}]
D2：forming a piezoelectric film including a high dielectric constant part in which an a-axis orientation component in a tetragonal component is more than a c-axis orientation component and a low dielectric constant part in which a c-axis orientation component is more than the high dielectric constant part; adjusting thermal expansion coefficients of base structure to be different between high and low dielectric constant parts; heating piezoelectric film to 1/4 Curie temperature or higher and 1/2 Curie temperature or lower and then cooling to ambient temperature
D3：在Si基板11的一个表面上形成依次包括应力调整层12和下部电极13的基底结构10，其中应力调整层12的热膨胀系数大于压电膜20；在基底结构10上沉积柱状结构膜20；使基底结构10的热膨胀系数在高介电常数部20a与低介电常数部20b之间不同；进行畴结构形成步骤：将压电膜20加热至1/4居里温度以上且1/2居里温度以下后冷却至环境温度。高介电常数部20a的四方晶成分中a轴取向成分多于c轴取向成分，低介电常数部20b的c轴取向成分多于高介电常数部20a。
状态：Still flagged by final Silver audit

### google:56018886 — Lost Process Sequence
core_mechanism将基底结构形成、柱状结构膜沉积、热膨胀系数调整、畴结构形成组合陈述，但摘要未明示这些步骤之间的执行顺序；组合结论不应暗示顺序。
证据：[{"end":896,"field":"abstract","id":"S004","start":597,"text":"which a c-axis orientation component is more than the high dielectric constant part 20a. On an Si substrate 11, the piezoelectric element is formed by: a base structure formation step for forming a base structure 10, on one surface of the Si substrate 11, successively including a stress adjustment "},{"end":1189,"field":"abstract","id":"S005","start":896,"text":"layer 12 of which the thermal expansion coefficient is larger than a piezoelectric film 20, and a lower electrode 13; a dielectric film deposition step for depositing a columnar structure film 20 on the base structure 10; a thermal expansion coefficient adjustment step for making the thermal "},{"end":1486,"field":"abstract","id":"S006","start":1189,"text":"expansion coefficient of the base structure 10 different between the high dielectric constant part 20a and the low dielectric constant part 20b; and a domain structure formation step for heating the piezoelectric film 20 to a 1/4 Curie temperature or higher and 1/2 Curie temperature or lower and "},{"end":1574,"field":"abstract","id":"S007","start":1486,"text":"then cooling the piezoelectric film to an ambient temperature.SELECTED DRAWING: Figure 1"}]
D2：forming a piezoelectric film including a high dielectric constant part in which an a-axis orientation component in a tetragonal component is more than a c-axis orientation component and a low dielectric constant part in which a c-axis orientation component is more than the high dielectric constant part; adjusting thermal expansion coefficients of base structure to be different between high and low dielectric constant parts; heating piezoelectric film to 1/4 Curie temperature or higher and 1/2 Curie temperature or lower and then cooling to ambient temperature
D3：在Si基板11的一个表面上形成依次包括应力调整层12和下部电极13的基底结构10，其中应力调整层12的热膨胀系数大于压电膜20；在基底结构10上沉积柱状结构膜20；使基底结构10的热膨胀系数在高介电常数部20a与低介电常数部20b之间不同；进行畴结构形成步骤：将压电膜20加热至1/4居里温度以上且1/2居里温度以下后冷却至环境温度。高介电常数部20a的四方晶成分中a轴取向成分多于c轴取向成分，低介电常数部20b的c轴取向成分多于高介电常数部20a。
状态：Still flagged by final Silver audit

### google:63448527 — Mechanism Hallucination
core_mechanism字段将层组成与层间位置关系表述为“核心机制”，但摘要未明示显色反应机制或压力-显色机制；应改为仅陈述层组成与位置关系，或标注机制未知。
证据：[{"end":297,"field":"abstract","id":"S002","start":0,"text":"A kind of material for measurement of pressure and its application, the material for measurement of pressure has supporter, the color development oxidant layer comprising electron donating property dyestuff former and a developer layer for being configured between supporter and color development "}]
D2：一种包含支持层、显色氧化剂层和显色剂层的压力测量材料，其中显色剂层包括电子受体化合物，且通过前端直径为5mm的终端施加50MPa压力时发生显色反应
D3：显色氧化层含电子给体性染料前体，显色剂层含电子受体化合物；显色剂层配置于支持体与显色氧化层之间。
状态：Still flagged by final Silver audit

### google:63448527 — Evidence Field Mismatch
composition[0]与composition[1]将电子给体性染料前体、电子受体化合物分别填入dopants字段，摘要仅说明其包含于对应层，未明示为掺杂剂；应改为层组成成分或标注角色未知。
证据：[{"end":297,"field":"abstract","id":"S002","start":0,"text":"A kind of material for measurement of pressure and its application, the material for measurement of pressure has supporter, the color development oxidant layer comprising electron donating property dyestuff former and a developer layer for being configured between supporter and color development "},{"end":553,"field":"abstract","id":"S003","start":297,"text":"oxidant layer and include electron acceptor compound, and the diameter for passing through front end be 5mm terminal pressurizeed with the pressure of 50MPa color development when the diameter in color development portion be more than 5mm and 10mm or less."}]
D2：一种包含支持层、显色氧化剂层和显色剂层的压力测量材料，其中显色剂层包括电子受体化合物，且通过前端直径为5mm的终端施加50MPa压力时发生显色反应
D3：显色氧化层含电子给体性染料前体，显色剂层含电子受体化合物；显色剂层配置于支持体与显色氧化层之间。
状态：Still flagged by final Silver audit

### google:91323403 — Evidence Field Mismatch
core_mechanism将|Vcf+ - Vcf-| < |Vcr+ - Vcr-|错误归于未设种子层的该一层压电膜；原文该不等式的主语是设种子层的另一层压电膜。
证据：[{"end":885,"field":"abstract","id":"S004","start":590,"text":"piezoelectric film or between the second electrode and the second piezoelectric film, one piezoelectric film that is not provided on the seed layer is polarized in a film thickness direction due to a spontaneous internal electric field, the other piezoelectric film that is provided on the seed "},{"end":1172,"field":"abstract","id":"S005","start":885,"text":"layer satisfies, in a case in which a positive-side coercive voltage is denoted by Vcr&lt;sup&gt;+&lt;/sup&gt; and a negative-side coercive voltage is denoted by Vcr&lt;sup&gt;-&lt;/sup&gt;, |Vcr&lt;sup&gt;+&lt;/sup&gt; + Vcr&lt;sup&gt;-&lt;/sup&gt;| &lt; |Vcr&lt;sup&gt;+&lt;/sup&gt; - "},{"end":1462,"field":"abstract","id":"S006","start":1172,"text":"Vcr&lt;sup&gt;-&lt;/sup&gt;|, and satisfies, in a case in which a positive-side coercive voltage is denoted by Vcf&lt;sup&gt;+&lt;/sup&gt; and a negative-side coercive voltage is denoted by Vcf in the one piezoelectric film, |Vcf&lt;sup&gt;+&lt;/sup&gt; - Vcf&lt;sup&gt;-&lt;/sup&gt;| &lt; "},{"end":1522,"field":"abstract","id":"S007","start":1462,"text":"|Vcr&lt;sup&gt;+&lt;/sup&gt; - Vcr&lt;sup&gt;-&lt;/sup&gt;|."}]
D2：Providing a seed layer only between the first electrode and the first piezoelectric film or between the second electrode and the second piezoelectric film, wherein one piezoelectric film that is not provided on the seed layer is polarized in a film thickness direction due to a spontaneous internal electric field, and the other piezoelectric film that is provided on the seed layer satisfies |Vcr+ + Vcr−| < |Vcr+ − Vcr−| and |Vcf+ − Vcf−| < |Vcr+ − Vcr−|.
D3：仅在第一电极与第一压电膜之间或第二电极与第二压电膜之间设置种子层；未设置种子层的一层压电膜因自发内电场在膜厚方向极化；设置种子层的另一层压电膜满足|Vcr+ + Vcr-| < |Vcr+ - Vcr-|，其中Vcr+、Vcr-为该另一层压电膜的正侧和负侧矫顽电压；在未设置种子层的该一层压电膜中，正侧矫顽电压Vcf+与负侧矫顽电压Vcf-满足|Vcf+ - Vcf-| < |Vcr+ - Vcr-|。
状态：Still flagged by final Silver audit

### google:100356188 — Insufficient Source
标题提制造方法，但摘要未公开任何形成/沉积步骤、工艺条件或机制；不能据此新增工艺贡献，需全文确认。
证据：[{"end":48,"field":"title","id":"S001","start":0,"text":"Piezoelectric laminate and piezoelectric element"},{"end":291,"field":"abstract","id":"S002","start":0,"text":"This piezoelectric laminate and this piezoelectric element comprise, on a substrate, a lower electrode, a first piezoelectric film, an intermediate electrode, and a second piezoelectric film in the indicated sequence. The first piezoelectric film, the intermediate electrode, and the second "},{"end":575,"field":"abstract","id":"S003","start":291,"text":"piezoelectric film are all epitaxial films. The intermediate electrode includes at least one metal oxide layer. A main component of the first piezoelectric film is a first perovskite-type oxide. A main component of the second piezoelectric film is a second perovskite-type oxide. The "},{"end":788,"field":"abstract","id":"S004","start":575,"text":"polarization-field characteristics of the second piezoelectric film exhibit a polarization-field hysteresis that is asymmetric with respect to the origin and has two coercive fields with different absolute values."}]
D2：通过在基板上依次堆叠下电极、第一压电薄膜、中间电极和第二压电薄膜形成压电层叠结构，其中各压电薄膜均为外延薄膜，且中间电极包含至少一层金属氧化物层，第一压电薄膜主要成分为第一钙钛矿型氧化物，第二压电薄膜主要成分为第二钙钛矿型氧化物，第二压电薄膜的极化-场特性呈现相对于原点不对称的磁滞现象并具有两个绝对值不同的矫顽场强。
D3：第一压电膜、中间电极和第二压电膜均为外延膜；中间电极包括至少一个金属氧化物层；第一压电膜主成分为第一钙钛矿型氧化物，第二压电膜主成分为第二钙钛矿型氧化物；第二压电膜的极化-电场特性表现出相对于原点不对称且具有两个绝对值不同的矫顽场的极化-电场滞后。
状态：Still flagged by final Silver audit；需全文/Claims

## 确定性运行失败
输出结构、引用和传输失败单独记录；失败不变成Uncertain/弃判。每指纹最多6次尝试，原响应全部保留。开发期90次本地凭据读失败发生在构造HTTP请求前，单独归因；凭据已移入SSD私密目录且不进入Git。

## 人工与全文队列
最终错误中545条要求补全文。Title-only与摘要未提供位点/阶段/窗口不能靠模型推断补齐。

## 服务失败与模型失败区分

[{"category":"Output validation only","family_id":"google:14917668","http_status_counts":{},"output_validation_failures":6},{"category":"Output validation only","family_id":"google:16590898","http_status_counts":{},"output_validation_failures":6},{"category":"Output validation only","family_id":"google:26618543","http_status_counts":{},"output_validation_failures":6},{"category":"Output validation only","family_id":"google:34214176","http_status_counts":{},"output_validation_failures":6},{"category":"Output validation only","family_id":"google:38552258","http_status_counts":{},"output_validation_failures":6},{"category":"Output validation only","family_id":"google:39595000","http_status_counts":{},"output_validation_failures":6},{"category":"Output validation only","family_id":"google:39739327","http_status_counts":{},"output_validation_failures":6},{"category":"Output validation only","family_id":"google:42069640","http_status_counts":{},"output_validation_failures":6},{"category":"Mixed service and validation","family_id":"google:47506065","http_status_counts":{"429":3},"output_validation_failures":3},{"category":"Mixed service and validation","family_id":"google:48008156","http_status_counts":{"429":3},"output_validation_failures":3},{"category":"Mixed service and validation","family_id":"google:51463248","http_status_counts":{"429":5},"output_validation_failures":3},{"category":"Mixed service and validation","family_id":"google:53768637","http_status_counts":{"429":4},"output_validation_failures":4},{"category":"Mixed service and validation","family_id":"google:54699711","http_status_counts":{"429":4},"output_validation_failures":4},{"category":"Output validation only","family_id":"google:57607984","http_status_counts":{},"output_validation_failures":6},{"category":"Mixed service and validation","family_id":"google:72608678","http_status_counts":{"402":1},"output_validation_failures":3},{"category":"Mixed service and validation","family_id":"google:74060847","http_status_counts":{"402":1},"output_validation_failures":3},{"category":"Mixed service and validation","family_id":"google:83397327","http_status_counts":{"402":1},"output_validation_failures":3},{"category":"Mixed service and validation","family_id":"google:85782338","http_status_counts":{"402":1},"output_validation_failures":3},{"category":"Output validation only","family_id":"google:94374918","http_status_counts":{},"output_validation_failures":6}]

HTTP429/402服务拒绝没有usage；不把这些请求直接称为技术理解错误。原始传输账本与恢复后的处理状态分别保留。
