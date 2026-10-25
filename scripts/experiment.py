"""A5.5-D1: checkpointed, query-free CPU experiments. All sources read-only."""
import os,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(W/'deps'))
os.environ.update(OMP_NUM_THREADS="2",OPENBLAS_NUM_THREADS="2",VECLIB_MAXIMUM_THREADS="2",MPLCONFIGDIR=str(W/'evidence/mpl'))
import json,time,hashlib,csv,sqlite3,gc,collections,platform,importlib.metadata,resource
import numpy as np,psutil
try:
 from threadpoolctl import threadpool_limits
 threadpool_limits(2)
except ImportError:pass
B=Path('/Volumes/Fuji_SSD_Work/patent/embedding_benchmark/vector_corpus/v1')
N=238541; SEEDS=[42,137]
def clean_json(v):
 if isinstance(v,dict):return {k:clean_json(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [clean_json(x) for x in v]
 if hasattr(v,'item'):v=v.item()
 if isinstance(v,float) and not np.isfinite(v):return None if np.isnan(v) else ('Infinity' if v>0 else '-Infinity')
 return v
def dump(p,obj):
 p=W/p;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
 tmp.write_text(json.dumps(clean_json(obj),ensure_ascii=False,indent=2,allow_nan=False,default=lambda o:o.item() if hasattr(o,'item') else str(o)));tmp.replace(p)
def log(event,**kw):
 rec=dict(time=time.strftime('%Y-%m-%dT%H:%M:%S%z'),event=event,rss_gib=psutil.Process().memory_info().rss/2**30,available_gib=psutil.virtual_memory().available/2**30,**kw)
 with (W/'logs/events.jsonl').open('a') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
 print(json.dumps(rec,ensure_ascii=False),flush=True)
def guard(need=.5):
 assert Path('/Volumes/Fuji_SSD_Work').is_mount()
 assert psutil.disk_usage('/Volumes/Fuji_SSD_Work').free>25*2**30
 assert psutil.virtual_memory().available>need*2**30,'Insufficient available RAM'
def vec(m):return np.load(B/f'{m}_index.f32.npy',mmap_mode='r')
def db():
 c=sqlite3.connect((B/'corpus.sqlite').as_uri()+'?mode=ro',uri=True);c.execute('PRAGMA query_only=ON');return c
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
def audit():
 if (W/'evidence/input_audit.json').exists():
  check=W/'evidence/input_file_stats.json'
  if check.exists():
   for name,record in json.loads(check.read_text()).items():
    st=(B/name).stat();assert st.st_size==record['bytes'] and st.st_mtime_ns==record['mtime_ns'],'Input changed since audit: '+name
  return
 guard();base=json.loads((B/'baseline.json').read_text());con=db()
 assert con.execute('select count(*),count(distinct family_id),min(row_idx),max(row_idx) from docs').fetchone()==(N,N,0,N-1)
 checks={}; hashes={}
 for m in ['bge','qwen']:
  x=vec(m);assert x.shape==(N,1024) and x.dtype==np.float32
  bad=zero=0;err=0
  for i in range(0,N,4096):
   z=x[i:i+4096];norm=np.linalg.norm(z,axis=1);bad+=int((~np.isfinite(z)).sum());zero+=int((norm==0).sum());err=max(err,float(abs(norm-1).max()))
  assert bad==zero==0 and err<2e-6
  name=f'{m}_index.f32.npy';hashes[name]=sha(B/name);assert hashes[name]==base['files'][name]['sha256']
  assert np.all(np.load(B/f'{m}_completion.npy')==1)
  checks[m]=dict(shape=list(x.shape),dtype=str(x.dtype),nonfinite=bad,zero=zero,max_norm_error=err,sha256=hashes[name])
  del x;gc.collect()
 # Stream every representative: verify CSV mapping and stored raw-text hash.
 qualities=collections.Counter();langs=collections.Counter();abstracts=collections.defaultdict(list);texts=collections.defaultdict(list);mapping=hashlib.sha256()
 with (B/'CORPUS_MANIFEST.csv').open(encoding='utf-8-sig') as f,(W/'manifests/family_mapping.csv').open('w') as out:
  writer=csv.writer(out);writer.writerow(['row_idx','family_id','pub_id','language','priority_date','text_quality','text_hash','abstract_hash','translated','text_length'])
  cur=con.execute('select row_idx,family_id,pub_id,language,priority_date,text_quality,text_hash,raw_text,abstract,translated,bge_input_hash,qwen_input_hash from docs order by row_idx')
  for r,c in zip(cur,csv.DictReader(f),strict=True):
   i,fid,pub,lang,date,quality,th,raw,ab,tr,bh,qh=r
   assert int(c['row_idx'])==i and c['family_id']==fid and c['pub_id']==pub and c['text_hash']==th and c['bge_input_hash']==bh and c['qwen_input_hash']==qh
   assert hashlib.sha256(raw.encode()).hexdigest()==th
   ah=hashlib.sha256(ab.encode()).hexdigest() if ab else ''
   writer.writerow([i,fid,pub,lang,date,quality,th,ah,tr,len(raw)])
   mapping.update(f'{i}\t{fid}\t{pub}\t{th}\n'.encode())
   qualities[quality]+=1;langs[lang]+=1;texts[th].append(i)
   if ah:abstracts[ah].append(i)
 duplicates=[]
 for typ,d in [('raw_text',texts),('abstract',abstracts)]:
  for h,ids in d.items():
   if len(ids)>1:duplicates.append(dict(type=typ,hash=h,count=len(ids),row_ids=ids))
 dump('evidence/duplicate_groups.json',duplicates)
 result=dict(status='PASS',families=N,dimensions=1024,vectors=checks,family_unique=True,same_model_row_mapping=True,all_text_hashes_and_manifest_rows_verified=True,mapping_sha256=mapping.hexdigest(),text_quality=dict(qualities),languages=dict(langs),duplicate_raw_groups=sum(r['type']=='raw_text' for r in duplicates),duplicate_abstract_groups=sum(r['type']=='abstract' for r in duplicates),duplicates_retained=True,baseline_id=base['baseline_id'])
 dump('evidence/input_audit.json',result)
 dump('manifests/source_baseline.json',base)
 dump('evidence/environment.json',dict(python=sys.version,platform=platform.platform(),cpu=platform.processor(),memory=psutil.virtual_memory()._asdict(),cpu_percent=psutil.cpu_percent(1),threads=2,dependencies={p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','hdbscan','faiss-cpu','igraph','leidenalg','matplotlib','pandas','pyarrow']}))
 log('audit_complete',**result)
def stats(labels):
 vals,c=np.unique(labels[labels>=0],return_counts=True)
 return dict(singleton_clusters=int((c==1).sum()),clusters_ge3=int((c>=3).sum()),small_nontrivial_3_30=int(((c>=3)&(c<=30)).sum()),fraction_in_clusters_ge3=float(c[c>=3].sum()/len(labels)),n=len(labels),clusters=len(vals),noise=int((labels<0).sum()),noise_fraction=float((labels<0).mean()),size_mean=float(c.mean()) if len(c) else 0,size_median=float(np.median(c)) if len(c) else 0,size_p5=float(np.quantile(c,.05)) if len(c) else 0,size_p95=float(np.quantile(c,.95)) if len(c) else 0,size_p99=float(np.quantile(c,.99)) if len(c) else 0,size_min=int(c.min()) if len(c) else 0,size_max=int(c.max()) if len(c) else 0,small_10_30=int(((c>=10)&(c<=30)).sum()),small_le30=int((c<=30).sum()),small_le30_coverage=float(c[c<=30].sum()/len(labels)),largest_fraction=float(c.max()/len(labels)) if len(c) else 0)
def save_run(run,labels,meta,extras=None):
 folder=W/meta['algorithm']/run;folder.mkdir(parents=True,exist_ok=True)
 np.save(folder/'labels.npy',labels.astype(np.int32))
 if extras:
  for name,v in extras.items():np.save(folder/f'{name}.npy',v)
 dump(str(folder.relative_to(W)/'result.json'),dict(run_id=run,**meta,**stats(labels),peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**30))
 log('run_complete',run=run,**stats(labels))
def kmeans(m,k,seed):
 from sklearn.cluster import MiniBatchKMeans
 run=f'{m}_k{k}_s{seed}'
 if (W/f'kmeans/{run}/result.json').exists():return
 guard(.8);log('run_start',run=run);start=time.time();x=vec(m)
 model=MiniBatchKMeans(n_clusters=k,random_state=seed,batch_size=2048,init='k-means++',n_init=3,max_iter=100,max_no_improvement=20,tol=0.0,init_size=max(3*k,6144),compute_labels=True,reassignment_ratio=.01)
 model.fit(x)
 labels=np.empty(N,np.int32);distance=np.empty(N,np.float32);similarity=np.empty(N,np.float32)
 centers=model.cluster_centers_;unit=centers/np.maximum(np.linalg.norm(centers,axis=1,keepdims=True),1e-12)
 for i in range(0,N,2048):
  z=x[i:i+2048];l=model.predict(z);labels[i:i+len(z)]=l
  distance[i:i+len(z)]=np.linalg.norm(z-centers[l],axis=1)
  similarity[i:i+len(z)]=np.einsum('ij,ij->i',z,unit[l])
 save_run(run,labels,dict(algorithm='kmeans',model=m,seed=seed,parameters=model.get_params(),space='original_normalized_1024D_euclidean_MiniBatchKMeans_not_strict_spherical',wall_s=time.time()-start,inertia=float(model.inertia_),n_iter=int(model.n_iter_),n_steps=int(model.n_steps_),mean_center_cosine=float(similarity.mean())),dict(centers=centers,distances=distance,center_cosine=similarity))
def pca(m):
 from sklearn.decomposition import IncrementalPCA
 if (W/f'hdbscan/{m}_pca.json').exists():return
 guard(.8);log('pca_start',model=m);start=time.time();x=vec(m);model=IncrementalPCA(n_components=50,batch_size=4096)
 for i in range(0,N,4096):model.partial_fit(x[i:min(i+4096,N)])
 out=np.lib.format.open_memmap(W/f'hdbscan/{m}_pca50.npy',mode='w+',dtype='float32',shape=(N,50))
 for i in range(0,N,4096):out[i:i+4096]=model.transform(x[i:i+4096])
 out.flush();np.savez(W/f'hdbscan/{m}_pca_model.npz',components=model.components_,mean=model.mean_,variance=model.explained_variance_ratio_)
 dump(f'hdbscan/{m}_pca.json',dict(method='IncrementalPCA',components=50,batch_size=4096,whiten=False,retained_variance_30=float(model.explained_variance_ratio_[:30].sum()),retained_variance_50=float(model.explained_variance_ratio_.sum()),wall_s=time.time()-start))
 log('pca_complete',model=m)
def samples():
 if (W/'manifests/sample_50000.npy').exists():return
 import pandas as pd
 meta=pd.read_csv(W/'manifests/family_mapping.csv',keep_default_na=False)
 # Stratify by language, priority decade and BGE vector-space region. No semantic keywords.
 coarse=np.load(W/'kmeans/bge_k100_s42/labels.npy')
 decade=meta.priority_date.astype(str).str[:3].where(meta.priority_date.astype(str).str.len()>=4,'unknown')
 groups=collections.defaultdict(list)
 for i,key in enumerate(zip(meta.language,decade,coarse)):groups[key].append(i)
 rng=np.random.default_rng(42);order=[]
 # Shuffle within strata, then interleave proportional quantiles; preserve rare strata in first 20k.
 ranked=[];reserved=[]
 for ids in groups.values():
  ids=rng.permutation(ids);reserved.append(int(ids[0]));ranked.extend((float((j+.5)/max(1,len(ids)-1)),int(v)) for j,v in enumerate(ids[1:]))
 assert len(reserved)<20000
 ranked.sort();order=np.array(reserved+[v for _,v in ranked],dtype=np.int32)
 # Nested proportional stratified samples, not all rare strata guaranteed.
 for n in [20000,50000]:np.save(W/f'manifests/sample_{n}.npy',np.sort(order[:n]))
 dump('manifests/sample_design.json',dict(seed=42,strata=['representative_language','priority_decade','BGE_K100_region'],method='one seeded representative per observed language/decade/vector-region stratum, then proportional relative quantile; nested samples',counts={str(n):int(n) for n in [20000,50000]},note='Metadata only controls diagnostics sampling, never full-corpus clustering membership.'))
def hdb(m,n,d,mcs,ms):
 import hdbscan
 run=f'{m}_n{n}_pca{d}_c{mcs}_s{ms}'
 if (W/f'hdbscan/{run}/result.json').exists():return
 guard(.8);ids=np.arange(N,dtype=np.int32) if n==N else np.load(W/f'manifests/sample_{n}.npy')
 x=np.asarray(np.load(W/f'hdbscan/{m}_pca50.npy',mmap_mode='r')[ids,:d],dtype=np.float64,order='C')
 log('run_start',run=run);start=time.time()
 model=hdbscan.HDBSCAN(min_cluster_size=mcs,min_samples=ms,metric='euclidean',algorithm='boruvka_kdtree',core_dist_n_jobs=1,approx_min_span_tree=True,gen_min_span_tree=False,leaf_size=40)
 labels=model.fit_predict(x)
 save_run(run,labels,dict(algorithm='hdbscan',model=m,seed=None,parameters=model.get_params(),space=f'IncrementalPCA_{d}D_unwhitened_euclidean',sample_size=n,wall_s=time.time()-start,persistence=model.cluster_persistence_.tolist()),dict(row_ids=ids,probabilities=model.probabilities_.astype('float32'),outlier_scores=model.outlier_scores_.astype('float32')))
def neighbors(m):
 import faiss
 run=f'{m}_knn'
 if (W/f'leiden/{run}.json').exists():return
 guard(1.4);log('knn_start',model=m);t=time.time();faiss.omp_set_num_threads(2);x=vec(m)
 # Single thread construction for repeatability; search can parallelize.
 index=faiss.IndexHNSWFlat(1024,24,faiss.METRIC_INNER_PRODUCT);index.hnsw.efConstruction=120;index.hnsw.efSearch=160
 faiss.omp_set_num_threads(1)
 for i in range(0,N,8192):index.add(np.ascontiguousarray(x[i:i+8192]))
 faiss.omp_set_num_threads(2)
 query_ids=np.sort(np.random.default_rng(42).choice(N,128,replace=False))
 # Exact reference in bounded 128 x 8192 blocks, with stable ID tie order.
 vals=np.full((128,51),-np.inf,np.float32);ids=np.full((128,51),-1,np.int64);q=np.asarray(x[query_ids])
 for i in range(0,N,8192):
  s=q@x[i:i+8192].T
  candidate=np.broadcast_to(np.arange(i,i+s.shape[1]),s.shape)
  cv=np.concatenate([vals,s],axis=1);ci=np.concatenate([ids,candidate],axis=1)
  pick=np.argpartition(-cv,50,axis=1)[:,:51];vals=np.take_along_axis(cv,pick,axis=1);ids=np.take_along_axis(ci,pick,axis=1)
 for j in range(128):
  o=np.lexsort((ids[j],-vals[j]));ids[j]=ids[j,o];vals[j]=vals[j,o]
 approx_d,approx_i=index.search(q,51)
 recall={}
 for k in [15,30,50]:
  recall[str(k)]=float(np.mean([len(set(approx_i[j][approx_i[j]!=v][:k])&set(ids[j][ids[j]!=v][:k]))/k for j,v in enumerate(query_ids)]))
 # Increase efSearch once if 50-neighbor recall inadequate.
 if recall['50']<.9:
  index.hnsw.efSearch=320;approx_d,approx_i=index.search(q,51)
  recall={str(k):float(np.mean([len(set(approx_i[j][approx_i[j]!=v][:k])&set(ids[j][ids[j]!=v][:k]))/k for j,v in enumerate(query_ids)])) for k in [15,30,50]}
 assert recall['50']>=.85,repr(recall)
 nn=np.lib.format.open_memmap(W/f'leiden/{m}_neighbors.npy',mode='w+',dtype='int32',shape=(N,50))
 sim=np.lib.format.open_memmap(W/f'leiden/{m}_similarities.npy',mode='w+',dtype='float32',shape=(N,50))
 for i in range(0,N,1024):
  d,j=index.search(np.ascontiguousarray(x[i:i+1024]),51)
  for z in range(len(j)):
   take=j[z]!=i+z;nn[i+z]=j[z][take][:50];sim[i+z]=d[z][take][:50]
 nn.flush();sim.flush()
 dump(f'leiden/{m}_knn.json',dict(index='FAISS IndexHNSWFlat',M=24,efConstruction=120,efSearch=int(index.hnsw.efSearch),metric='inner_product_on_L2_normalized_vectors',construction_threads=1,search_threads=2,query_seed=42,query_ids=query_ids.tolist(),exact_block_size=8192,recall_at_k=recall,recall_ties_note='Exact similarity ties may lower ID-set recall.',wall_s=time.time()-t))
 log('knn_complete',model=m,recall=recall)
def graph(m,k,rule,resolutions,seeds):
 import igraph as ig,leidenalg as la
 # Deduplicate unordered edges via integer keys; mutual requires both directions.
 ids=np.load(W/f'leiden/{m}_neighbors.npy',mmap_mode='r')[:,:k]
 src=np.repeat(np.arange(N,dtype=np.int64),k);dst=ids.reshape(-1).astype('int64')
 keys=np.minimum(src,dst)*N+np.maximum(src,dst);del src,dst
 unique,counts=np.unique(keys,return_counts=True);del keys
 keep=counts==2 if rule=='mutual' else counts>=1;unique=unique[keep];del counts,keep
 # Similarity recomputed from original vectors in bounded chunks; no approximate distances.
 x=vec(m);weights=np.empty(len(unique),np.float32)
 for i in range(0,len(unique),4096):
  a=unique[i:i+4096]//N;b=unique[i:i+4096]%N
  weights[i:i+len(a)]=np.maximum(np.einsum('ij,ij->i',x[a],x[b]),0)
 mask=weights>0;unique=unique[mask];weights=weights[mask];del mask
 edge_array=np.column_stack([unique//N,unique%N]);del unique
 g=ig.Graph(n=N,edges=edge_array,directed=False);del edge_array
 g.es['weight']=weights;del weights;gc.collect()
 sizes=g.connected_components().sizes();degree=np.array(g.degree())
 graphmeta=dict(k=k,rule=rule,edges=g.ecount(),components=len(sizes),largest_component=max(sizes),isolated=int((degree==0).sum()),degree_p99=float(np.quantile(degree,.99)),degree_max=int(degree.max()),density=g.density(),weight_transform='max(original_cosine_similarity,0); zero-weight edges omitted',weight_quantiles=np.quantile(g.es['weight'],[0,.05,.5,.95,1]).tolist(),self_loops=g.is_loop().count(True),multiple_edges=g.is_multiple().count(True))
 assert graphmeta['self_loops']==graphmeta['multiple_edges']==0
 dump(f'leiden/{m}_k{k}_{rule}_graph.json',graphmeta)
 for res in resolutions:
  for seed in seeds:
   run=f'{m}_k{k}_{rule}_r{res}_s{seed}'
   if (W/f'leiden/{run}/result.json').exists():continue
   guard(.4);log('run_start',run=run);t=time.time()
   part=la.find_partition(g,la.RBConfigurationVertexPartition,weights='weight',resolution_parameter=res,n_iterations=4,seed=seed)
   labels=np.array(part.membership,np.int32)
   save_run(run,labels,dict(algorithm='leiden',model=m,seed=seed,parameters=dict(k=k,graph_rule=rule,resolution=res,n_iterations=4,objective='RBConfigurationVertexPartition'),space='original_normalized_1024D_cosine_kNN',quality=float(part.quality()),modularity=float(part.modularity),graph=graphmeta,wall_s=time.time()-t))
def pilot():
 # Small-scale all three algorithms before full experiments.
 from sklearn.cluster import MiniBatchKMeans
 import hdbscan,faiss,igraph as ig,leidenalg as la
 if (W/'evidence/pilot.json').exists():return
 guard(.7);x=np.asarray(vec('bge')[np.random.default_rng(42).choice(N,2000,replace=False)])
 km=MiniBatchKMeans(n_clusters=20,random_state=42,batch_size=256,n_init=2).fit_predict(x)
 from sklearn.decomposition import PCA
 p=PCA(n_components=30,svd_solver='randomized',random_state=42).fit_transform(x)
 h=hdbscan.HDBSCAN(min_cluster_size=10,min_samples=5,algorithm='boruvka_kdtree',core_dist_n_jobs=1).fit_predict(p)
 idx=faiss.IndexFlatIP(1024);idx.add(x);d,j=idx.search(x,16)
 edges=sorted({tuple(sorted((i,int(v)))) for i,row in enumerate(j) for v in row if i!=v})
 g=ig.Graph(n=len(x),edges=edges);part=la.find_partition(g,la.RBConfigurationVertexPartition,seed=42)
 dump('evidence/pilot.json',dict(status='PASS',sample_seed=42,n=2000,kmeans=stats(km),hdbscan=stats(h),leiden=stats(np.array(part.membership)),note='Pilot verifies execution only; no semantic selection.'))
 log('pilot_complete')
def main():
 cmd=sys.argv[1];audit()
 if cmd=='inputaudit':return
 elif cmd=='audit':pilot()
 elif cmd=='kmeans':kmeans(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]))
 elif cmd=='pca':pca(sys.argv[2])
 elif cmd=='samples':samples()
 elif cmd=='hdb':hdb(sys.argv[2],*map(int,sys.argv[3:]))
 elif cmd=='neighbors':neighbors(sys.argv[2])
 elif cmd=='graph':graph(sys.argv[2],int(sys.argv[3]),sys.argv[4],list(map(float,sys.argv[5].split(','))),list(map(int,sys.argv[6].split(','))))
if __name__=='__main__':
 import fcntl
 lockdir=W/'evidence/run_locks';lockdir.mkdir(exist_ok=True)
 name=hashlib.sha256(' '.join(sys.argv[1:]).encode()).hexdigest()[:20]
 with (lockdir/(name+'.lock')).open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);main()
