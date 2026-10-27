"""Post-freeze limited audit closure. Never overwrite frozen benchmark predictions."""
from common import *
from client import call
from pipeline import source_input,prompt,RELEVANCE,validate_rel
from experiments import active_main
import collections,concurrent.futures

def main():
 guard();assert (W/'evidence/MODEL_FREEZE.json').exists()
 docs={d['family_id']:d for d in load('inputs/ALL_DOCUMENTS.json')};refs=collections.defaultdict(list)
 for p in (W/'working/node_relevance').glob('*.json'):
  r=load(p)
  for fid in r['selection']['family_ids']:
   refs[fid].append(dict(technology_id=r['selection']['technology_id'],reference=r['result'],source_review_request_id=r['request_id']))
 todo=[]
 for fid,rr in refs.items():
  m=active_main(fid)
  if m and any((x['reference']['axis_a'],x['reference']['axis_b'])!=(m['relevance']['axis_a'],m['relevance']['axis_b']) or x['reference']['source_families_disagree'] for x in rr):todo.append((fid,rr,m))
 save('inputs/RELEVANCE_ADJUDICATION_SELECTION.json',dict(at=now(),family_ids=[x[0] for x in todo],rule='Preselected independent node audit conflicts with frozen family prediction; different scopes may explain differences. Model re-reads raw source. Posthoc patches never replace benchmark predictions.',holdout_used_for_prompt_tuning=False))
 results=[]
 def task(row):
  fid,rr,m=row;d=docs[fid]
  try:
   r=call('relevance_adjudication',fid,prompt('relevance'),dict(source=source_input(d),extraction=m['final'],previous_prediction=m['relevance'],independent_node_audits=rr,review_scope='Source-based re-adjudication, node and whole-family scopes can differ; audits are fallible drafts. Use original source and preserve uncertainty.'),RELEVANCE,lambda v:validate_rel(v,d),max_tokens=4500)
   out=dict(family_id=fid,version='D3.1-R1',benchmark_version='D3.1 frozen; unchanged',original=m['relevance'],revised=r['result'],request_id=r['request_id'],review_request_ids=[x['source_review_request_id'] for x in rr],changed=(r['result']['axis_a'],r['result']['axis_b'])!=(m['relevance']['axis_a'],m['relevance']['axis_b']),adoption_reason=r['result']['mechanism_rationale'],label_tier='Silver',human_confirmed=False,posthoc_not_independent_evaluation=True,at=now())
   save('working/relevance_adjudication/'+fid.replace(':','_')+'.json',out);return dict(family_id=fid,status='VALID',changed=out['changed'])
  except Exception as e:return dict(family_id=fid,status='FAILED',error=str(e)[:800])
 event('relevance_closure_start',n=len(todo))
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
  for r in pool.map(task,todo):results.append(r)
 save('evidence/RELEVANCE_ADJUDICATION_BATCH.json',dict(at=now(),results=results,counts=dict(collections.Counter(r['status'] for r in results))))
 event('relevance_closure_done',counts=dict(collections.Counter(r['status'] for r in results)))
if __name__=='__main__':main()
