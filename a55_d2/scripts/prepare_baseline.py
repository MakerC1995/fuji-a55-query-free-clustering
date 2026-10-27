"""Post-freeze replication inputs for the actual D1 panel method."""
from common import *
from posthoc_relevance import verify_freeze
import ast,numpy as np,pandas as pd
def main():
 guard();freeze=verify_freeze();tree=ast.parse((D1/'scripts/name_topics.py').read_text());system=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SYSTEM' for t in n.targets))
 (W/'prompts/d1_baseline.txt').write_text(system+'\n')
 docs={d['family_id']:d for d in pd.read_parquet(W/'inputs/PATENT_TEXTS.parquet').to_dict('records')};members=pd.read_parquet(W/'inputs/CLUSTER_MEMBERS.parquet');cohorts=pd.read_csv(W/'inputs/COHORTS.csv');panels=[];vectors={}
 for co in cohorts.to_dict('records'):
  ms=members[members.selection_id==co['selection_id']].sort_values('row_idx');ids=ms.row_idx.to_numpy(dtype=int);fids=list(ms.family_id);n=len(ids);rng=np.random.default_rng(42+int(co['cluster_id']));chosen=[];roles=[]
  def add(i,role):
   i=int(i)
   if i not in chosen:chosen.append(i);roles.append(role)
  model='qwen' if co['run_id'].startswith('qwen') else 'bge'
  if model not in vectors:vectors[model]=np.load(BASE/(model+'_index.f32.npy'),mmap_mode='r')
  x=vectors[model]
  if co['role']=='noise':
   for i in rng.choice(n,min(8,n),replace=False):add(i,'uniform_noise_sample')
   sim=None;center_scope='No centroid for Noise; uniform sample from the frozen60'
  else:
   algorithm='leiden' if '_mutual_' in co['run_id'] else 'kmeans';p=D1/algorithm/co['run_id']/'semantic_center_cosine.npy'
   if p.exists():sim=np.asarray(np.load(p,mmap_mode='r')[ids]);center_scope='Frozen D1 semantic-center cosine, restricted to selected D2 pool'
   else:
    z=x[ids];center=z.mean(0);center/=np.linalg.norm(center);sim=z@center;center_scope='Selected-pool arithmetic-mean center; frozen scores absent'
   order=np.argsort(-sim,kind='stable')
   for i in order[:2]:add(i,'near_center')
   for i in order[-2:]:add(i,'edge')
   for i in rng.permutation(n)[:3]:add(i,'random')
   pool=rng.choice(n,min(256,n),replace=False)
   while len(chosen)<min(8,n):
    scores=x[ids[pool]]@x[ids[chosen]].T;best=int(pool[np.argmin(scores.max(axis=1))]);before=len(chosen);add(best,'diverse')
    if len(chosen)==before:break
  paneldocs=[dict(family_id=fids[i],title=docs[fids[i]]['title'],abstract=(docs[fids[i]]['abstract'] or '')[:1200],abstract_truncated=len(docs[fids[i]]['abstract'] or '')>1200,selection_role=role) for i,role in zip(chosen[:8],roles[:8])]
  panels.append(dict(selection_id=co['selection_id'],run_id=co['run_id'],cluster_id=int(co['cluster_id']),cluster_population=int(co['population_size']),selected_pool=n,docs=paneldocs,centroid_scope=center_scope,coverage='FULL_CLUSTER' if co['complete_cluster'] else 'SAMPLED_MEMBERS_ONLY',phase='POST_FREEZE_D1_STYLE_REPLICATION'))
 save('working/D1_BASELINE_PANELS.json',dict(at=now(),panels=panels,system_prompt_sha256=digest_bytes(system.encode()),source_method_sha256={str(p.relative_to(D1)):sha(p) for p in [D1/'scripts/name_topics.py',D1/'scripts/analyze.py',D1/'scripts/assemble.py']},core_freeze_sha256=object_hash(freeze),differences='Same D1 system prompt, up to8 center/edge/random/diverse documents and1200-character abstract cap. Selected D2 pools used for partial controls; Noise uses uniform8. New post-freeze calls, not original D1 results. Original D1 already supported1–3 themes, literal evidence, independent technology hashes and M:N tables.'))
 verify_freeze();print(stable(dict(panels=len(panels),docs=sum(len(p['docs']) for p in panels))))
if __name__=='__main__':main()
