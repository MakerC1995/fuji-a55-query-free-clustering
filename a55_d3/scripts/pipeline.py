from common import *
from client import call,validate
from design import EXTRACTION,FACTS,AUDIT,RELEVANCE,COMPARE,GRADES
import concurrent.futures,collections,argparse,random,copy,importlib.util,ast

def prompt(name):return (W/'prompts'/f'{name}_v1.txt').read_text()
def claims(extraction):
 out=[]
 for i,c in enumerate(extraction.get('contributions',[])):
  prefix=f'contributions[{i}]'
  for k in ['technical_object','technical_problem','core_mechanism','implementation','split_reason']:
   a=c[k]
   if a.get('text'):out.append(dict(path=prefix+'.'+k,text=a['text'],evidence_ids=a['evidence_ids']))
  for k in ['materials','composition','process_steps','process_conditions','equipment_components','control_variables','technical_effects']:
   for j,a in enumerate(c[k]):
    value={x:v for x,v in a.items() if x!='evidence_ids'}
    if value.get('text') is None and set(value)=={'text'}:continue
    out.append(dict(path=f'{prefix}.{k}[{j}]',text=stable(value),evidence_ids=a['evidence_ids']))
 return out

def validate_extraction(value,doc):
 validate(value,EXTRACTION)
 assert value['family_id']==doc['family_id'],'family ID mismatch'
 valid={s['id'] for s in spans(doc)};seen=set()
 if not doc.get('abstract'):
  assert value['source_status']=='TITLE_ONLY' and not value['contributions'],'Title-only must abstain'
 for c in value['contributions']:
  assert c['local_id'] not in seen,'Duplicate local contribution ID';seen.add(c['local_id'])
  assert c['core_mechanism']['text'] and c['core_mechanism']['evidence_ids'],'Missing disclosed mechanism'
 for row in claims(value):
  assert row['evidence_ids'],'No field evidence '+row['path']
  assert set(row['evidence_ids'])<=valid,'Unknown source ID '+row['path']
 for c in value['contributions']:
  for k in ['technical_object','technical_problem','core_mechanism','implementation','split_reason']:
   if c[k]['text'] is None:assert not c[k]['evidence_ids'],'Null field with evidence'
  for step in c['process_steps']:
   if not step['sequence_explicit']:assert step['order'] is None,'Unsupported order marked present'
 if not value['contributions']:assert value['abstention_reason'],'Missing abstention reason'

def validate_facts(v,doc):
 assert v['family_id']==doc['family_id'];ids={s['id'] for s in spans(doc)}
 seen=set()
 for f in v['facts']:
  assert f['id'] not in seen;seen.add(f['id']);assert f['evidence_ids'] and set(f['evidence_ids'])<=ids,'Fact missing source ID'

def validate_audit(v,doc,extraction):
 assert v['family_id']==doc['family_id']
 paths=[x['path'] for x in claims(extraction)];actual=[x['path'] for x in v['field_audits']]
 assert len(actual)==len(set(actual)),'Duplicate audit path'
 assert set(paths)==set(actual),'Audit paths missing/extra: '+str(sorted(set(paths)^set(actual)))[:800]
 valid={s['id'] for s in spans(doc)}
 for a in v['field_audits']:assert set(a['evidence_ids'])<=valid,'Audit invented source ID'
 for a in v['missing_critical_materials']+v['missing_critical_processes']+v['errors']:assert set(a['evidence_ids'])<=valid,'Audit missing fact bad ID'
 assert v['oversplit_count']>=0 and v['hallucinated_contributions_count']>=0

def extract(doc,kind='full'):
 fid=doc['family_id'];si=source_input(doc)
 if kind=='extract_only':
  return call('extract_only',fid,prompt('extract_only'),si,EXTRACTION,lambda x:validate_extraction(x,doc))
 fa=call('facts',fid,prompt('facts'),si,FACTS,lambda x:validate_facts(x,doc),max_tokens=6000)
 return call('organize',fid,prompt('organize'),dict(source=si,stage_a_facts=fa['result']),EXTRACTION,lambda x:validate_extraction(x,doc))

def audit(doc,extraction,kind='audit'):
 return call(kind,doc['family_id'],prompt('audit'),dict(source=source_input(doc),candidate=extraction,claims=claims(extraction)),AUDIT,lambda x:validate_audit(x,doc,extraction),max_tokens=8000)

def full(doc):
 fid=doc['family_id'];original=extract(doc);aud=audit(doc,original['result']);adopt=original;finalaudit=aud;revisions=[]
 for cycle in range(1,3):
  if not finalaudit['result']['revision_required']:break
  revision=call('revision' if cycle==1 else 'revision_2',fid,prompt('revise'),dict(source=source_input(doc),original=adopt['result'],audit=finalaudit['result']),EXTRACTION,lambda x:validate_extraction(x,doc))
  nextaudit=audit(doc,revision['result'],'revision_audit' if cycle==1 else 'revision_2_audit')
  revisions.append(dict(request_id=revision['request_id'],result=revision['result'],audit_request_id=nextaudit['request_id'],audit=nextaudit['result'],adoption_reason='Model requested source-based correction; retained as candidate and independently re-audited'))
  finalaudit=nextaudit;adopt=revision
 unresolved=finalaudit['result']['revision_required'] or any(a['grade'] in ['Inferred','Unsupported'] for a in finalaudit['result']['field_audits']) or (bool(adopt['result']['contributions']) and finalaudit['result']['conclusion_grade'] in ['Partial','Inferred','Unsupported','Insufficient'])
 rel=call('relevance',fid,prompt('relevance'),dict(source=source_input(doc),extraction=adopt['result']),RELEVANCE,lambda x:validate_rel(x,doc),max_tokens=3500)
 rec=dict(family_id=fid,status='QUARANTINED' if unresolved else 'VALID',version='D3.1',original_request_id=original['request_id'],audit_request_id=aud['request_id'],revision_request_id=revisions[-1]['request_id'] if revisions else None,final_request_id=adopt['request_id'],final_audit_request_id=finalaudit['request_id'],adoption_reason='Bounded source-based model revisions, independently audited' if revisions else 'Independent audit did not request revision',original=original['result'],audit=aud['result'],revisions=revisions,revision=revisions[-1]['result'] if revisions else None,final=adopt['result'],final_audit=finalaudit['result'],relevance=rel['result'],relevance_request_id=rel['request_id'],source_text_hash=doc['text_hash'],at=now())
 path='working/main/'+fid.replace(':','_')+'.json'
 if (W/path).exists():
  previous=load(path)
  if previous['final_request_id']!=rec['final_request_id'] or previous['final_audit_request_id']!=rec['final_audit_request_id']:save('working/main_history/'+fid.replace(':','_')+'/'+oh(previous)+'.json',previous)
 save(path,rec);return rec

def validate_rel(x,doc):
 assert x['family_id']==doc['family_id'];ids={s['id'] for s in spans(doc)};a=x['document_evidence'];assert set(a['evidence_ids'])<=ids,'Relevance source IDs invalid'
 if x['axis_a'] in ['A1','A2','A3']:assert a['text'] and a['evidence_ids'],'Explicit application needs source evidence'
 if x['axis_b']=='B3':assert x['engineering_inference'] and x['key_conditions'],'Transfer needs mechanism and conditions'

# D2 archive is the primary baseline; replay is separate and never conflated with original Qwen.
def d2_replay(doc):
 spec=importlib.util.spec_from_file_location('frozen_d2_schema',W/'inputs/d2_code/scripts/schema.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 src=module.make_source_spans(doc);schema=module.source_id_schema(module.EXTRACTION_WIRE_SCHEMA,src)
 tree=ast.parse((W/'inputs/d2_code/scripts/extract.py').read_text())
 literals=[x.value for x in ast.walk(tree) if isinstance(x,ast.Constant) and isinstance(x.value,str) and x.value.startswith('\n本次采用原文片段ID传输')]
 assert len(literals)==1
 p=(W/'inputs/d2_code/prompts/extraction_v2.txt').read_text()+literals[0]+json.dumps(schema,ensure_ascii=False)
 inp=dict(family_id=doc['family_id'],source_spans=[{k:v for k,v in s.items() if k not in ['start','end']} for s in src])
 def check(v):
  module.canonical_from_source_ids(v,schema,src)
 r=call('d2_prompt_replay',doc['family_id'],p,inp,schema,check,max_tokens=2200)
 c,_=module.canonical_from_source_ids(r['result'],schema,src)
 return dict(result=c,request_id=r['request_id'],baseline='D2 exact source-ID prompt/schema and 2200 output cap replayed on DeepSeek; not original Qwen backend')

def selection(stage):
 lock=load('inputs/SPLIT_LOCK.json');docs=load('inputs/ALL_DOCUMENTS.json');dm={d['family_id']:d for d in docs}
 if stage=='pilot30':ids=lock['pilot30']
 elif stage=='development':ids=lock['development']
 elif stage=='holdout':
  assert (W/'evidence/MODEL_FREEZE.json').exists(),'Holdout forbidden before final freeze';ids=lock['holdout']
 elif stage=='main':
  assert (W/'evidence/MODEL_FREEZE.json').exists(),'Main run forbidden before final freeze';ids=list(dm)
 else:raise ValueError(stage)
 return [dm[f] for f in ids]

def run(stage,mode,workers=8):
 guard();docs=selection(stage)
 if stage in ['holdout','main']:
  freeze=load('evidence/MODEL_FREEZE.json')
  for path,h in freeze['semantic_code_hashes'].items():assert sha(W/path)==h,'Frozen semantic code changed: '+path
 event('batch_start',stage=stage,mode=mode,required=len(docs),workers=workers)
 fn={'full':full,'extract_only':lambda d:extract(d,'extract_only'),'d2_replay':d2_replay}[mode]
 result=[]
 def task(d):
  f=d['family_id']
  try:
   r=fn(d);status=r.get('status','VALID');row=dict(family_id=f,status=status,mode=mode,stage=stage)
   if mode!='full':save('working/'+mode+'/'+f.replace(':','_')+'.json',r)
  except Exception as e:row=dict(family_id=f,status='FAILED',mode=mode,stage=stage,error=type(e).__name__+': '+str(e)[:1000])
  save('working/status/'+mode+'_'+f.replace(':','_')+'.json',row);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
  for row in pool.map(task,docs):
   result.append(row)
   if len(result)%10==0 or row['status']=='FAILED':event('batch_progress',stage=stage,mode=mode,finished=len(result),total=len(docs),counts=dict(collections.Counter(x['status'] for x in result)),last=row['family_id'],error=row.get('error'))
 save('evidence/BATCH_'+stage+'_'+mode+'.json',dict(at=now(),results=result,counts=dict(collections.Counter(r['status'] for r in result))))
 event('batch_done',stage=stage,mode=mode,counts=dict(collections.Counter(r['status'] for r in result)))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['pilot30','development','holdout','main'],required=True);p.add_argument('--mode',choices=['full','extract_only','d2_replay'],default='full');p.add_argument('--workers',type=int,default=8);a=p.parse_args();run(a.stage,a.mode,a.workers)
