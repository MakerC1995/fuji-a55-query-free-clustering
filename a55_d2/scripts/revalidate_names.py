"""Replay completed naming receipts with literal-safe optional-note normalization."""
from common import *
import concepts,copy
from schema import validate
def main():
 guard();assert not (W/'evidence/CORE_FREEZE.json').exists()
 data,records=concepts.load_groups('all_selected');groups={object_hash(g):g for g in data['groups']};conn=state_db()
 rows=conn.execute("SELECT request_id FROM requests WHERE kind='name' AND status='VALIDATION_FAILED' ORDER BY started_at DESC").fetchall()
 accepted=[];seen=set()
 for (rid,) in rows:
  rawpath=W/'responses'/(rid+'.raw.json')
  if not rawpath.exists():continue
  request=load('requests/'+rid+'.input.json');raw=load(str(rawpath))
  try:
   body=json.loads(request['payload']['messages'][1]['content'])['groups']
   result=json.loads(raw['message']['content']);normalizations=[]
   for item in result['concepts']:
    if item.get('review_notes','MISSING') is None:item['review_notes']='';normalizations.append('Optional review_notes null -> empty string; no factual field changed')
   validate(result,concepts.SCHEMA);got={r['group_key']:r for r in result['concepts']}
   assert len(got)==len(result['concepts'])==len(body) and set(got)=={c['group_key'] for c in body}
   for c in body:
    try:
     group=[r['contribution_id'] for r in c['representatives']]+c['unrepresented_member_ids'];key=object_hash(group)
     if key not in groups or key in seen:continue
     card=dict(c,group_key=key)
     if concepts.cached_valid(card,groups,records):seen.add(key);continue
     n=copy.deepcopy(got[c['group_key']]);lookup={r['representative_id']:r['contribution_id'] for r in c['representatives']}
     assert set(n['support_representative_ids'])<=set(lookup)
     n['support_contribution_ids']=[lookup[x] for x in n.pop('support_representative_ids')];n['group_key']=key
     problems={records[cid]['technical_problem']['text'] for cid in group};n['technical_problem']=next(iter(problems)) if len(problems)==1 else None
     n['scope_limit']='共同机制候选；各来源特有的问题、材料、定量参数和效果见贡献，不统一继承。'
     concepts.audit_common_scope(n,card,group,records)
     ck=concepts.naming_key(card);save('concept_names/'+ck+'.json',dict(cache_key=ck,request_id=rid,result=n,result_sha256=object_hash(n),at=now(),offline_revalidation=dict(raw_sha256=sha(rawpath),normalizations=normalizations,original_online_status='VALIDATION_FAILED',no_new_model_call=True),transport='short_group_and_representative_ids'))
     accepted.append(dict(group_key=key,request_id=rid,normalizations=normalizations));seen.add(key)
    except (ValueError,AssertionError,KeyError,TypeError):continue
  except (ValueError,AssertionError,KeyError,TypeError):continue
 old=load('evidence/NAME_VALIDATION_REPLAYS.json')['rows'] if (W/'evidence/NAME_VALIDATION_REPLAYS.json').exists() else []
 existing={r['group_key'] for r in old};old+=[r for r in accepted if r['group_key'] not in existing]
 save('evidence/NAME_VALIDATION_REPLAYS.json',dict(at=now(),rows=old,original_request_failures_preserved=True,new_inference_calls=0))
 print(stable(dict(newly_revalidated_groups=len(accepted),total_revalidated_groups=len(old))))
if __name__=='__main__':main()
