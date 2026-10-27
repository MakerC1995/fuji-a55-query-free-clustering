"""Material source corrections identified during the 30/100 and fixed source review."""
from common import *
import pandas as pd
def main():
 guard();docs={d['family_id']:d for d in pd.read_parquet(W/'inputs/PATENT_TEXTS.parquet').to_dict('records')};patches={}
 def quote(fid,marker):
  text=docs[fid]['abstract'];pos=text.find(marker);assert pos>=0,(fid,marker)
  start=max(0,pos-35);end=min(len(text),pos+205)
  return dict(field='abstract',start=start,end=end,quote=text[start:end])
 def edit(fid,field,text,markers,reason):
  patch=patches.setdefault(fid,dict(reason=reason,facets={},parameter_kind_fixes=[]))
  patch['reason']=reason;patch['facets'][field]=dict(text=text,quotes=[] if text is None else [quote(fid,m) for m in markers])
 def fix(fid,name,kind,reason):
  patches.setdefault(fid,dict(reason=reason,facets={},parameter_kind_fixes=[]))['parameter_kind_fixes'].append(dict(name=name,kind=kind))
 edit('google:40581936','technical_mechanism','依据具有不同对称性及分极方向的稳定结构X与Y之间的能量差，选择满足 |E(X)−E(Y)|≤E·P·V 的混合钙钛矿组成，其中E·P为电场与自发极化密度的内积，V为基本晶格体积。',['｜Ｅ（Ｘ）','Ｅ・Ｐは'],'模型概述漏掉晶格体积V；按原文恢复判据。')
 edit('google:40581936','applicable_conditions','端元的最稳定晶体结构X、Y具有不同对称性与分极方向；组成及其对应能量须满足原文能量—场耦合判据。',['最も安定な結晶構造Ｘ','｜Ｅ（Ｘ）'],'模型概述漏掉晶格体积V；按原文恢复判据。')
 edit('google:98864925','technical_problem',None,[],'原文直接给出驱动结构及条件，没有模型声称的对称滞回导致输出不足的问题；删去补充解释。')
 edit('google:45993406','technical_mechanism','在衬底上形成平均膜厚至少5μm的(K,A,B)(Nb,C,D)O3类钙钛矿膜，其组成及元素角色受摘要通式(P)和各变量范围限定。',['5μm以上','0&lt;w&lt;1.0'],'将模型误写的严格大于5μm恢复为原文“5μm以上”；完整通式限制仍查源文。')
 edit('google:90417293','technical_mechanism','依次形成多第一电极构成的第一电极层、压电层与含第二电极的第二电极层，并使传感器至少一部分形成曲面以测量曲面分布压力。',['A pressure sensor comprises','at least part of'],'补回摘要明确的曲面结构限制，避免将普通层叠传感器泛称当特异机制。')
 edit('google:39704160','applicable_conditions','基底主要为Si或SiO2；中间层与第一电极层合计厚度不低于压电层厚度的15%，压电层为铅基材料。',['The thickness of','substrate consisting mainly','lead-based piezoelectric material'],'补回中间层应力方案的厚度比例及材料限定。')
 edit('google:92590282','technical_mechanism','相邻压电膜经含粘接区和间隙区的粘接层层叠；在摘要规定的截面SEM取样条件下，粘接层/压电膜平均厚度比为0.15～1.0，粘接层间隙面积比为1%以上且小于40%。',['接着領域と間隙部','比ｄ'],'SEM是界定结构的观察条件，不是通过观察实施制造控制；改为来源披露的结构限定。')
 edit('google:92590282','implementation',None,[],'SEM是界定结构的观察条件，不是通过观察实施制造控制；改为来源披露的结构限定。')
 edit('google:51658295','technical_mechanism','先用第一蚀刻液图形化20～300nm金属膜，再用第二蚀刻液蚀刻压电膜；压电膜耐第一蚀刻液、金属膜耐第二蚀刻液，以此抑制侧蚀。',['forming a metal film','In the first etchant'],'修正耐蚀性主体：耐受蚀刻液的是对应膜，不是蚀刻液自身。')
 edit('google:51658295','applicable_conditions','第一蚀刻液中压电膜耐蚀；第二蚀刻液中金属硬掩膜耐蚀。',['In the first etchant'],'修正耐蚀性主体：耐受蚀刻液的是对应膜，不是蚀刻液自身。')
 edit('google:73458553','applicable_conditions','撞击位置须使配重在一次外力脉冲下仅撞击悬臂一次，并在下一次外力脉冲到来前不再接触悬臂。',['錘が衝突する部位'],'补回单脉冲单次撞击这一位置选择约束。')
 edit('google:34467468','implementation','经金属氧化物粘附层在支撑板形成导电下电极，再喷射沉积介电材料粉末并热处理；上电极可在热处理之前或之后形成。',['The manufacturing method comprises','spraying and depositing','before or after'],'模型仅保留层结构，补回摘要中独立披露的制造步骤；仍保留综合贡献，是否拆分待人审。')
 edit('google:87762874','applicable_conditions','两压电膜的自发极化沿相同厚度方向；按摘要分别定义的矫顽电压量，必须同时满足 ΔVcr < ΔVcf - 0.2 和 Vcr < Vcf - 0.2。',['directions of the spontaneous polarizations are the same','are satisfied'],'补回不能因传输失败当作不存在的两项矫顽电压限制；符号释义以原文为准。')
 edit('google:36033435','technical_mechanism','在压电体所定方向电场的低电位侧设置金属氧化物层以补偿该电场产生的氧空位；高电位侧另设金属氧化物层，以补偿反向电场造成的累积氧空位。',['金属酸化物層１６６','金属酸化物層１６４'],'细化两侧金属氧化物层分别对应正反方向电场的作用，防止泛化为任意氧化物覆盖。')
 fix('google:81000018','inclination','OTHER_QUANTITATIVE','原文角度1°的物理量类型不是计数。')
 fix('google:42630618','Piezoelectric constant d31','OTHER_QUANTITATIVE','压电系数不是组成比；原始值及单位保留。')
 fix('google:85602693','導熱率','OTHER_QUANTITATIVE','导热率不是时间；原始值及单位保留。')
 edit('google:81000017','applicable_conditions','上电极与含In金属氧化物层邻接，且其金属在氧化后呈N型半导体特性。',['N-type'],'补回上电极金属氧化后的N型半导体限制。')
 edit('google:45352133','technical_mechanism','采用柱状晶结构的铅基钙钛矿压电膜，以a<1、a+b>1和0<d<b限定铅不足、A位总量超额及B位掺杂之间的组成关系。',['柱状結晶','ａ＜１'],'原抽取只剩柱状晶泛称，恢复源文披露的组成关系。')
 edit('google:59500807','applicable_conditions','Nb掺杂量0.10≤y≤0.13，XRD峰强比0.85≤I(200)/I(100)≤1.00；粘附层含摘要所称电离能≤0.34eV的金属。该异常数值仅按源文保留，需全文核验。',['０．１０≦ｙ','０．８５≦'],'补回材料与衍射峰比条件；不自行合理化源文中的电离能数值。')
 edit('google:55399055','implementation',None,[],'摘要只披露晶相比例及组成，没有实际调整晶相的制造步骤；删除模型泛化制程。')
 edit('google:61016143','technical_mechanism','以(100)优先取向Nb-PZT的A/B组成比q与XRD峰强比r的耦合范围限定压电膜：0.28r+0.9≤q≤0.32r+0.95，同时1.10≤q≤1.25、r≤1.00。',['0.28r+0.9'],'摘要披露的是组成/晶体表征限制，而非具体制造操作。')
 edit('google:61016143','implementation',None,[],'摘要披露的是组成/晶体表征限制，而非具体制造操作。')
 edit('google:35632644','technical_problem',None,[],'标题和结构描述未明确提出模型所称“结构设计和制造方法”这一问题；保持问题未知。')
 edit('google:42815230','technical_mechanism','在压电体未被上电极覆盖的露出部分的至少一部分上，覆盖疏水且绝缘的流动性材料。',['露出した部分'],'澄清被覆盖的是露出的压电体，而非上电极本身。')
 edit('google:98864925','expected_effect',None,[],'摘要只说明驱动构造与斜率比条件，没有明确输出效率提升结论；删除模型补充的效果。')
 edit('google:83322208','technical_mechanism','对经粘贴层层叠的压电膜限定端部几何：端面内43μm区域的最大高度与内侧43μm位置高度之差不超过4.2μm，以防褶皱。',['貼着層','４３μｍ'],'明确原文几何限制，不把未披露的控制/制程当事实。')
 patches.setdefault('google:58557302',dict(reason='机器译文中的位置数据—振动区域关系不清，保留综合贡献而不推断独立转换过程。',facets={},parameter_kind_fixes=[]))['ambiguity_notes_append']='摘要末句关于位置数据与振动区域对应关系的译文不清；保留综合贡献，独立控制步骤未确认。'
 patches['google:58557302']['mechanism_type']='COMPOSITE'
 edit('google:11818487','implementation',None,[],'模型实现字段在单词中途结束，且重复主机制；删除不完整实现句，保留完整来源支持的机制。')
 edit('google:75980650','technical_mechanism','将压电薄膜封装于贴在振动板上的可开封再封闭阻气部件内，并在部件内部与振动板相对贴附；由该封装同时支持防吸湿与元件更换。',['具有阻气性'],'原机制只剩普通双面电极膜，恢复可重复开封阻气封装这一具体结构。')
 edit('google:12129463','applicable_conditions','上下壳体绕一角滑动旋转形成开口；上壳的卡匣压肋在开壳时将内腔卡匣推向开口并弹出。',['rotated around one corner','cartridge pressing rib'],'补回推动卡匣弹出的压肋，不能仅以可开壳体概括退出机构。')
 edit('google:13893972','applicable_conditions','连接弹出旋钮与卡爪滑板的连杆绕偏向滑板侧的轴转动，弹簧沿卡匣弹出方向对旋钮施力。',['offset to the side'],'补回偏心连杆支点这一几何条件，不把普通连杆均视为同一退出机制。')
 edit('google:13508659','technical_problem',None,[],'摘要只给目的与构成，未明确旧装置只能如何工作；删除模型补造的旧技术能力陈述。')
 edit('google:13508659','applicable_conditions','多个蒸发源及加热装置设于仅用于输送系统的输送室；目标是在带状体上一次过程形成多层蒸镀膜。',['conveying room'],'摘要强调输送室位置；不补充热隔离、温度或室间结构。')
 edit('google:83455294','implementation',None,[],'原文只限定表面Rsk范围，没有给出调节粗糙度的制备工序；保留材料结构限定。')
 edit('google:56073954','implementation','采用气相成长法成膜；摘要没有进一步说明如何调节Si掺杂及晶相峰强比。',['気相成長法'],'保留原文气相成长方法，不把XRD观察条件改成实际制造控制步骤。')
 edit('google:38428973','expected_effect','摘要主张可在不高于900℃的低温下烧结并具有所需压电性；未给出实测性能数据。',['PROBLEM TO BE SOLVED:'],'区分发明目的/主张与已完成的实验结论。')
 edit('google:39377937','applicable_conditions','总容忍因子0.98≤TF(P)≤1.01，且TF(ADO3)>1、TF(BEO3)<1及TF(BEO3)<TF(CFO3)<TF(ADO3)。',['０．９８'],'补回源文的窗口及端元因子相对关系，避免仅以泛称容忍因子设计归并。')
 edit('google:13418014','applicable_conditions','双鼓中心高度错位，基材在狭缝内反向运行且两侧沉积膜不相擦；蒸发源开口位于狭缝下方共同切线所示阴影区外侧。精确方位依赖未提供附图，须核验。',['deviated heights','do not rub each other','on the side outer'],'恢复明确文字中的外侧约束，并保留精确几何需附图核验的限制。')
 edit('google:19085123','implementation','在可激振载台上放置含间隔吸附区分析单元的卡匣，并配置分别供给杂交液、探针液、洗液及抽出溶液的针；摘要未规定动作先后时序。',['excitable vibration table','hybridization solution injection pin','solution extraction pin'],'原文是装置构成列表，不能把列举顺序升级为实际杂交操作时序。')
 edit('google:34101262','technical_mechanism','交替电极层在相反的侧区露出第一电极材料端面，并在各层另一侧区的第二电极材料端面形成绝缘膜，构成交错引出与绝缘的层叠结构。',['first electrode layer','The second electrode layer'],'将原文已有的交错端面结构明确表达并补齐原文引句；不补制造参数。')
 edit('google:38149581','technical_mechanism','在0.1～5Pa条件下，使基板在蒸发单元上方做直线往复运动；按0<L1/L2<1.25配置蒸发单元及往复返回位置，L1和L2分别是摘要定义的垂直与水平几何距离。',['reciprocating straight above','0&lt;L','horizontal distance'],'原文的above表示位置，不能误写成垂直运动；恢复几何比与压力限制。')
 edit('google:42705590','technical_mechanism','在中空阴极等离子枪的等离子放出口与蒸镀室之间设置隔壁，隔壁具有可通过等离子的孔，从而在允许等离子通过的同时隔离两侧压力。',['ホローカソード型プラズマガン３のプラズマ放出部'],'hollow cathode是中空阴极，原文未披露Hall型；删除模型误译增加的霍尔限定。')
 edit('google:42705590','implementation','组合中空阴极等离子枪、蒸镀室及带等离子通孔的压差隔壁。',['ホローカソード型プラズマガン３のプラズマ放出部'],'hollow cathode是中空阴极，原文未披露Hall型；删除模型误译增加的霍尔限定。')
 edit('google:42705590','applicable_conditions','采用中空阴极等离子枪的等离子辅助蒸镀装置。',['ホローカソード型プラズマガン３'],'hollow cathode是中空阴极，原文未披露Hall型；删除模型误译增加的霍尔限定。')
 edit('google:41141126','implementation','各蒸发源的温度传感器测量加热容器距底部预定高度处的温度；到达预定温度后求测温均值，当测值达到或高于均值加预设温差时停止对应蒸发源的蒸发。',['底部から所定の高さ','平均値を求め'],'删除原文未披露的内部加热线圈与底部传感器说法，明确停止判据与对应蒸发源。')
 edit('google:41061590','technical_mechanism','在卷绕基材的旋转鼓与相对的RF成膜电极间隙供给原料气，使气体沿鼓旋转方向比沿鼓轴向更易流动。摘要未披露产生该流动差异的具体结构，不能仅归因于鼓的旋转。',['In the space'],'原文披露方向流动差异，没有说明是鼓转动单独造成；保留手段条件与实现未知边界。')
 edit('google:49387621','expected_effect','通过卡匣插入设备时遮盖识别码，抑制已用检验卡匣再次使用。',['when the inspection cartridge'],'遮码动作发生在插入时，不能改写成使用结束后才遮码。')
 edit('google:51400522','technical_problem',None,[],'外观新颖性声明不是已披露的工程问题，附图未提供，保持机制未披露。')
 edit('google:67297762','technical_problem',None,[],'外观新颖性声明不是已披露的工程问题，附图未提供，保持机制未披露。')
 patches.setdefault('google:34468469',dict(reason='模型两次仍合并多种相对独立办法；保留综合贡献，需人工原子拆分。',facets={},parameter_kind_fixes=[]))['ambiguity_notes_append']='摘要分别披露嵌件注塑、下斜排液肋及盖口端面厚度；两次模型均未稳定拆分。本条是待拆的综合贡献，不作为已完成原子分解的证据。'
 patches['google:34468469']['mechanism_type']='COMPOSITE'
 patches['google:92590282']['mechanism_type']='STRUCTURE'
 patches['google:98864925']['drop_parameter_names']=['最小電圧値','0[V]での傾き','最小電圧値V1での傾き']
 edit('google:44719320','technical_problem',None,[],'命名源文对读发现模型补写距离控制不精确的问题，原摘要仅披露结构；删除未披露问题和效果。')
 edit('google:44719320','technical_mechanism','沿带状基材输送方向，薄膜沉积电极的上游端部比周围接地屏蔽的对应上游端部更靠近基材。',['薄膜沉积电极沿输送方向的上游端部'],'删除模型附加的均匀性与稳定性效果，仅保留原文结构关系。')
 edit('google:44719320','expected_effect',None,[],'原摘要未声称提高均匀性、稳定性或改善质量，删除模型补写的效果。')
 edit('google:44719320','applicable_conditions','带状基材沿输送方向移动，接地屏蔽沿基材平面方向围绕薄膜沉积电极设置。',['在输送方向上输送基材的带的输送机'],'以摘要披露的带材和屏蔽布置替代泛化性能目标。')
 edit('google:14080699','technical_problem','抑制版材脏污并提高耐久性；另一目的的源文英译语义不清。',['to prevent a scumming'],'insensible fat productivity为不清晰机器译文，不能直接当作已理解的工程问题。')
 patches.setdefault('google:14080699',dict(reason='机器译文与缺失通式限制。',facets={},parameter_kind_fixes=[]))['ambiguity_notes_append']='源文insensible fat productivity语义不清；具体基团的通式图形未显示，仅有变量说明，不补造完整化学结构，需核对全文。'
 edit('google:40587181','technical_mechanism','以非Pb的A位元素与Nb、Ta、V、Sb、Mo、W中的B位元素共同取代PZT，材料通式及x、y、z范围受摘要组成关系限定。',['where Pb and A','Nb, Ta, V'],'A/B位共同取代与仅A位Bi/镧系取代不是相同具体组成方案；保持角色与原文范围。')
 edit('google:40587181','applicable_conditions','0.01<x≤0.4、0<y≤0.7、0.1≤z≤0.4；δ=0、w=3为标准值，保持钙钛矿结构范围内可偏离标准。',['0.01&lt;x≤0.4'],'修正原抽取把x的严格下界误写成含等号；不改源文目的与组成条件之间的粒度差异。')
 edit('google:40587181','implementation',None,[],'摘要披露材料组成与取代位置，没有给出实际制造工序；不把组成限定升级为制备步骤。')
 edit('google:40587181','expected_effect','摘要主张可在A、B位加入较多替代离子且A位缺陷较少；未给出实测性能数据。',['A site defects are few'],'删去未披露的结构稳定性提高结论，保留源文主张。')
 patches['google:40587181']['ambiguity_notes_append']='目的称B位替代超过10 mol%，组成通式却给z≥0.1；两种表述按原文分别保留，不自行消除边界差异。'
 edit('google:40130510','implementation',None,[],'摘要给出A位取代的组成窗口和目标，没有实际制造工序；保持制程未知。')
 save('evidence/ASSISTANT_SOURCE_AMENDMENTS.json',dict(version='assistant-source-amendment-v1',reviewer='AI assistant, not human Gold',raw_model_outputs_unchanged=True,families=patches))
 print(stable(dict(amended_families=len(patches))))
if __name__=='__main__':main()
