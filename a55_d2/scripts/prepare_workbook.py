"""Prepare reader-facing views from frozen KB and separate post-hoc records."""
from common import *
import pandas as pd,collections,math
from posthoc_relevance import verify_freeze
def cell(x):
 if x=='':return None # Empty textual notes display as blank; zero/False remain typed values.
 if isinstance(x,float) and math.isnan(x):return None
 if isinstance(x,(dict,list)):return stable(x)
 return x
def table(headers,records,keys,widths,**extra):
 assert len(headers)==len(keys)==len(widths),'Workbook header/key/width mismatch'
 rows=[[cell(r.get(k)) for k in keys] for r in records]
 assert all(len(str(v))<=32767 for row in rows for v in row if v is not None),'Excel cell limit: split the field, do not truncate source'
 return dict(headers=headers,rows=rows,widths=widths,**extra)
def main():
 guard();verify_freeze()
 kb=load('working/all_selected/KB_RECORDS.json');cs=load('working/all_selected/contributions.json')
 hist=load('outputs/HISTORICAL_VALIDATION.json')['rows']
 rel=load('outputs/PRINTHEAD_RELEVANCE.json');assert rel['completed']==rel['required']
 relevance={r['technology_id']:r for r in rel['results']};concepts={t['technology_id']:dict(t) for t in kb['concepts']}
 bycid={c['contribution_id']:c for c in cs};techbycid={l['contribution_id']:l['technology_id'] for l in kb['patent_technology']}
 docs={d['family_id']:d for d in pd.read_parquet(W/'inputs/PATENT_TEXTS.parquet').to_dict('records')}
 for t in concepts.values():
  p=concepts.get(t['parent_technology_id']);t['domain_name']=p['name'] if p else None
  r=relevance.get(t['technology_id'],{})
  t.update(relevance_category=r.get('category'),relevance_origin=r.get('evidence_origin'),head_application=r.get('application'),transfer_conditions=r.get('conditions'),engineering_inference=r.get('engineering_inference'),requires_full_text=r.get('needs_full_text'),head_object=r.get('head_object'),relevance_rationale=r.get('rationale'),relevance_source_quotes=r.get('source_evidence_quotes') or r.get('patent_evidence'),relevance_review_reason=r.get('review_reason'),frozen_definition_issue=r.get('frozen_definition_issue'))
 domain_relevance=[]
 for t in concepts.values():
  if t['level']!='A':continue
  children=[c['technology_id'] for c in concepts.values() if c['parent_technology_id']==t['technology_id'] and c['level']=='B']
  counts=dict(collections.Counter(relevance[tid]['category'] for tid in children))
  t.update(relevance_category='子机制分布：'+stable(counts),relevance_origin='CHILD_ASSESSMENT_DISTRIBUTION',relevance_rationale='对象/问题域包含不同方案，显示所有子机制分类分布，不强制归为单一喷头类别。',relevance_source_quotes=dict(child_technology_ids=children),requires_full_text=any(relevance[tid]['needs_full_text'] for tid in children))
  domain_relevance.append(dict(domain_id=t['technology_id'],domain_name=t['name'],child_count=len(children),category_counts=counts,child_technology_ids=children,origin='DERIVED_FROM_POSTHOC_CHILD_ASSESSMENTS_NOT_SINGLE_MECHANISM_CLASSIFICATION'))
 save('outputs/DOMAIN_PRINTHEAD_RELEVANCE.json',dict(at=now(),domains=domain_relevance,mechanism_count=len(relevance),human_gold=False))
 for issue in load('evidence/KNOWN_FROZEN_DEFINITION_ISSUES.json')['rows']:
  t=concepts[issue['technology_id']];t['frozen_definition_issue']='; '.join(filter(None,[t.get('frozen_definition_issue'),issue['issue']]))
 for issue in load('evidence/HISTORICAL_CROSS_ROUTE_SOURCE_REVIEW.json')['rows']:
  t=concepts[issue['technology_id']];t['frozen_definition_issue']='; '.join(filter(None,[t.get('frozen_definition_issue'),issue['reason']]))
 case_families=['google:25533490','google:35900903','google:36033435','google:42069640','google:64105183','google:40581936','google:51658295','google:39704160','google:42705590','google:17063741','google:88730031','google:31934213','google:53004031','google:11818487','google:97217650','google:27456174','google:49387621','google:38149581','google:83456095','google:36574358']
 chosen=[];used=set()
 for fid in case_families+sorted(docs):
  candidates=[c for c in cs if c['family_id']==fid and c['contribution_id'] in techbycid]
  for c in candidates:
   tid=techbycid[c['contribution_id']]
   if tid in used:continue
   t=concepts[tid];r=relevance[tid];ev=[e for e in c['evidence_spans'] if e['field']=='abstract' and e['id'] in c['technical_mechanism']['evidence_ids']]
   if not ev:ev=[e for e in c['evidence_spans'] if e['field']=='abstract']
   if not ev:continue
   # Merge overlapping source spans into exact contiguous runs. Ellipsis explicitly separates omitted text.
   runs=[]
   for e in sorted(ev,key=lambda x:x['start']):
    assert c['source_abstract'][e['start']:e['end']]==e['quote']
    if runs and e['start']<=runs[-1][1]:runs[-1][1]=max(runs[-1][1],e['end'])
    else:runs.append([e['start'],e['end']])
   report_quote=' … '.join(c['source_abstract'][a:b] for a,b in runs)
   excerpt_parts=[dict(start=a,end=b,quote=c['source_abstract'][a:b]) for a,b in runs]
   short=report_quote if len(report_quote)<=420 else report_quote[:230]+' […] '+report_quote[-180:]
   chosen.append(dict(technology_id=tid,name=t['name'],domain=t['domain_name'],family_id=fid,evidence=ev,evidence_report=report_quote,evidence_excerpt_parts=excerpt_parts,evidence_short=short,source_field='abstract',relevance=r['category'],evidence_origin=r['evidence_origin'],mechanism=c['technical_mechanism']['text'],review=('助手源文修订；' if c.get('curation_provenance_json') else ('采用二次抽取；' if c.get('refinement_provenance_json') else '原始模型抽取；'))+(t['review_notes'] or '摘要范围，未做Claims/Description核验')))
   used.add(tid)
   if len(chosen)==20:break
  if len(chosen)==20:break
 assert len(chosen)==20
 assert any(c['relevance']=='Unrelated' for c in chosen),'Include a genuine non-head example, not only potential transfers'
 save('outputs/REAL_TECHNOLOGY_CASES.json',dict(cases=chosen,source_verbatim_verified=True,human_gold=False))
 contributions=[]
 for c in cs:
  r=dict(c)
  for key in ['technical_object','technical_problem','technical_mechanism','implementation','expected_effect','applicable_conditions']:r[key]=c[key]['text']
  r['technology_id']=techbycid.get(c['contribution_id']);contributions.append(r)
 review=pd.read_parquet(W/'outputs/REVIEW_QUEUE.parquet').to_dict('records')
 tables={}
 tables['Technology Concepts']=table(
 ['技术名称','Technology ID','层级','上级对象/问题域','Family ID数','不同原文数','核心机制','适用条件','对象','问题','支持Family IDs','支持Contribution IDs','喷头关系','关系证据性质','喷头对象','原文关系证据','判断理由','事后源文复核','冻结定义疑点','可能用途','迁移条件','工程推断','需全文核验','证据状态','复核备注','版本'],
 list(concepts.values()),['name','technology_id','level','domain_name','family_count','distinct_source_text_count','core_mechanism','applicable_conditions','technical_object','technical_problem','support_family_ids_json','support_contribution_ids_json','relevance_category','relevance_origin','head_object','relevance_source_quotes','relevance_rationale','relevance_review_reason','frozen_definition_issue','head_application','transfer_conditions','engineering_inference','requires_full_text','evidence_status','review_notes','version'],
 [44,27,10,30,12,14,80,75,35,55,45,55,18,24,45,110,80,90,90,60,70,70,16,40,65,12])
 tables['Patent Contributions']=table(
 ['Contribution ID','Family ID','原始标题','技术对象','技术问题','具体手段','实现','摘要主张效果','适用条件','定量参数原文','原文证据与位置','完整原始Abstract','材料','工艺','结构','证据级别','机制类型','语义复核状态','Technology ID','字段引用缺口','未采纳的模型参数','原始模型Contribution ID','助手原文修订','二次抽取记录','Publication ID','Request ID','Source Hash'],
 contributions,['contribution_id','family_id','source_title','technical_object','technical_problem','technical_mechanism','implementation','expected_effect','applicable_conditions','parameters','evidence_spans','source_abstract','materials','process_methods','structures','evidence_level','mechanism_type','semantic_validation_status','technology_id','field_evidence_gaps','rejected_parameter_claims','source_model_contribution_id','curation_provenance_json','refinement_provenance_json','publication_id','request_id','source_text_hash'],
 [28,24,55,38,55,85,75,65,75,80,120,135,40,40,45,28,20,42,28,80,80,28,100,85,27,34,68])
 tables['Patent–Technology']=table(
 ['Family ID','Technology ID','Contribution ID','关系','原文证据与位置','证据级别','语义复核状态','Source Hash'],
 kb['patent_technology'],['family_id','technology_id','contribution_id','relation_type','evidence_spans_json','evidence_level','semantic_validation_status','source_text_hash'],
 [24,28,28,38,130,28,45,68])
 tables['Technology Relations']=table(
 ['来源Technology ID','目标Technology ID','关系类型','层级含义','判断理由','来源Contribution IDs','双侧证据IDs','判断来源','关系证据状态','Request ID'],
 kb['technology_relations'],['source_technology_id','target_technology_id','relation_type','hierarchy_type','rationale','source_contribution_ids_json','evidence_ids_json','origin','evidence_status','request_id'],
 [28,28,22,38,100,65,65,45,50,35])
 tables['Cluster–Technology']=table(
 ['来源选择ID','Technology ID','Run ID','Cluster ID','支持唯一Family数','贡献数','Cluster总体族数','抽取族数','覆盖口径','支持Family IDs','支持Contribution IDs'],
 kb['cluster_technology'],['selection_id','technology_id','run_id','cluster_id','unique_families','contributions','cluster_population','sampled_families','coverage_scope','support_family_ids_json','support_contribution_ids_json'],
 [52,28,37,14,18,14,20,16,35,75,75])
 keys=['family_id','human_status','review_priority','source_title','source_abstract','extracted_mechanisms','source_first_AI_note','assistant_review_status','assistant_review_notes','human_reviewer','human_object_accuracy','human_problem_source_support','human_mechanism_source_support','human_multi_contribution_completeness','human_parameter_fidelity','human_over_split_check','human_over_merge_check','human_edit','human_notes','fixed_audit80','contribution_ids_json','field_evidence_gaps_json','rejected_parameter_claims_json','processing_error','discovery_scope']
 headers=['Family ID','人工状态','复核优先级','原始标题','完整原始Abstract','当前抽取手段','助手原文预读','助手复核状态','助手复核备注','人工复核者','人工：对象','人工：问题依据','人工：手段依据','人工：多贡献完整性','人工：参数忠实','人工：过拆分','人工：过归并','人工修订','人工备注','固定80族','Contribution IDs','字段证据缺口','未采纳模型参数','处理失败原因','发现/事后探针范围']
 tables['Review Queue']=table(headers,review,keys,[24,18,26,55,135,100,100,40,90,20,28,28,28,30,28,28,28,100,100,16,65,100,100,100,36],editableColumns=[i for i,k in enumerate(keys) if k.startswith('human_')],reviewStatusColumn=1)
 tables['Historical Validation']=table(
 ['Family ID','历史组','历史节点','发现样本覆盖','恢复结果','判断理由','源文充分性','支持Technology IDs','原文证据','历史参照','复核来源','需全文核验','原始标题','完整原始Abstract','Publication ID'],
 hist,['family_id','history_group','expected_node_ids','discovery_scope','outcome','reason','source_sufficiency','technology_ids','evidence_quotes','history_reference','validation_origin','needs_full_text','source_title','source_abstract','publication_id'],
 [24,20,48,35,36,110,40,65,120,100,45,18,60,135,27])
 status=collections.Counter(x['status'] for x in kb['processing_status']);explicit={c['family_id'] for c in cs if c['evidence_level']=='EXPLICIT_MECHANISM'}
 cohorts=pd.read_csv(W/'inputs/COHORTS.csv');members=pd.read_parquet(W/'inputs/CLUSTER_MEMBERS.parquet');cohort_rows=[]
 for cohort in cohorts.to_dict('records'):
  ids=set(members[members.selection_id==cohort['selection_id']].family_id);mapped=[m for m in kb['cluster_technology'] if m['selection_id']==cohort['selection_id']]
  cohort_rows.append([cohort['run_id']+' #'+str(cohort['cluster_id']),int(cohort['population_size']),int(cohort['selected_size']),len(ids&explicit),len({m['technology_id'] for m in mapped}),'全群' if cohort['complete_cluster'] else '抽样'])
 data=dict(subtitle='固定1117族试验。候选技术与原文双向可追踪；人工编辑列为浅黄色。',metrics=[['纳入唯一专利族',len(docs)],['有效结构记录族',status.get('VALID',0)],['失败族',status.get('FAILED_VALIDATION',0)],['有明确手段标签的族',len(explicit)],['贡献/弃判记录',len(cs)],['候选机制节点',sum(t['level']=='B' for t in concepts.values())],['对象/问题域节点',sum(t['level']=='A' for t in concepts.values())],['固定审计样本族',80]],cohorts=cohort_rows,cases=[[c[k] for k in ['name','technology_id','domain','family_id','evidence_short','source_field','relevance','evidence_origin','review']] for c in chosen],tables=tables)
 save('working/WORKBOOK_DATA.json',data)
 print(stable(dict(sheets=len(tables)+1,records={n:len(d['rows']) for n,d in tables.items()},cases=len(chosen))))
if __name__=='__main__':main()
