"""Build editable review records; AI review is separate from human annotations."""
from common import *
from consolidate import current_records
import pandas as pd,argparse
CRITERIA=['object_accuracy','problem_source_support','mechanism_source_support','multi_contribution_completeness','parameter_fidelity','over_split_check','over_merge_check']
def prepare(stage='all_selected'):
 guard();rows,status,objects=current_records(stage);byfamily={}
 for c in objects:byfamily.setdefault(c['family_id'],[]).append(c)
 urgent=set()
 selection=load('inputs/AUDIT_SELECTION.json')['family_ids'];notes=load('evidence/AUDIT80_SOURCE_READING.json')['family_notes']
 ratings=load('evidence/ASSISTANT_AUDIT80_RATINGS.json')['rows'] if (W/'evidence/ASSISTANT_AUDIT80_RATINGS.json').exists() else []
 ratings={x['family_id']:x for x in ratings}
 auxiliary={}
 for filename in ['evidence/PILOT30_SOURCE_AUDIT.json','evidence/TRIAL100_SOURCE_AUDIT.json']:
  if (W/filename).exists():
   for r in load(filename).get('rows',[]):
    auxiliary[r['family_id']]=dict(decision='AI_PILOT_SOURCE_REVIEW',notes=r.get('note') or r.get('notes'))
 pairnotes={}
 if (W/'evidence/PAIR_ASSISTANT_SOURCE_REVIEW_APPLIED.json').exists():
  for r in load('evidence/PAIR_ASSISTANT_SOURCE_REVIEW_APPLIED.json')['rows']:
   for fid in [r['left_family_id'],r['right_family_id']]:pairnotes.setdefault(fid,[]).append(r['source_reason'])
 if (W/'evidence/FINAL_SOURCE_PAIR_REVIEW_APPLIED.json').exists():
  for r in load('evidence/FINAL_SOURCE_PAIR_REVIEW_APPLIED.json')['rows']:
   for fid in [r['left_family_id'],r['right_family_id']]:pairnotes.setdefault(fid,[]).append(r['reason'])
 if (W/'evidence/NAMING_SOURCE_REVIEW.json').exists():
  for r in load('evidence/NAMING_SOURCE_REVIEW.json')['curated_names']:pairnotes.setdefault(r['family_id'],[]).append('命名源文修订：'+r['reason'])
 if (W/'evidence/DOMAIN_SOURCE_REVIEW.json').exists():
  for r in load('evidence/DOMAIN_SOURCE_REVIEW.json')['changes']:pairnotes.setdefault(r['family_id'],[]).append('上层对象域修订：'+r['reason'])
 if (W/'evidence/LATE_NAMING_AUDIT_REPAIRS.json').exists():
  r=load('evidence/LATE_NAMING_AUDIT_REPAIRS.json')['pair'];bycid={c['contribution_id']:c for c in objects}
  for cid in r['new_cids']:pairnotes.setdefault(bycid[cid]['family_id'],[]).append(r['reason'])
 if (W/'evidence/KNOWN_FROZEN_DEFINITION_ISSUES.json').exists():
  for r in load('evidence/KNOWN_FROZEN_DEFINITION_ISSUES.json')['rows']:
   urgent.add(r['family_id']);pairnotes.setdefault(r['family_id'],[]).append('冻结后发现、未回写核心：'+r['issue'])
 if (W/'evidence/RELEVANCE_SOURCE_REVIEW_SUMMARY.json').exists():
  techs={t['technology_id']:json.loads(t['support_family_ids_json']) for t in load('working/all_selected/KB_RECORDS.json')['concepts']}
  for r in load('evidence/RELEVANCE_SOURCE_REVIEW_SUMMARY.json')['frozen_definition_issues']:
   for fid in techs[r['technology_id']]:
    urgent.add(fid);pairnotes.setdefault(fid,[]).append('相关性事后复核发现的冻结定义疑点：'+r['issue'])
 if (W/'evidence/CROSS_SOURCE_WITNESS_REVIEW.json').exists():
  techs={t['technology_id']:json.loads(t['support_family_ids_json']) for t in load('working/all_selected/KB_RECORDS.json')['concepts']}
  for r in load('evidence/CROSS_SOURCE_WITNESS_REVIEW.json')['rows']:
   if r['status'] in ['IMPLEMENTATION_VARIANTS_REQUIRE_HUMAN_EQUIVALENCE_CHECK','SOURCE_SPECIFIC_CMP_AND_TRANSLATION_DUPLICATION_RISK']:
    for fid in techs[r['technology_id']]:
     urgent.add(fid);pairnotes.setdefault(fid,[]).append('冻结后跨源诊断：'+r['note'])
 if (W/'evidence/HISTORICAL_CROSS_ROUTE_SOURCE_REVIEW.json').exists():
  for r in load('evidence/HISTORICAL_CROSS_ROUTE_SOURCE_REVIEW.json')['rows']:
   for fid in r['family_ids']:
    urgent.add(fid);pairnotes.setdefault(fid,[]).append('冻结后已知误并/粒度问题：'+r['reason']+'；'+r['action'])
 if (W/'evidence/HISTORICAL_ASSISTANT_REVIEW.json').exists():
  for r in load('evidence/HISTORICAL_ASSISTANT_REVIEW.json')['category_changes']:
   urgent.add(r['family_id']);pairnotes.setdefault(r['family_id'],[]).append('历史源文事后复核：'+r['before']+' → '+r['after']+'；'+r['reason'])
 ids=set(pairnotes)|set(selection)|{s['family_id'] for s in status if s['status']=='FAILED_VALIDATION'}
 # All technical facet gaps are reviewable, but do not change the fixed audit denominator.
 for c in objects:
  if c['field_evidence_gaps'] or c.get('rejected_parameter_claims'):ids.add(c['family_id'])
 docs={r['family_id']:r for r in pd.read_parquet(W/'inputs/PATENT_TEXTS.parquet').to_dict('records')}
 probe_statuses={}
 if (W/'inputs/HISTORY_SUPPLEMENT_TEXTS.json').exists():docs.update({d['family_id']:d for d in load('inputs/HISTORY_SUPPLEMENT_TEXTS.json')['docs']})
 if (W/'working/HISTORY_SUPPLEMENT_CONTRIBUTIONS.json').exists():
  probe_data=load('working/HISTORY_SUPPLEMENT_CONTRIBUTIONS.json');probe_statuses={r['family_id']:r for r in probe_data['statuses']};ids.update(probe_statuses)
  for c in probe_data['contributions']:byfamily.setdefault(c['family_id'],[]).append(c)
 st={x['family_id']:x for x in status};st.update({fid:dict(r,status='POST_FREEZE_PROBE_'+r['status']) for fid,r in probe_statuses.items()});out=[]
 for fid in sorted(ids):
  d=docs[fid];cs=byfamily.get(fid,[]);rating=ratings.get(fid,auxiliary.get(fid,{}))
  row=dict(family_id=fid,discovery_scope='POST_FREEZE_SUPPLEMENT_PROBE' if fid in probe_statuses else 'CORE_DISCOVERY_COHORT',fixed_audit80=fid in selection,processing_status=st.get(fid,{}).get('status','UNATTEMPTED'),processing_error=st.get(fid,{}).get('error'),source_title=d['title'],source_abstract=d['abstract'],contribution_ids_json=stable([c['contribution_id'] for c in cs]),extracted_mechanisms='\n'.join(c['technical_mechanism']['text'] or '[ABSTAIN]' for c in cs),source_first_AI_note=notes.get(fid),assistant_review_status=rating.get('decision','SOURCE_READ_OUTPUT_COMPARISON_PENDING' if fid in selection else 'NOT_AUDITED'),assistant_review_notes=rating.get('notes'),human_status='待人工',human_reviewer=None,human_edit=None,human_notes=None,field_evidence_gaps_json=stable({c['contribution_id']:c['field_evidence_gaps'] for c in cs}),rejected_parameter_claims_json=stable({c['contribution_id']:c.get('rejected_parameter_claims',[]) for c in cs}),not_human_gold=True)
  if fid in pairnotes:
   row['assistant_review_notes']='\n'.join([str(row['assistant_review_notes'] or ''),'技术对源文诊断（AI，非Gold）：']+pairnotes[fid])
  for criterion in CRITERIA:row['human_'+criterion]=None
  row['review_priority']='01 已知语义疑点' if fid in urgent else ('02 固定80审计' if fid in selection else ('03 事后探针' if fid in probe_statuses else ('04 处理失败' if row['processing_status']=='FAILED_VALIDATION' else '05 字段引用/参数缺口')))
  out.append(row)
 out.sort(key=lambda r:(r['review_priority'],r['family_id']))
 pd.DataFrame(out).to_parquet(W/'outputs/ALL_REVIEW_FLAGS.parquet',index=False)
 all_flag_count=len(out)
 out=[r for r in out if r['review_priority']!='05 字段引用/参数缺口']
 pd.DataFrame(out).to_parquet(W/'outputs/REVIEW_QUEUE.parquet',index=False)
 save('evidence/AUDIT80_PROGRESS.json',dict(at=now(),fixed_families=80,source_read=80,output_comparisons_completed=len(ratings),human_gold_labels=0,editable_review_rows=len(out),all_review_flag_rows=all_flag_count,review_queue_scope='Fixed80 plus known semantic issues, processing failures and post-freeze probes; complete gap flags retained separately',semantic_accuracy_estimate=None,reason='No independent human gold set; assistant source reviews are qualitative diagnostics'))
 return out
def cards(stage,start,stop):
 _,status,objects=current_records(stage);ids=load('inputs/AUDIT_SELECTION.json')['family_ids'][start:stop]
 selected=[c for c in objects if c['family_id'] in ids];notes=load('evidence/AUDIT80_SOURCE_READING.json')['family_notes']
 for fid in ids:
  cs=[c for c in selected if c['family_id']==fid]
  print(stable(dict(family_id=fid,source_note=notes[fid],processing_status=next((s['status'] for s in status if s['family_id']==fid),'UNATTEMPTED'),contributions=[{k:c.get(k) for k in ['contribution_id','technical_object','technical_problem','technical_mechanism','implementation','expected_effect','applicable_conditions','parameters','evidence_level','ambiguity_notes']} for c in cs])))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',default='all_selected');p.add_argument('--cards',action='store_true');p.add_argument('--start',type=int,default=0);p.add_argument('--stop',type=int,default=10);a=p.parse_args()
 if a.cards:cards(a.stage,a.start,a.stop)
 else:prepare(a.stage)
