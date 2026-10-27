from common import *
from client import call
from pipeline import selection,prompt,COMPARE,source_input
import collections,random,concurrent.futures,argparse

def active_main(fid):
 p=W/'working/main'/(fid.replace(':','_')+'.json')
 if not p.exists():return None
 r=load(p);q=load('requests/'+r['original_request_id']+'.json')
 if q['fingerprint']['prompt_sha']!=oh(prompt('organize')):return None
 return r

def archived_records():
 rows=json.loads((D2/'working/all_selected/contributions.json').read_text());out=collections.defaultdict(list)
 fields=['contribution_id','technical_object','technical_problem','technical_mechanism','implementation','expected_effect','applicable_conditions','materials','process_methods','structures','parameters','evidence_level','mechanism_type','ambiguity_notes','evidence_spans']
 for r in rows:out[r['family_id']].append({k:r.get(k) for k in fields})
 return out

def validate_comparison(v,doc,ids):
 assert v['family_id']==doc['family_id']
 actual=[r['candidate_id'] for r in v['scores']];assert len(actual)==len(set(actual)) and set(actual)==set(ids),'Candidate IDs mismatch'
 source_ids={s['id'] for s in source_input(doc)['source_spans']}
 for r in v['source_only_reference']:
  assert r['evidence_ids'] and set(r['evidence_ids'])<=source_ids,'Reference source invalid'
 for r in v['scores']:
  for k in ['correct_contribution_count','expected_contribution_count','oversplit_count','missing_contribution_count','hallucination_count','critical_material_retained','critical_material_expected','critical_process_retained','critical_process_expected']:
   if r[k] is not None:assert r[k]>=0,'Negative count'
  assert r['critical_material_retained']<=r['critical_material_expected'],'Retained materials exceed reference'
  assert r['critical_process_retained']<=r['critical_process_expected'],'Retained processes exceed reference'
  for e in r['errors']:assert set(e['evidence_ids'])<=source_ids,'Error source invalid'

def evaluate(doc,old,ablation):
 fid=doc['family_id'];main=active_main(fid);assert main,'Current complete D3 record unavailable'
 candidates=dict(D2_ARCHIVED=dict(contributions=old.get(fid,[]),source='Archive AI output; no result if original failure'),D3_FIDELITY=main['original'],D3_EVIDENCE=main['final'])
 omissions=[]
 if ablation:
  for mode,name in [('extract_only','D3_EXTRACT_ONLY'),('d2_replay','D2_DEEPSEEK_REPLAY')]:
   p=W/'working'/mode/(fid.replace(':','_')+'.json')
   if p.exists():
    r=load(p)
    if mode=='extract_only' and r['fingerprint']['prompt_sha']!=oh(prompt('extract_only')):omissions.append(name+': stale development round');continue
    candidates[name]=r['result']
   else:omissions.append(name+': failed/unavailable')
 names=sorted(candidates);rng=random.Random(int(oh([fid,'anonymous_candidate_order_v1'])[:10],16));rng.shuffle(names)
 mapping={chr(65+i):n for i,n in enumerate(names)}
 payload=dict(source=source_input(doc),candidates=[dict(candidate_id=i,extraction=candidates[n]) for i,n in mapping.items()])
 r=call('comparison',fid,prompt('compare'),payload,COMPARE,lambda x:validate_comparison(x,doc,mapping),max_tokens=9500)
 score=dict(family_id=fid,candidate_mapping=mapping,candidate_omissions=omissions,request_id=r['request_id'],result=r['result'],not_gold=True,label_tier='Silver',anonymous_order_seed='sha256(fid,anonymous_candidate_order_v1)',at=now())
 save('working/comparison/'+fid.replace(':','_')+'.json',score);return score

def run(stage,workers):
 guard();docs=selection(stage);old=archived_records();pilot=set(load('inputs/SPLIT_LOCK.json')['pilot30']);results=[]
 def task(d):
  try:
   r=evaluate(d,old,stage=='holdout' or d['family_id'] in pilot);return dict(family_id=d['family_id'],status='VALID',candidates=list(r['candidate_mapping'].values()))
  except Exception as e:return dict(family_id=d['family_id'],status='FAILED',error=type(e).__name__+': '+str(e)[:900])
 event('comparison_start',stage=stage,n=len(docs),workers=workers)
 with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
  for i,row in enumerate(pool.map(task,docs),1):
   results.append(row)
   if i%10==0 or row['status']=='FAILED':event('comparison_progress',stage=stage,finished=i,total=len(docs),counts=dict(collections.Counter(r['status'] for r in results)),error=row.get('error'))
 save('evidence/COMPARISON_'+stage+'.json',dict(at=now(),results=results,counts=dict(collections.Counter(r['status'] for r in results))))
 event('comparison_done',stage=stage,counts=dict(collections.Counter(r['status'] for r in results)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['pilot30','development','holdout'],required=True);p.add_argument('--workers',type=int,default=12);a=p.parse_args();run(a.stage,a.workers)

def active_comparison(fid):
 p=W/'working/comparison'/(fid.replace(':','_')+'.json')
 if not p.exists():return None
 r=load(p);req=load('requests/'+r['request_id']+'.json')
 if req['fingerprint']['prompt_sha']!=oh(prompt('compare')) or req['fingerprint']['schema_sha']!=oh(COMPARE):return None
 return r
