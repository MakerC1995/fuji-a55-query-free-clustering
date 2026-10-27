from common import *
import collections,re
from client import estimate
import pyarrow.parquet as pq
guard();old=json.loads((D2/'working/all_selected/contributions.json').read_text());counts=collections.Counter(c['family_id'] for c in old)
requests=[]
for fid in load('inputs/SPLIT_LOCK.json')['pilot30']:
 cs=[c for c in old if c['family_id']==fid]
 for c in cs:
  rid=c.get('request_id');p=D2/'responses'/(str(rid)+'.raw.json')
  if p.exists():
   r=json.loads(p.read_text());requests.append(dict(family_id=fid,request_id=rid,done=r.get('done'),done_reason=r.get('done_reason'),output_tokens=r.get('eval_count')))
summary=dict(at=now(),family_count=len(counts),contribution_count=len(old),distribution=dict(collections.Counter(counts.values())),schema_allows='1–4 per family',prompt_prior='通常1项;2–4 only clearly different',postprocessing='consolidate loops over every contribution; no first-only slice found',transport='Full Title/Abstract covered by source spans; 240-character chunks; per-contribution evidence cap12 model-facing /18 canonical; materials/process/structures cap8; quantitative parameters cap8',output_token_cap='2200 initial, bounded retry up to3600; may constrain very rich abstracts',pilot_request_receipts=requests,interpretation='Observed single-contribution concentration cannot establish omissions. Prompt prior, schema item limits and token caps are plausible constraints, to be assessed through same-source Silver contrast, not confirmed root cause.',not_gold=True)
save('evidence/D2_DIAGNOSTIC.json',summary);print(stable({k:v for k,v in summary.items() if k!='pilot_request_receipts'}))
receipts=[json.loads(p.read_text()) for p in (W/'responses').glob('*.receipt.json')];local=[r['request_id'] for r in receipts if 'Legacy Mac' in r.get('error','')]
save('evidence/PREFLIGHT_LOCAL_FAILURE_CLASSIFICATION.json',dict(at=now(),request_ids=local,http_requests_sent=0,reason='Credential read failed before urllib Request construction; these are local attempts, not API calls or billed zero claims. Original attempt ledgers retained.'))
