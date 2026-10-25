from experiment import *
import pandas as pd
m=pd.read_csv(W/'manifests/family_mapping.csv',keep_default_na=False)
s20=np.load(W/'manifests/sample_20000.npy');s50=np.load(W/'manifests/sample_50000.npy')
assert set(s20)<=set(s50)
out={}
for n,ids in [(20000,s20),(50000,s50)]:
 md=m.iloc[ids]
 out[str(n)]=dict(n=len(ids),unique=len(set(ids)),languages=md.language.value_counts().to_dict(),text_quality=md.text_quality.value_counts().to_dict(),priority_decades=md.priority_date.astype(str).str[:3].value_counts().to_dict(),bge_k100_regions=len(set(np.load(W/'kmeans/bge_k100_s42/labels.npy')[ids])))
 assert set(md.language)==set(m.language)
dump('evidence/sample_coverage.json',dict(nested=True,all_observed_languages_covered=True,samples=out))
# Verify replay resumes without modifying a completed assignment.
p=W/'kmeans/bge_k100_s42/labels.npy';before=(p.stat().st_mtime_ns,sha(p))
kmeans('bge',100,42)
after=(p.stat().st_mtime_ns,sha(p));assert before==after
dump('evidence/checkpoint_replay.json',dict(status='PASS',run='bge_k100_s42',labels_hash=before[1],mtime_unchanged=True,recomputed=False))
print('Sample coverage and checkpoint replay PASS')
