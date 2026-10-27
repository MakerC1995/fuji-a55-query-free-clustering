from common import *
import random,re,collections,shutil
import pyarrow as pa,pyarrow.parquet as pq
SEED=20261027
KNOWN='61300486 41346026 41681057 41736165 39794835 40130510 40587181 40581936 97217328 97218156 92590282 51658295 39704160 42705590 41141126 41061590 38149581 19085123 49387621 44719320 14080699 45351863 43903909 34468469 49512008 58557302 41541242 16586379 39008916 40653572 38922757 40507396 38455368 36911941 42737164 34206471 40130930 17829349 35322406 15343657 42239224 36985093 16847035 51840117 47995898'.split()
PIN=['61300486','41346026','41681057','41736165','39794835','40581936','45351863','43903909','34468469','49512008','39008916','40653572','38922757','40507396','39704160']
def main():
 guard();assert not (W/'inputs/SPLIT_LOCK.json').exists(),'Sampling already frozen'
 paths=['inputs/PATENT_TEXTS.parquet','inputs/CLUSTER_MEMBERS.parquet','outputs/PATENT_CONTRIBUTIONS.parquet','outputs/TECHNOLOGY_CONCEPTS.parquet','outputs/PATENT_TECHNOLOGY_RELATIONS.parquet','outputs/TECHNOLOGY_RELATIONS.parquet','outputs/MERGE_AUDIT.parquet','outputs/PRINTHEAD_RELEVANCE.json','working/all_selected/contributions.json','evidence/CORE_FREEZE.json','prompts/extraction_v2.txt','configs/EXTRACTION_WIRE_SCHEMA.json','scripts/extract.py','scripts/schema.py','scripts/consolidate.py']
 hashes={x:sha(D2/x) for x in paths};save('inputs/D2_LOCK.json',dict(at=now(),root=str(D2),files=hashes))
 docs=pq.read_table(D2/paths[0]).to_pylist();members=pq.read_table(D2/paths[1]).to_pylist();dmap={d['family_id']:d for d in docs}
 mm=collections.defaultdict(list)
 for m in members:mm[m['family_id']].append(m)
 old=json.loads((D2/'working/all_selected/contributions.json').read_text());oc=collections.defaultdict(list)
 for c in old:oc[c['family_id']].append(c)
 hist=json.loads((D2/'working/HISTORY_CASES.json').read_text())['cases'];hids={c['family_id'] for c in hist}
 # Only historical IDs accessed here to prevent overlap. Historical names/details are not extraction input.
 excluded={'google:'+x for x in KNOWN}|hids
 rng=random.Random(SEED)
 strata=collections.defaultdict(list)
 for d in docs:
  fid=d['family_id'];ms=mm[fid];cohort=sorted(ms,key=lambda x:('primary' not in x['role'],x['selection_id']))[0]['selection_id']
  d['sampling_cohort']=cohort;d['memberships']=ms
  if fid not in excluded:strata[(cohort,bool(d.get('abstract')))].append(fid)
 for v in strata.values():rng.shuffle(v)
 # Random, proportional-to-square-root strata quotas, with title-only floor and coverage of every cohort.
 hold=[];keys=sorted(strata)
 for k in keys:
  if strata[k]:hold.append(strata[k].pop())
 while len(hold)<42:
  available=[k for k in keys if strata[k]]
  k=rng.choices(available,weights=[len(strata[k])**.5 for k in available])[0];hold.append(strata[k].pop())
 selected=['google:'+x for x in PIN if 'google:'+x in dmap];dev=list(dict.fromkeys(selected))
 def tags(d):
  text=(d.get('title') or '')+' '+(d.get('abstract') or '');t=text.lower();cs=oc[d['family_id']]
  out=[]
  # These are sampling proxies only; semantic category is left to Silver/human review.
  if len(cs)==1 and len(d.get('abstract') or '')>250:out.append('single_proxy')
  if len(d.get('abstract') or '')>900 or len(cs)>1 or re.search(r'first.+second|furthermore|moreover|independently|independent|それぞれ',t):out.append('multi_proxy')
  if re.search(r'composition|dop|perovskite|phase|alloy|配合|掺|組成|結晶|材料',t):out.append('material_proxy')
  if re.search(r'sputter|deposit|temperature|pressure|forming|formed|溅射|成膜|形成|工序',t):out.append('process_proxy')
  if re.search(r'control|apparatus|electrode|circuit|voltage|anode|device|装置|制御|電極',t):out.append('equipment_proxy')
  if not d.get('abstract') or len(d.get('abstract') or '')<300:out.append('insufficient_proxy')
  if 'random' in d['sampling_cohort'] or 'mixed' in d['sampling_cohort'] or re.search(r'head|ink.?jet|液滴|吐出|噴|喷',t):out.append('boundary_proxy')
  return out
 for d in docs:d['sampling_tags']=tags(d)
 quotas={'single_proxy':24,'multi_proxy':24,'material_proxy':20,'process_proxy':20,'equipment_proxy':20,'insufficient_proxy':20,'boundary_proxy':28}
 for tag,n in quotas.items():
  have=sum(tag in dmap[f]['sampling_tags'] for f in dev+hold)
  pool=[d['family_id'] for d in docs if tag in d['sampling_tags'] and d['family_id'] not in set(dev+hold) and d['family_id'] not in hids];rng.shuffle(pool)
  dev+=pool[:max(0,n-have)]
 assert len(dev)<=98,(len(dev),'quota overflow')
 # Complete cohort coverage and balanced remaining development set.
 for k in keys:
  if not any(dmap[f]['sampling_cohort']==k[0] for f in dev):
   pool=[f for f in strata[k] if f not in dev and f not in hids]
   if pool:dev.append(pool[0])
 pool=[d['family_id'] for d in docs if d['family_id'] not in set(dev+hold) and d['family_id'] not in hids];rng.shuffle(pool)
 dev+=pool[:98-len(dev)];assert len(dev)==98 and len(hold)==42
 evalrows=[]
 for split,ids in [('development',dev),('holdout',hold)]:
  for i,f in enumerate(ids):
   d=dmap[f];evalrows.append(dict(family_id=f,split=split,pilot30=split=='development' and i<30,source_text_hash=d['text_hash'],sampling_cohort=d['sampling_cohort'],sampling_tags=d['sampling_tags'],known_issue=f in excluded,language=d.get('language'),abstract_chars=len(d.get('abstract') or ''),selection_reason='priority_known_issue' if f in selected else 'seeded_stratified_proxy_sampling',human_gold=None))
 assert not set(dev)&set(hold);assert not set(hold)&excluded;assert len({r['family_id'] for r in evalrows})==140
 save('inputs/ALL_DOCUMENTS.json',docs);save('inputs/EVALUATION_SELECTION.json',evalrows)
 pq.write_table(pa.Table.from_pylist(evalrows),W/'inputs/EVALUATION_SELECTION.parquet',compression='zstd')
 counts={tag:sum(tag in dmap[f]['sampling_tags'] for f in dev+hold) for tag in quotas}
 lock=dict(at=now(),seed=SEED,development=dev,holdout=hold,pilot30=dev[:30],historical_ids_excluded_from_independent_eval=sorted(hids),known_issues_excluded_from_holdout=sorted(excluded),sampling_proxy_counts=counts,cohort_counts=dict(collections.Counter(dmap[f]['sampling_cohort'] for f in dev+hold)),selection_sha256=sha(W/'inputs/EVALUATION_SELECTION.json'),d2_input_lock_sha256=sha(W/'inputs/D2_LOCK.json'),holdout_policy='Do not read content or run until MODEL_FREEZE.json; IDs and sampling metadata only during development; single frozen experiment pass. Technical repairs cannot use holdout for prompt tuning.')
 save('inputs/SPLIT_LOCK.json',lock)
 for name in ['prompts/extraction_v2.txt','configs/EXTRACTION_WIRE_SCHEMA.json','scripts/schema.py','scripts/extract.py','scripts/consolidate.py']:
  dest=W/'inputs/d2_code'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(D2/name,dest)
 event('split_frozen',development=98,holdout=42,pilot=30,proxy_counts=counts,cohort_counts=lock['cohort_counts'])
if __name__=='__main__':main()
