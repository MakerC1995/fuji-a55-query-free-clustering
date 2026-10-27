"""Apply documented post-hoc AI source review, preserving original local-model history."""
from common import *
from posthoc_relevance import verify_freeze
from posthoc_history import OUTCOMES
def main():
 guard();freeze=verify_freeze();review=load('evidence/HISTORY_ASSISTANT_FINAL_REVIEW_DECISIONS.json')
 original=W/'outputs/HISTORICAL_VALIDATION_LOCAL_MODEL.json'
 if not original.exists():
  current=load('outputs/HISTORICAL_VALIDATION.json');assert current['completed']==current['required']==45
  save(str(original),current)
 base=load(str(original));rows={r['family_id']:dict(r) for r in base['rows']};seen=set();changed=[];accepted=[]
 for d in review['rows']:
  fid=d['family_id'];assert fid in rows and fid not in seen;seen.add(fid);r=rows[fid]
  assert d['outcome'] in OUTCOMES and d['reason'].strip()
  assert isinstance(d['needs_full_text'],bool)
  before=r['outcome']
  r['original_local_model_outcome']=before;r['original_local_model_reason']=r['reason']
  r['outcome']=d['outcome'];r['reason']=d['reason'];r['source_sufficiency']=d['source_sufficiency'];r['needs_full_text']=d['needs_full_text']
  r['assistant_source_review']=dict(at=review['at'],origin='ASSISTANT_REAL_SOURCE_REVIEW_NOT_HUMAN_GOLD',local_model_request_id=r['request_id'],local_outcome_changed=before!=d['outcome'])
  r['validation_origin']='LOCAL_LLM_PLUS_ASSISTANT_SOURCE_REVIEW_NOT_HUMAN_GOLD'
  if before!=r['outcome']:changed.append(dict(family_id=fid,before=before,after=r['outcome'],reason=d['reason']))
  else:accepted.append(fid)
 assert seen==set(rows),'Review all 45 source cases explicitly; never label unread cases reviewed'
 final=dict(base);final.update(at=now(),rows=[rows[r['family_id']] for r in base['rows']],assistant_source_reviewed=45,original_local_model_file=original.name,human_gold=False)
 save('outputs/HISTORICAL_VALIDATION.json',final)
 save('evidence/HISTORICAL_ASSISTANT_REVIEW.json',dict(at=now(),reviewed=45,category_changes=changed,accepted_category_family_ids=accepted,not_human_gold=True,core_definitions_modified=False,local_model_file_sha256=sha(original),decisions_sha256=sha(W/'evidence/HISTORY_ASSISTANT_FINAL_REVIEW_DECISIONS.json')))
 verify_freeze();print(stable(dict(reviewed=45,changed=len(changed),core_unchanged=True)))
if __name__=='__main__':main()
