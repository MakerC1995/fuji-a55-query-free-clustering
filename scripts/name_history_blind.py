"""Supplemental historical check: history selects clusters, never prompt labels."""
from name_topics import *
def main():
 assert (W/'evidence/FIRST_NAMING_FROZEN.json').exists()
 panels=json.loads((W/'technology_catalog/posthoc_blind_panels.json').read_text());assert len(panels)<=8
 digest=json.loads((W/'evidence/local_llm_lock.json').read_text())['model']['digest']
 folder=W/'technology_catalog/posthoc_blind';folder.mkdir(exist_ok=True)
 dump('evidence/POSTHOC_BLIND_INPUT_FREEZE.json',dict(panels=len(panels),sha256=sha(W/'technology_catalog/posthoc_blind_panels.json'),selection_uses_historical_membership=True,prompt_has_no_historical_labels=True,representatives_not_seeded_with_core_families=True,not_first_pass_discovery=True))
 for panel in panels:
  pid=panel['panel_id'];dest=folder/f'{pid}.json'
  if dest.exists():continue
  ensure_digest(digest);attempt=next_attempt(folder,pid)
  docs=[{**d,'abstract':d['abstract'][:1200],'abstract_truncated':len(d['abstract'])>1200} for d in panel['docs']]
  inp={k:v for k,v in panel.items() if k not in ['docs','selection_stage']};inp['docs']=docs
  payload=dict(model=NAME,messages=[dict(role='system',content=SYSTEM),dict(role='user',content=json.dumps(inp,ensure_ascii=False))],format='json',stream=False,options=dict(temperature=0,num_ctx=16384,num_predict=3600))
  dump(f'technology_catalog/posthoc_blind/{attempt}.input.json',payload)
  t=time.time();raw=api('/api/chat',payload);dump(f'technology_catalog/posthoc_blind/{attempt}.raw.json',raw)
  parsed=json.loads(raw['message']['content']);parsed,bad=check(parsed,docs)
  dump(str(dest.relative_to(W)),dict(panel_id=pid,run_id=panel['run_id'],cluster_id=panel['cluster_id'],cluster_size=panel['cluster_size'],analysis=parsed,invalid_evidence=bad,llm_digest=digest,selection_is_posthoc=True,model_received_historical_names=False,input_sha256=sha(folder/f'{attempt}.input.json'),wall_s=time.time()-t))
  log('posthoc_blind_naming_complete',panel=pid)
 dump('evidence/posthoc_blind_completion.json',dict(panels=len(panels),complete=True,not_first_pass_discovery=True))
if __name__=='__main__':main()
