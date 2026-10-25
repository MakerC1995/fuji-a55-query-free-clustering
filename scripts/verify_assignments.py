"""Read back every Parquet assignment against frozen source mappings and label arrays."""
from experiment import *
from analyze import allruns,load
import pyarrow.parquet as pq
import pandas as pd
def main():
 runs=allruns();lookup={r['run_id']:r for r in runs};arrays={};counts=collections.Counter();last={}
 for r in runs:
  labels,ids=load(r);assert np.all(np.diff(ids)>0);assert len(np.unique(ids))==len(ids)
  assert stats(labels)['clusters']==r['clusters'];arrays[r['run_id']]=(labels,ids)
  last[r['run_id']]=-1
 families=pd.read_csv(W/'manifests/family_mapping.csv',usecols=['family_id'],keep_default_na=False).family_id.to_numpy()
 f=pq.ParquetFile(W/'CLUSTER_ASSIGNMENTS.parquet')
 assert f.metadata.num_rows==sum(r['n'] for r in runs)
 for batch in f.iter_batches(batch_size=50000,columns=['run_id','row_idx','family_id','cluster_id','scope_size']):
  frame=batch.to_pandas()
  for rid,part in frame.groupby('run_id',sort=False):
   labels,ids=arrays[rid];ri=part.row_idx.to_numpy()
   assert ri[0]>last[rid] and np.all(np.diff(ri)>0);last[rid]=int(ri[-1])
   pos=np.searchsorted(ids,ri);assert np.array_equal(ids[pos],ri)
   assert np.array_equal(labels[pos],part.cluster_id.to_numpy())
   assert np.array_equal(families[ri],part.family_id.to_numpy())
   assert np.all(part.scope_size.to_numpy()==len(ids));counts[rid]+=len(ri)
 assert all(counts[r['run_id']]==r['n'] for r in runs)
 frozen=json.loads((W/'evidence/ASSIGNMENTS_FROZEN.json').read_text())
 for p,h in frozen['sha256'].items():assert sha(W/p)==h,p
 for p,h in frozen['parameters_sha256'].items():assert sha(W/p)==h,p
 for name,rec in json.loads((W/'evidence/input_file_stats.json').read_text()).items():
  st=(B/name).stat();assert st.st_size==rec['bytes'] and st.st_mtime_ns==rec['mtime_ns'],name
 dump('evidence/assignment_readback.json',dict(status='PASS',parquet_rows=f.metadata.num_rows,experiments=len(runs),full_scope_experiments=sum(r['n']==N for r in runs),partial_scope_experiments=sum(r['n']!=N for r in runs),all_rows_checked=True,unique_sorted_ids_per_experiment=True,labels_exact_match=True,family_mapping_exact_match=True,all_frozen_labels_and_parameters_unchanged=True,source_file_stats_unchanged=True,counts=dict(counts),parquet_sha256=sha(W/'CLUSTER_ASSIGNMENTS.parquet')))
 print('All',f.metadata.num_rows,'Parquet rows verified against',len(runs),'frozen experiments',flush=True)
if __name__=='__main__':main()
