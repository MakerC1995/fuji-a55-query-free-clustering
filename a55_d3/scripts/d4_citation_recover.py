"""Recover exact source IDs annotated by the model; retain raw failures and descriptions."""
from common import *
from d4_cases import SCHEMA
from client import validate
from pipeline import source_input
from experiments import active_main
import collections,re

def canonical(value,allowed):
 out=[];annotations=[]
 for x in value:
  if x in allowed:sid=x
  else:
   match=re.match(r'^(S\d{3})(?:[:：\s]|$)',x)
   if not match or match[1] not in allowed:raise ValueError('Unresolvable source citation: '+x)
   sid=match[1];annotations.append(dict(original=x,source_id=sid,rule='exact_leading_source_id_with_description'))
  if sid not in out:out.append(sid)
 return out,annotations

def main():
 guard();pairs=load('inputs/D4_PAIR_SELECTION.json')['pairs'];old={c['contribution_id']:c for c in json.loads((D2/'working/all_selected/contributions.json').read_text())};docs={d['family_id']:d for d in load('inputs/ALL_DOCUMENTS.json')};receipts=[load(p) for p in (W/'responses').glob('*.receipt.json')];results=[];recoveries=[]
 for p in pairs:
  ridlist=sorted([r for r in receipts if r['kind']=='d4_merge_test' and r['family_id']==p['pair_id']],key=lambda r:r['started_at'],reverse=True)
  done=False;last_error='No raw response (D3 main candidate unavailable)'
  for r in ridlist:
   try:
    raw=load('responses/'+r['request_id']+'.raw.json');v=json.loads(raw['choices'][0]['message']['content']);validate(v,SCHEMA);assert v['pair_id']==p['pair_id']
    a,b=old[p['cid_a']],old[p['cid_b']];sa,sb=source_input(docs[a['family_id']]),source_input(docs[b['family_id']]);ma,mb=active_main(a['family_id']),active_main(b['family_id']);assert ma and mb
    ca,aa=canonical(v['evidence_a'],{x['id'] for x in sa['source_spans']});cb,ab=canonical(v['evidence_b'],{x['id'] for x in sb['source_spans']});normalized=dict(v,evidence_a=ca,evidence_b=cb)
    # Raw response, semantic recommendation and rationale unchanged.
    rec=dict(selection=p,family_a=a['family_id'],family_b=b['family_id'],request_id=r['request_id'],result=normalized,source_a=sa,source_b=sb,d2_contribution_a=a,d2_contribution_b=b,d3_contributions_a=ma['final']['contributions'],d3_contributions_b=mb['final']['contributions'],human_confirmed=False,label_tier='Silver',citation_normalization=dict(a=aa,b=ab),original_result=v,original_request_status=r['status'])
    save('working/d4/'+p['pair_id']+'.json',rec);recoveries.append(dict(pair_id=p['pair_id'],request_id=r['request_id'],normalization=rec['citation_normalization'],semantic_changes=False));results.append(dict(pair_id=p['pair_id'],status='VALID_RECOVERED_CITATIONS'));done=True;break
   except Exception as e:last_error=str(e)
  if not done:results.append(dict(pair_id=p['pair_id'],status='FAILED',error=last_error))
 save('evidence/D4_CITATION_RECOVERY.json',dict(at=now(),recoveries=recoveries,original_ledgers_unchanged=True,new_api_calls=0,semantics_changed=False));save('evidence/D4_PAIR_BATCH_FINAL.json',dict(at=now(),results=results,counts=dict(collections.Counter(r['status'] for r in results))))
 assert len(recoveries)>=30,'Insufficient real difficult pairs; no artificial filler'
 event('d4_citation_recovered',counts=dict(collections.Counter(r['status'] for r in results)))
if __name__=='__main__':main()
