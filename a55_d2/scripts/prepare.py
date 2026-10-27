"""Freeze cohort without reading history, D1 names, queries or classifications."""
from common import *
import numpy as np,pandas as pd,pyarrow as pa,pyarrow.parquet as pq,collections
SEED=20261026
TARGET=[('qwen',300,139,384),('qwen',800,286,258),('qwen',800,168,153),('bge',800,223,190),('bge',800,475,57),('qwen',800,404,272)]
def main():
 guard()
 if (W/'inputs/DATASET_FROZEN.json').exists():
  frozen=load('inputs/DATASET_FROZEN.json')
  for name,h in frozen['sha256'].items():assert sha(W/name)==h,name
  event('dataset_reused',families=frozen['unique_families']);return
 rng=np.random.default_rng(SEED);cache={};selections=[];members=[]
 def get(run):
  if run not in cache:
   p=D1/('kmeans' if '_k800_' in run or '_k300_' in run else 'leiden')/run/'labels.npy'
   cache[run]=np.load(p,mmap_mode='r');assert cache[run].shape==(238541,)
  return cache[run]
 def add(run,cl,role,expected=None,sample=None):
  labels=get(run);ids=np.flatnonzero(labels==cl)
  if expected is not None:assert len(ids)==expected,(run,cl,len(ids),expected)
  chosen=np.sort(rng.choice(ids,size=min(sample,len(ids)),replace=False)) if sample else ids
  sid=role+'__'+run+'__c'+str(cl)
  selections.append(dict(selection_id=sid,role=role,run_id=run,cluster_id=int(cl),population_size=len(ids),selected_size=len(chosen),complete_cluster=len(chosen)==len(ids)))
  members.extend(dict(selection_id=sid,run_id=run,cluster_id=int(cl),row_idx=int(idx),role=role) for idx in chosen)
 for j,(model,k,cl,n) in enumerate(TARGET):add(f'{model}_k{k}_s42',cl,'primary' if j==0 else 'specified_control',n)
 cols=['run_id','algorithm','model','cluster_id','cluster_size','mean_center_cosine']
 stats=pd.read_csv(D1/'comparison/cluster_catalog.csv',usecols=cols)
 excluded={(s['run_id'],s['cluster_id']) for s in selections}
 for run in ['qwen_k800_s42','bge_k800_s42']:
  cluster_ids,cluster_counts=np.unique(get(run),return_counts=True)
  choices=[int(cl) for cl,n in zip(cluster_ids,cluster_counts) if 100<=n<=220 and (run,int(cl)) not in excluded]
  cl=int(rng.choice(choices));add(run,cl,'random_medium')
  excluded.add((run,cl))
 mixed=stats[(stats.run_id=='qwen_k300_s42')&stats.cluster_size.between(800,3000)].sort_values(['mean_center_cosine','cluster_id']).iloc[0]
 add(str(mixed.run_id),int(mixed.cluster_id),'mixed_proxy',sample=80)
 tight=stats[(stats.run_id=='qwen_k30_mutual_r1.0_s42')&stats.cluster_size.between(8,30)&stats.mean_center_cosine.notna()].sort_values(['mean_center_cosine','cluster_id'],ascending=[False,True])
 top=tight.head(max(1,len(tight)//10));tiny=top.iloc[int(rng.integers(len(top)))];add(str(tiny.run_id),int(tiny.cluster_id),'small_tight')
 hrun='bge_n238541_pca30_c30_s15';hp=D1/'hdbscan'/hrun/'labels.npy';a=np.load(hp,mmap_mode='r')
 assert a.shape==(238541,);noise=np.flatnonzero(a==-1);ids=np.sort(rng.choice(noise,60,replace=False));sid='noise__'+hrun
 selections.append(dict(selection_id=sid,role='noise',run_id=hrun,cluster_id=-1,population_size=len(noise),selected_size=60,complete_cluster=False))
 members.extend(dict(selection_id=sid,run_id=hrun,cluster_id=-1,row_idx=int(idx),role='noise') for idx in ids)
 wanted=sorted({r['row_idx'] for r in members});c=source_db();docs=[]
 cols='row_idx,family_id,pub_id,publication_id,title,abstract,language,title_language,raw_text,text_hash,text_quality,source,bge_input_hash,qwen_input_hash'
 for start in range(0,len(wanted),300):
  ids=wanted[start:start+300]
  docs.extend(dict(row) for row in c.execute('select '+cols+' from docs where row_idx in ('+','.join('?' for _ in ids)+')',ids))
 c.close();docs.sort(key=lambda d:d['row_idx']);byrow={r['row_idx']:r for r in docs};assert len(docs)==len(wanted)
 for d in docs:
  assert digest_bytes(d['raw_text'].encode())==d['text_hash'],d['family_id']
  assert d['title'] or d['abstract']
 for r in members:r['family_id']=byrow[r['row_idx']]['family_id']
 # Independent readback from the actual delivered Parquet for all selected source rows.
 clauses=[('run_id','in',sorted({r['run_id'] for r in selections})),('row_idx','in',wanted)]
 tab=pq.read_table(D1/'CLUSTER_ASSIGNMENTS.parquet',columns=['run_id','row_idx','family_id','cluster_id'],filters=clauses).to_pydict()
 lookup={(rid,int(idx)):(fid,int(cl)) for rid,idx,fid,cl in zip(tab['run_id'],tab['row_idx'],tab['family_id'],tab['cluster_id'])}
 for r in members:assert lookup[(r['run_id'],r['row_idx'])]==(r['family_id'],r['cluster_id'])
 # Nested 30/100/384 stages cover source language and abstract-length strata, not centroid proximity.
 primary=[d for d in docs if any(r['row_idx']==d['row_idx'] and r['role']=='primary' for r in members)]
 strata=collections.defaultdict(list)
 for d in primary:strata[(d['language'],d['text_quality'],min(3,len(d['abstract'] or '')//500))].append(d['family_id'])
 for group in strata.values():rng.shuffle(group)
 order=[]
 while any(strata.values()):
  for key in sorted(strata):
   if strata[key]:order.append(strata[key].pop())
 assert len(order)==384 and len(set(order))==384
 other=[d['family_id'] for d in docs if d['family_id'] not in set(order)]
 all_order=order+other
 pd.DataFrame(members).to_parquet(W/'inputs/CLUSTER_MEMBERS.parquet',index=False)
 pd.DataFrame(docs).to_parquet(W/'inputs/PATENT_TEXTS.parquet',index=False)
 pd.DataFrame(selections).to_csv(W/'inputs/COHORTS.csv',index=False)
 save('inputs/STAGES.json',dict(pilot30=order[:30],trial100=order[:100],primary384=order,all_selected=all_order))
 save('inputs/SELECTION_RULES.json',dict(seed=SEED,target_clusters=TARGET,random_medium='Uniform cluster ID draw among non-target K800 clusters of 100..220 families; complete membership',mixed='Lowest original centroid cosine among Qwen K300 clusters of size 800..3000, 80 uniform members. Proxy for heterogeneity, not semantic ground truth.',small='Uniform seeded draw from top cohesion decile of Qwen mutual-Leiden communities of size 8..30; complete membership',noise='60 uniform BGE full-scope HDBSCAN Noise rows',allowed_features=['frozen labels','cluster size','original centroid cosine','source language','text length','source quality'],forbidden_inputs=['historical tree','D1 LLM candidate names','query banks','IPC/CPC','printhead labels','keyword route filtering'],partial_control_coverage_explicit=True))
 # Lock only existing immutable inputs used. Never hash or modify old databases as a migration exercise.
 paths=[BASE/'corpus.sqlite',BASE/'bge_index.f32.npy',BASE/'qwen_index.f32.npy',BASE/'baseline.json',D1/'CLUSTER_ASSIGNMENTS.parquet',D1/'EXPERIMENT_MANIFEST.json',hp]
 paths+=list({D1/('leiden' if '_mutual_' in r else 'kmeans')/r/'labels.npy' for r in cache})
 source_locks={str(p):dict(bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,sha256=sha(p) if p.stat().st_size<150*2**20 else None) for p in paths}
 save('inputs/SOURCE_LOCKS.json',source_locks)
 names=['CLUSTER_MEMBERS.parquet','PATENT_TEXTS.parquet','COHORTS.csv','STAGES.json','SELECTION_RULES.json','SOURCE_LOCKS.json']
 frozen=dict(created_at=now(),unique_families=len(docs),membership_rows=len(members),primary_families=384,sha256={'inputs/'+n:sha(W/'inputs'/n) for n in names},query_free_selection=True,historical_inputs_opened=False,all_memberships_read_back_from_d1_parquet=True)
 save('inputs/DATASET_FROZEN.json',frozen)
 event('dataset_frozen',families=len(docs),memberships=len(members),selections=selections)
if __name__=='__main__':main()
