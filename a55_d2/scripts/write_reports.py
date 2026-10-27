"""Factual D2 reports, generated only after frozen and post-hoc data exist."""
from common import *
from posthoc_relevance import verify_freeze
import pandas as pd,collections,statistics
def md(x):return str(x if x is not None else 'n.a.').replace('|',' / ').replace('\n',' ')
def table(h,rows):return '\n'.join(['| '+' | '.join(h)+' |','|'+'|'.join(['---']*len(h))+'|']+['| '+' | '.join(md(v) for v in r)+' |' for r in rows])
def write(n,s):(W/'outputs'/n).write_text(s.strip()+'\n')
def union_seconds(rows):
 spans=sorted((datetime.datetime.fromisoformat(r['started_at']).timestamp(),datetime.datetime.fromisoformat(r['finished_at']).timestamp()) for r in rows if r['finished_at'])
 total=0;start=end=None
 for a,b in spans:
  if start is None:start,end=a,b
  elif a<=end:end=max(end,b)
  else:total+=end-start;start,end=a,b
 return total+(end-start if start is not None else 0)
def main():
 guard();freeze=verify_freeze();kb=load('working/all_selected/KB_RECORDS.json');cs=load('working/all_selected/contributions.json');cases=load('outputs/REAL_TECHNOLOGY_CASES.json')['cases']
 hist=load('outputs/HISTORICAL_VALIDATION.json');assert hist['completed']==45
 rel=load('outputs/PRINTHEAD_RELEVANCE.json');assert rel['completed']==rel['required']
 comp=load('outputs/D1_D2_COMPARISON.json')
 cm=load('outputs/CROSS_MODEL_COMPARISON.json');selected=set(pd.read_csv(W/'inputs/COHORTS.csv').query("role in ['primary','specified_control']").selection_id)
 pair_md=table(['左侧群','右侧群','重复族','共享候选节点','不同族/不同原文支持节点'],[[r['left'],r['right'],r['family_intersection'],r['shared_concept_count'],r['distinct_family_and_text_witness_count']] for r in cm['pairs'] if r['left'] in selected and r['right'] in selected])
 grouped=load('working/all_selected/CONTRIBUTION_GROUPS.json');proposal=load('working/all_selected/RELATION_PROPOSALS.json')
 audit=load('evidence/ASSISTANT_AUDIT80_RATINGS.json');assert len(audit['rows'])==80
 name_replays=load('evidence/NAME_VALIDATION_REPLAYS.json');name_review=load('evidence/NAMING_SOURCE_REVIEW.json');final_pair_review=load('evidence/FINAL_SOURCE_PAIR_REVIEW_APPLIED.json')
 concepts={t['technology_id']:t for t in kb['concepts']};ct={r['contribution_id']:r['technology_id'] for r in kb['patent_technology']}
 members=pd.read_parquet(W/'inputs/CLUSTER_MEMBERS.parquet');cohorts=pd.read_csv(W/'inputs/COHORTS.csv')
 conn=state_db();conn.row_factory=sqlite3.Row;req=[dict(r) for r in conn.execute('select * from requests order by started_at')];conn.close()
 options_by_kind={}
 for row in req:
  input_path=W/'requests'/(row['request_id']+'.input.json')
  if not input_path.exists():continue
  payload=load(str(input_path)).get('payload',{});options=payload.get('options',{})
  key=object_hash(options);entry=options_by_kind.setdefault(row['kind'],{}).setdefault(key,dict(options=options,requests=0));entry['requests']+=1
 options_by_kind={kind:list(sets.values()) for kind,sets in options_by_kind.items()}
 from performance_metrics import compute as performance_compute
 performance=performance_compute(req,union_seconds)
 cost=[]
 for kind in sorted({r['kind'] for r in req}):
  rr=[r for r in req if r['kind']==kind];p=[r['prompt_tokens'] for r in rr if r['prompt_tokens'] is not None];o=[r['output_tokens'] for r in rr if r['output_tokens'] is not None]
  cost.append(dict(kind=kind,requests=len(rr),repeated_cache_requests=sum(max(0,n-1) for n in collections.Counter(r['cache_key'] for r in rr).values()),receipts=len(p),input_tokens=sum(p) if p else None,output_tokens=sum(o) if o else None,mean_input=statistics.mean(p) if p else None,mean_output=statistics.mean(o) if o else None,original_contract_failures=sum(r['status']=='VALIDATION_FAILED' for r in rr),api_rejections=sum(r['status']=='API_REJECTED' for r in rr),network_failures=sum(r['status']=='NETWORK_FAILED' for r in rr),summed_request_wall_s=sum(r['wall_s'] or 0 for r in rr),interval_union_s=union_seconds(rr)))
 cost_md=table(['请求类型','请求数','已知输入token回执数','同键追加请求','输入token','输出token','均输入','均输出','原契约失败','API拒绝','网络失败','区间并集小时'],[[r['kind'],r['requests'],r['receipts'],r['repeated_cache_requests'],r['input_tokens'],r['output_tokens'],round(r['mean_input'],1) if r['mean_input'] is not None else None,round(r['mean_output'],1) if r['mean_output'] is not None else None,r['original_contract_failures'],r['api_rejections'],r['network_failures'],round(r['interval_union_s']/3600,3)] for r in cost])
 performance_md=table(['阶段','并发客户端','本段增量尝试族','规则弃判族','墙钟小时','族/小时'],[[w['stage'],w['client_concurrency'],w['incremental_families_attempted'],w['rule_abstention_families'],round(w['elapsed_s']/3600,3),round(w['observed_families_per_hour'],1) if w['observed_families_per_hour'] is not None else None] for w in performance['explicit_stage_windows']])
 extrapolation=performance.get('conditional_full_corpus_extraction_extrapolation')
 extrapolation_md=('以明确记录的对照批次吞吐作同分布条件外推，238,541族仅抽取阶段约'+str(round(extrapolation['days'],1))+'天；不含归并、命名、人审及当前质量修订。来源组成、模型、并发或服务性能不同则此数不适用。' if extrapolation else '没有适合直接外推的完整批次，未补造全库时间。')
 pair_receipts=[load(str(p)) for p in (W/'pairs').glob('*.json')];active_cids={c['contribution_id'] for c in cs};pair_receipts=[r for r in pair_receipts if {r['result']['left'],r['result']['right']}<=active_cids];same_check_counts=dict(collections.Counter(r.get('same_confirmation',{}).get('status','NO_SECOND_SAME_CHECK') for r in pair_receipts));pair_diagnostic=load('evidence/PAIR_ASSISTANT_SOURCE_REVIEW_APPLIED.json')
 syntax={}
 for r in req:
  p=W/'responses'/(r['request_id']+'.raw.json')
  if r['kind']=='embed' or not p.exists():continue
  raw=load(str(p));v=syntax.setdefault(r['kind'],dict(responses=0,json_parse_failures=0,truncated=0));v['responses']+=1;v['truncated']+=raw.get('done_reason')=='length'
  try:json.loads(raw['message']['content'])
  except (ValueError,KeyError,TypeError):v['json_parse_failures']+=1
 status={r['family_id']:r['status'] for r in kb['processing_status']};explicit={c['family_id'] for c in cs if c['evidence_level']=='EXPLICIT_MECHANISM'}
 primary=set(load('inputs/STAGES.json')['primary384']);pcs=[c for c in cs if c['family_id'] in primary];pt={ct[c['contribution_id']] for c in pcs if c['contribution_id'] in ct}
 bn=[t for t in concepts.values() if t['level']=='B'];an=[t for t in concepts.values() if t['level']=='A'];domains={concepts[t]['parent_technology_id'] for t in pt}
 cohort_rows=[]
 for co in cohorts.to_dict('records'):
  ids=set(members[members.selection_id==co['selection_id']].family_id);cc=[c for c in cs if c['family_id'] in ids];tt={ct[c['contribution_id']] for c in cc if c['contribution_id'] in ct}
  cohort_rows.append([co['selection_id'],int(co['population_size']),len(ids),sum(status[f]=='FAILED_VALIDATION' for f in ids),len(ids&explicit),len(cc),len(tt),'全群' if co['complete_cluster'] else '抽样'])
 cohort_md=table(['选择','群总体','抽取族','失败族','明确手段标签族','贡献/弃判记录','候选机制','覆盖'],cohort_rows)
 hc=[]
 for group in ['Recipe','Equipment']:
  for outcome in ['Mechanism Recovered','Broad Topic Only','Mechanism Missed','Insufficient Source Evidence']:
   rr=[r for r in hist['rows'] if r['history_group']==group and r['outcome']==outcome]
   hc.append([group,outcome,len(rr),sum(r['discovery_scope']=='CORE_DISCOVERY_COHORT' for r in rr)])
 hist_md=table(['历史组','恢复结果','族数','冻结发现范围内'],hc)
 cross=[]
 for t in bn:
  mm=[m for m in kb['cluster_technology'] if m['technology_id']==t['technology_id']]
  if t['family_count']<2 or t['distinct_source_text_count']<2 or len(mm)<2:continue
  byrun={}
  for m in mm:byrun.setdefault(m['run_id'],set()).add(m['cluster_id'])
  cross.append(dict(technology_id=t['technology_id'],name=t['name'],families=t['family_count'],multiple_clusters_in_same_run=any(len(s)>1 for s in byrun.values()),support_family_ids=json.loads(t['support_family_ids_json']),support_cids=json.loads(t['support_contribution_ids_json'])))
 save('outputs/CROSS_CLUSTER_MECHANISM_EVIDENCE.json',dict(rows=cross,rule='At least two Family IDs and two distinct source title/abstract texts; identical source clones and repeated placement of one family are excluded',scope='Selected cohorts only'))
 domain_rows=[]
 for aid in domains:
  t=concepts[aid];domain_rows.append([t['name'],len(set(json.loads(t['support_family_ids_json']))&primary),sum(concepts[tid]['parent_technology_id']==aid for tid in pt)])
 domain_md=table(['主群上层对象/问题域','支持主群族数','主群候选机制'],sorted(domain_rows,key=lambda r:(-r[1],-r[2],r[0]))[:12])
 witnesses=[];used_witnesses=set()
 for pair in cm['pairs']:
  if pair['left'] not in selected or pair['right'] not in selected:continue
  for row in pair['witnesses']:
   tid=row['technology_id']
   if tid in used_witnesses:continue
   used_witnesses.add(tid);witnesses.append([concepts[tid]['name'],tid,pair['left'],row['left_family_id'],pair['right'],row['right_family_id']])
 witness_md=table(['共用候选机制','Technology ID','左侧群','左侧族','右侧群','右侧族'],witnesses[:5])
 spans=sum(len(c['evidence_spans']) for c in cs);gaps=sum(bool(c['field_evidence_gaps']) for c in cs);rejected=sum(len(c.get('rejected_parameter_claims',[])) for c in cs);curated=sum(bool(c.get('curation_provenance_json')) for c in cs);refined=sum(bool(c.get('refinement_provenance_json')) for c in cs)
 case_text=[]
 for i,c in enumerate(cases,1):
  case_text.append(f"### {i}. {c['name']}\n\n{c['technology_id']} · {c['family_id']} · {c['domain']}\n\n原文（{c['source_field']}）：\n\n> "+c['evidence_report'].replace('\n','\n> ')+"\n\n喷头关联："+c['relevance']+"；证据性质："+c['evidence_origin']+"。")
 report="# A5.5-D2 真实技术发现\n\n"+"\n\n".join(case_text)
 report+=f"""

## 范围

冻结1117个唯一族、1688条选定群来源关系，原238,541族向量与聚类只读复用。未重编码、未重聚类。本轮不是全库穷尽知识库。以下机制数量均为当前候选，不是人类真值。

{cohort_md}

## 十个问题

1. **主群有多少机制？** 384族全部尝试，{len(primary&explicit)}族有明确手段标签，{len(pcs)}条贡献/弃判记录，其中{sum(c['evidence_level']=='EXPLICIT_MECHANISM' for c in pcs)}条有明确手段标签；归并为{len(pt)}个候选机制节点。缺少独立人审与穷尽比较，不能把候选数当真实不同机制总数。
2. **哪些具体技术可识别？** 首页20例均可回到族、原字段、逐字原文。晶种定向生长、氧空位补偿、粉体撞击沉积、互耐蚀硬掩膜及非目标领域案例展示了来源支持的具体办法。来源支持范围是摘要披露，不是Claims或实际采用。
3. **群内路线是否不同？** 是。结构、材料组成、加工和驱动办法并存；主群候选分入{len(domains)}个开放对象/问题域。域标签仍需人审整合，不能仅靠域数量判断质量。
4. **是否跨群复用？** {len(cross)}个候选节点由不同Family ID且不同原文支持，并关联多个选定群，其中{sum(r['multiple_clusters_in_same_run'] for r in cross)}个跨同一run不同群。CID、Family和理由见CROSS_CLUSTER_MECHANISM_EVIDENCE.json与关系表；单族在多模型重复出现不作为技术一致证明。
5. **是否明显优于群级主题归纳？** D1已允许多主题、原文引句和M:N关系；D2新增逐族贡献层、坐标证据与机制成对归并，使每族限定和差异更易追溯。但覆盖、调用成本与助手修订不同，未建立同成本的独立人类Gold对照，不能宣称语义准确率显著提高。
6. **设备、工艺、材料可否区分？** 可在贡献层区分结构、过程、控制、材料/化学、计算及复合办法。压差隔壁、先蚀硬掩膜再蚀压电膜、组成/晶相限定提供真实来源例子；不从Cluster ID推导类别。
7. **信息不足如何避免伪造？** 仅标题确定性弃判，保留标题并记录零模型调用。外观声明无附图、缺公式或未披露手段的摘要保留不足/未披露/不确定。符号定义不当作数值参数；不合契约的模型值留在拒收审计而不进入事实参数。失败不等于无技术价值。
8. **历史45族恢复如何？** 以下为冻结后的AI源文回归，不是独立人工真值。范围外探针另列；历史标签不补写摘要，历史回归不推出未知技术全库Recall。

{hist_md}

9. **随机及非目标群有效吗？** 两个随机中群、混合抽样、紧密小群和Noise均纳入。真实出现蛋白稳定性建模、CO2饱和pH膜、扫描单元吸附增重避振等办法。部分紧密群只有标题或外观模板；语义紧密不保证摘要可抽机制。各组真实分母见上表。
10. **能否扩展238,541族？** 缓存、稳定ID、近邻候选与有限关系比较已构成增量原型，本轮未执行全库抽取。当前质量尚不适合无人复核的全库生产。主要成本是逐族生成、关系比较、命名和源文复核；瓶颈是关键限定、参数/单位、公式和多贡献拆分。应分片逐批扩大并保留人审；本轮偏向目标领域的吞吐与质量不能直接作为全库保证。

## 跨模型与跨群对照

{pair_md}

以上是统一贡献库归并后的共用节点，不是各Embedding模型独立发现相同技术的准确率。重复族单独计数；最后一列要求双侧至少存在不同Family ID、不同Title/Abstract的来源。不同Family ID及不同文字仍不证明独立发明，未核对优先权链或跨族翻译重复。完整逐族位置见ALL_SELECTED_FAMILY_POSITIONS.parquet；全55对群和机制类型分布见CROSS_MODEL_COMPARISON.json。抽样群的结果只代表抽到的成员。

## 主群主要开放域

{domain_md}

目录从平衡选取的120个源文机制样本开放归纳，再逐机制按对象/问题归类；源标签同义归一的中间版单独保留。目录不表示同域全部机制物理等价，不能当作已定型技术树。

## 不同来源的跨群复用实例

{witness_md}

两侧Family ID可在贡献表回到完整原文和具体限制；共享ID是候选共同机制，来源特有条件保留在贡献。

## 关系召回范围

本轮新贡献描述近邻使用k={proposal['k']}，初始提议{len(proposal['pairs'])}对，另补组内一致性检查。受成本约束采用有限候选；它会漏掉未被近邻提议的同机制对，因此最终候选节点数既受抽取完整性影响，也可能被欠归并抬高。所有未比较对保持未判断，不能当成不同技术。最终{grouped['group_count']}组由第二轮Same确认及保守一致性规则构建；两轮模型判断均不是独立Gold。

## 实际调用

{cost_md}

“同键追加请求”统计每种请求类型按cache_key重复发起的请求数，包含校验重试、断点恢复和有意重试；不能解读为只有网络重试。贡献/有效族均值为{len(cs)/sum(v=='VALID' for v in status.values()):.3f}，最终失败率为{sum(v=='FAILED_VALIDATION' for v in status.values())/len(status):.2%}。

以上仅统计LAN Ollama回执，不含Codex对话token。调试、失败、二次抽取全部记账。并发请求耗时之和包含排队和重叠，不是GPU计算小时；区间并集也包含网络服务等待。累计token仅统计已有回执；网络超时未返回的生成量未知，缺失不当零。HTTP拒绝不当已生成内容。原始在线契约失败、JSON语法失败与离线重放通过分别记录。

{performance_md}

{extrapolation_md}

实际吞吐与运行耗时另见 PERFORMANCE_METRICS.json：包含显式阶段时间、模型请求区间并集、项目首末请求墙钟时间和有条件的全库抽取外推。队列等待及开发/断网间隔不当成GPU计算时间。

## 可追溯性与限制

五类核心逻辑表在SQLite和Parquet中按ID联查；Excel提供阅读与人工修订。完整Title/Abstract保留，{spans}个证据片段逐个核对字符坐标。{gaps}条贡献仍有字段标记缺口；{curated}条含助手原文修订，{refined}条采用二次抽取，{rejected}个参数提议未进入事实参数表。原始响应未改写。程序VALID不是语义准确，助手复核不是人类Gold。
核心定义先冻结，之后才开展喷头相关性、历史核验和D1对照。Transferable是有条件工程推断，不表示实际采用。混合群与Noise只覆盖抽样成员。
"""
 write('D2_REPORT.md',report)
 errors="""## 已证实的错误与边界

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

"""
 quality=f"# 抽取质量\n\n范围1117族，状态{dict(collections.Counter(status.values()))}，贡献/弃判记录{len(cs)}条（明确手段贡献{sum(c['evidence_level']=='EXPLICIT_MECHANISM' for c in cs)}条），明确手段标签族{len(explicit)}个。逐字/坐标通过{spans}条，只代表结构与复制完整性。\n\n固定80族有源文预读与逐族AI对照记录；人审栏留空，没有独立Gold，不提供全样本语义准确率。\n\n"+errors+f"当前{gaps}条贡献有字段证据缺口，{rejected}个参数提议被留在拒收记录，{curated}条含助手修订。不能用修订后结果冒充原始模型准确率。\n\n## 归并诊断\n\n当前有效贡献的原第二轮Same检查状态（包含后来又经助手撤销的判断）：{same_check_counts}。固定随机抽查十对原始Same提议，并诊断六对当时已双轮确认的Same。源文诊断指出共同材料、对象和上位结构可能掩盖具体办法；其中仍残留的{pair_diagnostic['same_downgrades']}对Same在命名前由助手按原文撤销，记录及原始响应均保留。该小样本是AI诊断，不是独立人工精确率。逐字相同摘要即使Family ID不同，也不当两份独立佐证。\n\n## 归并边界\n\n向量只提候选，Same由双侧源文LLM判断，并另作一次保守源文复核；两轮同意才可支持归并。两轮均是同一本地模型，不是独立人类Gold。小组要求全对Same，大组双锚点加冲突否决。未比较不当Uncertain。对象/问题域组织与机制范围继承分开，循环继承暂缓；关系均是可追溯候选。有限近邻不能保证找齐同义技术。\n\n## 命名及源文修订\n\n{len(name_replays['rows'])}个命名记录由原响应离线重校验恢复，可选备注null只转为空字符串，原始在线失败状态保留；无新模型调用。{len(name_review['curated_names'])}条命名源文修订及{len(name_review.get('contribution_corrections',[]))}处后续贡献修订有单独审计，最终另区分{len(final_pair_review['rows'])}对凸起结构相关的来源关系。\n\n## 成本\n\n"+cost_md+"\n\nJSON语法统计："+stable(syntax)
 review_queue_progress=load('evidence/AUDIT80_PROGRESS.json')
 history_source_review=load('evidence/HISTORICAL_ASSISTANT_REVIEW.json');assert history_source_review['reviewed']==45
 cross_route_review=load('evidence/HISTORICAL_CROSS_ROUTE_SOURCE_REVIEW.json')
 source_review=load('evidence/RELEVANCE_SOURCE_REVIEW_SUMMARY.json')
 assistant_relevance=load('evidence/RELEVANCE_ASSISTANT_SOURCE_REVIEW.json')
 known_issues=load('evidence/KNOWN_FROZEN_DEFINITION_ISSUES.json')
 review_counts=dict(collections.Counter(r['category'] for r in rel['results']))
 cross_route_md=table(['Technology ID','已知源文差异/误并','处置'],[[r['technology_id'],r['reason'],r['action']] for r in cross_route_review['rows']])
 report=report.replace('## 十个问题','## 已知冻结结果质量问题\n\n以下两组在冻结后对读原文确认存在具体手段差异；保留错误作为实验结果，未借历史名称回改。926仅为候选节点数，含误并及欠归并，不能视为真实机制总量。\n\n'+cross_route_md+'\n\n## 十个问题',1)
 report+='\n\n## 喷头关联源文复核\n\n'+str(source_review['completed'])+'个节点经定向复核（全部首轮正向关联及命中头部词的非正向案例）；'+str(len(source_review['category_changes']))+'个类别发生修订。关键词只用于复核选样，不决定最终类别。首轮保留在PRINTHEAD_RELEVANCE_FIRST_PASS.json，最终926个B级机制类别计数：'+stable(review_counts)+'。26个A级对象/问题域显示其全部子机制的分类分布，不强制将混合领域归成一种喷头关系。这不是随机精度抽样或人类Gold。\n\n已知冻结定义/抽取疑点：'+ '；'.join(r['family_id']+' '+r['issue'] for r in known_issues['rows'])+'。其余事后发现的冻结定义疑点见RELEVANCE_SOURCE_REVIEW_SUMMARY.json。核心不受历史揭盲后的修订污染，阅读时以原文和贡献限定为准。'
 witness_review=load('evidence/CROSS_SOURCE_WITNESS_REVIEW.json')
 report+='\n\n## 跨群候选的源文边界复核\n\n'+table(['Technology ID','源文诊断','边界'],[[r['technology_id'],r['status'],r['note']] for r in witness_review['rows']])+'\n\n以上保留冻结节点并明确边界，不在看到历史参照后改组。尚未经独立人审，不能将共同节点计数转为等价精确率。'
 write('D2_REPORT.md',report)
 quality+='\n\n助手最终对读'+str(assistant_relevance['reviewed'])+'个相关性案例，判断及原始模型响应分别保存；其中早先未通过本地契约的5项，经真实原文审查采用助手判断，明确标为ASSISTANT而非本地模型成功。字符规则漏识别drop/droplet、delivering head及液体喷出等真实措辞导致过误拒收，修复与回读另存；契约失败数不能直接解释成模型语义错误率。'
 quality+='\n\n## 相关性复核接口失败与修复\n\n原双节点复核230项，仅54项整批通过；其余有目标字段缺失或源片段编号错误。按同一逐项契约离线恢复'+str(len(load('evidence/RELEVANCE_INDIVIDUAL_REPLAY.json')['recovered']))+'项，未新增模型调用；失败批次状态未改为成功。剩余采用单概念、全局X源片段枚举的独立协议补跑；缓存、Prompt/Schema与采用映射另存，原始错误和成本保留。格式通过仍不是工程关联判断准确。'
 quality+='\n\n主人工审核队列'+str(review_queue_progress['editable_review_rows'])+'族，包含固定80族、已知语义疑点、处理失败与独立事后探针。全量'+str(review_queue_progress['all_review_flag_rows'])+'族的引用/参数标记保存在ALL_REVIEW_FLAGS.parquet，未进入主审核页不代表问题已解决。'
 quality+='\n\n## 冻结后相关性与命名疑点\n\n定向相关性复核'+str(source_review['completed'])+'个节点，类别修订'+str(len(source_review['category_changes']))+'个；样本偏向可疑与正向案例，不估计总体准确率。保留首轮与复核请求、逐字S源片段。\n\n'+table(['Family ID','已知冻结定义疑点','处理'],[[r['family_id'],r['issue'],r['action']] for r in known_issues['rows']])+'\n\n其他冻结定义疑点：'+stable(source_review['frozen_definition_issues'])
 write('EXTRACTION_QUALITY.md',quality)
 write('HISTORICAL_TECHNOLOGY_VALIDATION.md','# 历史技术事后回归\n\n核心冻结：'+freeze['at']+'。历史名称未用于抽取、归并、命名或层级。以下为AI源文核验，待人审；范围外补充探针不得冒充首次发现。\n\n'+hist_md+'\n\n'+table(['Family ID','组','覆盖','结果','理由'],[[r['family_id'],r['history_group'],r['discovery_scope'],r['outcome'],r['reason']] for r in hist['rows']])+'\n\n历史只是已知路线回归，不能推出全库未知技术Recall。')
 comparison_metrics=comp['operational_metrics']
 comparison_detail='\n\n## 相同代表族子集\n\n'+table(comp['same_input_family_headers'],comp['same_input_family_rows'])+'\n\nD2此处仅计D1面板内Family ID所连接的冻结全局节点。D1只读前1200字符，D2读完整摘要并使用全池归并；子集相同也不意味着同等信息量或成本。手段非空不是机制正确，字面匹配不是语义支持。\n\n## 可观测质量指标及分母\n\n'+table(['指标','D1式群级命名','D2逐族贡献'],[
 ['记录单位',str(comparison_metrics['d1']['theme_records'])+'条主题',str(comparison_metrics['d2']['contribution_or_abstention_records'])+'条贡献/弃判'],
 ['字面来源追溯',str(comparison_metrics['d1']['literal_verified_references'])+'/'+str(comparison_metrics['d1']['literal_evidence_references'])+'引用逐字匹配',str(comparison_metrics['d2']['all_source_spans'])+'源片段逐字及坐标检查'],
 ['机制表示（结构指标）',str(comparison_metrics['d1']['themes_with_nonempty_means'])+'主题手段字段非空',str(comparison_metrics['d2']['explicit_mechanism_records'])+'贡献有明确手段标签'],
 ['不足/不确定（单位不同）',str(comparison_metrics['d1']['insufficient_theme_records'])+'/'+str(comparison_metrics['d1']['theme_records'])+'主题无法确定',str(comparison_metrics['d2']['nonexplicit_records'])+'/'+str(comparison_metrics['d2']['contribution_or_abstention_records'])+'记录无明确手段'],
 ['重复合并（规则不同）',str(comparison_metrics['d1']['exact_string_duplicate_named_records'])+'具名记录按名称/对象/手段完全字符串去重',str(comparison_metrics['d2']['contribution_reduction_into_candidates'])+'贡献经候选等价归并减少；'+str(comparison_metrics['d2']['nodes_with_distinct_source_texts'])+'节点有不同原文'],
 ['混合技术真实拆分率','无法测量：无独立机制清单','无法测量：多节点数不能替代拆分准确率'],
 ['独立语义准确率','未建立人工Gold','未建立人工Gold']
 ])+'\n\n逐字证据中标题、重复片段或重复原文可能同时出现，不代表独立发明证据。当前程序可逐条回查，引文支持何种机制仍待人审。调用成本见下表；未把共同缓存调用重复归属每个Cluster。'
 write('EXPERIMENT_COMPARISON.md','# D1群级主题归纳与D2逐族抽取\n\n'+comp['method_notes']+'\n\n'+table(comp['headers'],comp['rows'])+comparison_detail+f'\n\nD2共{len(cs)}条贡献、{len(bn)}候选机制，{gaps}条字段引用缺口。更多、更细名称不自动表示更准确。原文覆盖、成本、修订和审核条件不同，没有独立人类Gold下的同成本准确率对照。\n\n'+cost_md)
 history_path=W/'outputs/HISTORICAL_TECHNOLOGY_VALIDATION.md'
 history_path.write_text(history_path.read_text()+'\n\n## AI源文复核链\n\n45族均经助手原文与冻结贡献对读；对本地模型分类修订'+str(len(history_source_review['category_changes']))+'项。原始本地判断单独保留在HISTORICAL_VALIDATION_LOCAL_MODEL.json，修订理由/作者性质/原请求ID逐行可查。两者均不是独立人工Gold。\n\n## 不同历史路线共用节点的源文诊断\n\n'+cross_route_md+'\n\n同一节点关联不同历史标签本身不能证明误并；这里的判断来自双方原始摘要中明确不同的结构/材料窗口。核心未调整，原始判定和源文仍可追查。\n')
 quality_path=W/'outputs/EXTRACTION_QUALITY.md'
 quality_path.write_text(quality_path.read_text()+'\n\n## 冻结后确认的归并差异\n\n'+cross_route_md+'\n')
 gates=[
 dict(gate='Gate 1 逐族抽取',status='STRUCTURE_PASSED_WITH_KNOWN_SEMANTIC_LIMITS',evidence='Schema、完整源文与'+str(spans)+'个逐字坐标通过；多贡献接口已实际使用，但仍有未可靠原子化及泛化问题，非独立语义准确率验收。'),
 dict(gate='Gate 2 主群384',status='ALL_FAMILIES_ATTEMPTED',evidence='384族全部尝试；有效'+str(sum(status[f]=='VALID' for f in primary))+'，失败'+str(sum(status[f]=='FAILED_VALIDATION' for f in primary))+'；明确手段标签族'+str(len(primary&explicit))+'，候选机制'+str(len(pt))+'。'),
 dict(gate='Gate 3 跨群归并',status='FUNCTIONAL_COMPLETE_WITH_KNOWN_OVERMERGES',evidence='指定群与控制组完成选定范围；M:N及稳定ID可复用；事后原文诊断确认两组具体结构/材料窗口差异仍共用节点，不能宣称归并语义质量全部达标。'),
 dict(gate='Gate 4 历史核验',status='45_CASES_CHECKED_BY_AI',evidence='Recipe27/Equipment18；39个主发现范围、6个独立事后源文探针；人工Gold0，不能推导未知全库Recall。'),
 dict(gate='Gate 5 原型交付',status='AWAITING_FINAL_DELIVERY_INTEGRITY_CHECK',evidence='报告、8表工作簿、Parquet、SQLite、请求与修订链；最终文件/回读/完整性收据另见FINAL_INTEGRITY_CHECKS.json。')
 ]
 save('outputs/GATE_ASSESSMENT.json',dict(at=now(),gates=gates,semantic_accuracy_verified=False,human_gold_families=0))
 report_path=W/'outputs/D2_REPORT.md'
 report_path.write_text(report_path.read_text()+'\n\n## 验收口径\n\n'+table(['Gate','完成状态','依据与边界'],[[g['gate'],g['status'],g['evidence']] for g in gates])+'\n')
 import pyarrow.parquet as pq
 parquet_schemas={p.name:[dict(name=f.name,type=str(f.type),nullable=f.nullable) for f in pq.read_schema(p)] for p in sorted((W/'outputs').glob('*.parquet'))}
 files=lambda folder,pattern:{str(p.relative_to(W)):sha(p) for p in sorted((W/folder).glob(pattern)) if p.is_file()}
 save('outputs/PERFORMANCE_METRICS.json',performance)
 save('outputs/EXPERIMENT_MANIFEST.json',dict(performance=performance,at=now(),task='A5.5-D2',task_package_sha256=sha(W/'TASK_PACKAGE.md'),output_parquet_schemas=parquet_schemas,evidence_offset_convention='Unicode code points, Python str indexing, half-open [start,end)',scope_families=1117,selected_memberships=1688,core_freeze=freeze,runtime_environment=load('evidence/RUNTIME_ENVIRONMENT.json'),actual_generation_options_by_kind=options_by_kind,request_summary=cost,name_validation_replays=name_replays,naming_source_review=name_review,final_source_pair_review=final_pair_review,same_confirmation_status_counts=same_check_counts,json_syntax_stats=syntax,request_status_counts=dict(collections.Counter(r['status'] for r in req)),source_locks=load('inputs/SOURCE_LOCKS.json'),dataset_freeze=load('inputs/DATASET_FROZEN.json'),selection_rules=load('inputs/SELECTION_RULES.json'),audit_selection=load('inputs/AUDIT_SELECTION.json'),model_lock=load('evidence/MODEL_LOCK.json'),embedding_lock=load('vectors/MODEL_LOCK.json'),code_sha256=files('scripts','*'),prompt_sha256=files('prompts','*'),schema_sha256=files('configs','*.json'),actual_generation_options_and_code='Per-request inputs/raw receipts plus code_snapshots',historical_assistant_source_review=history_source_review,historical_cross_route_source_review=cross_route_review,cross_source_witness_review=witness_review,assistant_relevance_source_review=assistant_relevance,relevance_individual_replay=load('evidence/RELEVANCE_INDIVIDUAL_REPLAY.json'),relevance_repair_adoptions=load('evidence/RELEVANCE_REPAIR_ADOPTIONS.json'),posthoc_relevance_source_review=source_review,known_frozen_definition_issues=known_issues,historical_source_input_lock=load('evidence/HISTORICAL_INPUT_PREPARED.json'),historical_probe_summary=load('evidence/HISTORICAL_PROBE_SUMMARY.json'),domain_seed_selection=load('evidence/DOMAIN_SEED_SELECTION.json'),new_description_vector_files=len(list((W/'vectors').glob('*.npy'))),active_explicit_contribution_rows=sum(c['evidence_level']=='EXPLICIT_MECHANISM' for c in cs),human_gold_families=0,semantic_accuracy_estimate=None,raw_patents_reencoded=0,reclustering_runs=0,github_publication_performed=False))
 print(stable(dict(reports_written=4,manifest_written=True,requests=len(req))))
if __name__=='__main__':main()
