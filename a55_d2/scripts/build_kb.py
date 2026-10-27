"""Build cluster-independent IDs and source-traceable KB; freeze before post-hoc analysis."""
from common import *
import pandas as pd,pyarrow as pa,pyarrow.parquet as pq,re,argparse,collections
from consolidate import current_records,table_schema
def norm(s):return re.sub(r'\s+','',s).casefold()
class Registry:
 def __init__(self,path):
  self.path=Path(path);self.data=json.loads(self.path.read_text()) if self.path.exists() else dict(nodes={},membership={},aliases={})
  self.used=set()
 def allocate(self,level,key,members):
  def resolve(tid):
   seen=set()
   while tid in self.data['aliases']:
    assert tid not in seen,'Registry alias cycle';seen.add(tid);tid=self.data['aliases'][tid]
   return tid
  existing=sorted({resolve(self.data['membership'][c]) for c in members if c in self.data['membership']} - self.used)
  if level=='A':
   tid='D_'+object_hash(norm(key))[:20]
  elif existing:
   tid=existing[0]
   for alias in existing[1:]:self.data['aliases'][alias]=tid
  else:
   tid='T_'+object_hash(key)[:20]
   if tid in self.used or tid in self.data['aliases']:
    tid='T_'+object_hash(dict(key=key,members=sorted(members),reason='split-lineage-v1'))[:20]
   assert tid not in self.used and tid not in self.data['aliases'],'Ambiguous registry identity'
  self.used.add(tid)
  self.data['nodes'].setdefault(tid,dict(created_at=now(),level=level,identity_anchor=key))
  for cid in members:self.data['membership'][cid]=tid
  return tid
 def commit(self):
  save(str(self.path),self.data)
def flat_write(rows,path):
 path=Path(path);write_guard(path);path.parent.mkdir(parents=True,exist_ok=True)
 if rows:pd.DataFrame(rows).to_parquet(path,index=False)
 else:pq.write_table(pa.table(dict(status=pa.array([],type=pa.string()))),path)
def build(stage='all_selected'):
 guard()
 if (W/'evidence/CORE_FREEZE.json').exists():
  from posthoc_relevance import verify_freeze
  old=verify_freeze();event('core_already_frozen_reused',core_freeze_sha256=object_hash(old));return old
 for required in ['FINAL_SOURCE_PAIR_REVIEW_APPLIED.json','NAMING_SOURCE_REVIEW.json','NAME_VALIDATION_REPLAYS.json','LATE_NAMING_AUDIT_REPAIRS.json','DOMAIN_SEED_SELECTION.json','DOMAIN_SOURCE_REVIEW.json']:
  assert (W/'evidence'/required).is_file(),'Finish documented source review before core build: '+required
 summary=load('working/'+stage+'/SUMMARY.json');assert summary['complete']
 rows,status,objects=current_records(stage);records={c['contribution_id']:c for c in objects}
 grouped=load('working/'+stage+'/CONTRIBUTION_GROUPS.json');assert grouped.get('same_confirmation_receipt')=='evidence/SAME_CONFIRMATION_POLICY.json','Complete conservative second look first';assert load('evidence/SAME_CONFIRMATION_POLICY.json')['enabled'];names=load('working/'+stage+'/CONCEPT_NAMES.json')
 assert not names['missing'],'Resolve failed concept naming first'
 named={x['group_key']:x for x in names['names']}
 assert set(named)=={object_hash(g) for g in grouped['groups']},'Names must match final reviewed groups'
 from concepts import audit_common_scope,group_card
 for g in grouped['groups']:
  assert set(named[object_hash(g)]['support_contribution_ids'])<=set(g)
  audit_common_scope(named[object_hash(g)],group_card(g,records),g,records)
 domain_organization=load('working/'+stage+'/DOMAIN_ORGANIZATION.json');domain_rows={r['group_key']:r for r in domain_organization['mappings']};domain_map={key:r['canonical_domain'] for key,r in domain_rows.items()}
 assert domain_organization.get('shared_directory')
 assert set(domain_map)==set(named)
 registry=Registry(W/'state/TECHNOLOGY_ID_REGISTRY.json')
 concepts=[];links=[];relations=[];mergeaudit=[];cidtech={};domains={}
 for group in grouped['groups']:
  n=named[object_hash(group)];tid=registry.allocate('B',group[0],group);aid=registry.allocate('A',domain_map[n['group_key']],[])
  domains.setdefault(aid,dict(name=domain_map[n['group_key']],scope=domain_rows[n['group_key']]['domain_scope'],children=[],source_cids=[]));domains[aid]['children'].append(tid);domains[aid]['source_cids']+=group
  c=[records[x] for x in group];families=sorted({x['family_id'] for x in c})
  concepts.append(dict(technology_id=tid,level='B',name=n['name_zh'],parent_technology_id=aid,technical_object=n['technical_object'],technical_problem=n['technical_problem'],core_mechanism=n['core_mechanism'],applicable_conditions=n['applicable_conditions'],description=n['core_mechanism']+'\n'+n['scope_limit'],evidence_status='SOURCE_BACKED_CANDIDATE_NOT_HUMAN_GOLD',version='D2.1',family_count=len(families),distinct_source_text_count=len({object_hash(dict(title=x['source_title'],abstract=x['source_abstract'])) for x in c}),contribution_count=len(group),support_contribution_ids_json=stable(group),support_family_ids_json=stable(families),review_notes=n['review_notes'],naming_support_cids_json=stable(n['support_contribution_ids']),cluster_id_used_as_identity=False))
  relations.append(dict(source_technology_id=aid,target_technology_id=tid,relation_type='Parent-Child',hierarchy_type='OBJECT_PROBLEM_ORGANIZATION',rationale=domain_rows[n['group_key']]['domain_scope']+' 仅作对象/问题目录，不主张子节点机理等价。',request_id=domain_rows[n['group_key']]['request_id'],classification_method=domain_rows[n['group_key']]['classification_origin'],source_contribution_ids_json=stable(group),evidence_ids_json=None,origin='LLM_SOURCE_DOMAIN_ORGANIZATION'))
  for cid in group:
   cidtech[cid]=tid;cc=records[cid]
   links.append(dict(family_id=cc['family_id'],contribution_id=cid,technology_id=tid,relation_type='DISCLOSES_CANDIDATE_MECHANISM',evidence_level=cc['evidence_level'],evidence_spans_json=stable(cc['evidence_spans']),source_text_hash=cc['source_text_hash'],semantic_validation_status=cc['semantic_validation_status']))
 for aid,domain in sorted(domains.items()):
  concepts.append(dict(technology_id=aid,level='A',name=domain['name'],parent_technology_id=None,technical_object=domain['name'],technical_problem=None,core_mechanism=None,applicable_conditions=None,description=domain['scope']+'\n组织目录；各子节点的物理机制与证据独立保留。',evidence_status='ORGANIZATIONAL_DOMAIN',version='D2.1',family_count=len({records[c]['family_id'] for c in domain['source_cids']}),distinct_source_text_count=len({object_hash(dict(title=records[c]['source_title'],abstract=records[c]['source_abstract'])) for c in domain['source_cids']}),contribution_count=len(domain['source_cids']),support_contribution_ids_json=stable(domain['source_cids']),support_family_ids_json=stable(sorted({records[c]['family_id'] for c in domain['source_cids']})),review_notes='Domain labels are open-vocabulary and may require human consolidation',naming_support_cids_json=stable([]),cluster_id_used_as_identity=False))
 from merge import Judge
 judge=Judge([records[c] for c in cidtech],state_db())
 for p in sorted((W/'pairs').glob('*.json')):
  saved=json.loads(p.read_text());j=saved['result'];a,b=j['left'],j['right']
  if a not in cidtech or b not in cidtech or p.stem!=judge.key(a,b):continue
  ta,tb=cidtech[a],cidtech[b]
  if j['relation']=='Same' and saved.get('equivalence_usable') is False:
   mergeaudit.append(dict(left=a,right=b,left_technology_id=ta,right_technology_id=tb,merged=False,rationale='Second confirmation failed; unjudged, not model Uncertain',request_id=saved['request_id']));continue
  if j['relation']=='Same':mergeaudit.append(dict(left=a,right=b,left_technology_id=ta,right_technology_id=tb,merged=ta==tb,rationale=j['rationale'],request_id=saved['request_id']))
  if ta==tb:continue
  if j['relation']=='Parent-Child' and j['parent_id']==b:ta,tb=tb,ta
  relations.append(dict(source_technology_id=ta,target_technology_id=tb,relation_type=j['relation'],hierarchy_type='MECHANISM_SCOPE' if j['relation']=='Parent-Child' else None,rationale=j['rationale'],source_contribution_ids_json=stable([a,b]),evidence_ids_json=stable(dict(left=j['evidence_ids_left'],right=j['evidence_ids_right'])),origin=('AI_SOURCE_REVIEW_OVERRIDE' if saved.get('source_review') else ('LLM_SECOND_SOURCE_REVIEW' if saved.get('same_confirmation') else 'LLM_BILATERAL_MECHANISM_COMPARISON')),original_llm_relation=saved.get('original_llm_result',j)['relation'],request_id=saved['request_id'],confirmation_request_id=saved.get('same_confirmation',{}).get('request_id')))
 # Mechanism-scope inheritance is only a proposal and must be acyclic.
 scope_edges={};clean_relations=[]
 def reachable(start,target):
  seen=set();todo=[start]
  while todo:
   node=todo.pop()
   if node==target:return True
   if node in seen:continue
   seen.add(node);todo.extend(scope_edges.get(node,[]))
  return False
 for relation in relations:
  relation['evidence_status']='ORGANIZATIONAL_CLASSIFICATION' if relation['origin']=='LLM_SOURCE_DOMAIN_ORGANIZATION' else 'PAIR_SUPPORTED_CANDIDATE_NOT_GROUP_EQUIVALENCE'
  if relation['relation_type']=='Parent-Child' and relation['hierarchy_type']=='MECHANISM_SCOPE':
   source,target=relation['source_technology_id'],relation['target_technology_id']
   if reachable(target,source):
    relation['proposed_relation_type']='Parent-Child';relation['relation_type']='Uncertain';relation['rationale']='Cycle detected; inheritance withheld. Original pair rationale: '+relation['rationale']
   else:scope_edges.setdefault(source,[]).append(target)
  clean_relations.append(relation)
 relations=clean_relations
 registry.commit()
 members=pd.read_parquet(W/'inputs/CLUSTER_MEMBERS.parquet');cohorts=pd.read_csv(W/'inputs/COHORTS.csv')
 ld=pd.DataFrame(links)
 mapped=members.merge(ld[['family_id','contribution_id','technology_id']],on='family_id',how='inner')
 mapping=[]
 for keys,g in mapped.groupby(['selection_id','run_id','cluster_id','technology_id']):
  cohort=cohorts[cohorts.selection_id==keys[0]].iloc[0]
  mapping.append(dict(selection_id=keys[0],run_id=keys[1],cluster_id=int(keys[2]),technology_id=keys[3],unique_families=int(g.family_id.nunique()),contributions=int(g.contribution_id.nunique()),support_family_ids_json=stable(sorted(g.family_id.unique())),support_contribution_ids_json=stable(sorted(g.contribution_id.unique())),cluster_population=int(cohort.population_size),sampled_families=int(cohort.selected_size),complete_cluster=bool(cohort.complete_cluster),coverage_scope='FULL_CLUSTER' if bool(cohort.complete_cluster) else 'SAMPLED_MEMBERS_ONLY'))
 out=W/'outputs';write_guard(out);out.mkdir(exist_ok=True)
 pq.write_table(pa.Table.from_pylist(rows,schema=table_schema()),out/'PATENT_CONTRIBUTIONS.parquet',compression='zstd')
 for name,data in [('TECHNOLOGY_CONCEPTS',concepts),('PATENT_TECHNOLOGY_RELATIONS',links),('TECHNOLOGY_RELATIONS',relations),('CLUSTER_TECHNOLOGY_MAPPING',mapping),('PATENT_PROCESSING_STATUS',status),('MERGE_AUDIT',mergeaudit)]:
  flat_write(data,out/(name+'.parquet'))
 save('working/'+stage+'/KB_RECORDS.json',dict(concepts=concepts,patent_technology=links,technology_relations=relations,cluster_technology=mapping,processing_status=status))
 write_guard(out/'TECHNOLOGY_KNOWLEDGE_BASE.sqlite');db=sqlite3.connect(out/'TECHNOLOGY_KNOWLEDGE_BASE.sqlite');db.execute('PRAGMA foreign_keys=ON')
 for name,df in [('technology_concepts',pd.DataFrame(concepts)),('patent_contributions',pd.DataFrame([{**r,**{k:stable(v) for k,v in r.items() if isinstance(v,(dict,list))}} for r in rows])),('patent_technology_relations',pd.DataFrame(links)),('technology_relations',pd.DataFrame(relations)),('cluster_technology',pd.DataFrame(mapping)),('patent_processing_status',pd.DataFrame(status))]:
  df.to_sql(name,db,if_exists='replace',index=False)
 source_families=pd.read_parquet(W/'inputs/PATENT_TEXTS.parquet')[['family_id','publication_id','title','abstract','language','text_hash','text_quality','row_idx']]
 source_families.to_sql('patent_families',db,if_exists='replace',index=False)
 db.execute('CREATE UNIQUE INDEX IF NOT EXISTS patent_family_id_idx ON patent_families(family_id)')
 db.execute('CREATE UNIQUE INDEX IF NOT EXISTS technology_id_idx ON technology_concepts(technology_id)')
 db.execute('CREATE UNIQUE INDEX IF NOT EXISTS contribution_id_idx ON patent_contributions(contribution_id)')
 db.execute('CREATE INDEX IF NOT EXISTS family_idx ON patent_contributions(family_id)')
 assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok';db.commit();db.close()
 files=['PATENT_CONTRIBUTIONS.parquet','TECHNOLOGY_CONCEPTS.parquet','PATENT_TECHNOLOGY_RELATIONS.parquet','TECHNOLOGY_RELATIONS.parquet','CLUSTER_TECHNOLOGY_MAPPING.parquet','PATENT_PROCESSING_STATUS.parquet','MERGE_AUDIT.parquet']
 freeze=dict(at=now(),stage=stage,files_sha256={f:sha(out/f) for f in files},source_dataset_sha256=sha(W/'inputs/DATASET_FROZEN.json'),groups_sha256=sha(W/'working'/stage/'CONTRIBUTION_GROUPS.json'),names_sha256=sha(W/'working'/stage/'CONCEPT_NAMES.json'),contributions=len(rows),mechanism_concepts=sum(c['level']=='B' for c in concepts),domain_nodes=len(domains),history_used=False,printhead_relevance_used=False,d1_names_used=False,limitations='Candidate mechanisms and relations; no human gold or exhaustive discovery claim')
 frozen_working=['working/'+stage+'/contributions.json','working/'+stage+'/KB_RECORDS.json','working/'+stage+'/CONCEPT_NAMES.json','working/'+stage+'/DOMAIN_ORGANIZATION.json','working/'+stage+'/CONTRIBUTION_GROUPS.json','state/TECHNOLOGY_ID_REGISTRY.json','evidence/ASSISTANT_SOURCE_AMENDMENTS.json','evidence/SAME_CONFIRMATION_POLICY.json','evidence/PAIR_ASSISTANT_AUDIT_SELECTION.json','evidence/DUAL_SAME_ASSISTANT_DIAGNOSTIC_SELECTION.json','evidence/PAIR_ASSISTANT_SOURCE_REVIEW_APPLIED.json','evidence/NAMING_SOURCE_REVIEW.json','evidence/FINAL_SOURCE_PAIR_REVIEW_APPLIED.json','evidence/NAME_VALIDATION_REPLAYS.json','evidence/LATE_NAMING_AUDIT_REPAIRS.json','evidence/DOMAIN_SEED_SELECTION.json','evidence/DOMAIN_SOURCE_REVIEW.json']
 freeze['working_sha256']={f:sha(W/f) for f in frozen_working}
 freeze['pair_cache_sha256']={str(p.relative_to(W)):sha(p) for p in sorted((W/'pairs').glob('*.json'))}
 freeze['selected_input_sha256']=load('inputs/DATASET_FROZEN.json')['sha256']
 assert not (W/'evidence/CORE_FREEZE.json').exists()
 save('evidence/CORE_FREEZE.json',freeze)
 event('core_kb_frozen',**freeze)
if __name__=='__main__':build()
