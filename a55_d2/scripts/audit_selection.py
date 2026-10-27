"""Freeze audit family selection and all selected families' positions in reused D1 runs."""
from common import *
import pandas as pd,numpy as np
def main():
 guard();members=pd.read_parquet(W/'inputs/CLUSTER_MEMBERS.parquet');docs=pd.read_parquet(W/'inputs/PATENT_TEXTS.parquet')
 seed=20261027;rng=np.random.default_rng(seed);selected=[]
 for sid,g in members.groupby('selection_id',sort=True):
  candidates=sorted(set(g.family_id)-set(selected));n=min(6,len(candidates))
  if n:selected.extend(rng.choice(candidates,n,replace=False).tolist())
 remaining=sorted(set(docs.family_id)-set(selected));selected.extend(rng.choice(remaining,80-len(selected),replace=False).tolist())
 assert len(selected)==len(set(selected))==80
 p=W/'inputs/AUDIT_SELECTION.json'
 rec=dict(seed=seed,family_ids=selected,selection="Six unique seeded uniform families per selected cohort, then fill uniformly from remaining selected families to 80; no keywords or output-based success filtering",selected_before_controls_extraction=True,not_human_gold=True)
 if p.exists():assert load(str(p))==rec
 else:save(str(p),rec)
 rows=[]
 for run in sorted(members.run_id.unique()):
  kind='hdbscan' if run.startswith('bge_n') else ('leiden' if '_mutual_' in run else 'kmeans')
  path=D1/kind/run/'labels.npy';labels=np.load(path,mmap_mode='r')
  for d in docs.to_dict('records'):
   cluster=int(labels[d['row_idx']])
   rows.append(dict(family_id=d['family_id'],row_idx=d['row_idx'],run_id=run,cluster_id=cluster,is_noise=cluster<0,selected_cohort_member=bool(((members.family_id==d['family_id'])&(members.run_id==run)&(members.cluster_id==cluster)).any())))
 pd.DataFrame(rows).to_parquet(W/'inputs/ALL_SELECTED_FAMILY_POSITIONS.parquet',index=False)
 save('evidence/FAMILY_POSITIONS.json',dict(at=now(),families=len(docs),runs=len(set(members.run_id)),rows=len(rows),scope="Positions in frozen D1 runs, not additional extracted families or full extra clusters",sha256=sha(W/'inputs/ALL_SELECTED_FAMILY_POSITIONS.parquet')))
 print(stable(dict(audit_families=len(selected),position_rows=len(rows))))
if __name__=='__main__':main()
