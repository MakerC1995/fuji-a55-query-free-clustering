from common import *
import collections,random
import pyarrow as pa,pyarrow.parquet as pq
guard();assert not list((W/'requests').glob('*'))
x=load('inputs/EVALUATION_SELECTION.json');lock=load('inputs/SPLIT_LOCK.json');hist=set(lock['historical_ids_excluded_from_independent_eval']);docs=load('inputs/ALL_DOCUMENTS.json');dm={d['family_id']:d for d in docs};taken={r['family_id'] for r in x};rng=random.Random(2026102701);changes=[]
for r in x:
 if r['family_id'] in hist:
  assert r['split']=='development'
  pool=[d for d in docs if d['family_id'] not in taken|hist and bool(d['abstract'])==bool(r['abstract_chars'])];rng.shuffle(pool);pool.sort(key=lambda d:(d['sampling_cohort']!=r['sampling_cohort'],-len(set(d['sampling_tags'])&set(r['sampling_tags']))));d=pool[0];old=r['family_id'];taken.add(d['family_id'])
  r.update(family_id=d['family_id'],source_text_hash=d['text_hash'],sampling_cohort=d['sampling_cohort'],sampling_tags=d['sampling_tags'],known_issue=False,language=d.get('language'),abstract_chars=len(d['abstract'] or ''),selection_reason='metadata_only_history_overlap_replacement')
  changes.append(dict(old=old,new=r['family_id']))
save('evidence/SPLIT_PRECALL_AMENDMENT.json',dict(at=now(),previous_lock=lock,reason='Remove 6 historical overlaps before any model request; holdout unchanged',changes=changes))
save('inputs/EVALUATION_SELECTION.json',x);pq.write_table(pa.Table.from_pylist(x),W/'inputs/EVALUATION_SELECTION.parquet',compression='zstd')
for k,split in [('development','development'),('holdout','holdout')]:lock[k]=[r['family_id'] for r in x if r['split']==split]
lock['pilot30']=[r['family_id'] for r in x if r['pilot30']];lock['selection_sha256']=sha(W/'inputs/EVALUATION_SELECTION.json');lock['amended_at']=now();lock['historical_overlap']=0;save('inputs/SPLIT_LOCK.json',lock)
assert not {r['family_id'] for r in x}&hist
print('Historical overlap removed; holdout unchanged',len(changes))
