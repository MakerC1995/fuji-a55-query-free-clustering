"""Deterministic D2 wrapper adaptation; frozen extraction and history prompt/schema unchanged."""
from common import *
from client import call
from history import HIST
from pipeline import source_input,full
from experiments import active_main
import collections,concurrent.futures

def main():
 guard();assert (W/'evidence/BATCH_main_full.json').exists()
 for p,h in load('evidence/MODEL_FREEZE.json')['semantic_code_hashes'].items():assert sha(W/p)==h
 docs=load('inputs/ALL_DOCUMENTS.json');dm={d['family_id']:d for d in docs};core_ids=set(dm)
 probes=json.loads((D2/'inputs/HISTORY_SUPPLEMENT_TEXTS.json').read_text())['docs'];dm.update({d['family_id']:d for d in probes})
 cases=json.loads((D2/'working/HISTORY_CASES.json').read_text())['cases']
 old=json.loads((D2/'working/all_selected/contributions.json').read_text())+json.loads((D2/'working/HISTORY_SUPPLEMENT_CONTRIBUTIONS.json').read_text())['contributions'];oc=collections.defaultdict(list)
 for c in old:oc[c['family_id']].append({k:c.get(k) for k in ['technical_object','technical_problem','technical_mechanism','implementation','materials','parameters','evidence_spans']})
 import pyarrow.parquet as pq
 pts=pq.read_table(D2/'outputs/PATENT_TECHNOLOGY_RELATIONS.parquet').to_pylist();rel={r['technology_id']:r['category'] for r in json.loads((D2/'outputs/PRINTHEAD_RELEVANCE.json').read_text())['results']};oldcats=collections.defaultdict(set)
 for r in pts:oldcats[r['family_id']].add(rel[r['technology_id']])
 save('evidence/HISTORY_LOADER_ADAPTATION.json',dict(at=now(),reason='D2 historical texts are wrapped under docs; supplement contributions under contributions. Original loader failed before API calls. Separate corrected reader retains frozen history prompt/schema and all main semantic hashes. Actual D2 relevance categories included for false-Unrelated assessment.',semantic_prompt_changed=False,holdout_predictions_changed=False,inputs={n:sha(D2/n) for n in ['working/HISTORY_CASES.json','inputs/HISTORY_SUPPLEMENT_TEXTS.json','working/HISTORY_SUPPLEMENT_CONTRIBUTIONS.json','outputs/HISTORICAL_VALIDATION.json']}))
 results=[]
 def task(c):
  fid=c['family_id'];d=dm[fid]
  try:
   r=active_main(fid)
   if r is None and fid not in core_ids:r=full(d)
   if r is None:
    ext=dict(processing_status='FAILED',contributions=[],note='Main extraction failed under fixed bounded retries; do not invent recovered result');relevance=None;d3status='FAILED'
   else:ext=r['final'];relevance=r['relevance'];d3status=r['status']
   ids={s['id'] for s in source_input(d)['source_spans']}
   def check(v):
    assert v['family_id']==fid
    for a in v['source_available_means']+v['extraction_omissions']:assert a['evidence_ids'] and set(a['evidence_ids'])<=ids, 'Each claimed means/omission must cite valid Sxxx source IDs; if there is no omission use [] and keep source insufficiency as a gap, not an omission.'
   rr=call('historical_regression',fid,(W/'prompts/history_v1.txt').read_text(),dict(source=source_input(d),historical_expectations=c['history_reference'],d2_extraction=oc[fid],d2_actual_relevance_categories=sorted(oldcats[fid]),d3_extraction=ext,d3_relevance=relevance),HIST,check,max_tokens=5500)
   rec=dict(case=c,scope='main_discovery39' if fid in core_ids else 'postfreeze_probe6',request_id=rr['request_id'],result=rr['result'],d3_status=d3status,label_tier='Silver',human_confirmed=False)
   save('working/history/'+fid.replace(':','_')+'.json',rec);return dict(family_id=fid,status='VALID',scope=rec['scope'])
  except Exception as e:return dict(family_id=fid,status='FAILED',error=type(e).__name__+': '+str(e)[:900])
 with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
  for i,r in enumerate(pool.map(task,cases),1):
   results.append(r)
   if i%10==0 or r['status']=='FAILED':event('history_complete_progress',finished=i,counts=dict(collections.Counter(x['status'] for x in results)),error=r.get('error'))
 save('evidence/HISTORY_BATCH.json',dict(at=now(),results=results,counts=dict(collections.Counter(r['status'] for r in results))))
 event('history_complete_done',counts=dict(collections.Counter(r['status'] for r in results)))
if __name__=='__main__':main()
