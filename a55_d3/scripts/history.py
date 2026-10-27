from common import *
from client import call
from design import obj,arr,enum,S,N,ATOM,LABELS
from pipeline import source_input,full
from experiments import active_main
import collections,concurrent.futures,argparse
HIST=obj(family_id=S,object_judgment=enum(*LABELS),problem_judgment=enum(*LABELS),means_judgment=enum(*LABELS),material_parameter_judgment=enum(*LABELS),source_adequacy=enum('sufficient','partially_sufficient','insufficient','uncertain'),historical_recovery=enum('Recovered','Broad Topic Only','Insufficient Source Evidence','Missing Despite Available Evidence','Uncertain'),source_available_means=arr(ATOM,20),historical_details_absent=arr(S,20),extraction_omissions=arr(ATOM,20),needs_full_text=dict(type='boolean'),false_unrelated=enum('yes','no','uncertain','not_applicable'),d2_to_d3_change=S,reason=S)
PROMPT='''你是历史专项回归审核员。主Query-Free版本已冻结。本次历史预期只用于事后评估，不能视为来源事实，不能用它补写摘要缺失内容或改主抽取。重新阅读原始Title/Abstract，核对D2归档和D3抽取/双轴相关性，分别审核对象/问题/办法/材料参数。逐项区分摘要有但抽取漏掉与摘要未提供；历史机制若只有组成而要求制造窗口/设备控制，不可因材料名称吻合算Recovered。若只宽主题匹配用Broad Topic Only；摘要无足够细节用Insufficient Source Evidence；有足够细节但漏抽用Missing Despite Available Evidence。解释变化，不把模型自评叫Gold。引文Sxxx必须原文支持，中文简明，输出JSON。历史细节无法证明写historical_details_absent及全文队列，不发明。false_unrelated只评实际D2标签是否违背原文/明确工程机制，无法判断用uncertain。'''

def prepare_schema():
 guard();save('schemas/HISTORY.json',HIST);(W/'prompts/history_v1.txt').write_text(PROMPT+'\n')

def run(workers=10):
 guard();assert (W/'evidence/MODEL_FREEZE.json').exists()
 # Historical targets only opened after every main family has terminal processing status.
 docs=load('inputs/ALL_DOCUMENTS.json');dm={d['family_id']:d for d in docs}
 assert all((W/'working/status'/('full_'+f.replace(':','_')+'.json')).exists() for f in dm),'Finish main attempts before historical audit'
 cases=json.loads((D2/'working/HISTORY_CASES.json').read_text())['cases'];assert len(cases)==45
 supplement=json.loads((D2/'inputs/HISTORY_SUPPLEMENT_TEXTS.json').read_text())
 if isinstance(supplement,dict):
  if 'documents' in supplement:supplement=supplement['documents']
  elif 'texts' in supplement:supplement=supplement['texts']
  else:supplement=list(supplement.values())
 for d in supplement:
  if isinstance(d,dict) and d.get('family_id'):dm[d['family_id']]=d
 old=json.loads((D2/'working/all_selected/contributions.json').read_text());old+=json.loads((D2/'working/HISTORY_SUPPLEMENT_CONTRIBUTIONS.json').read_text())
 oc=collections.defaultdict(list)
 for c in old:oc[c['family_id']].append({k:c.get(k) for k in ['technical_object','technical_problem','technical_mechanism','implementation','materials','parameters','evidence_spans']})
 oldhist=json.loads((D2/'outputs/HISTORICAL_VALIDATION.json').read_text())
 # Original historical classifications retained separately in manifest, not extraction inputs.
 save('inputs/HISTORICAL_SOURCE_LOCK.json',dict(at=now(),files={str(p.relative_to(D2)):sha(p) for p in [D2/'working/HISTORY_CASES.json',D2/'inputs/HISTORY_SUPPLEMENT_TEXTS.json',D2/'working/HISTORY_SUPPLEMENT_CONTRIBUTIONS.json',D2/'outputs/HISTORICAL_VALIDATION.json']}))
 results=[]
 def task(c):
  fid=c['family_id']
  try:
   d=dm[fid];r=active_main(fid)
   if r is None:
    assert fid not in {x['family_id'] for x in docs},'Main failure is not a new successful historical probe'
    # The 6 outside probes are source-only, using identical frozen prompts.
    d=dict(d);d.setdefault('text_hash',oh([d.get('title'),d.get('abstract')]))
    r=full(d)
   ids={s['id'] for s in source_input(d)['source_spans']}
   def check(v):
    assert v['family_id']==fid
    for a in v['source_available_means']+v['extraction_omissions']:assert a['evidence_ids'] and set(a['evidence_ids'])<=ids
   out=call('historical_regression',fid,(W/'prompts/history_v1.txt').read_text(),dict(source=source_input(d),historical_expectations=c.get('history_reference',[]),d2_extraction=oc[fid],d3_extraction=r['final'],d3_relevance=r['relevance']),HIST,check,max_tokens=5500)
   rec=dict(case=c,scope='main_discovery39' if fid in {x['family_id'] for x in docs} else 'postfreeze_probe6',request_id=out['request_id'],result=out['result'],d3_status=r['status'],label_tier='Silver',human_confirmed=False);save('working/history/'+fid.replace(':','_')+'.json',rec);return dict(family_id=fid,status='VALID',scope=rec['scope'])
  except Exception as e:return dict(family_id=fid,status='FAILED',error=type(e).__name__+': '+str(e)[:800])
 event('history_start',required=45)
 with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
  for i,r in enumerate(pool.map(task,cases),1):
   results.append(r)
   if i%10==0 or r['status']=='FAILED':event('history_progress',finished=i,counts=dict(collections.Counter(r['status'] for r in results)),error=r.get('error'))
 save('evidence/HISTORY_BATCH.json',dict(at=now(),results=results,counts=dict(collections.Counter(r['status'] for r in results))))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--workers',type=int,default=10);a=p.parse_args()
 if a.prepare:prepare_schema()
 if a.run:run(a.workers)
