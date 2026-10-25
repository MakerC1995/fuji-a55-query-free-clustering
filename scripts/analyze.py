"""Metrics, sampling and evidence prepared only after frozen cluster assignments."""
from experiment import *
import pandas as pd
from sklearn.metrics import adjusted_rand_score,normalized_mutual_info_score,silhouette_score
import scipy.sparse as sp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
META=pd.read_csv(W/'manifests/family_mapping.csv',keep_default_na=False)
def allruns():
 records=[]
 for a in ['kmeans','hdbscan','leiden']:
  for p in sorted((W/a).glob('*/result.json')):
   r=clean_json(json.loads(p.read_text()));r.update(stats(np.load(p.parent/'labels.npy')));records.append(r)
 return records
def load(r):
 folder=W/r['algorithm']/r['run_id'];lab=np.load(folder/'labels.npy')
 ids=np.load(folder/'row_ids.npy') if (folder/'row_ids.npy').exists() else np.arange(N)
 return lab,ids
def pairs(runs):
 records=[]
 for ai,a in enumerate(runs):
  for b in runs[ai+1:]:
   # Compare seeds, model matched parameters, and selected cross-algorithm baselines.
   seed_pair=a['model']==b['model'] and a['algorithm']==b['algorithm'] and a.get('seed')!=b.get('seed') and a['parameters']=={**b['parameters'],**({'random_state':a['parameters']['random_state']} if 'random_state' in a['parameters'] else {})}
   model_pair=a['model']!=b['model'] and a['algorithm']==b['algorithm'] and a.get('seed')==b.get('seed') and a['parameters']==b['parameters'] and a.get('sample_size',N)==b.get('sample_size',N) and a['space']==b['space']
   param_pair=a['model']==b['model'] and a['algorithm']==b['algorithm'] and a.get('seed')==b.get('seed') and a['algorithm']=='leiden'
   cross=a['model']==b['model']=='bge' and a['algorithm']!=b['algorithm'] and a['run_id'] in PRIMARY and b['run_id'] in PRIMARY
   if not(seed_pair or model_pair or param_pair or cross):continue
   la,ia=load(a);lb,ib=load(b);common,pa,pb=np.intersect1d(ia,ib,return_indices=True);aa=la[pa];bb=lb[pb];mask=(aa>=0)&(bb>=0)
   records.append(dict(run_a=a['run_id'],run_b=b['run_id'],scope_n=len(common),comparison='seed' if seed_pair else 'model' if model_pair else 'parameter' if param_pair else 'algorithm',ari_noise_as_one_label=adjusted_rand_score(aa,bb),nmi_noise_as_one_label=normalized_mutual_info_score(aa,bb),nonnoise_n=int(mask.sum()),ari_both_nonnoise=adjusted_rand_score(aa[mask],bb[mask]) if mask.sum()>1 else None,nmi_both_nonnoise=normalized_mutual_info_score(aa[mask],bb[mask]) if mask.sum()>1 else None))
 pd.DataFrame(records).to_csv(W/'comparison/partition_comparison.csv',index=False)
 return records
def metric(r):
 folder=W/r['algorithm']/r['run_id'];target=folder/'quality.json'
 if target.exists():return json.loads(target.read_text())
 labels,ids=load(r);x=vec(r['model']);valid=labels>=0;labs=labels[valid];rowids=ids[valid];nc=int(labs.max()+1) if len(labs) else 0
 sizes=np.bincount(labs,minlength=nc);sums=np.zeros((nc,1024),np.float64)
 for start in range(0,len(ids),4096):
  sl=labels[start:start+4096];si=ids[start:start+4096];keep=sl>=0
  if keep.any():
   mat=sp.csr_matrix((np.ones(keep.sum(),np.float32),(sl[keep],np.arange(keep.sum()))),shape=(nc,keep.sum()))
   sums+=mat@x[si[keep]]
 norms=np.linalg.norm(sums,axis=1);centers=(sums/np.maximum(norms[:,None],1e-12)).astype(np.float32)
 avg_pair=(norms**2-sizes)/np.maximum(sizes*(sizes-1),1);avg_pair[sizes<2]=np.nan
 np.save(folder/'semantic_centers.npy',centers)
 per=np.empty(len(ids),np.float32);per[:]=np.nan
 for start in range(0,len(ids),4096):
  sl=labels[start:start+4096];si=ids[start:start+4096];keep=sl>=0
  vals=per[start:start+4096];vals[keep]=np.einsum('ij,ij->i',x[si[keep]],centers[sl[keep]])
 np.save(folder/'semantic_center_cosine.npy',per)
 rng=np.random.default_rng(42);sample=[]
 for c in np.flatnonzero(sizes>1):
  pos=np.flatnonzero(labels==c)
  sample.extend(rng.choice(pos,min(2,len(pos)),replace=False).tolist())
 if len(sample)<2000:
  remain=np.setdiff1d(np.flatnonzero(valid),sample)
  sample+=rng.choice(remain,min(2000-len(sample),len(remain)),replace=False).tolist()
 if len(sample)>3000:sample=rng.choice(sample,3000,replace=False).tolist()
 ss=np.array(sample,np.int32);sil=float(silhouette_score(x[ids[ss]],labels[ss],metric='cosine')) if len(np.unique(labels[ss])) in range(2,len(ss)) else None
 md=META.iloc[ids];lang=md.language.astype(str);quality=md.text_quality.astype(str)
 length_bins=np.digitize(md.text_length,[100,300,600,1000,2000])
 nearest=[];nonempty=centers[sizes>0]
 for start in range(0,len(nonempty),256):
  sm=nonempty[start:start+256]@nonempty.T
  for j in range(len(sm)):sm[j,start+j]=-np.inf
  nearest.extend(sm.max(axis=1).tolist())
 result=dict(nearest_other_center_cosine_mean=float(np.mean(nearest)) if len(nonempty)>1 else None,run_id=r['run_id'],mean_pair_cosine_weighted=float(np.nansum(avg_pair*sizes)/max(sizes[sizes>1].sum(),1)),mean_center_cosine=float(np.nanmean(per)),silhouette_cosine=sil,silhouette_n=len(ss),silhouette_sample_rows=ids[ss].tolist(),language_nmi=float(normalized_mutual_info_score(labels,lang)),text_quality_nmi=float(normalized_mutual_info_score(labels,quality)),length_bin_nmi=float(normalized_mutual_info_score(labels,length_bins)),noise_language=md.loc[labels<0,'language'].value_counts().to_dict(),cluster_pair_mean_cosine=avg_pair.tolist(),metric_note='Silhouette uses fixed cluster-stratified subset, original 1024D; centroid pair cosine uses exact sufficient statistics, excludes singleton pairs.')
 dump(str(target.relative_to(W)),result);log('quality_complete',run=r['run_id'],silhouette=sil)
 return result
def panel(r,c):
 labels,ids=load(r);pos=np.flatnonzero(labels==c);rows=ids[pos];folder=W/r['algorithm']/r['run_id']
 sim=np.load(folder/'semantic_center_cosine.npy')[pos]
 order=np.argsort(-sim,kind='stable');rng=np.random.default_rng(42+c);chosen=[];roles=[]
 def add(index,role):
  v=int(index)
  if v not in chosen:chosen.append(v);roles.append(role)
 for v in order[:2]:add(v,'near_center')
 for v in order[-2:]:add(v,'edge')
 for v in rng.permutation(len(pos))[:3]:add(v,'random')
 # Additional farthest-first candidate from a bounded pool.
 x=vec(r['model']);pool=rng.choice(len(pos),min(256,len(pos)),replace=False)
 while len(chosen)<min(8,len(pos)):
  sims=x[rows[pool]]@x[rows[chosen]].T
  best=int(pool[np.argmin(sims.max(axis=1))]);before=len(chosen);add(best,'diverse')
  if len(chosen)==before:break
 con=db();docs=[]
 for i,role in zip(chosen[:8],roles[:8]):
  con.row_factory=sqlite3.Row;d=dict(con.execute('select row_idx,family_id,pub_id,publication_id,title,abstract,language,title_language,text_quality,text_hash,title_text_id,abstract_text_id,source,translated,priority_date from docs where row_idx=?',(int(rows[i]),)).fetchone())
  d.update(selection_role=role,center_cosine=float(sim[i]));docs.append(d)
 con.close()
 return dict(panel_id=f"{r['run_id']}__c{c}",run_id=r['run_id'],algorithm=r['algorithm'],model=r['model'],cluster_id=int(c),cluster_size=len(rows),clustering_scope_size=r.get('sample_size',N),unique_representative_texts=int(META.iloc[rows].text_hash.nunique()),title_only_fraction=float((META.iloc[rows].text_quality=='title_only').mean()),docs=docs)
def choose(r,n):
 labels,ids=load(r);cs,cnt=np.unique(labels[labels>=0],return_counts=True);keep=cnt>=3;cs=cs[keep];cnt=cnt[keep];sort=np.argsort(cnt);positions=np.linspace(0,len(cs)-1,min(n,len(cs))).astype(int);selected=cs[sort[positions]].tolist()
 if r['algorithm']=='kmeans' and n>=10:
  scores=np.array(metric(r)['cluster_pair_mean_cosine'],dtype=float);hetero=np.argsort(np.nan_to_num(scores,nan=2))[:5].tolist()
  selected=selected[:max(0,n-5)]
  for c in hetero:
   if c not in selected and (labels==c).sum()>=3:selected.append(c)
  for c in cs[sort]:
   if len(selected)>=n:break
   if int(c) not in selected:selected.append(int(c))
 return [panel(r,int(c)) for c in selected]
def figures(runs):
 for r in runs:
  if r['run_id'] not in PRIMARY:continue
  labels,ids=load(r);sizes=np.unique(labels[labels>=0],return_counts=True)[1]
  fig,axs=plt.subplots(2,2,figsize=(12,8));fig.suptitle(r['run_id']+f" | n={len(ids):,}, noise={(labels<0).mean():.1%}")
  axs[0,0].hist(sizes,bins=40);axs[0,0].set(xlabel='Cluster size',ylabel='Clusters')
  axs[0,1].hist(sizes,bins=np.geomspace(max(1,sizes.min()),max(2,sizes.max()),40));axs[0,1].set(xscale='log',xlabel='Cluster size (log)',ylabel='Clusters')
  axs[1,0].bar(range(min(20,len(sizes))),sorted(sizes,reverse=True)[:20]);axs[1,0].set(xlabel='Top 20 size rank',ylabel='Families')
  bins=[1,3,10,31,101,501,10**9];counts=np.histogram(sizes,bins)[0];axs[1,1].bar(['1–2','3–9','10–30','31–100','101–500','>500'],counts);axs[1,1].set(ylabel='Clusters')
  fig.tight_layout();fig.savefig(W/f"figures/{r['run_id']}_sizes.png",dpi=150);plt.close(fig)
 # PCA display sample fixed stratified subset; visualization never defines clusters.
 sample=np.load(W/'manifests/sample_20000.npy');rng=np.random.default_rng(42);sample=np.sort(rng.choice(sample,10000,replace=False))
 for m in ['bge','qwen']:
  xy=np.load(W/f'hdbscan/{m}_pca50.npy',mmap_mode='r')[sample,:2]
  fig,axes=plt.subplots(1,3,figsize=(15,5))
  hds=[r for r in runs if r['model']==m and r['algorithm']=='hdbscan' and r['parameters']['min_cluster_size']==30 and r['parameters']['min_samples']==15 and 'PCA_30' in r['space']]
  chosen=[r for r in runs if r['run_id']==f'{m}_k300_s42']+[max(hds,key=lambda r:r['sample_size'])]+[r for r in runs if r['run_id']==f'{m}_k30_mutual_r1.0_s42']
  for ax,r in zip(axes,chosen):
   labels,ri=load(r);pl=labels[np.searchsorted(ri,sample)];cs,cnt=np.unique(labels[labels>=0],return_counts=True);top=cs[np.argsort(-cnt)[:20]];palette={int(c):plt.get_cmap('tab20')(i) for i,c in enumerate(top)};colors=[palette.get(int(c),(0.65,0.65,0.65,1)) if c>=0 else (0.1,0.1,0.1,1) for c in pl];ax.scatter(xy[:,0],xy[:,1],c=colors,s=2,alpha=.35,rasterized=True);ax.set(title=r['run_id'],xlabel='PC1',ylabel='PC2')
  fig.suptitle('Fixed stratified sample; 2D projection is display only; top 20 clusters colored within panel; others gray, Noise black');fig.tight_layout();fig.savefig(W/f'figures/{m}_pca_display.png',dpi=160);plt.close(fig)
def pca_diag():
 rows=[]
 for m in ['bge','qwen']:
  x=vec(m);z=np.load(W/f'hdbscan/{m}_pca50.npy',mmap_mode='r');qs=np.sort(np.random.default_rng(42).choice(N,64,replace=False))
  # Top20 exact streamed queries in original and reduced spaces.
  from sklearn.metrics import pairwise_distances
  top={}
  for d in [1024,30,50]:
   ar=x if d==1024 else z[:,:d];best=np.full((len(qs),21),np.inf);ind=np.full((len(qs),21),-1,np.int32)
   for i in range(0,N,8192):
    dist=pairwise_distances(ar[qs],ar[i:i+8192],metric='euclidean',n_jobs=1)
    ci=np.broadcast_to(np.arange(i,i+dist.shape[1]),dist.shape);v=np.concatenate([best,dist],1);j=np.concatenate([ind,ci],1);p=np.argpartition(v,20,axis=1)[:,:21];best=np.take_along_axis(v,p,1);ind=np.take_along_axis(j,p,1)
   top[d]=[set(ind[j][ind[j]!=v]) for j,v in enumerate(qs)]
  for d in [30,50]:rows.append(dict(model=m,pca_dimensions=d,queries=64,neighbor_k=20,mean_original_neighbor_overlap=float(np.mean([len(a&b)/20 for a,b in zip(top[1024],top[d])]))))
 pd.DataFrame(rows).to_csv(W/'comparison/pca_neighbor_retention.csv',index=False)
 return rows
def assignments(runs):
 import pyarrow as pa,pyarrow.parquet as pq
 writer=None
 try:
  for r in runs:
   labels,ids=load(r);folder=W/r['algorithm']/r['run_id'];dist=np.load(folder/'distances.npy',mmap_mode='r') if (folder/'distances.npy').exists() else None
   for i in range(0,len(ids),30000):
    ri=ids[i:i+30000].astype(np.int64,copy=False);num=len(ri)
    frame=pd.DataFrame(dict(row_idx=ri,family_id=META.iloc[ri].family_id.to_list(),cluster_id=labels[i:i+num],model=r['model'],algorithm=r['algorithm'],run_id=r['run_id'],parameter_json=json.dumps(r['parameters'],sort_keys=True),version='A55-D1-v1',distance=dist[i:i+num].astype(float) if dist is not None else np.full(num,np.nan),scope_size=len(ids)))
    tab=pa.Table.from_pandas(frame,preserve_index=False)
    if writer is None:writer=pq.ParquetWriter(W/'CLUSTER_ASSIGNMENTS.parquet',tab.schema,compression='zstd')
    writer.write_table(tab)
 finally:
  if writer:writer.close()
def freeze(runs):
 files={str(p.relative_to(W)):sha(p) for a in ['kmeans','hdbscan','leiden'] for p in (W/a).glob('*/labels.npy')}
 dump('evidence/ASSIGNMENTS_FROZEN.json',dict(time=time.strftime('%Y-%m-%dT%H:%M:%S%z'),sha256=files,run_count=len(runs),no_history_or_keywords_used=True))
def main():
 global PRIMARY
 audit()
 if (W/'evidence/FIRST_NAMING_FROZEN.json').exists() and (W/'evidence/D1-G3.json').exists():
  frozen=json.loads((W/'evidence/ASSIGNMENTS_FROZEN.json').read_text())
  for name,h in frozen['sha256'].items():assert sha(W/name)==h
  inp=json.loads((W/'evidence/LLM_INPUT_FREEZE.json').read_text());assert sha(W/'technology_catalog/cluster_panels.json')==inp['sha256']
  log('analysis_checkpoint_reused',no_label_or_input_changes=True);return
 runs=allruns();assert (W/'evidence/D1-G2.json').exists(),'Experiments not complete'
 hd=[r for r in runs if r['algorithm']=='hdbscan' and r['model']=='bge' and r['parameters']['min_cluster_size']==30 and r['parameters']['min_samples']==15 and 'PCA_30' in r['space']]
 mainhd=max(hd,key=lambda r:r['sample_size'])
 PRIMARY=['bge_k100_s42','bge_k300_s42','bge_k800_s42','qwen_k300_s42',mainhd['run_id'],'bge_k30_mutual_r1.0_s42','bge_k30_sym_r1.0_s42','qwen_k30_mutual_r1.0_s42','qwen_k30_sym_r1.0_s42','bge_n50000_pca30_c10_s5']
 dump('comparison/primary_runs.json',PRIMARY);freeze(runs)
 pair=pairs(runs)
 for r in runs:
  if r['run_id'] in PRIMARY:metric(r)
 panels=[]
 for runid,n in [('bge_k300_s42',30),('bge_k30_mutual_r1.0_s42',10),('bge_k30_sym_r1.0_s42',5),(mainhd['run_id'],10),('bge_n50000_pca30_c10_s5',5)]:
  r=next(r for r in runs if r['run_id']==runid);panels+=choose(r,n)
 if len(panels)<60:
  fallback=next(r for r in runs if r['run_id']=='bge_n50000_pca30_c10_s5')
  metric(fallback)
  extras=choose(fallback,60-len(panels))
  panels+=extras
 for qid,qn in [('qwen_k300_s42',5),('qwen_k30_mutual_r1.0_s42',3),('qwen_k30_sym_r1.0_s42',2)]:
  qr=next(r for r in runs if r['run_id']==qid);panels+=choose(qr,qn)
 dump('technology_catalog/cluster_panels.json',panels)
 # Snapshot raw evidence before any local LLM naming.
 dump('evidence/LLM_INPUT_FREEZE.json',dict(panels=len(panels),sha256=sha(W/'technology_catalog/cluster_panels.json'),unprompted_by_known_technologies=True))
 figures(runs);pca_diag();assignments(runs)
 pd.DataFrame([{k:v for k,v in r.items() if isinstance(v,(str,int,float,bool)) or v is None} for r in runs]).to_csv(W/'comparison/run_statistics.csv',index=False)
 dump('evidence/D1-G3.json',dict(status='METRICS_COMPLETE_SEMANTIC_REVIEW_PENDING',panels=len(panels),primary_runs=PRIMARY))
 log('comparison_complete',panels=len(panels))
if __name__=='__main__':main()
