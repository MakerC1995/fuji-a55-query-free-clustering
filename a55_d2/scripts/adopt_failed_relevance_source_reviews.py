"""Adopt explicitly read assistant decisions only for failed post-hoc source reviews."""
from common import *
import repair_relevance_reviews as repair
from schema import make_source_spans
def main():
 guard();db=state_db();assert db.execute("SELECT count(*) FROM requests WHERE status='RUNNING'").fetchone()[0]==0,'Wait until model worker stops'
 freeze,cards,ck=repair.cards_and_key();ledger=load('evidence/RELEVANCE_REPAIR_ADOPTIONS.json');decisions={d['technology_id']:d for d in load('evidence/RELEVANCE_ASSISTANT_REVIEW_DECISIONS.json')['rows']}
 missing=[c for c in cards if not (W/'relevance_reviews'/(ck(c)+'.json')).exists() and c['technology_id'] not in ledger['rows']]
 assert all(c['technology_id'] in decisions for c in missing),'Read missing source cases before adopting: '+str([c['technology_id'] for c in missing if c['technology_id'] not in decisions])
 adopted=[]
 for c in missing:
  tid=c['technology_id'];d=decisions[tid];fail=[p for p in (W/'relevance_repair_failures').glob('*.json') if load(str(p))['technology_id']==tid];assert fail
  requests=[]
  for p in fail:requests+=db.execute('SELECT request_id,started_at FROM requests WHERE cache_key=? ORDER BY started_at DESC',(p.stem,)).fetchall()
  rid=sorted(requests,key=lambda r:r[1])[-1][0];raw=load('responses/'+rid+'.raw.json');model=json.loads(raw['message']['content'])
  quotes=[dict(contribution_id=src['contribution_id'],**q) for src in c['sources'] for q in src['source_spans']]
  if d['category']=='Direct':assert d['source_explicit_head_relation'] and any(repair.rr.HEAD.search(q['text']) for q in quotes)
  if d['category'] in ['Direct','Manufacturing','Transferable']:assert d['head_object'] and d['application']
  if d['category']=='Transferable':assert d['conditions'] and d['engineering_inference']
  r=dict(d,patent_evidence=[],source_evidence_quotes=quotes,core_freeze_sha256=object_hash(freeze),source_review_request_id=rid,source_review_origin='ASSISTANT_SOURCE_REVIEW',source_review_protocol='ASSISTANT_POSTHOC_SOURCE_REVIEW_V1',status='POSTHOC_ASSISTANT_SOURCE_ASSESSMENT_NOT_PROOF_OF_ADOPTION',triage_flags=c['triage_flags'],first_pass_category=c['first_pass']['category'],original_local_model_category=model.get('category'),original_local_model_rationale=model.get('rationale'),assistant_source_review=dict(at=now(),origin='ASSISTANT_READ_ORIGINAL_SOURCE_NOT_HUMAN_GOLD',local_model_request_id=rid))
  key=object_hash(dict(decision=d,freeze=object_hash(freeze),local_request_id=rid,origin='ASSISTANT_POSTHOC_SOURCE_REVIEW_V1'));p=W/'relevance_review_repairs'/('assistant_'+key+'.json')
  save(str(p),dict(result=r,result_sha256=object_hash(r),cache_key=key,request_id=None,source_local_model_request_id=rid,origin='ASSISTANT_SOURCE_REVIEW_NOT_LOCAL_MODEL_OUTPUT'))
  ledger['rows'][tid]=dict(path=str(p.relative_to(W)),result_sha256=object_hash(r),request_id=None,source_local_model_request_id=rid,protocol=r['source_review_protocol']);adopted.append(tid)
 ledger['at']=now();save('evidence/RELEVANCE_REPAIR_ADOPTIONS.json',ledger)
 save('evidence/RELEVANCE_FAILED_SOURCE_ASSISTANT_ADOPTIONS.json',dict(at=now(),technology_ids=adopted,human_gold=False,raw_model_responses_unchanged=True,core_definitions_modified=False))
 print(stable(dict(adopted=len(adopted),technology_ids=adopted)))
if __name__=='__main__':main()
