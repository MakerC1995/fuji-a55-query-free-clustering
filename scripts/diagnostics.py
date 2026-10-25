"""Local second-level Leiden and rare/boundary/model-disagreement review queues."""
from experiment import *
import pandas as pd
import faiss,igraph as ig,leidenalg as la
def main():
 assert (W/'evidence/D1-G2.json').exists()
 meta=pd.read_csv(W/'manifests/family_mapping.csv',keep_default_na=False)
 # Compare local neighborhoods for every family, preserving low-overlap evidence.
 a=np.load(W/'leiden/bge_neighbors.npy',mmap_mode='r');b=np.load(W/'leiden/qwen_neighbors.npy',mmap_mode='r')
 overlap=np.empty(N,np.float32)
 for i in range(N):overlap[i]=len(set(a[i,:30])&set(b[i,:30]))/30
 np.save(W/'comparison/model_neighbor_overlap30.npy',overlap)
 dump('comparison/model_neighbors.json',dict(k=30,n=N,mean_overlap=float(overlap.mean()),quantiles=np.quantile(overlap,[0,.05,.25,.5,.75,.95,1]).tolist(),note='Both models use validated approximate HNSW; differences include residual ANN error.'))
 records=[]
 def add(ids,kind,run='',cluster=-1,scope=N):
  for i in ids:
   r=meta.iloc[int(i)].to_dict();r.update(candidate_type=kind,run_id=run,cluster_id=int(cluster),scope_size=scope,neighbor_overlap30=float(overlap[i]),bge_neighbor_families=';'.join(meta.iloc[a[i,:5]].family_id.to_list()),qwen_neighbor_families=';'.join(meta.iloc[b[i,:5]].family_id.to_list()),duplicate_text=False,data_issue_flags=[])
   if r['text_quality']=='title_only':r['data_issue_flags'].append('title_only')
   records.append(r)
 add(np.argsort(overlap,kind='stable')[:160],'model_disagreement')
 # KMeans cosine-margin boundary is a diagnostic; assignments remain Euclidean.
 x=vec('bge');cent=np.load(W/'kmeans/bge_k300_s42/centers.npy');cent/=np.linalg.norm(cent,axis=1,keepdims=True)
 margin=np.empty(N,np.float32)
 for i in range(0,N,1024):
  sim=x[i:i+1024]@cent.T;top=np.partition(sim,-2,axis=1)[:,-2:];margin[i:i+len(sim)]=top.max(1)-top.min(1)
 np.save(W/'comparison/bge_k300_cosine_margin.npy',margin)
 add(np.argsort(margin,kind='stable')[:160],'cross_cluster_boundary_cosine_margin','bge_k300_s42')
 runs=[json.loads(p.read_text()) for a in ['hdbscan','leiden'] for p in (W/a).glob('*/result.json')]
 hd=[r for r in runs if r['algorithm']=='hdbscan' and r['model']=='bge' and r['parameters']['min_cluster_size']==30 and r['parameters']['min_samples']==15 and 'PCA_30' in r['space']]
 selected=[max(hd,key=lambda r:r['sample_size']),next(r for r in runs if r['run_id']=='bge_k30_mutual_r1.0_s42'),next(r for r in runs if r['run_id']=='bge_n50000_pca30_c10_s5')]
 rng=np.random.default_rng(42)
 for r in selected:
  f=W/r['algorithm']/r['run_id'];labels=np.load(f/'labels.npy');ids=np.load(f/'row_ids.npy') if (f/'row_ids.npy').exists() else np.arange(N)
  cs,cnt=np.unique(labels[labels>=0],return_counts=True)
  candidates=cs[(cnt>=3)&(cnt<=30)]
  for c in candidates[:60]:
   ri=ids[labels==c];add(ri,'small_cluster',r['run_id'],c,len(ids))
  noise=ids[labels<0]
  if len(noise):
   # Sample each observed language/quality category, then fill with reproducible random noise.
   md=meta.iloc[noise];picked=[]
   for _,g in md.groupby(['language','text_quality']):picked.extend(rng.choice(g.index,min(5,len(g)),replace=False).tolist())
   remain=np.setdiff1d(noise,picked);picked+=rng.choice(remain,min(160,len(remain)),replace=False).tolist();add(picked,'hdbscan_noise',r['run_id'],-1,len(ids))
 # Data-quality flags stay separate from potential technology status.
 dup=json.loads((W/'evidence/duplicate_groups.json').read_text());duplicate_ids={i for g in dup for i in g['row_ids']}
 for r in records:
  r['duplicate_text']=r['row_idx'] in duplicate_ids
  if r['duplicate_text']:r['data_issue_flags'].append('shared_raw_text_or_abstract')
  r['data_issue_flags']=';'.join(r['data_issue_flags'])
 con=db();con.row_factory=sqlite3.Row
 for r in records:
  d=dict(con.execute('select title,abstract from docs where row_idx=?',(int(r['row_idx']),)).fetchone());r.update(d)
 pd.DataFrame(records).drop_duplicates(['row_idx','candidate_type','run_id','cluster_id']).to_csv(W/'comparison/rare_candidates.csv',index=False)
 # Rebuild neighborhood graph within two largest communities. No predefined categories.
 parent='bge_k30_mutual_r1.0_s42';labels=np.load(W/f'leiden/{parent}/labels.npy');cs,cnt=np.unique(labels,return_counts=True)
 for c in cs[np.argsort(-cnt)[:2]]:
  ids=np.flatnonzero(labels==c);z=np.ascontiguousarray(x[ids]);n=len(z)
  faiss.omp_set_num_threads(1);idx=faiss.IndexHNSWFlat(1024,16,faiss.METRIC_INNER_PRODUCT);idx.hnsw.efConstruction=100;idx.hnsw.efSearch=200;idx.add(z);d,j=idx.search(z,min(16,n))
  exact=faiss.IndexFlatIP(1024);exact.add(z);qi=np.random.default_rng(42).choice(n,min(64,n),replace=False);ed,ej=exact.search(z[qi],min(16,n));local_recall=float(np.mean([len(set(j[v][j[v]!=v][:15])&set(ej[t][ej[t]!=v][:15]))/min(15,n-1) for t,v in enumerate(qi)]));del exact
  edges=sorted({tuple(sorted((i,int(v)))) for i,row in enumerate(j) for v in row if i!=v})
  g=ig.Graph(n=n,edges=edges);weights=[float(max(0,np.dot(z[i],z[j]))) for i,j in edges]
  p=la.find_partition(g,la.RBConfigurationVertexPartition,weights=weights,resolution_parameter=1,n_iterations=4,seed=42)
  sub=np.array(p.membership,np.int32)
  f=W/f'leiden/local_{parent}_c{c}';f.mkdir(exist_ok=True);np.save(f/'labels.npy',sub);np.save(f/'row_ids.npy',ids)
  pd.DataFrame(dict(row_idx=ids,family_id=meta.iloc[ids].family_id.to_list(),parent_cluster=int(c),local_cluster=sub)).to_csv(f/'local_assignments.csv',index=False)
  dump(str((f/'local_result.json').relative_to(W)),dict(parent_run=parent,parent_cluster=int(c),**stats(sub),k=min(15,n-1),index='local HNSW M16 efConstruction100 efSearch200',objective='RBConfigurationVertexPartition',resolution=1,seed=42,local_recall_at15=local_recall,recall_queries=len(qi),modularity=p.modularity,note='Exploratory rebuilt local graph; approximate neighbors; no category labels or forced split.'))
 dump('evidence/rare_and_local_completion.json',dict(status='PASS',review_rows=len(records),local_parents=2))
 log('rare_local_complete',review_rows=len(records))
if __name__=='__main__':main()
