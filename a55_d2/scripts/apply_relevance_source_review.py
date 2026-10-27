"""Document a small explicit assistant source audit without changing raw model caches."""
from common import *
from posthoc_relevance import verify_freeze
from schema import make_source_spans
def main():
 guard();freeze=verify_freeze();final=load('outputs/PRINTHEAD_RELEVANCE.json');assert final['completed']==926
 original=W/'outputs/PRINTHEAD_RELEVANCE_BEFORE_FINAL_ASSISTANT_AUDIT.json'
 if not original.exists():save(str(original),final)
 base=load(str(original));rows={r['technology_id']:dict(r) for r in base['results']}
 decisions=load('evidence/RELEVANCE_ASSISTANT_REVIEW_DECISIONS.json')['rows']
 cs={c['contribution_id']:c for c in load('working/all_selected/contributions.json')}
 ts={t['technology_id']:t for t in load('working/all_selected/KB_RECORDS.json')['concepts']}
 changes=[]
 for d in decisions:
  tid=d['technology_id'];r=rows[tid];before=dict(r);quotes=[]
  for cid in json.loads(ts[tid]['support_contribution_ids_json']):
   c=cs[cid]
   quotes.extend(dict(contribution_id=cid,**q) for q in make_source_spans(dict(title=c['source_title'],abstract=c['source_abstract'])))
  r.update({k:v for k,v in d.items() if k!='technology_id'})
  r.update(source_evidence_quotes=quotes,original_local_model_category=before.get('original_local_model_category',before['category']),original_local_model_rationale=before.get('original_local_model_rationale',before['rationale']),assistant_source_review=dict(at=now(),origin='ASSISTANT_ORIGINAL_SOURCE_AUDIT_NOT_HUMAN_GOLD',local_model_request_id=before.get('source_review_request_id')),status='POSTHOC_ASSISTANT_SOURCE_ASSESSMENT_NOT_PROOF_OF_ADOPTION')
  changes.append(dict(technology_id=tid,before=before['category'],after=r['category'],reason=r['review_reason']))
 final=dict(base);final.update(at=now(),results=[rows[r['technology_id']] for r in base['results']],assistant_source_reviewed=len(decisions),human_gold=False)
 save('outputs/PRINTHEAD_RELEVANCE.json',final)
 summary=load('evidence/RELEVANCE_SOURCE_REVIEW_SUMMARY.json')
 save('evidence/RELEVANCE_SOURCE_REVIEW_BEFORE_FINAL_ASSISTANT_AUDIT_SUMMARY.json',summary)
 first={r['technology_id']:r for r in load('outputs/PRINTHEAD_RELEVANCE_FIRST_PASS.json')['results']}
 reviewed=set(load('evidence/RELEVANCE_SOURCE_REVIEW_SELECTION.json')['technology_ids'])
 summary['category_changes']=[dict(technology_id=tid,before=first[tid]['category'],after=r['category'],reason=r.get('review_reason',r['rationale'])) for tid,r in rows.items() if tid in reviewed and r['category']!=first[tid]['category']]
 summary['assistant_source_corrections']=changes;summary['assistant_source_reviewed']=len(decisions);summary['at']=now()
 save('evidence/RELEVANCE_SOURCE_REVIEW_SUMMARY.json',summary)
 save('evidence/RELEVANCE_ASSISTANT_SOURCE_REVIEW.json',dict(at=now(),reviewed=len(decisions),changes=changes,human_gold=False,core_definitions_modified=False,raw_local_model_file_sha256=sha(original)))
 verify_freeze();print(stable(dict(assistant_source_reviewed=len(decisions),changes=changes)))
if __name__=='__main__':main()
