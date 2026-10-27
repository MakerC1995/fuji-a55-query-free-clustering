"""Final integrity checks. A missing output cannot be reported as a completed gate."""
from common import *
from schema import ENRICHED_SCHEMA,validate
from posthoc_relevance import verify_freeze
import pandas as pd,collections,zipfile,xml.etree.ElementTree as ET
def main():
 guard();freeze=verify_freeze();kb=load('working/all_selected/KB_RECORDS.json');cs=load('working/all_selected/contributions.json')
 docs={d['family_id']:d for d in pd.read_parquet(W/'inputs/PATENT_TEXTS.parquet').to_dict('records')}
 formal=ENRICHED_SCHEMA['properties']['contributions']['items'];quote_count=0
 for c in cs:
  validate({k:v for k,v in c.items() if k in formal['properties']},formal)
  assert c['source_text_hash']==docs[c['family_id']]['text_hash']
  for e in c['evidence_spans']:
   assert docs[c['family_id']][e['field']][e['start']:e['end']]==e['quote'];quote_count+=1
 assert len({c['contribution_id'] for c in cs})==len(cs)
 concepts={t['technology_id']:t for t in kb['concepts']};cids={c['contribution_id'] for c in cs}
 for r in kb['patent_technology']:assert r['contribution_id'] in cids and r['technology_id'] in concepts and r['family_id'] in docs
 for r in kb['technology_relations']:
  assert r['source_technology_id'] in concepts and r['target_technology_id'] in concepts
  assert set(json.loads(r['source_contribution_ids_json']))<=cids
 for r in kb['cluster_technology']:assert r['technology_id'] in concepts
 state=state_db();assert state.execute("SELECT count(*) FROM requests WHERE status='RUNNING'").fetchone()[0]==0,'Inspect unclosed model request receipts before delivery';state.close()
 statuses={r['family_id']:r['status'] for r in kb['processing_status']}
 stages=load('inputs/STAGES.json')
 assert len(statuses)==1117
 for stage,ids in stages.items():assert all(statuses[f] in ['VALID','FAILED_VALIDATION'] for f in ids)
 assert len(stages['primary384'])==384
 contrast=load('evidence/CONDITION_CONTRAST_CHECK.json');assert contrast['separate_groups']
 final_groups=load('working/all_selected/CONTRIBUTION_GROUPS.json')['groups'];a,b=contrast['contribution_ids'];assert not any(a in g and b in g for g in final_groups)
 memberships=pd.read_parquet(W/'inputs/CLUSTER_MEMBERS.parquet')
 assert len(memberships)==1688
 assert all(t['technology_id'].startswith(('T_','D_')) for t in concepts.values())
 hist=load('outputs/HISTORICAL_VALIDATION.json');assert hist['completed']==45
 assert load('evidence/HISTORICAL_ASSISTANT_REVIEW.json')['reviewed']==45
 source_review=load('evidence/RELEVANCE_SOURCE_REVIEW_SUMMARY.json');assert source_review['selected']==source_review['completed']
 assert not source_review['core_definitions_modified']
 assert load('outputs/D1_D2_COMPARISON.json')['operational_metrics']['mixed_mechanism_split_rate'] is None
 history_docs=dict(docs);history_docs.update({d['family_id']:d for d in load('inputs/HISTORY_SUPPLEMENT_TEXTS.json')['docs']})
 for r in hist['rows']:
  d=history_docs[r['family_id']];assert r['source_title']==d['title'] and r['source_abstract']==d['abstract']
  for q in r['evidence_quotes']:assert d[q['field']][q['start']:q['end']]==q['text']
 assert collections.Counter(r['history_group'] for r in hist['rows'])=={'Recipe':27,'Equipment':18}
 relevance=load('outputs/PRINTHEAD_RELEVANCE.json');assert relevance['completed']==relevance['required']==sum(t['level']=='B' for t in concepts.values())
 bycid={c['contribution_id']:c for c in cs};relevance_spans=0
 for r in relevance['results']:
  assert r['technology_id'] in concepts and concepts[r['technology_id']]['level']=='B'
  own=set(json.loads(concepts[r['technology_id']]['support_contribution_ids_json']))
  for e in r['patent_evidence']:
   assert e['contribution_id'] in own
   assert set(e['evidence_ids'])<={x['id'] for x in bycid[e['contribution_id']]['evidence_spans']}
  for q in r.get('source_evidence_quotes',[]):
   assert q['contribution_id'] in own;c=bycid[q['contribution_id']]
   assert c['source_'+q['field']][q['start']:q['end']]==q['text'];relevance_spans+=1
  if r['category'] in ['Direct','Manufacturing','Transferable']:
   assert r.get('source_review_request_id'),'All positive associations must have post-freeze source review'
   assert r['head_object'] and r['application']
  if r['category']=='Direct':assert r['source_explicit_head_relation'] and r['source_evidence_quotes']
  if r['category']=='Transferable':assert r['conditions'] and r['engineering_inference']
 domains=load('outputs/DOMAIN_PRINTHEAD_RELEVANCE.json')['domains'];assert len(domains)==sum(t['level']=='A' for t in concepts.values())
 assert sum(r['child_count'] for r in domains)==relevance['completed']
 assert all(sum(r['category_counts'].values())==r['child_count'] for r in domains)
 audit=load('evidence/ASSISTANT_AUDIT80_RATINGS.json');assert len({r['family_id'] for r in audit['rows']})==80
 wb=load('evidence/WORKBOOK_READBACK.json');assert len(wb['worksheets'])==8
 review=pd.read_parquet(W/'outputs/REVIEW_QUEUE.parquet');assert (review.human_status=='待人工').all()
 assert review.human_reviewer.isna().all(),'Never fabricate a human reviewer'
 multi=collections.Counter(c['family_id'] for c in cs)
 required=['D2_REPORT.md','TECHNOLOGY_CONCEPTS.parquet','PATENT_CONTRIBUTIONS.parquet','TECHNOLOGY_RELATIONS.parquet','CLUSTER_TECHNOLOGY_MAPPING.parquet','EXTRACTION_QUALITY.md','HISTORICAL_TECHNOLOGY_VALIDATION.md','EXPERIMENT_COMPARISON.md','EXPERIMENT_MANIFEST.json','TECHNOLOGY_KNOWLEDGE_BASE.sqlite']
 for name in required:assert (W/'outputs'/name).is_file(),name
 dbpath=W/'outputs/TECHNOLOGY_KNOWLEDGE_BASE.sqlite'
 db=sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True);db.execute('PRAGMA query_only=ON')
 assert db.execute('select count(*) from patent_families').fetchone()[0]==1117
 assert db.execute('select count(*) from patent_contributions').fetchone()[0]==len(cs)
 assert db.execute('select count(*) from patent_technology_relations r left join patent_contributions c using(contribution_id) left join technology_concepts t using(technology_id) where c.contribution_id is null or t.technology_id is null').fetchone()[0]==0
 assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok';db.close()
 xlsx=W/'outputs/01a171fb-0dd6-7792-b36b-80e200aba942/TECHNOLOGY_KNOWLEDGE_BASE.xlsx';assert xlsx.is_file()
 with zipfile.ZipFile(xlsx) as z:
  assert z.testzip() is None
  ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
  sheets=[ET.fromstring(z.read(name)) for name in z.namelist() if name.startswith('xl/worksheets/') and name.endswith('.xml')]
  assert len(sheets)==8,'Saved worksheet count'
  assert sum(len(t.findall('x:sheetViews/x:sheetView/x:pane',ns)) for t in sheets)>=7,'Frozen identity/header panes missing'
  assert sum(len(t.findall('x:dataValidations/x:dataValidation',ns)) for t in sheets)>0,'Editable review status validation missing'
  assert len([n for n in z.namelist() if n.startswith('xl/tables/') and n.endswith('.xml')])==7,'Flat filter tables missing'
 # Original data source identities must still match frozen metadata.
 for path,record in load('inputs/SOURCE_LOCKS.json').items():
  p=Path(path);st=p.stat();assert st.st_size==record['bytes'] and st.st_mtime_ns==record['mtime_ns'],path
  if record.get('sha256'):assert sha(p)==record['sha256'],path
 rec=dict(at=now(),status='INTEGRITY_CHECKS_PASSED',families=len(statuses),contributions=len(cs),exact_source_spans=quote_count,exact_posthoc_relevance_spans=relevance_spans,mechanism_concepts=sum(t['level']=='B' for t in concepts.values()),multi_contribution_families=sum(n>1 for n in multi.values()),historical_cases=45,reviewed_by_AI=80,human_gold_families=0,core_freeze_sha256=object_hash(freeze),semantic_accuracy_verified=False,scope='Integrity and completion checks; not an independent semantic accuracy or global discovery recall proof')
 save('evidence/FINAL_INTEGRITY_CHECKS.json',rec);print(stable(rec))
if __name__=='__main__':main()
