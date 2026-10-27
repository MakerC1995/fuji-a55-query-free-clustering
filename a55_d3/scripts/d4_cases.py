from common import *
from client import call
from design import obj,arr,enum,S,N
from pipeline import source_input
from experiments import active_main
import collections,itertools,heapq,re,concurrent.futures,argparse
import pyarrow.parquet as pq,pyarrow as pa
SCHEMA=obj(pair_id=S,recommended_relation=enum('Same Mechanism','Parent-Child','Variant','Related','Complementary','Distinct','Uncertain'),parent_side=enum('A','B','neither','uncertain'),rationale=S,distinguishing_elements=arr(S,20),evidence_a=arr(S,30),evidence_b=arr(S,30),ambiguity=arr(S,15),needs_full_text=dict(type='boolean'))
PROMPT='''你是D4接口困难样本审核员，本次只提出测试案例关系，不执行归并或改D2概念ID。原始Title/Abstract是真实唯一事实来源，D2和D3都是待审候选，不得凭相似词判同一机制。比较具体实体—关系—对象、材料限定、参数相反条件、结构/工序差异和来源充分性，推荐Same Mechanism / Parent-Child / Variant / Related / Complementary / Distinct / Uncertain。若Parent-Child注明parent_side；同材料不同办法不是Same，一般设备和具体方案可能层级或Related而非同一，来源不足不强判。Sxxx分别对应A/B各自原文，不引用候选编号充原文。原D2是否同ID不决定你的判断。仅Silver，人工未确认，中文简明，JSON。'''
def prepare_schema():
 guard();save('schemas/D4_PAIRS.json',SCHEMA);(W/'prompts/d4_pairs_v1.txt').write_text(PROMPT+'\n')
def tokens(s):
 s=re.sub(r'\s+','',s.lower());return {s[i:i+2] for i in range(len(s)-1)}
def select():
 nodes=[n for n in pq.read_table(D2/'outputs/TECHNOLOGY_CONCEPTS.parquet').to_pylist() if n['level']=='B'];old=json.loads((D2/'working/all_selected/contributions.json').read_text());cm={c['contribution_id']:c for c in old}
 for n in nodes:n['cids']=json.loads(n['support_contribution_ids_json'])
 pairs=[];seen=set()
 def add(a,b,ta,tb,reason,score=None):
  key=tuple(sorted([a,b]))
  if a==b or key in seen or cm[a]['family_id']==cm[b]['family_id']:return
  seen.add(key);pairs.append(dict(pair_id='P_'+oh(key)[:18],cid_a=a,cid_b=b,technology_id_a=ta,technology_id_b=tb,selection_reason=reason,lexical_triage_score=score))
 # Real same-ID multi-family groups, including known over-merges, not fabricated positives.
 for n in nodes:
  if len(n['cids'])>1:
   for a,b in list(itertools.combinations(n['cids'],2))[:2]:add(a,b,n['technology_id'],n['technology_id'],'same_D2_concept_diagnostic')
 # At most32 same-ID cases, prioritizing the two explicitly named task boundaries.
 priority=[{'google:41681057','google:41736165'},{'google:41346026','google:61300486'}]
 pairs.sort(key=lambda p:(not any({cm[p['cid_a']]['family_id'],cm[p['cid_b']]['family_id']}==x for x in priority),p['pair_id']))
 pairs=pairs[:24];seen={tuple(sorted([p['cid_a'],p['cid_b']])) for p in pairs}
 ts=[tokens(n['core_mechanism'] or '') for n in nodes]
 heap=[]
 for i,a in enumerate(nodes):
  for j in range(i+1,len(nodes)):
   b=nodes[j];u=ts[i]|ts[j]
   if not u:continue
   score=len(ts[i]&ts[j])/len(u)
   if score>=.18:heap.append((score,i,j))
 for score,i,j in heapq.nlargest(160,heap):
  a,b=nodes[i],nodes[j];add(a['cids'][0],b['cids'][0],a['technology_id'],b['technology_id'],'different_D2_concepts_high_lexical_similarity',round(score,5))
  if len(pairs)>=48:break
 assert len(pairs)>=30,'Not enough evidence-bearing candidates; do not invent'
 save('inputs/D4_PAIR_SELECTION.json',dict(at=now(),pairs=pairs,method='Real shared D2 IDs plus high lexical similarity cross-ID triage; similarity does not determine relation',not_gold=True));return pairs

def run(workers=10):
 guard();assert (W/'evidence/MODEL_FREEZE.json').exists();pairs=load('inputs/D4_PAIR_SELECTION.json')['pairs'] if (W/'inputs/D4_PAIR_SELECTION.json').exists() else select()
 docs={d['family_id']:d for d in load('inputs/ALL_DOCUMENTS.json')};old={c['contribution_id']:c for c in json.loads((D2/'working/all_selected/contributions.json').read_text())};results=[]
 def task(p):
  try:
   a,b=old[p['cid_a']],old[p['cid_b']];da,db=docs[a['family_id']],docs[b['family_id']];ma,mb=active_main(a['family_id']),active_main(b['family_id'])
   assert ma and mb,'Main D3 record unavailable'
   sa,sb=source_input(da),source_input(db)
   def check(v):
    assert v['pair_id']==p['pair_id'];assert set(v['evidence_a'])<={s['id'] for s in sa['source_spans']};assert set(v['evidence_b'])<={s['id'] for s in sb['source_spans']}
   payload=dict(pair_id=p['pair_id'],a=dict(source=sa,d2_candidate=a['technical_mechanism'],d3_contributions=ma['final']['contributions']),b=dict(source=sb,d2_candidate=b['technical_mechanism'],d3_contributions=mb['final']['contributions']))
   r=call('d4_merge_test',p['pair_id'],(W/'prompts/d4_pairs_v1.txt').read_text(),payload,SCHEMA,check,max_tokens=4500)
   rec=dict(selection=p,family_a=a['family_id'],family_b=b['family_id'],request_id=r['request_id'],result=r['result'],source_a=sa,source_b=sb,d2_contribution_a=a,d2_contribution_b=b,d3_contributions_a=ma['final']['contributions'],d3_contributions_b=mb['final']['contributions'],human_confirmed=False,label_tier='Silver');save('working/d4/'+p['pair_id']+'.json',rec);return dict(pair_id=p['pair_id'],status='VALID')
  except Exception as e:return dict(pair_id=p['pair_id'],status='FAILED',error=str(e)[:800])
 with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
  for r in pool.map(task,pairs):results.append(r)
 save('evidence/D4_PAIR_BATCH.json',dict(at=now(),results=results,counts=dict(collections.Counter(r['status'] for r in results))))
 event('d4_pairs_done',counts=dict(collections.Counter(r['status'] for r in results)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--workers',type=int,default=10);a=p.parse_args()
 if a.prepare:prepare_schema()
 if a.run:run(a.workers)
