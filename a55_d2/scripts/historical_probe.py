"""Source-only probes for six historical cases outside the frozen discovery cohort."""
from common import *
from posthoc_relevance import verify_freeze
import extract
from schema import EXTRACTION_WIRE_SCHEMA,audit_wire_extraction,apply_anchor_positions,ENRICHED_SCHEMA,validate
def main():
 import posthoc_relevance,relevance_source_review
 posthoc_relevance.main() # Reuse complete caches, retry only truly missing first-pass results.
 relevance_source_review.main()
 guard();freeze=verify_freeze();extract.freeze_code();extract.preflight();conn=state_db();docs=load('inputs/HISTORY_SUPPLEMENT_TEXTS.json')['docs'];prompt=(W/'prompts/extraction_v2.txt').read_text();all_contributions=[];statuses=[]
 for d in docs:
  key=object_hash(dict(family_id=d['family_id'],text_hash=d['text_hash'],prompt=prompt,model=extract.DIGEST,schema=EXTRACTION_WIRE_SCHEMA,phase='POST_FREEZE_SOURCE_ONLY_PROBE'));p=W/'historical_probes'/(key+'.json')
  if p.exists():
   saved=load(str(p));assert saved['result_sha256']==object_hash(saved['result']);result=saved['result'];rid=saved['request_id']
  else:
   errors=[];result=None;rid=None
   for attempt in range(1,4):
    messages=[dict(role='system',content=prompt),dict(role='user',content=stable(dict(family_id=d['family_id'],title=d['title'],abstract=d['abstract'])))]
    if errors:messages.append(dict(role='user',content='修正输出契约，不补造事实：'+errors[-1][:700]))
    try:
     raw,rid=extract.request('refine_extract',key,messages,EXTRACTION_WIRE_SCHEMA,attempt,conn);parsed=audit_wire_extraction(raw,d)
     transformed=load('responses/'+rid+'.canonical.json');parsed=apply_anchor_positions(parsed,transformed['source_anchor_lineage'],d);validate(parsed,ENRICHED_SCHEMA);result=parsed
     save(str(p),dict(cache_key=key,request_id=rid,result=result,result_sha256=object_hash(result),phase='POST_FREEZE_SOURCE_ONLY_PROBE',core_frozen_at=freeze['at'],model_received_historical_names=False));break
    except (ValueError,AssertionError,KeyError,TypeError,extract.ServiceUnavailable) as e:
     errors.append(str(e))
     if isinstance(e,extract.ServiceUnavailable):extract.preflight();continue
     error_rid=getattr(e,'request_id',None) or rid
     if error_rid:conn.execute('UPDATE requests SET status=?,error=? WHERE request_id=?',('VALIDATION_FAILED',str(e),error_rid));conn.commit()
   if result is None:
    save('historical_probe_failures/'+key+'.json',dict(family_id=d['family_id'],errors=errors,status='FAILED_VALIDATION',not_source_absence=True));statuses.append(dict(family_id=d['family_id'],status='FAILED_VALIDATION',errors=errors));continue
  for c in result['contributions']:
   all_contributions.append(dict(c,source_title=d['title'],source_abstract=d['abstract'],language=d['language'],publication_id=d['publication_id'],row_idx=d['row_idx'],request_id=rid,probe_scope='POST_FREEZE_SUPPLEMENT_PROBE'))
  statuses.append(dict(family_id=d['family_id'],status='VALID',request_id=rid))
  event('historical_source_probe_complete',family_id=d['family_id'],scope='POST_FREEZE_SUPPLEMENT_PROBE')
 save('working/HISTORY_SUPPLEMENT_CONTRIBUTIONS.json',dict(contributions=all_contributions,statuses=statuses,core_discovery=False))
 save('evidence/HISTORICAL_PROBE_SUMMARY.json',dict(at=now(),families=len(docs),valid=sum(r['status']=='VALID' for r in statuses),failed=sum(r['status']!='VALID' for r in statuses),statuses=statuses,core_discovery=False))
 verify_freeze()
if __name__=='__main__':main()
