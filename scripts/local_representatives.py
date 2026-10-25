from experiment import *
import pandas as pd
records=[]
x=vec('bge');con=db();con.row_factory=sqlite3.Row
rng=np.random.default_rng(42)
for folder in sorted((W/'leiden').glob('local_*')):
 labels=np.load(folder/'labels.npy');ids=np.load(folder/'row_ids.npy')
 for c in np.unique(labels):
  positions=np.flatnonzero(labels==c);ri=ids[positions];z=x[ri];center=z.mean(0);center/=np.linalg.norm(center);sim=z@center
  order=np.argsort(-sim,kind='stable');choices=[]
  for j,role in [(int(order[0]),'near_center'),(int(order[1]),'near_center'),(int(order[-1]),'edge')]+[(int(j),'random') for j in rng.choice(len(ri),min(3,len(ri)),replace=False)]:
   if j not in [p for p,_ in choices]:choices.append((j,role))
  for j,role in choices[:5]:
   d=dict(con.execute('select family_id,pub_id,title,abstract,language,text_quality from docs where row_idx=?',(int(ri[j]),)).fetchone())
   records.append(dict(parent_run=folder.name,local_cluster=int(c),cluster_size=len(ri),selection_role=role,**d,abstract_excerpt=d['abstract'][:400],center_cosine=float(sim[j]),llm_name_status='not separately named; raw evidence for local subdivision'))
pd.DataFrame(records).to_csv(W/'comparison/local_cluster_representatives.csv',index=False)
dump('evidence/local_representative_readout.json',dict(rows=len(records),child_clusters=len({(r['parent_run'],r['local_cluster']) for r in records}),labels_unchanged=True,method='2 centroid representatives, 1 edge and seeded random representatives'))
print('Local raw-evidence readout',len(records),'records')
