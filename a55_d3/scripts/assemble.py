from common import *
from design import DIM
from pipeline import claims,spans
from experiments import active_main,active_comparison
from metrics import collect_comparisons,make_metrics,relevance_metrics
from client import estimate
import collections,copy,statistics,os
import pyarrow as pa,pyarrow.parquet as pq

OUTDIR=W/'outputs/01a171fb-0dd6-7792-b36b-80e200aba942'
GOOD={'Explicit','Supported Paraphrase'}
def text(v):return stable(v) if isinstance(v,(dict,list)) else v
def brief(v):
 if not v:return ''
 if isinstance(v,list):return '\n'.join(brief(x) for x in v)
 if 'core_mechanism' in v:return v['core_mechanism'].get('text') or ''
 a=v.get('technical_mechanism');return a.get('text') or '' if isinstance(a,dict) else str(a or '')
def para(name,rows):
 p=W/name;write_guard(p)
 if rows:pq.write_table(pa.Table.from_pylist(rows),p,compression='zstd')
 else:pq.write_table(pa.table({'no_records':pa.array([],pa.string())}),p,compression='zstd')
 return p

def audit_rows(doc,record):
 result=[];phases=[('original',record['original'],record['audit'],record['original_request_id'],record['audit_request_id'])]
 for i,r in enumerate(record.get('revisions',[]),1):phases.append(('revision_'+str(i),r['result'],r['audit'],r['request_id'],r['audit_request_id']))
 sm={s['id']:s for s in spans(doc)}
 for phase,ex,au,rid,aid in phases:
  final=rid==record['final_request_id'];am={a['path']:a for a in au['field_audits']}
  for claim in claims(ex):
   path=claim['path'];a=am[path];ss=[sm[e] for e in claim['evidence_ids']];ok=all((doc.get(s['field']) or '')[s['start']:s['end']]==s['text'] for s in ss)
   assert ok,'Exact Unicode source mismatch'
   result.append(dict(family_id=doc['family_id'],version='D3.1',phase=phase,is_final=final,level='FIELD',field_path=path,field_text=claim['text'],grade=a['grade'],rationale=a['reason'],source_text_hash=doc['text_hash'],evidence_ids=claim['evidence_ids'],source_spans_json=stable(ss),span_reference_count=len(ss),level1_exact_pass=ok,source_supported_silver=a['grade'] in GOOD,human_confirmed=False,extraction_request_id=rid,audit_request_id=aid,source_adequacy=au['source_adequacy']))
  result.append(dict(family_id=doc['family_id'],version='D3.1',phase=phase,is_final=final,level='CONCLUSION',field_path='$contributions',field_text=brief(ex['contributions']),grade=au['conclusion_grade'],rationale=stable(au['errors']),source_text_hash=doc['text_hash'],evidence_ids=[],source_spans_json='[]',span_reference_count=0,level1_exact_pass=True,source_supported_silver=au['conclusion_grade'] in GOOD,human_confirmed=False,extraction_request_id=rid,audit_request_id=aid,source_adequacy=au['source_adequacy']))
 return result

def main():
 guard();OUTDIR.mkdir(exist_ok=True,parents=True)
 docs=load('inputs/ALL_DOCUMENTS.json');dm={d['family_id']:d for d in docs};selection=load('inputs/EVALUATION_SELECTION.json');split={r['family_id']:r['split'] for r in selection}
 frozen=load('evidence/MODEL_FREEZE.json')
 for p,h in frozen['semantic_code_hashes'].items():assert sha(W/p)==h,'Frozen semantic code changed: '+p
 for p,h in load('inputs/D2_LOCK.json')['files'].items():assert sha(D2/p)==h,'D2 input modified: '+p
 mainrows={f:active_main(f) for f in dm};mainrows={f:r for f,r in mainrows.items() if r}
 status=[]
 for f,d in dm.items():
  p=W/'working/status'/('full_'+f.replace(':','_')+'.json');r=load(p) if p.exists() else dict(family_id=f,status='UNPROCESSED')
  if f not in mainrows and r['status'] in ['VALID','QUARANTINED']:r=dict(r,status='STALE_NOT_CURRENT')
  status.append(dict(family_id=f,split=split.get(f,'main_outside_evaluation'),source_text_hash=d['text_hash'],source_content_sha256=oh({k:d.get(k) for k in ['title','abstract']}),source_title=d['title'],source_abstract=d['abstract'],status=r['status'],error=r.get('error'),source_status=mainrows[f]['final']['source_status'] if f in mainrows else None))
 assert len(status)==1117 and all(r['status']!='UNPROCESSED' for r in status),'Main still running'
 old=json.loads((D2/'working/all_selected/contributions.json').read_text());oc=collections.defaultdict(list)
 for c in old:oc[c['family_id']].append(c)
 pt=pq.read_table(D2/'outputs/PATENT_TECHNOLOGY_RELATIONS.parquet').to_pylist();ft=collections.defaultdict(set)
 for p in pt:ft[p['family_id']].add(p['technology_id'])
 d2_rel_map={r['technology_id']:r['category'] for r in json.loads((D2/'outputs/PRINTHEAD_RELEVANCE.json').read_text())['results']}
 contrib=[];audits=[];errors=[]
 for f,rec in mainrows.items():
  d=dm[f];am={a['path']:a for a in rec['final_audit']['field_audits']};ss=spans(d)
  audits+=audit_rows(d,rec)
  for i,c in enumerate(rec['final']['contributions']):
   prefix=f'contributions[{i}]';aa={p:a for p,a in am.items() if p.startswith(prefix+'.')};supported=[p for p,a in aa.items() if a['grade'] in GOOD];inferred=[dict(path=p,grade=a['grade'],reason=a['reason']) for p,a in aa.items() if a['grade']=='Inferred'];withheld=[dict(path=p,grade=a['grade'],reason=a['reason']) for p,a in aa.items() if a['grade'] in ['Partial','Unsupported','Insufficient']]
   cid='D3C_'+oh([f,d['text_hash'],c])[:24]
   contrib.append(dict(family_id=f,contribution_id=cid,version='D3.1',record_type='CANDIDATE_CONTRIBUTION',processing_status=rec['status'],source_status=rec['final']['source_status'],source_text_hash=d['text_hash'],source_content_sha256=oh({k:d.get(k) for k in ['title','abstract']}),source_title=d['title'],source_abstract=d['abstract'],language=d.get('language'),publication_id=d.get('publication_id'),parent_d2_contribution_ids=[x['contribution_id'] for x in oc[f]],d2_technology_ids=sorted(ft[f]),d2_link_semantics='same-family version references; no automatic one-to-one equivalence',local_id=c['local_id'],technical_object=c['technical_object']['text'],technical_problem=c['technical_problem']['text'],core_mechanism=c['core_mechanism']['text'],implementation=c['implementation']['text'],materials_json=stable(c['materials']),composition_json=stable(c['composition']),process_steps_json=stable(c['process_steps']),process_conditions_json=stable(c['process_conditions']),equipment_components_json=stable(c['equipment_components']),control_variables_json=stable(c['control_variables']),technical_effects_json=stable(c['technical_effects']),evidence_spans_json=stable(ss),field_support_json=stable(aa),supported_candidate_paths=supported,inferences_json=stable(inferred),withheld_claims_json=stable(withheld),uncertainty=c['uncertainty'],full_conclusion_grade=rec['final_audit']['conclusion_grade'],silver_supported_candidate=rec['status']=='VALID' and all(a['grade'] in GOOD for a in aa.values()) and rec['final_audit']['conclusion_grade'] in GOOD,human_confirmed=False,model='deepseek-flash',model_digest=None,original_request_id=rec['original_request_id'],final_request_id=rec['final_request_id'],final_audit_request_id=rec['final_audit_request_id'],modification_source='DeepSeek original / bounded DeepSeek audit revision; no Codex semantic substitution',adoption_reason=rec['adoption_reason'],created_at=rec['at']))
  for stage,au in [('original',rec['audit']),('final',rec['final_audit'])]:
   finaltypes={e['type'] for e in rec['final_audit']['errors']}
   for e in au['errors']:
    sm={s['id']:s for s in spans(d)};ev=[sm[x] for x in e['evidence_ids'] if x in sm]
    errors.append(dict(family_id=f,stage=stage,error_type=e['type'],description=e['description'],evidence_spans_json=stable(ev),d2_result=brief(oc[f]),d3_result=brief(rec['final']['contributions']),source_title=d['title'],source_abstract=d['abstract'],source_text_hash=d['text_hash'],root_cause_silver=e['description'],fix_status='Still flagged by final Silver audit' if e['type'] in finaltypes else 'Not re-flagged after model revision; not human verified',change=rec['adoption_reason'],needs_full_text=e['needs_full_text'],label_tier='Silver',human_confirmed=False))
 for s in status:
  if s['status']=='FAILED':errors.append(dict(family_id=s['family_id'],stage='processing',error_type='Model Output Failure',description=s['error'] or 'Unknown',evidence_spans_json='[]',d2_result=brief(oc[s['family_id']]),d3_result=None,source_title=s['source_title'],source_abstract=s['source_abstract'],source_text_hash=s['source_text_hash'],root_cause_silver=None,fix_status='Terminal bounded failure; not abstention',change=None,needs_full_text=False,label_tier='Automatic',human_confirmed=False))
 para('D3_PATENT_CONTRIBUTIONS.parquet',contrib);para('D3_EVIDENCE_AUDIT.parquet',audits);para('D3_PROCESSING_STATUS.parquet',status);para('D3_ERRORS.parquet',errors)
 comparisons=collect_comparisons();metrics=make_metrics(comparisons)
 nodes=[load(p) for p in sorted((W/'working/node_relevance').glob('*.json'))];rm,confusions,relconflicts=relevance_metrics(mainrows,nodes);metrics+=rm
 finalfields=[r for r in audits if r['is_final'] and r['level']=='FIELD'];finalconc=[r for r in audits if r['is_final'] and r['level']=='CONCLUSION' and mainrows[r['family_id']]['final']['contributions']]
 def metric(name,num,den,tier='Automatic',notes='',unit='rate'):metrics.append(dict(scope='main_1117',split='all',configuration='D3_FULL',metric=name,numerator=num,denominator=den,value=num/den if den else None,label_tier=tier,sample_n=1117,unknown_n=1117-len(mainrows),unit=unit,notes=notes))
 metric('processing_success_rate',len(mainrows),1117,notes='Includes quarantined outputs; not semantic correctness')
 metric('quarantined_family_rate',sum(r['status']=='QUARANTINED' for r in mainrows.values()),1117,notes='Original/modified output retained; not accepted as fully supported facts')
 metric('failure_rate',sum(r['status']=='FAILED' for r in status),1117)
 metric('abstention_rate',sum(not r['final']['contributions'] for r in mainrows.values()),len(mainrows),notes='Only successful outputs with no disclosed mechanism; failures excluded')
 metric('mean_contributions_per_attempted_family',len(contrib),1117,unit='contributions/family')
 metric('level1_exact_span_reference_rate',sum(r['span_reference_count'] for r in finalfields if r['level1_exact_pass']),sum(r['span_reference_count'] for r in finalfields),notes='Programmatic Unicode [start,end) exactness; not semantic accuracy')
 metric('level2_field_support_rate',sum(r['grade'] in GOOD for r in finalfields),len(finalfields),'Silver',notes='Independent same-model source re-read; explicit/supported paraphrase only')
 metric('level3_conclusion_support_rate',sum(r['grade'] in GOOD for r in finalconc),len(finalconc),'Silver',notes='Nonempty family conclusions; not human accuracy')
 metric('human_gold_accuracy',None,None,'Gold',notes='N/A: no independent humans')
 para('D3_METRICS.parquet',metrics);para('D3_RELEVANCE_CONFUSIONS.parquet',confusions)
 labels=[]
 for r in comparisons:
  for conf,s in r['scores'].items():
   for dim,label in s['dimensions'].items():labels.append(dict(family_id=r['selection']['family_id'],split=r['selection']['split'],configuration=conf,dimension=dim,label=label,label_tier='Silver',model='deepseek-flash',request_id=r['comparison']['request_id'],human_label=None,human_reviewer=None,human_reviewed_at=None,human_reason=None,source_text_hash=dm[r['selection']['family_id']]['text_hash']))
 # No filled human placeholders: editable rows are separate template records.
 for s in selection:
  for conf in ['D2_ARCHIVED','D3_FULL']:
   for dim in DIM+['source_adequacy','axis_a','axis_b']:labels.append(dict(family_id=s['family_id'],split=s['split'],configuration=conf,dimension=dim,label=None,label_tier='Human template (unlabeled)',model=None,request_id=None,human_label=None,human_reviewer=None,human_reviewed_at=None,human_reason=None,source_text_hash=s['source_text_hash']))
 para('D3_LABELS.parquet',labels)
 histories=[load(p) for p in sorted((W/'working/history').glob('*.json'))];d4=[load(p) for p in sorted((W/'working/d4').glob('*.json'))]
 pairrows=[]
 for r in d4:
  p=r['selection'];v=r['result'];pairrows.append(dict(pair_id=p['pair_id'],family_a=r['family_a'],family_b=r['family_b'],d2_contribution_a=p['cid_a'],d2_contribution_b=p['cid_b'],d2_technology_a=p['technology_id_a'],d2_technology_b=p['technology_id_b'],d2_relation='Same Technology ID' if p['technology_id_a']==p['technology_id_b'] else 'Different Technology IDs',recommended_relation=v['recommended_relation'],parent_side=v['parent_side'],rationale=v['rationale'],distinguishing_elements=v['distinguishing_elements'],ambiguity=v['ambiguity'],source_a_json=stable(r['source_a']),source_b_json=stable(r['source_b']),d2_contribution_a_json=stable(r['d2_contribution_a']),d2_contribution_b_json=stable(r['d2_contribution_b']),d3_contributions_a_json=stable(r['d3_contributions_a']),d3_contributions_b_json=stable(r['d3_contributions_b']),evidence_a=v['evidence_a'],evidence_b=v['evidence_b'],needs_full_text=v['needs_full_text'],human_confirmed=False,label_tier='Silver',request_id=r['request_id'],selection_reason=p['selection_reason']))
 para('D4_MERGE_TEST_CASES.parquet',pairrows)
 patches={load(p)['family_id']:load(p) for p in (W/'working/relevance_adjudication').glob('*.json')}
 relrows=[]
 for f,d in dm.items():
  m=mainrows.get(f);v=patches[f]['revised'] if f in patches else m['relevance'] if m else None
  relrows.append(dict(family_id=f,version='D3.1-R1 posthoc' if f in patches else 'D3.1 frozen',processing_status=m['status'] if m else 'FAILED',axis_a=v['axis_a'] if v else None,axis_b=v['axis_b'] if v else None,frozen_axis_a=m['relevance']['axis_a'] if m else None,frozen_axis_b=m['relevance']['axis_b'] if m else None,d2_categories=sorted({next(n['selection']['d2_category'] for n in nodes if n['selection']['technology_id']==t) for t in ft[f] if any(n['selection']['technology_id']==t for n in nodes)}),result_json=stable(v) if v else None,human_confirmed=False,posthoc_not_independent=f in patches))
 para('D3_PRINTHEAD_RELEVANCE.parquet',relrows)
 receipts=[load(p) for p in (W/'responses').glob('*.receipt.json')];api=[r for r in receipts if 'Legacy Mac' not in r.get('error','')];usage=[]
 for kind in sorted({r['kind'] for r in api}):
  rr=[r for r in api if r['kind']==kind];have=[r for r in rr if r.get('usage')];usage.append(dict(kind=kind,attempts=len(rr),model_responses=len(have),validated=sum(r['status']=='VALID' for r in rr),failed=sum(r['status']!='VALID' for r in rr),prompt_tokens=sum(r['usage'].get('prompt_tokens',0) for r in have),output_tokens=sum(r['usage'].get('completion_tokens',0) for r in have),cache_hit_tokens=sum(r['usage'].get('prompt_cache_hit_tokens',0) for r in have),peak_usd_upper_estimate=sum(estimate(r['usage']) or 0 for r in have),missing_usage=len(rr)-len(have),wall_s_sum=sum(r.get('wall_s',0) for r in rr)))
 cost=sum(r['peak_usd_upper_estimate'] for r in usage);stats=dict(main_required=1117,main_complete=len(mainrows),main_status_counts=dict(collections.Counter(r['status'] for r in status)),contribution_count=len(contrib),contribution_distribution=dict(collections.Counter(len(r['final']['contributions']) for r in mainrows.values())),source_status_counts=dict(collections.Counter(r['final']['source_status'] for r in mainrows.values())),field_audit_rows=len(finalfields),all_audit_rows=len(audits),span_reference_count=sum(r['span_reference_count'] for r in finalfields),level2_supported=sum(r['grade'] in GOOD for r in finalfields),human_gold_n=0,api_attempts=len(api),api_responses=sum(r.get('usage') is not None for r in api),usage_peak_usd_upper_estimate=cost,unknown_usage_count=sum(not r.get('usage') for r in api),node_audits=len(nodes),relevance_patches=len(patches),relevance_changed=sum(r['changed'] for r in patches.values()),historical_complete=len(histories),d4_pairs=len(pairrows),independent_compared=len(comparisons))
 save('evidence/FINAL_STATISTICS.json',stats)
 # Workbook source matrices. Source text is lossless in <=300-character span rows.
 wb=dict(stats=stats,metrics=metrics,usage=usage,status=status,confusions=confusions,relevance_conflicts=relconflicts,selection=selection,dev=[],holdout=[],human=[],sources_eval=[],sources_all=[],history=[],relevance=[],node_audits=[],error_rows=errors)
 for d in docs:
  for s in spans(d):
   row=[d['family_id'],s['id'],s['field'],s['start'],s['end'],s['text'],d['text_hash']];wb['sources_all'].append(row)
   if d['family_id'] in split:wb['sources_eval'].append(row)
 for s in selection:
  f=s['family_id'];d=dm[f];m=mainrows.get(f);cmp=active_comparison(f)
  line=[f,s['split'],s['sampling_cohort'],d.get('language'),len(d.get('abstract') or ''),'; '.join(s['sampling_tags']),d['title'],brief(oc[f]),brief(m['final']['contributions']) if m else None,m['status'] if m else 'FAILED',s['source_text_hash'],s['selection_reason']]
  wb['dev' if s['split']=='development' else 'holdout'].append(line)
  for conf in ['D2_ARCHIVED','D3_FULL']:wb['human'].append([f,s['split'],conf,s['source_text_hash'],None,None,None]+[None]*(len(DIM)+3))
 for r in histories:
  c=r['case'];v=r['result'];f=c['family_id'];wb['history'].append([f,r['scope'],c.get('history_group'),'; '.join(c.get('expected_node_ids',[])),v['historical_recovery'],v['source_adequacy'],v['object_judgment'],v['problem_judgment'],v['means_judgment'],v['material_parameter_judgment'],v['false_unrelated'],v['d2_to_d3_change'],v['reason'],'; '.join(v['historical_details_absent']),v['needs_full_text'],r['request_id']])
 for f,d in dm.items():
  m=mainrows.get(f);v=patches[f]['revised'] if f in patches else m['relevance'] if m else None;oldcats=sorted({d2_rel_map[t] for t in ft[f] if t in d2_rel_map})
  wb['relevance'].append([f,v['axis_a'] if v else None,v['axis_b'] if v else None,','.join(oldcats),v['head_object'] if v else None,v['possible_application'] if v else None,v['mechanism_rationale'] if v else None,v['engineering_inference'] if v else None,'; '.join(v['key_conditions']) if v else None,'; '.join(v['open_questions']) if v else None,v['document_evidence']['text'] if v else None,m['status'] if m else 'FAILED','D3.1-R1 posthoc' if f in patches else 'D3.1 frozen',m['relevance']['axis_a'] if m else None,m['relevance']['axis_b'] if m else None,v['needs_full_text'] if v else None,d['text_hash']])
 for r in nodes:
  n=r['selection'];v=r['result'];wb['node_audits'].append([n['technology_id'],'; '.join(n['family_ids']),'; '.join(n['reasons']),n['d2_category'],v['legacy_reference'],v['axis_a'],v['axis_b'],v['mechanism_rationale'],v['engineering_inference'],'; '.join(v['key_conditions']),v['source_families_disagree'],v['disagreement_explanation'],v['source_mechanism_supported'],v['needs_full_text'],r['request_id']])
 save('working/WORKBOOK_DATA.json',wb)
 write_reports(stats,metrics,errors,histories,pairrows,relconflicts,usage,mainrows)
 artifacts=['D3_PATENT_CONTRIBUTIONS.parquet','D3_EVIDENCE_AUDIT.parquet','D3_PROCESSING_STATUS.parquet','D3_ERRORS.parquet','D3_METRICS.parquet','D3_LABELS.parquet','D3_RELEVANCE_CONFUSIONS.parquet','D4_MERGE_TEST_CASES.parquet','D3_PRINTHEAD_RELEVANCE.parquet','D3_REPORT.md','D3_ERROR_ANALYSIS.md','D3_EXPERIMENT_COMPARISON.md','D3_HISTORICAL_REGRESSION.md','D3_EVALUATION_PROTOCOL.md']
 save('D3_MANIFEST.json',dict(version='D3.1',created_at=now(),statistics=stats,ssd_uuid=UUID,workspace=str(W),d2_input_lock=load('inputs/D2_LOCK.json'),split_lock=load('inputs/SPLIT_LOCK.json'),model_policy=load('evidence/MODEL_POLICY.json'),actual_returned_models=sorted({r.get('actual_model') for r in api if r.get('actual_model')}),weight_digest=None,model_freeze=frozen,semantic_code_commit=frozen['code_commit'],posthoc_relevance=dict(version='D3.1-R1',scope='Only fixed-node-audit conflicts, fresh same-model source re-read',benchmark_predictions_unchanged=True,not_independent_quality_proof=True,patches=stats['relevance_patches']),human_gold_n=0,labels='Silver and unlabeled Human template separated',failure_and_retry=dict(max_per_invocation=3,max_total_per_fingerprint=6,semantic_revision_cycles=2,local_pre_api_credential_failures=90,unknown_usage_attempts=stats['unknown_usage_count']),cost=dict(peak_usd_upper_estimate=cost,billed_cost=None,reason='Real usage priced at published peak rates; bill unavailable; unknown usage not assumed zero',official_price_source='https://api-docs.deepseek.com/quick_start/pricing/'),artifacts={n:dict(sha256=sha(W/n),bytes=(W/n).stat().st_size) for n in artifacts},frozen_inputs_unchanged=True,not_modified=['E3 original corpus','BGE/Qwen full vectors','D1 assignments','D2 core and IDs/merges'],scope_exclusions=['No acquisition','No embeddings','No clustering','No formal D4 merge']))
 event('assembly_done',**stats)

def write_reports(stats,metrics,errors,histories,pairs,relconflicts,usage,mainrows):
 def find(split,conf,name,scope='paired_full'):
  return next((r for r in metrics if r['split']==split and r['configuration']==conf and r['metric']==name and r['scope']==scope),None)
 def fmt(r):
  if not r or r['value'] is None:return 'N/A'
  return f"{r['value']:.1%} ({r['numerator']}/{r['denominator']}; N={r['sample_n']}, unknown={r['unknown_n']})"
 comparison=['# D3 实验对照','', '所有下列判断为同模型Silver，人工Gold=0。匿名顺序随机化不能消除同模型偏差。D2归档含原实际AI/审定修订，不是纯Qwen裸输出；DeepSeek复演为另一独立基线。','', '| 分集 | 配置 | 机制Correct | 材料保留 | 工艺保留 | 完整结论支持 |','|---|---|---|---|---|---|']
 for split in ['development','holdout']:
  for conf in ['D2_ARCHIVED','D2_DEEPSEEK_REPLAY','D3_EXTRACT_ONLY','D3_FIDELITY','D3_EVIDENCE','D3_FULL']:
   scope='paired_ablation';comparison.append('| '+' | '.join([split,conf]+[fmt(find(split,conf,n,scope)) for n in ['technical_mechanism_correct_rate','material_retention','process_retention','full_conclusion_support_rate']])+' |')
 comparison+=['','上表严格使用全部五种贡献配置均可用的同源交集；失败与缺失会使分母小于98/42。D3_FULL与D3_EVIDENCE贡献文本相同，区别是独立双轴相关性。扩展95+盲测同源D2/完整D3对照见指标工作簿paired_full。不同配置的应有贡献/要素数若不一致，相关召回指标排除该样本并增加unknown。','', '## 可复现基线与消融限制','D2精确提示词/Schema/source-ID传输和2200输出上限已复演，但API模型、tokenizer和结构约束执行方式不同，不能声称复现原Qwen随机轨迹。原D2实际归档仍是主要基线。主版本、消融和费用均不补造失败。', '', '## 贡献数量不能直接证明改善',stable(stats['contribution_distribution']), '', '正确贡献覆盖、过拆、遗漏、虚构、要素保真、两轴错误、来源不足、成本的numerator/denominator逐项在D3_METRICS及工作簿。Gold准确率全部N/A；Silver结果仅支持工程诊断。']
 (W/'D3_EXPERIMENT_COMPARISON.md').write_text('\n'.join(comparison)+'\n')
 original=[e for e in errors if e['stage']=='original'];final=[e for e in errors if e['stage']=='final'];oc=collections.Counter(e['error_type'] for e in original);fc=collections.Counter(e['error_type'] for e in final)
 err=['# D3 失败分析','', '模型抽取/证据错误与摘要不足分列。以下根因和修复判断来自DeepSeek Silver审计，不是独立人工确认。修订后未再报出不等于证明修复。全部逐族记录在D3_ERRORS.parquet。','', '| 类型 | 原始审计条目 | 最终审计条目 |','|---|---:|---:|']
 from design import ERRORS
 for name in ERRORS:err.append(f'| {name} | {oc[name]} | {fc[name]} |')
 err+=['', '## 仍待复核案例']
 priority=sorted(final,key=lambda e:(e['error_type']=='Insufficient Source',e['family_id']))[:30]
 for e in priority:err+=['',f"### {e['family_id']} — {e['error_type']}",e['description'],'证据：'+e['evidence_spans_json'],'D2：'+str(e['d2_result']),'D3：'+str(e['d3_result']),'状态：'+e['fix_status']+('；需全文/Claims' if e['needs_full_text'] else '')]
 err+=['', '## 确定性运行失败','输出结构、引用和传输失败单独记录；失败不变成Uncertain/弃判。每指纹最多6次尝试，原响应全部保留。开发期90次本地凭据读失败发生在构造HTTP请求前，单独归因；凭据已移入SSD私密目录且不进入Git。','', '## 人工与全文队列',f"最终错误中{sum(e['needs_full_text'] for e in final)}条要求补全文。Title-only与摘要未提供位点/阶段/窗口不能靠模型推断补齐。"]
 (W/'D3_ERROR_ANALYSIS.md').write_text('\n'.join(err)+'\n')
 hist=['# 历史45族专项回归','', '历史预期在主提示词/Schema/代码冻结后用于事后回归，不进入Query-Free抽取。39原发现与6补充探针独立统计；不与holdout混算。所有判定为Silver，Gold=0。', '', '| 范围 | 完成 | 结果分布 |','|---|---:|---|']
 for scope in ['main_discovery39','postfreeze_probe6']:
  rr=[r for r in histories if r['scope']==scope];hist.append(f'| {scope} | {len(rr)} | {dict(collections.Counter(r["result"]["historical_recovery"] for r in rr))} |')
 hist+=['','| Family ID | 范围 | D3恢复判定 | 来源充分性 | D2到D3变化 | 未披露历史细节 |','|---|---|---|---|---|---|']
 for r in histories:
  v=r['result'];hist.append('| '+' | '.join([r['case']['family_id'],r['scope'],v['historical_recovery'],v['source_adequacy'],v['d2_to_d3_change'].replace('|','/'),'; '.join(v['historical_details_absent']).replace('|','/')])+' |')
 hist+=['','原D2报告17 Recovered、3 Broad、25 Insufficient作为历史归档；新判定为独立本次Silver，不能把类别差直接叫真实准确率提升。每族对象/问题/办法/材料参数、摘要不足或遗漏、喷头判断、证据与请求在工作簿及working/history保留。']
 (W/'D3_HISTORICAL_REGRESSION.md').write_text('\n'.join(hist)+'\n')
 devold=find('development','D2_ARCHIVED','technical_mechanism_correct_rate');devnew=find('development','D3_FULL','technical_mechanism_correct_rate');holdold=find('holdout','D2_ARCHIVED','technical_mechanism_correct_rate');holdnew=find('holdout','D3_FULL','technical_mechanism_correct_rate')
 report=['# A5.5-D3 交付报告','', '## 首页结论','', '1. 已实现修复：去除通常一条贡献的先验；两阶段事实/贡献组织；材料与组成、工艺对象/顺序/阶段/联合窗口独立字段；字段与完整结论的原文重读审计；有上限的修订链、争议隔离及双轴喷头相关性。实际效果以下列Silver同源对照为限。',f"2. 仍有问题：{stats['main_status_counts'].get('FAILED',0)}族模型输出失败，{stats['main_status_counts'].get('QUARANTINED',0)}族争议隔离；来源不足不能补全，仍存在遗漏/过拆/字段支持争议。",'3. 是否优于旧方法：同模型Silver显示趋势，不能宣称已被人工或真正独立模型证实。',f"   - development：D2 {fmt(devold)}；D3 {fmt(devnew)}。",f"   - holdout：D2 {fmt(holdold)}；D3 {fmt(holdnew)}。",'4. 最严重错误：实体—关系—对象错配、关键要素/参数上下文丢失及独立贡献过拆。模型审核也可能误判，所有原始与修订输出保留。','5. D4建议：可进入受控开发和困难样本验证；正式批量自动归并及D5扩大规模No-Go，需先完成人工Gold审核、争议队列复核及来源不足隔离。未设虚构99%门槛。','6. 需补充人工/全文：140族审核入口已准备，Human列全部留空。对Title-only、联合窗口、位点、设备关系等缺口按队列补全文/Claims，不通过历史预期补写摘要。','', '## 主范围与证据',f"- 既有1117族：{stats['main_status_counts']}；贡献{stats['contribution_count']}，分布{stats['contribution_distribution']}。",f"- 最终字段审计{stats['field_audit_rows']}条，其中{stats['level2_supported']}条为Explicit/Supported Paraphrase。L1引文引用{stats['span_reference_count']}次全部逐字定位；这不等于语义正确率。",'- Inferred/Unsupported保存在独立推断/排除字段，争议记录不作为已确认节点。没有删除A4/B5节点，也未改D2概念ID/归并。','', '## 喷头相关性',f"固定151个节点逐项复审，含32个严格术语Unrelated、30个扩大喷射/喷嘴/头部候选、7个首轮Unrelated已被D2修订的候选、30随机Unrelated、25 Direct、25 Manufacturing（优先族可重叠）。实际以选择表为准，术语只用于抽样。",f"另有{stats['relevance_patches']}族在不同范围的Silver审计冲突后重新读原文裁决，{stats['relevance_changed']}族双轴标签变化；单独标D3.1-R1，原冻结预测/盲测指标不覆盖。该审计闭环结果不再充当独立验证。",'', '## 评估和范围限制','98 development /42 holdout在首次模型调用前冻结，历史45不重叠。盲测前锁定语义代码commit：'+load('evidence/MODEL_FREEZE.json')['code_commit']+'。所有成功结果缓存复用；固定重试不改提示词。题目建议的类别可重叠，抽样代理不是语义标签；各来源/语言/Title-only比例见样本表。',f"D4提供{stats['d4_pairs']}组真实D2概念冲突/相似候选的Silver关系建议，没有正式执行归并。历史专项完成{stats['historical_complete']}/45，39+6独立呈现。",'', '## 模型、费用与可复现性',f"官方deepseek-flash真实返回{stats['api_responses']}次，实际usage按官方峰时单价估算上界USD {stats['usage_peak_usd_upper_estimate']:.4f}；{stats['unknown_usage_count']}次无usage不能假设免费。账单金额未取得。云API不返回权重Digest，留null，不冒称锁定模型权重。",'DeepSeek官方模型/价格与JSON模式参考：[模型与价格](https://api-docs.deepseek.com/quick_start/pricing/)、[JSON模式](https://api-docs.deepseek.com/guides/json_mode/)。Codex只做程序、确定性位置/结构校验、汇总和导出，语义提取、审核、裁决均由接口模型完成。', '', '## Gate结论','- G1：冻结分集、协议、可编辑人工入口与可复现归档/复演基线已建立。','- G2：多贡献及要素保真结构和风险回归实现，Silver提升不能替代人工证据。','- G3：三级证据、原始/修订链、异常隔离与来源不足队列实现。','- G4：双轴、疑似漏判与反向样本审计完成；保留冲突与可修订标签。','- G5：冻结holdout同源对照、成本与分母可追溯；人工质量改善尚未验证，不能据此批准全自动扩大规模。','', '## 交付','三份Excel提供样本/人工入口、同源指标分母、双轴相关性；Parquet提供版本化贡献、证据、标签、错误、处理状态及D4对接口。D3_MANIFEST记录输入哈希、模型/Prompt/Schema、commit、真实范围和失败。原始请求/响应、缓存和修订链保存在本SSD工作区；发布包另列清单。']
 (W/'D3_REPORT.md').write_text('\n'.join(report)+'\n')
if __name__=='__main__':main()
