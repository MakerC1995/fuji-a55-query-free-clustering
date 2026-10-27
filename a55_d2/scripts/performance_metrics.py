"""Observed operational timing; never equate queued wall time with GPU compute."""
from common import *
def compute(requests,union_seconds):
 extraction=[r for r in requests if r['kind']=='extract']
 fid_by_request={}
 for r in extraction:
  p=W/'requests'/(r['request_id']+'.input.json')
  if not p.exists():continue
  m=load(str(p));body=m.get('canonical_source_input')
  if not body:
   try:body=json.loads(m['payload']['messages'][1]['content'])
   except (ValueError,KeyError,TypeError):continue
  if isinstance(body,dict) and body.get('family_id'):fid_by_request[r['request_id']]=body['family_id']
 events=[json.loads(line) for line in (W/'logs/events.jsonl').read_text().splitlines() if line.strip()]
 starts={};windows=[]
 for e in events:
  if e.get('event')=='stage_execution_started':starts[e['stage']]=e
  if e.get('event')=='stage_finished' and e['stage'] in starts:
   a=starts.pop(e['stage']);start=datetime.datetime.fromisoformat(a['at']);end=datetime.datetime.fromisoformat(e['at'])
   rr=[r for r in extraction if a['at']<=r['started_at']<=e['at']]
   fs={fid_by_request[r['request_id']] for r in rr if r['request_id'] in fid_by_request}
   rules={v['family_id'] for v in events if v.get('event')=='family_title_only_abstention' and a['at']<=v['at']<=e['at']}
   seconds=(end-start).total_seconds()
   windows.append(dict(stage=e['stage'],start=a['at'],end=e['at'],client_concurrency=a['client_concurrency'],request_count=len(rr),families_with_requests=len(fs),rule_abstention_families=len(rules),incremental_families_attempted=len(fs|rules),elapsed_s=seconds,observed_families_per_hour=len(fs|rules)*3600/seconds if seconds>0 else None))
 nonempty=[r for r in requests if r.get('finished_at')]
 elapsed=(max(datetime.datetime.fromisoformat(r['finished_at']) for r in nonempty)-min(datetime.datetime.fromisoformat(r['started_at']) for r in requests)).total_seconds() if nonempty else None
 result=dict(at=now(),model_request_families=len(set(fid_by_request.values())),extraction_requests=len(extraction),extraction_interval_union_s=union_seconds(extraction),all_model_interval_union_s=union_seconds(requests),wall_clock_first_to_last_request_s=elapsed,explicit_stage_windows=windows,timing_scope='HTTP request intervals include queue/network/model service; not GPU benchmark. Wall clock includes pauses and development gaps.',unlogged_stage_start_not_inferred=True)
 bulk=next((w for w in windows if w['stage']=='all_selected' and w['incremental_families_attempted']>500),None)
 if bulk:
  hours=238541/bulk['observed_families_per_hour']
  result['conditional_full_corpus_extraction_extrapolation']=dict(hours=hours,days=hours/24,basis='Only if source mix, model, concurrency and service throughput matched this control batch; excludes merging, naming and review; not a full-corpus runtime promise')
 return result
