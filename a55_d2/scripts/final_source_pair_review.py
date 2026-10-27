"""Apply two additional source-read distinctions after the current naming worker stops."""
from common import *
import merge,copy,fcntl
def main():
 guard();assert not (W/'evidence/CORE_FREEZE.json').exists()
 if (W/'evidence/FINAL_SOURCE_PAIR_REVIEW_APPLIED.json').exists():return
 records=merge.load_stage('all_selected');byid={c['contribution_id']:c for c in records};byfamily={c['family_id']:c['contribution_id'] for c in records};judge=merge.Judge(records,state_db());rows=[]
 for fid in ['google:51840117','google:47995898']:
  a,b=sorted([byfamily['google:55217532'],byfamily[fid]]);p=W/'pairs'/(judge.key(a,b)+'.json');saved=load(str(p));old=copy.deepcopy(saved['result'])
  note='两侧共享室温粘弹性基体分散压电颗粒和双侧电极，但55217532另以主面单侧凸起作为具体声学结构办法；材料和基础层叠结构不足以证明完整贡献等价，保留Related及分别的机制节点。'
  if old['relation']=='Same':
   new=dict(old,relation='Related',parent_id=None,rationale=note,evidence_ids_left=[e['id'] for e in byid[a]['evidence_spans'] if e['field']=='abstract'][:8],evidence_ids_right=[e['id'] for e in byid[b]['evidence_spans'] if e['field']=='abstract'][:8],judgment_origin='AI_ASSISTANT_SOURCE_DIAGNOSTIC_NOT_HUMAN_GOLD')
   merge.verify_judgment_evidence(new,byid);saved.setdefault('original_llm_result',old);saved['pre_final_source_result']=old;saved['result']=new;saved['result_sha256']=object_hash(new);saved['equivalence_usable']=False
   saved['source_review']=dict(at=now(),reviewer='AI_ASSISTANT_NOT_HUMAN_GOLD',reason=note,original_cache_sha256=sha(p));save(str(p),saved)
  rows.append(dict(left_family_id=byid[a]['family_id'],right_family_id=byid[b]['family_id'],pair_path=str(p.relative_to(W)),before=old['relation'],after=saved['result']['relation'],reason=note,human_gold=False))
 class ExistingOnly(merge.Judge):
  def ensure(self,pairs):return [self.existing(p['left'],p['right']) for p in pairs]
 x,keys=merge.embeddings(records,judge.conn);groups,audit=merge.conservative_groups(records,x,ExistingOnly(records,judge.conn))
 data=load('working/all_selected/CONTRIBUTION_GROUPS.json');data.update(at=now(),groups=groups,audit=audit,group_count=len(groups),final_source_review='evidence/FINAL_SOURCE_PAIR_REVIEW_APPLIED.json');save('working/all_selected/CONTRIBUTION_GROUPS.json',data)
 save('evidence/FINAL_SOURCE_PAIR_REVIEW_APPLIED.json',dict(at=now(),rows=rows,groups=len(groups),scope='Three complete member abstracts read during common-condition naming audit; AI diagnostic, not independent human Gold'))
 event('final_source_pair_review_applied',pairs=len(rows),groups=len(groups))
if __name__=='__main__':
 lock=(W/'state/worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
